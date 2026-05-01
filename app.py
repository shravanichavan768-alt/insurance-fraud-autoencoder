
# app.py
from flask import Flask, request, jsonify, render_template
import numpy as np
import joblib
import tensorflow as tf
from datetime import datetime
from db import init_db, get_policy_by_number, save_new_claim, get_stats, get_claim

app = Flask(__name__)

init_db()

# Load models
scaler = joblib.load('models/scaler.pkl')
iso_forest = joblib.load('models/isolation_forest.pkl')
xgb_model = joblib.load('models/xgboost_model.pkl')
autoencoder = tf.keras.models.load_model(
    'models/autoencoder_model.h5',
    custom_objects={'mse': tf.keras.losses.MeanSquaredError()}
)
best_threshold = joblib.load('models/threshold.pkl')

print(f"Best Threshold loaded: {best_threshold:.4f}")

@app.route('/')
def home():
    stats = get_stats()
    return render_template('index.html', stats=stats)

@app.route('/lookup_policy', methods=['POST'])
def lookup_policy():
    """Look up policy from database"""
    data = request.json
    policy_number = data.get('policy_number', '').strip().upper()

    policy, past_claims = get_policy_by_number(policy_number)

    if not policy:
        return jsonify({'error': f'Policy {policy_number} not found!'}), 404

    # Calculate derived features from history
    now = datetime.now()
    policy_start = datetime.strptime(policy['policy_start_date'], '%Y-%m-%d')
    policy_age_months = max(1, (now - policy_start).days // 30)

    # Claims in last year
    num_claims_last_year = sum(
        1 for c in past_claims
        if (now - datetime.strptime(c['treatment_date'], '%Y-%m-%d')).days <= 365
    )

    # Average claim amount
    avg_claim = np.mean([c['claim_amount'] for c in past_claims]) if past_claims else 0

    return jsonify({
        'found': True,
        'policy_number': policy['policy_number'],
        'patient_name': policy['patient_name'],
        'patient_age': policy['patient_age'],
        'policy_start_date': policy['policy_start_date'],
        'policy_age_months': policy_age_months,
        'monthly_premium': policy['monthly_premium'],
        'coverage_amount': policy['coverage_amount'],
        'num_claims_last_year': num_claims_last_year,
        'total_past_claims': len(past_claims),
        'avg_past_claim': round(avg_claim, 2),
        'past_claims': [dict(c) for c in past_claims[:5]]
    })

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json

    policy_number = data['policy_number']
    policy, past_claims = get_policy_by_number(policy_number)

    # Calculate derived features
    now = datetime.now()
    policy_start = datetime.strptime(policy['policy_start_date'], '%Y-%m-%d')
    policy_age_months = max(1, (now - policy_start).days // 30)

    num_claims_last_year = sum(
        1 for c in past_claims
        if (now - datetime.strptime(c['treatment_date'], '%Y-%m-%d')).days <= 365
    )

    claim_amount = float(data['claim_amount'])
    monthly_premium = policy['monthly_premium']
    claim_to_premium_ratio = round(
        claim_amount / max(1, monthly_premium * policy_age_months), 4)

    # Check duplicate
    is_duplicate = 1 if any(
        abs(c['claim_amount'] - claim_amount) < 1000 and
        c['hospital_name'] == data['hospital_name']
        for c in past_claims
    ) else 0

    hospital_stay_days = int(data['hospital_stay_days'])
    num_procedures = max(1, int(hospital_stay_days * 0.8))
    num_diagnoses = int(data.get('num_diagnoses', 2))
    doctor_experience_years = int(data.get('doctor_experience_years', 10))
    patient_age = policy['patient_age']

    # Build feature vector
    features = np.array([[
        claim_amount,
        hospital_stay_days,
        num_procedures,
        num_diagnoses,
        doctor_experience_years,
        num_claims_last_year,
        policy_age_months,
        claim_to_premium_ratio,
        is_duplicate,
        patient_age,
        monthly_premium
    ]])

    features_scaled = scaler.transform(features)

    # Autoencoder
    reconstruction = autoencoder.predict(features_scaled, verbose=0)
    recon_error = float(np.mean(np.power(features_scaled - reconstruction, 2)))
    ae_pred = 'FRAUD' if recon_error > best_threshold else 'LEGIT'

    # Isolation Forest
    iso_raw = iso_forest.predict(features_scaled)
    iso_pred = 'FRAUD' if iso_raw[0] == -1 else 'LEGIT'

    # XGBoost
    xgb_raw = xgb_model.predict(features_scaled)
    xgb_proba = xgb_model.predict_proba(features_scaled)[0][1]
    xgb_pred = 'FRAUD' if xgb_raw[0] == 1 else 'LEGIT'

    # Weighted voting
    fraud_votes = [ae_pred, iso_pred, xgb_pred].count('FRAUD')
    final = 'FRAUD' if fraud_votes >= 2 else 'LEGIT'
    fraud_score = round((xgb_proba * 0.5 +
                        (recon_error/best_threshold) * 0.3 +
                        (fraud_votes/3) * 0.2) * 100)
    fraud_score = min(100, max(0, fraud_score))

    # Save to database
    save_new_claim({
        'policy_number': policy_number,
        'patient_name': policy['patient_name'],
        'patient_age': patient_age,
        'hospital_name': data['hospital_name'],
        'diagnosis_type': data['diagnosis_type'],
        'claim_amount': claim_amount,
        'hospital_stay_days': hospital_stay_days,
        'num_procedures': num_procedures,
        'num_diagnoses': num_diagnoses,
        'doctor_experience_years': doctor_experience_years,
        'num_claims_last_year': num_claims_last_year,
        'policy_age_months': policy_age_months,
        'claim_to_premium_ratio': claim_to_premium_ratio,
        'is_duplicate_claim': is_duplicate,
        'treatment_date': datetime.now().strftime('%Y-%m-%d'),
        'monthly_premium': monthly_premium,
        'verdict': 1 if final == 'FRAUD' else 0
    })

    return jsonify({
        'autoencoder': ae_pred,
        'isolation_forest': iso_pred,
        'xgboost': xgb_pred,
        'reconstruction_error': round(recon_error, 4),
        'final_verdict': final,
        'fraud_score': fraud_score,
        'derived_features': {
            'num_claims_last_year': num_claims_last_year,
            'policy_age_months': policy_age_months,
            'claim_to_premium_ratio': claim_to_premium_ratio,
            'is_duplicate': is_duplicate,
            'num_procedures': num_procedures
        }
    })

if __name__ == '__main__':
    app.run(debug=True)

# app.py
from flask import Flask, request, jsonify, render_template
import numpy as np
import joblib
import tensorflow as tf
from db import init_db, get_claim, get_stats, save_new_claim

app = Flask(__name__)

# Initialize database
init_db()

# Load models
scaler = joblib.load('models/scaler.pkl')
iso_forest = joblib.load('models/isolation_forest.pkl')
xgb_model = joblib.load('models/xgboost_model.pkl')
autoencoder = tf.keras.models.load_model(
    'models/autoencoder_model.h5',
    custom_objects={'mse': tf.keras.losses.MeanSquaredError()}
)

THRESHOLD = 2.5543

@app.route('/')
def home():
    stats = get_stats()
    return render_template('index.html', stats=stats)

@app.route('/lookup', methods=['POST'])
def lookup():
    """Look up claim from database by claim ID"""
    data = request.json
    claim_id = data.get('claim_id')

    claim = get_claim(claim_id)
    if not claim:
        return jsonify({'error': 'Claim ID not found in database'}), 404

    return jsonify({
        'found': True,
        'claim_id': claim['claim_id'],
        'patient_age': claim['patient_age'],
        'claim_amount': claim['claim_amount'],
        'num_procedures': claim['num_procedures'],
        'hospital_stay_days': claim['hospital_stay_days'],
        'num_claims_last_year': claim['num_claims_last_year'],
        'doctor_experience_years': claim['doctor_experience_years'],
        'is_duplicate_claim': claim['is_duplicate_claim'],
        'claim_approved_quickly': claim['claim_approved_quickly'],
        'num_diagnoses': claim['num_diagnoses'],
        'patient_income_level': claim['patient_income_level'],
        'policy_age_months': claim['policy_age_months'],
        'actual_class': claim['Class']
    })

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json

    features = np.array([[
        data['patient_age'],
        data['claim_amount'],
        data['num_procedures'],
        data['hospital_stay_days'],
        data['num_claims_last_year'],
        data['doctor_experience_years'],
        data['is_duplicate_claim'],
        data['claim_approved_quickly'],
        data['num_diagnoses'],
        data['patient_income_level'],
        data['policy_age_months']
    ]])

    features_scaled = scaler.transform(features)

    # Autoencoder
    reconstruction = autoencoder.predict(features_scaled, verbose=0)
    recon_error = float(np.mean(np.power(features_scaled - reconstruction, 2)))
    ae_pred = 'FRAUD' if recon_error > THRESHOLD else 'LEGIT'

    # Isolation Forest
    iso_raw = iso_forest.predict(features_scaled)
    iso_pred = 'FRAUD' if iso_raw[0] == -1 else 'LEGIT'

    # XGBoost
    xgb_raw = xgb_model.predict(features_scaled)
    xgb_pred = 'FRAUD' if xgb_raw[0] == 1 else 'LEGIT'

    # Majority voting
    votes = [ae_pred, iso_pred, xgb_pred].count('FRAUD')
    final = 'FRAUD' if votes >= 2 else 'LEGIT'
    fraud_score = round((votes / 3) * 100)

    # Save to database
    save_new_claim({
        'patient_age': data['patient_age'],
        'claim_amount': data['claim_amount'],
        'num_procedures': data['num_procedures'],
        'hospital_stay_days': data['hospital_stay_days'],
        'num_claims_last_year': data['num_claims_last_year'],
        'doctor_experience_years': data['doctor_experience_years'],
        'is_duplicate_claim': data['is_duplicate_claim'],
        'claim_approved_quickly': data['claim_approved_quickly'],
        'num_diagnoses': data['num_diagnoses'],
        'patient_income_level': data['patient_income_level'],
        'policy_age_months': data['policy_age_months'],
        'verdict': 1 if final == 'FRAUD' else 0
    })

    return jsonify({
        'autoencoder': ae_pred,
        'isolation_forest': iso_pred,
        'xgboost': xgb_pred,
        'reconstruction_error': round(recon_error, 4),
        'final_verdict': final,
        'fraud_score': fraud_score
    })

if __name__ == '__main__':
    app.run(debug=True)
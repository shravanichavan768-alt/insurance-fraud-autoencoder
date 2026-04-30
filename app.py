
from flask import Flask, request, jsonify, render_template
import numpy as np
import joblib
import tensorflow as tf
import random
import hashlib

app = Flask(__name__)

# Load models
scaler = joblib.load('models/scaler.pkl')
iso_forest = joblib.load('models/isolation_forest.pkl')
xgb_model = joblib.load('models/xgboost_model.pkl')
autoencoder = tf.keras.models.load_model(
    'models/autoencoder_model.h5',
    custom_objects={'mse': tf.keras.losses.MeanSquaredError()}
)

THRESHOLD = 2.5543

def simulate_patient_history(policy_number, claim_amount, days):
    """Simulate pulling patient history from database using policy number"""
    
    # Use policy number as seed for consistent results
    seed = int(hashlib.md5(policy_number.encode()).hexdigest(), 16) % 10000
    rng = random.Random(seed)

    # Simulate internal flags based on policy number patterns
    policy_age_months = rng.randint(1, 240)
    num_claims_last_year = rng.randint(0, 15)
    doctor_experience_years = rng.randint(1, 35)
    num_procedures = max(1, int(days * rng.uniform(0.8, 2.5)))
    num_diagnoses = rng.randint(1, 6)
    patient_income_level = rng.randint(1, 5)
    is_duplicate_claim = 1 if num_claims_last_year > 8 else 0
    claim_approved_quickly = 1 if policy_age_months < 6 else rng.randint(0, 1)

    return {
        'policy_age_months': policy_age_months,
        'num_claims_last_year': num_claims_last_year,
        'doctor_experience_years': doctor_experience_years,
        'num_procedures': num_procedures,
        'num_diagnoses': num_diagnoses,
        'patient_income_level': patient_income_level,
        'is_duplicate_claim': is_duplicate_claim,
        'claim_approved_quickly': claim_approved_quickly
    }

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json

    # Get user inputs
    patient_age = int(data['patient_age'])
    claim_amount = float(data['claim_amount'])
    hospital_stay_days = int(data['hospital_stay_days'])
    policy_number = data['policy_number']

    # Simulate pulling history from database
    history = simulate_patient_history(policy_number, claim_amount, hospital_stay_days)

    # Build feature vector
    features = np.array([[
        patient_age,
        claim_amount,
        history['num_procedures'],
        hospital_stay_days,
        history['num_claims_last_year'],
        history['doctor_experience_years'],
        history['is_duplicate_claim'],
        history['claim_approved_quickly'],
        history['num_diagnoses'],
        history['patient_income_level'],
        history['policy_age_months']
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

    return jsonify({
        'autoencoder': ae_pred,
        'isolation_forest': iso_pred,
        'xgboost': xgb_pred,
        'reconstruction_error': round(recon_error, 4),
        'final_verdict': final,
        'fraud_score': fraud_score,
        'history': history
    })

if __name__ == '__main__':
    app.run(debug=True)
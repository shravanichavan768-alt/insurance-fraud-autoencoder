# app.py
from flask import Flask, request, jsonify, render_template
import numpy as np
import joblib
import tensorflow as tf

app = Flask(__name__)

# Load models
scaler = joblib.load('models/scaler.pkl')
iso_forest = joblib.load('models/isolation_forest.pkl')
xgb_model = joblib.load('models/xgboost_model.pkl')
autoencoder = tf.keras.models.load_model('models/autoencoder_model.h5')

THRESHOLD = 2.5543

@app.route('/')
def home():
    return render_template('index.html')

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
    reconstruction = autoencoder.predict(features_scaled)
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

    return jsonify({
        'autoencoder': ae_pred,
        'isolation_forest': iso_pred,
        'xgboost': xgb_pred,
        'reconstruction_error': round(recon_error, 4),
        'final_verdict': final
    })

if __name__ == '__main__':
    app.run(debug=True)
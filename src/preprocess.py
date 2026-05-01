# src/preprocess.py
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib
import os

FEATURE_COLS = [
    'claim_amount',
    'hospital_stay_days',
    'num_procedures',
    'num_diagnoses',
    'doctor_experience_years',
    'num_claims_last_year',
    'policy_age_months',
    'claim_to_premium_ratio',
    'is_duplicate_claim',
    'patient_age',
    'monthly_premium'
]

def load_data(filepath='data/insurance_fraud_dataset.csv'):
    df = pd.read_csv(filepath)
    print(f"Dataset loaded: {df.shape}")
    print(f"Fraud rate: {df['Class'].mean()*100:.2f}%")
    return df

def preprocess(df):
    X = df[FEATURE_COLS]
    y = df['Class']

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    X_scaled = pd.DataFrame(X_scaled, columns=FEATURE_COLS)

    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.2, random_state=42, stratify=y)

    X_train_legit = X_train[y_train == 0]

    os.makedirs('models', exist_ok=True)
    joblib.dump(scaler, 'models/scaler.pkl')

    print(f"Train: {X_train.shape}, Test: {X_test.shape}")
    print(f"Legit only (Autoencoder): {X_train_legit.shape}")
    return X_train, X_test, y_train, y_test, X_train_legit, scaler

if __name__ == "__main__":
    df = load_data()
    preprocess(df)
    print("Preprocessing complete ")
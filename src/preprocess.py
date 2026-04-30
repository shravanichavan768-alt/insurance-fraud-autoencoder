
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib
import os

def load_data(filepath='data/insurance_fraud_dataset.csv'):
    df = pd.read_csv(filepath)
    print(f"Dataset loaded: {df.shape}")
    return df

def preprocess(df):
    df_model = df.drop('claim_id', axis=1)
    X = df_model.drop('Class', axis=1)
    y = df_model['Class']

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    X_scaled = pd.DataFrame(X_scaled, columns=X.columns)

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
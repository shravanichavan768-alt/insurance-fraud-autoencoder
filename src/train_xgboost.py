
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from xgboost import XGBClassifier
from sklearn.metrics import (classification_report, confusion_matrix,
                             roc_auc_score, roc_curve)
import joblib
import os

def train_xgboost(X_train, y_train, fraud_rate=0.07):
    scale = int((1 - fraud_rate) / fraud_rate)
    
    xgb_model = XGBClassifier(
        n_estimators=100,
        scale_pos_weight=scale,
        learning_rate=0.1,
        max_depth=5,
        random_state=42,
        eval_metric='logloss',
        verbosity=0
    )
    xgb_model.fit(X_train, y_train)
    print("XGBoost trained ")
    return xgb_model

def evaluate_xgboost(xgb_model, X_test, y_test):
    xgb_pred = xgb_model.predict(X_test)
    xgb_pred_proba = xgb_model.predict_proba(X_test)[:, 1]

    print("XGBoost Results:")
    print(classification_report(y_test, xgb_pred,
          target_names=['Legitimate', 'Fraud']))

    # Confusion Matrix
    os.makedirs('outputs', exist_ok=True)
    cm = confusion_matrix(y_test, xgb_pred)
    plt.figure(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Oranges',
                xticklabels=['Legitimate', 'Fraud'],
                yticklabels=['Legitimate', 'Fraud'])
    plt.title('XGBoost - Confusion Matrix')
    plt.ylabel('Actual')
    plt.xlabel('Predicted')
    plt.tight_layout()
    plt.savefig('outputs/xgboost_cm.png', dpi=150)
    plt.close()

    roc = roc_auc_score(y_test, xgb_pred_proba)
    print(f"XGBoost ROC-AUC: {roc:.4f}")
    return xgb_pred, xgb_pred_proba, roc

def save_xgboost(model, path='models/xgboost_model.pkl'):
    os.makedirs('models', exist_ok=True)
    joblib.dump(model, path)
    print(f"XGBoost saved to {path} ")

def load_xgboost(path='models/xgboost_model.pkl'):
    model = joblib.load(path)
    print(f"XGBoost loaded from {path} ")
    return model

if __name__ == "__main__":
    print("XGBoost module ready ")
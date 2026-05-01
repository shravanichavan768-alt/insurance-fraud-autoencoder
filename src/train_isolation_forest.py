# src/train_isolation_forest.py
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import IsolationForest
from sklearn.metrics import (classification_report, confusion_matrix,
                             roc_auc_score)
import joblib
import os

def train_isolation_forest(X_train, contamination=0.13):
    iso_forest = IsolationForest(
        n_estimators=100,
        contamination=contamination,
        random_state=42,
        n_jobs=-1
    )
    iso_forest.fit(X_train)
    print("Isolation Forest trained ")
    return iso_forest

def evaluate_isolation_forest(iso_forest, X_test, y_test):
    iso_pred_raw = iso_forest.predict(X_test)
    iso_pred = np.where(iso_pred_raw == -1, 1, 0)

    print("Isolation Forest Results:")
    print(classification_report(y_test, iso_pred,
          target_names=['Legitimate', 'Fraud']))

    os.makedirs('outputs', exist_ok=True)
    cm = confusion_matrix(y_test, iso_pred)
    plt.figure(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=['Legitimate', 'Fraud'],
                yticklabels=['Legitimate', 'Fraud'])
    plt.title('Isolation Forest - Confusion Matrix')
    plt.ylabel('Actual')
    plt.xlabel('Predicted')
    plt.tight_layout()
    plt.savefig('outputs/iso_forest_cm.png', dpi=150)
    plt.close()

    roc = roc_auc_score(y_test, iso_pred)
    print(f"Isolation Forest ROC-AUC: {roc:.4f}")
    return iso_pred, roc

def save_isolation_forest(model, path='models/isolation_forest.pkl'):
    os.makedirs('models', exist_ok=True)
    joblib.dump(model, path)
    print(f"Isolation Forest saved ")

def load_isolation_forest(path='models/isolation_forest.pkl'):
    model = joblib.load(path)
    print(f"Isolation Forest loaded ")
    return model

if __name__ == "__main__":
    print("Isolation Forest module ready ")
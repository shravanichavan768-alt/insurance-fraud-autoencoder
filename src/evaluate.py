# src/evaluate.py
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (roc_curve, roc_auc_score,
                             f1_score, classification_report)
import os

def find_best_threshold(reconstruction_error, y_test):
    thresholds = np.percentile(reconstruction_error, np.arange(50, 100, 0.5))
    f1_scores = []
    for thresh in thresholds:
        y_pred = (reconstruction_error > thresh).astype(int)
        f1_scores.append(f1_score(y_test, y_pred))
    best_threshold = thresholds[np.argmax(f1_scores)]
    best_f1 = max(f1_scores)
    print(f"Best Threshold: {best_threshold:.4f}")
    print(f"Best F1 Score: {best_f1:.4f}")
    return best_threshold, best_f1

def plot_reconstruction_error(reconstruction_error, y_test, best_threshold):
    os.makedirs('outputs', exist_ok=True)
    plt.figure(figsize=(8, 5))
    plt.hist(reconstruction_error[y_test == 0], bins=50,
             alpha=0.7, label='Legitimate', color='#2ecc71')
    plt.hist(reconstruction_error[y_test == 1], bins=50,
             alpha=0.7, label='Fraud', color='#e74c3c')
    plt.axvline(x=best_threshold, color='blue', linestyle='--',
                label=f'Threshold: {best_threshold:.3f}')
    plt.title('Reconstruction Error Distribution')
    plt.xlabel('Reconstruction Error')
    plt.ylabel('Count')
    plt.legend()
    plt.tight_layout()
    plt.savefig('outputs/reconstruction_error.png', dpi=150)
    plt.close()
    print("Reconstruction error plot saved ")

def plot_roc_curves(y_test, reconstruction_error,
                   xgb_pred_proba, iso_pred,
                   ae_roc, xgb_roc, iso_roc):
    os.makedirs('outputs', exist_ok=True)
    plt.figure(figsize=(8, 6))

    fpr_ae, tpr_ae, _ = roc_curve(y_test, reconstruction_error)
    plt.plot(fpr_ae, tpr_ae,
             label=f'Autoencoder (AUC={ae_roc:.4f})',
             color='#3498db')

    fpr_xgb, tpr_xgb, _ = roc_curve(y_test, xgb_pred_proba)
    plt.plot(fpr_xgb, tpr_xgb,
             label=f'XGBoost (AUC={xgb_roc:.4f})',
             color='#e74c3c')

    fpr_iso, tpr_iso, _ = roc_curve(y_test, iso_pred)
    plt.plot(fpr_iso, tpr_iso,
             label=f'Isolation Forest (AUC={iso_roc:.4f})',
             color='#2ecc71')

    plt.plot([0, 1], [0, 1], 'k--', label='Random')
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('ROC Curves - All Models')
    plt.legend()
    plt.tight_layout()
    plt.savefig('outputs/roc_curves.png', dpi=150)
    plt.close()
    print("ROC curves saved ")

def plot_model_comparison(ae_f1, iso_f1, xgb_f1,
                          ae_roc, iso_roc, xgb_roc):
    os.makedirs('outputs', exist_ok=True)
    models = ['Autoencoder\n(Deep Learning)',
              'Isolation Forest\n(Unsupervised)',
              'XGBoost\n(Supervised)']
    f1_scores = [ae_f1, iso_f1, xgb_f1]
    roc_scores = [ae_roc, iso_roc, xgb_roc]
    x = np.arange(len(models))

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle('Insurance Fraud Detection - Model Comparison',
                 fontsize=14, fontweight='bold')

    bars1 = axes[0].bar(x, f1_scores, 0.35,
                        color='#3498db', alpha=0.8)
    axes[0].set_title('F1 Score Comparison (Fraud Class)')
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(models)
    axes[0].set_ylim(0, 1.1)
    for bar in bars1:
        axes[0].text(bar.get_x() + bar.get_width()/2.,
                    bar.get_height() + 0.02,
                    f'{bar.get_height():.4f}',
                    ha='center', fontweight='bold')

    bars2 = axes[1].bar(x, roc_scores, 0.35,
                        color='#e74c3c', alpha=0.8)
    axes[1].set_title('ROC-AUC Comparison')
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(models)
    axes[1].set_ylim(0, 1.1)
    for bar in bars2:
        axes[1].text(bar.get_x() + bar.get_width()/2.,
                    bar.get_height() + 0.02,
                    f'{bar.get_height():.4f}',
                    ha='center', fontweight='bold')

    plt.tight_layout()
    plt.savefig('outputs/model_comparison.png', dpi=150)
    plt.close()
    print("Model comparison saved ")

if __name__ == "__main__":
    print("Evaluate module ready ")
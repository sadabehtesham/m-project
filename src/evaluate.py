"""
Shared evaluation/plotting helpers, used across all 5 disease
04_evaluation.ipynb notebooks. Extracts the repeated ROC curve,
feature importance, and confusion matrix plotting into reusable
functions instead of copy-pasting the same matplotlib code 5 times.
"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from sklearn.metrics import (
    roc_curve, roc_auc_score, confusion_matrix, classification_report
)


def print_classification_report(y_test, y_pred, target_names=("Negative", "Positive")):
    print(classification_report(y_test, y_pred, target_names=list(target_names)))


def plot_roc_curve(y_test, y_proba, title="ROC Curve", save_path=None):
    """Plots and optionally saves an ROC curve. Returns the AUC score."""
    fpr, tpr, _ = roc_curve(y_test, y_proba)
    auc = roc_auc_score(y_test, y_proba)

    plt.figure(figsize=(6, 6))
    plt.plot(fpr, tpr, label=f"Model (AUC = {auc:.3f})")
    plt.plot([0, 1], [0, 1], linestyle="--", color="gray", label="Random guess")
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title(title)
    plt.legend()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.show()

    return auc


def plot_feature_importance(model, feature_names, title="Feature importance", save_path=None):
    """Plots feature importances (tree-based models) or coefficients
    (linear models like Logistic Regression). Returns None if the
    model exposes neither."""
    if hasattr(model, "feature_importances_"):
        importances = pd.Series(model.feature_importances_, index=feature_names)
    elif hasattr(model, "coef_"):
        importances = pd.Series(model.coef_[0], index=feature_names)
    else:
        print("This model type doesn't expose feature importances directly.")
        return None

    importances = importances.sort_values(ascending=True)
    plt.figure(figsize=(8, max(4, len(feature_names) * 0.3)))
    importances.plot(kind="barh")
    plt.title(title)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.show()

    return importances


def plot_confusion_matrix(y_test, y_pred, labels=("Negative", "Positive"),
                           title="Confusion Matrix", save_path=None):
    cm = confusion_matrix(y_test, y_pred)

    plt.figure(figsize=(5, 4))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
                xticklabels=list(labels), yticklabels=list(labels))
    plt.xlabel("Predicted")
    plt.ylabel("Actual")
    plt.title(title)

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.show()

    return cm

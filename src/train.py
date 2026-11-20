"""
Shared model training/comparison logic, used across all 5 disease
03_model_training.ipynb notebooks. Extracts the repeated "train
several models, compare metrics, pick the best" pattern into one
reusable function.
"""

import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
)

try:
    from xgboost import XGBClassifier
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False


def get_candidate_models(random_state=42):
    """Returns the standard set of models compared for every disease.
    Kept as a function (not a module-level constant) so each call
    gets fresh, unfitted model instances."""
    models = {
        "Logistic Regression": LogisticRegression(max_iter=1000, random_state=random_state),
        "Decision Tree": DecisionTreeClassifier(random_state=random_state),
        "Random Forest": RandomForestClassifier(n_estimators=200, random_state=random_state),
    }
    if HAS_XGBOOST:
        models["XGBoost"] = XGBClassifier(
            use_label_encoder=False, eval_metric="logloss", random_state=random_state
        )
    return models


def train_and_compare(X_train, y_train, X_test, y_test, models=None):
    """
    Trains each candidate model, evaluates on the test set, and
    returns (results_df, fitted_models_dict) sorted by ROC-AUC
    (descending) -- the same metric used to auto-pick the best model
    in every disease notebook.
    """
    if models is None:
        models = get_candidate_models()

    results = []

    for name, model in models.items():
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        y_proba = model.predict_proba(X_test)[:, 1]

        results.append({
            "Model": name,
            "Accuracy": accuracy_score(y_test, y_pred),
            "Precision": precision_score(y_test, y_pred),
            "Recall": recall_score(y_test, y_pred),
            "F1": f1_score(y_test, y_pred),
            "ROC-AUC": roc_auc_score(y_test, y_proba),
        })

    results_df = pd.DataFrame(results).sort_values("ROC-AUC", ascending=False).reset_index(drop=True)
    return results_df, models


def get_best_model(results_df, fitted_models):
    """Returns (best_model_name, best_model_object) using the top row
    of a results_df produced by train_and_compare (already sorted by
    ROC-AUC descending)."""
    best_name = results_df.iloc[0]["Model"]
    return best_name, fitted_models[best_name]

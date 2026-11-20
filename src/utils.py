"""
Misc helper functions used across the project -- mainly saving and
loading trained models/scalers consistently, so both the training
notebooks and the Flask app (src/predict.py) use the exact same
file-naming convention.
"""

import os
import joblib

MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "models")
PROCESSED_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")


def save_model_and_scaler(model, scaler, disease_key, models_dir=MODELS_DIR):
    """Saves a trained model + its scaler using the naming convention
    the rest of the project (src/predict.py) expects:
    <disease_key>_model.pkl and <disease_key>_scaler.pkl"""
    os.makedirs(models_dir, exist_ok=True)
    model_path = os.path.join(models_dir, f"{disease_key}_model.pkl")
    scaler_path = os.path.join(models_dir, f"{disease_key}_scaler.pkl")

    joblib.dump(model, model_path)
    joblib.dump(scaler, scaler_path)

    print(f"Saved {model_path}")
    print(f"Saved {scaler_path}")
    return model_path, scaler_path


def load_model_and_scaler(disease_key, models_dir=MODELS_DIR):
    """Loads a previously saved model + scaler for one disease."""
    model_path = os.path.join(models_dir, f"{disease_key}_model.pkl")
    scaler_path = os.path.join(models_dir, f"{disease_key}_scaler.pkl")

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"No trained model found at {model_path}")
    if not os.path.exists(scaler_path):
        raise FileNotFoundError(f"No scaler found at {scaler_path}")

    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path)
    return model, scaler


def save_processed_splits(disease_key, X_train, X_test, y_train, y_test,
                            processed_dir=PROCESSED_DATA_DIR):
    """Saves train/test splits with the naming convention used across
    all 5 disease preprocessing notebooks."""
    os.makedirs(processed_dir, exist_ok=True)
    X_train.to_csv(os.path.join(processed_dir, f"{disease_key}_X_train.csv"), index=False)
    X_test.to_csv(os.path.join(processed_dir, f"{disease_key}_X_test.csv"), index=False)
    y_train.to_csv(os.path.join(processed_dir, f"{disease_key}_y_train.csv"), index=False)
    y_test.to_csv(os.path.join(processed_dir, f"{disease_key}_y_test.csv"), index=False)
    print(f"Saved train/test splits for {disease_key} to {processed_dir}")

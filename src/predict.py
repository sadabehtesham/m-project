"""
Loads all 5 trained models + scalers, and turns one unified patient
data dict (from the health form) into 5 risk predictions.

Each disease's model was trained on ITS OWN dataset's columns, in
THAT dataset's original order. This module maps the unified form
field names back into each disease's exact expected column order
before scaling and predicting -- get the order wrong and the model
will silently give garbage predictions (no error, just wrong numbers),
so FEATURE_MAPS below must exactly match the column order each
02_preprocessing.ipynb produced.
"""

import os
import joblib

MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "models")

# Each entry: (column_name_the_model_expects, form_field_name_to_read_it_from)
# Order matters -- must match X.columns from each disease's
# 02_preprocessing.ipynb, in that exact order.

FEATURE_MAPS = {
    "diabetes": [
        ("Pregnancies", "pregnancies"),
        ("Glucose", "glucose"),
        ("BloodPressure", "resting_bp_diastolic"),
        ("SkinThickness", "skin_thickness"),
        ("Insulin", "insulin"),
        ("BMI", "bmi"),
        ("DiabetesPedigreeFunction", "family_diabetes_score"),
        ("Age", "age"),
    ],
    "heart_disease": [
        ("age", "age"),
        ("sex", "gender"),
        ("cp", "chest_pain_type"),
        ("trestbps", "resting_bp_systolic"),
        ("chol", "total_cholesterol"),
        ("fbs", "fasting_blood_sugar_high"),
        ("restecg", "resting_ecg"),
        ("thalach", "max_heart_rate"),
        ("exang", "exercise_angina"),
        ("oldpeak", "st_depression"),
        ("slope", "st_slope"),
        ("ca", "major_vessels"),
        ("thal", "thalassemia"),
    ],
    "ckd": [
        ("age", "age"),
        ("bp", "resting_bp_diastolic"),
        ("sg", "urine_specific_gravity"),
        ("al", "urine_albumin"),
        ("su", "urine_sugar"),
        ("rbc", "rbc_in_urine"),
        ("pc", "pus_cell"),
        ("pcc", "pus_cell_clumps"),
        ("ba", "bacteria"),
        ("bgr", "glucose"),
        ("bu", "blood_urea"),
        ("sc", "serum_creatinine"),
        ("sod", "sodium"),
        ("pot", "potassium"),
        ("hemo", "hemoglobin"),
        ("pcv", "pcv"),
        ("wc", "wbc_count"),
        ("rc", "rbc_count"),
        ("htn", "existing_hypertension"),
        ("dm", "existing_diabetes"),
        ("cad", "existing_cad"),
        ("appet", "appetite"),
        ("pe", "pedal_edema"),
        ("ane", "anemia"),
    ],
    "hypertension": [
        ("male", "gender"),
        ("age", "age"),
        ("education", "education_level"),
        ("currentSmoker", "current_smoker"),
        ("cigsPerDay", "cigs_per_day"),
        ("BPMeds", "bp_meds"),
        ("prevalentStroke", "prevalent_stroke"),
        ("diabetes", "existing_diabetes"),
        ("totChol", "total_cholesterol"),
        ("sysBP", "resting_bp_systolic"),
        ("diaBP", "resting_bp_diastolic"),
        ("BMI", "bmi"),
        ("heartRate", "resting_heart_rate"),
        ("glucose", "glucose"),
    ],
    "liver_disease": [
        ("Age", "age"),
        ("Gender", "gender"),
        ("Total_Bilirubin", "total_bilirubin"),
        ("Direct_Bilirubin", "direct_bilirubin"),
        ("Alkaline_Phosphotase", "alkaline_phosphotase"),
        ("Alamine_Aminotransferase", "sgpt_alt"),
        ("Aspartate_Aminotransferase", "sgot_ast"),
        ("Total_Protiens", "total_proteins"),
        ("Albumin", "serum_albumin"),
        ("Albumin_and_Globulin_Ratio", "albumin_globulin_ratio"),
    ],
}

DISEASE_DISPLAY_NAMES = {
    "diabetes": "Diabetes",
    "heart_disease": "Heart Disease",
    "ckd": "Chronic Kidney Disease",
    "hypertension": "Hypertension",
    "liver_disease": "Liver Disease",
}

_models_cache = None
_scalers_cache = None


def load_models():
    """Loads all 5 models + scalers once, then reuses them from memory
    on every subsequent call (avoids re-reading .pkl files from disk
    on every single form submission)."""
    global _models_cache, _scalers_cache

    if _models_cache is not None:
        return _models_cache, _scalers_cache

    models = {}
    scalers = {}

    for disease in FEATURE_MAPS:
        model_path = os.path.join(MODELS_DIR, f"{disease}_model.pkl")
        scaler_path = os.path.join(MODELS_DIR, f"{disease}_scaler.pkl")

        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Missing {model_path} -- run notebooks/{disease}/03_model_training.ipynb first."
            )
        if not os.path.exists(scaler_path):
            raise FileNotFoundError(
                f"Missing {scaler_path} -- run notebooks/{disease}/02_preprocessing.ipynb first."
            )

        models[disease] = joblib.load(model_path)
        scalers[disease] = joblib.load(scaler_path)

    _models_cache = models
    _scalers_cache = scalers
    return models, scalers


def _risk_level(probability):
    if probability < 0.33:
        return "Low"
    elif probability < 0.66:
        return "Moderate"
    else:
        return "High"


def predict_all(patient_data):
    """
    patient_data: dict of {unified_form_field_name: float_value}
    Returns: dict of {disease_key: {probability, risk_level, display_name}}
    """
    models, scalers = load_models()
    results = {}

    for disease, feature_map in FEATURE_MAPS.items():
        # Build the feature vector in the EXACT order this model expects
        row = [patient_data.get(form_field, 0) for _, form_field in feature_map]

        scaler = scalers[disease]
        model = models[disease]

        scaled_row = scaler.transform([row])
        probability = float(model.predict_proba(scaled_row)[0][1])

        results[disease] = {
            "probability": probability,
            "risk_level": _risk_level(probability),
            "display_name": DISEASE_DISPLAY_NAMES[disease],
        }

    return results

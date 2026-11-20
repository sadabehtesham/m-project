"""
Maps {disease: {risk_level: advice_text}}.
Used by the /predict route to attach a "next step" to every risk score.
This is plain lookup logic, no ML involved.
"""

SUGGESTIONS = {
    "diabetes": {
        "Low": "No signs of elevated diabetes risk. Keep up a balanced diet and regular activity.",
        "Moderate": "Some risk factors present. Consider getting an HbA1c or fasting glucose test at your next checkup.",
        "High": "Elevated diabetes risk. Consult a doctor soon and get an HbA1c test to confirm.",
    },
    "heart_disease": {
        "Low": "No strong indicators of heart disease risk. Maintain a heart-healthy lifestyle.",
        "Moderate": "Some cardiac risk factors present. A routine ECG or check-up with a physician is a good precaution.",
        "High": "Elevated heart disease risk. See a cardiologist soon, especially if you have chest pain or breathlessness.",
    },
    "ckd": {
        "Low": "No strong indicators of kidney disease. Stay hydrated and monitor blood pressure regularly.",
        "Moderate": "Some kidney risk factors present. A follow-up kidney function test (creatinine, eGFR) is advisable.",
        "High": "Elevated CKD risk. Consult a nephrologist and get kidney function tests done promptly.",
    },
    "hypertension": {
        "Low": "Blood pressure and related factors look within a healthy range.",
        "Moderate": "Some hypertension risk factors present. Monitor blood pressure regularly and reduce salt intake.",
        "High": "Elevated hypertension risk. See a doctor for blood pressure management and further evaluation.",
    },
    "liver_disease": {
        "Low": "No strong indicators of liver disease. Maintain a balanced diet and limit alcohol intake.",
        "Moderate": "Some liver risk factors present. A liver function test (LFT) at your next checkup is advisable.",
        "High": "Elevated liver disease risk. Consult a doctor and get a full liver function panel done.",
    },
}


def get_suggestion(disease_key, risk_level):
    return SUGGESTIONS.get(disease_key, {}).get(risk_level, "Consult a healthcare professional for guidance.")

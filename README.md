# AI-Based Clinical Decision Support System

## Early Diagnosis of Chronic Diseases Using Patient Health Records

Predicts risk for 5 chronic diseases (Diabetes, Heart Disease, CKD,
Hypertension, Liver Disease) from a single patient health form, and
shows a risk score + recommended next step for each.

## Project structure

- `data/` — raw and cleaned datasets (one CSV per disease)
- `notebooks/` — EDA, preprocessing, training, evaluation (per disease)
- `models/` — trained model files (.pkl), one per disease
- `src/` — shared Python modules used by notebooks and the web app
- `webapp/` — Flask website (auth, unified form, results page)
- `reports/` — figures and the written project report
- `presentation/` — slides for demo/viva

## Setup

1. Create a virtual environment: `python -m venv venv`
2. Activate it and run: `pip install -r requirements.txt`
3. Copy `webapp/.env.example` to `webapp/.env` and fill in a real SECRET_KEY
4. (After models are trained) run the app: `python webapp/app.py`

## GitHub auto-sync

This workspace includes a VS Code background task that watches for saved changes
and commits and pushes them to GitHub after 8 quiet seconds. Allow the task when
VS Code prompts after opening the folder. To start it manually, run the task
named `GitHub: auto-sync changes` from the Command Palette.

## Build order

See project plan — datasets → EDA/preprocessing → train & save models →
Flask skeleton → auth → unified form → prediction route → results page →
testing → deployment.

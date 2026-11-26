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

## Create the submission ZIP
Run the submission packaging script from PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/create-submission.ps1
```

This creates `m-project-submission.zip` in the project root. The archive
includes all five raw CSV datasets in `data/raw/`, as well as notebooks,
models, source code, reports, and presentation files. Local secrets and
SQLite databases are excluded.

## Setup
1. Create a virtual environment: `python -m venv venv`
2. Activate it and run: `pip install -r requirements.txt`
3. Install PostgreSQL (see "Database setup" below) and create a database
4. Copy `webapp/.env.example` to `webapp/.env`, fill in a real SECRET_KEY,
   and update DATABASE_URL with your PostgreSQL username/password
5. (After models are trained) run the app: `python webapp/app.py`

## Deploy to Vercel

The Vercel entry point and deployment settings are included in the project root:
`app.py`, `requirements.txt`, `.python-version`, and `vercel.json`. The trained
models are bundled with the function, while static CSS and JavaScript are served
from `public/static/` through Vercel's CDN.

1. Push this repository to GitHub, GitLab, or Bitbucket and import it into Vercel.
2. Keep Vercel's **Root Directory** at the repository root (the `m-project`
   directory in this workspace, where this README and `vercel.json` live).
3. Add these environment variables in the Vercel project settings for Preview and
   Production:
   - `SECRET_KEY`: a long, random value used to sign sessions.
   - `DATABASE_URL`: a persistent PostgreSQL connection string. Vercel function
     filesystems are temporary, so do not use the local SQLite database in a
     deployed environment. Use a hosted PostgreSQL provider and enable SSL if
     its connection string requires it.
   - `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USE_TLS`, `MAIL_USERNAME`,
     `MAIL_PASSWORD`, and `MAIL_DEFAULT_SENDER`: SMTP settings used to deliver
     signup verification codes. `MAIL_USE_TLS` should be `true` for port 587.
4. Deploy. Vercel installs the root `requirements.txt` and serves the Flask
   application through its Python runtime.

For local Vercel-style development, install the Vercel CLI and run `vercel dev`
from the repository root. The normal local path remains `python webapp/app.py`; it serves
the same assets from `public/static/` and uses the local `.env` file.

The forgot-password route currently prints reset links to the application log
instead of sending them by email. Configure an email flow in the app before
relying on password recovery for production users.

## Database setup (PostgreSQL)
1. Install PostgreSQL:
   - Windows/Mac: download from https://www.postgresql.org/download/
   - During install, set a password for the default `postgres` user — remember it
2. Open a terminal and connect to PostgreSQL:
   ```
   psql -U postgres
   ```
3. Create a dedicated database and user for this project:
   ```sql
   CREATE DATABASE models_db;
   CREATE USER models_user WITH PASSWORD 'your_password_here';
   GRANT ALL PRIVILEGES ON DATABASE models_db TO models_user;
   ```
4. Update `webapp/.env` with matching credentials:
   ```
   DATABASE_URL=postgresql://models_user:your_password_here@localhost:5432/models_db
   ```
5. Run the Flask app once (`python webapp/app.py`) — it auto-creates the
   `users` and `prediction_history` tables inside `models_db` on first run,
   no manual table creation needed.

**Tip:** if you'd rather not install PostgreSQL locally, free hosted options
like [Neon](https://neon.tech) or [Supabase](https://supabase.com) give you
a ready-to-use PostgreSQL database and connection string in a couple of
minutes — paste that connection string into DATABASE_URL instead.

## Email setup (Gmail SMTP, for OTP verification emails)
1. Use a Gmail account (yours or a dedicated one for the project).
2. Turn on 2-Step Verification: https://myaccount.google.com/security
   (required before Google will let you create an App Password).
3. Generate an App Password: https://myaccount.google.com/apppasswords
   - Select "Mail" as the app, "Other" as the device, name it "CDSS"
   - Google gives you a 16-character password — copy it (no spaces)
4. Update `webapp/.env`:
   ```
   MAIL_USERNAME=your_gmail_address@gmail.com
   MAIL_PASSWORD=<the 16-character App Password, NOT your real Gmail password>
   MAIL_DEFAULT_SENDER=your_gmail_address@gmail.com
   ```
5. Restart the Flask app. Signing up should now send a real email with
   the 6-digit verification code.

**If email sending fails** (wrong credentials, no internet, Gmail
blocking it), the code automatically falls back to printing the OTP
to your terminal console instead — look for a `[WARN]` / `[FALLBACK]`
line, so testing is never completely blocked.

## Build order
See project plan — datasets → EDA/preprocessing → train & save models →
Flask skeleton → auth → unified form → prediction route → results page →
testing → deployment.

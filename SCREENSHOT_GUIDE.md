# 📸 Screenshot Guide for Proposal Document

## Screenshot Opportunity #1: Development Environment Overview

### Part 1: Python Environment / Virtual Environment

You have **two options** for this screenshot:

#### Option A: Show `requirements.txt` (Recommended - Cleaner)
1. Open `requirements.txt` in your editor
2. Take a screenshot showing the file contents
3. This shows all dependencies organized by category

#### Option B: Show `pip list` output
1. Open Terminal
2. Run:
   ```bash
   cd /Users/lincksmorara/Desktop/portfoliai_ml_model_project
   source venv/bin/activate
   pip list
   ```
3. Take a screenshot of the terminal showing the installed packages

#### Option C: Show Virtual Environment Info
1. Open Terminal
2. Run:
   ```bash
   cd /Users/lincksmorara/Desktop/portfoliai_ml_model_project
   source venv/bin/activate
   which python
   python --version
   pip --version
   ```
3. Take a screenshot showing:
   - Python path (showing venv)
   - Python version
   - pip version

---

### Part 2: FastAPI Swagger UI (Auto-generated API Documentation)

#### Step 1: Start Your Server

Open Terminal and run:
```bash
cd /Users/lincksmorara/Desktop/portfoliai_ml_model_project
source venv/bin/activate
python server.py
```

Or if you prefer uvicorn directly:
```bash
uvicorn server:app --reload --port 8000
```

Wait for the message: `Application startup complete.` or `Uvicorn running on http://127.0.0.1:8000`

#### Step 2: Open Swagger UI in Browser

1. Open your web browser (Chrome, Safari, Firefox)
2. Navigate to: **http://localhost:8000/docs**
   - This is the default Swagger UI endpoint for FastAPI
   - Alternative: http://127.0.0.1:8000/docs

#### Step 3: Take Screenshot

You should see:
- **Title**: "PortfoliAI ML Service"
- **Version**: "1.0.0"
- **List of endpoints** organized by tags:
  - `/api/chatbot` (POST)
  - `/api/portfolio/summary` (GET)
  - `/api/portfolio/position/add` (POST)
  - `/api/portfolio/withdrawal/add` (POST)
  - `/predict/survey-risk-v2` (POST)
  - `/generate/profile-card` (POST)
  - `/auth/signup` (POST)
  - `/auth/login` (POST)
  - And many more...

**What to capture:**
- The top section showing API title and description
- At least 5-10 visible endpoints in the list
- The expandable endpoint details (click one to show request/response schemas)

**Pro tip:** Expand one endpoint (like `/api/portfolio/summary`) to show:
- Request parameters
- Response schema
- "Try it out" button

This demonstrates the auto-generated documentation feature of FastAPI.

---

## Alternative: ReDoc Documentation

FastAPI also provides ReDoc at: **http://localhost:8000/redoc**

This shows a different style of documentation (more traditional API docs format).

---

## Quick Checklist

- [ ] Screenshot 1: Python environment (requirements.txt OR pip list OR venv info)
- [ ] Screenshot 2: FastAPI Swagger UI at `/docs` showing endpoints
- [ ] Optional: Screenshot 3: Expanded endpoint details showing schema

---

## Troubleshooting

**If server won't start:**
- Make sure you're in the project directory
- Activate virtual environment: `source venv/bin/activate`
- Check if port 8000 is already in use: `lsof -i :8000`
- Try a different port: `uvicorn server:app --reload --port 8001`

**If `/docs` doesn't load:**
- Make sure server is running (check terminal for errors)
- Try `http://127.0.0.1:8000/docs` instead of `localhost`
- Check browser console for errors (F12)

**If you see "Not Found":**
- Your FastAPI app might have custom docs URL
- Check `server.py` for `docs_url` parameter in `FastAPI()` call
- Default is `/docs` but could be `/api/docs` or disabled

---

## Example Screenshot Composition

**Screenshot 1 (Environment):**
```
┌─────────────────────────────────────┐
│  requirements.txt                    │
│  ─────────────────────────────────── │
│  pandas>=1.5.0                      │
│  numpy>=1.24.0                       │
│  scikit-learn==1.6.1                │
│  fastapi>=0.104.0                   │
│  ...                                 │
└─────────────────────────────────────┘
```

**Screenshot 2 (Swagger UI):**
```
┌─────────────────────────────────────┐
│  PortfoliAI ML Service  v1.0.0     │
│  ───────────────────────────────── │
│  POST /api/chatbot                 │
│  GET  /api/portfolio/summary       │
│  POST /api/portfolio/position/add  │
│  ...                               │
└─────────────────────────────────────┘
```




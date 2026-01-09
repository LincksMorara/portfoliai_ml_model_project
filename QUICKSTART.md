# ⚡ PortfoliAI - 30-Second Quick Start

## 📋 Prerequisites

Make sure you have Python 3.11+ installed:
```bash
python3 --version  # Should be 3.11 or higher
```

## 🚀 Start Server

### Option A: Easy Scripts (Recommended) ⭐

**First time setup:**
```bash
cd /Users/lincksmorara/Desktop/portfoliai_ml_model_project
./setup.sh
```

**Start server:**
```bash
./start.sh
```

That's it! The scripts handle everything automatically.

---

### Option B: Manual Setup

#### Method 1: Direct Python (Always Works)

```bash
cd /Users/lincksmorara/Desktop/portfoliai_ml_model_project

# Install dependencies (first time only)
./venv/bin/python3 -m pip install -r requirements.txt

# Start server
./venv/bin/python3 -m uvicorn server:app --host 0.0.0.0 --port 8000
```

#### Method 2: With Virtual Environment Activation

```bash
cd /Users/lincksmorara/Desktop/portfoliai_ml_model_project

# Activate venv
source venv/bin/activate

# Install dependencies (first time only)
pip install -r requirements.txt

# Start server
uvicorn server:app --host 0.0.0.0 --port 8000
```

**Note:** If Method 2 doesn't work, use Method 1 (direct Python path).

## 🌐 Open App

**Visit:** http://localhost:8000

## ✅ Test Complete Flow

1. **Homepage** - Click "Start Investor Survey"
2. **Survey** - Complete 13 questions (toggle to KES if you want)
3. **Results** - Get Living Profile Card with AI recommendations
4. **Signup** - Click "Activate AI Consultant" → Create account
5. **Dashboard** - View your saved profile
6. **Logout** - Sign out when done

## 🔑 Enable Groq AI (Optional - FREE)

```bash
# Get key: https://console.groq.com
echo "GROQ_API_KEY=gsk_your_key_here" > .env

# Restart server
pkill -f uvicorn && uvicorn server:app --port 8000
```

Look for: `✨ Groq client initialized (FREE, real-time enhanced)`

## 🧪 Test API

```bash
# Health check
curl http://localhost:8000/health

# Get profile
curl -X POST http://localhost:8000/generate/profile-card \
  -H 'Content-Type: application/json' \
  -d '{"happiness_outcome":"c","horizon":"c","risk_slider":9,...}' | python3 -m json.tool
```

## 📚 Full Documentation

See `README.md` for complete guide!

---

**That's it! The app is running!** 🎉

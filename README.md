````md
# 🤖 PortfoliAI – Investor Profiling & AI Consultant Module

**TL;DR:**  
PortfoliAI is a modular FastAPI-based backend that combines ML-driven investor risk profiling with LLM-generated, market-aware investment guidance, localized for the Kenyan market.

A complete, modular investor profiling system designed as a **production-ready MVP**, with clear upgrade paths for full-scale deployment.

**Status:** ✅ Production-Ready (MVP / Demo) | Modular | Plug-and-Play

---

## 📋 Table of Contents
- [Quick Start](#quick-start)
- [Features](#features)
- [Architecture](#architecture)
- [User Flow](#user-flow)
- [API Documentation](#api-documentation)
- [Integration Guide](#integration-guide)
- [Database Migration](#database-migration)
- [Groq AI Setup](#groq-ai-setup-free)
- [Market Data Integration](#market-data-integration)
- [Project Structure](#project-structure)
- [Configuration](#configuration)

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.11+**
- **Virtual environment** (included)
- **Terminal / Command Line**

```bash
python3 --version
````

---

### 1. Setup (First Time Only)

**Recommended**

```bash
cd portfoliai_ml_model_project
./setup.sh
```

This script:

* Verifies Python installation
* Creates/checks virtual environment
* Installs dependencies
* Creates `.env` from template

**Manual Setup**

```bash
./venv/bin/python3 -m pip install -r requirements.txt
```

> Method 1 uses the virtual environment’s Python directly and avoids common activation issues.

---

### 2. Start the Server

**Recommended**

```bash
./start.sh
```

Or manually:

```bash
./venv/bin/python3 -m uvicorn server:app --host 0.0.0.0 --port 8000
```

---

### 3. Access the Application

Homepage:
👉 [http://localhost:8000](http://localhost:8000)

Options:

* 🎯 New User – Take Investor Survey
* 👤 Existing User – Sign In

---

## ✨ Features

### 🎯 Core Features

* **13-question behavioral survey** designed to capture real risk behavior
* **USD/KES currency switcher** (configurable)
* **ML-based risk scoring** (R² = 0.89 on validation data)
* **LLM-generated “Living Profile Cards”** with market-aware context
* **User authentication** (signup, login, dashboard)
* **Modular architecture** designed for integration into larger systems

---

### 💫 Living Profile Card Components

Each profile card includes:

* WHO YOU ARE (behavioral persona)
* PORTFOLIO BLUEPRINT (🟩 Core / 🟦 Growth / 🟨 Safety)
* Kenya-focused + international allocation strategy
* Strengths, pitfalls, and actionable tips
* Expected return ranges contextualized to market conditions

---

### ⚠️ Market Data Disclaimer (Important)

By default, the system uses **simulated or externally provided market data** (typical price ranges and recent trends), not live exchange APIs.

This design is intentional.

* LLMs **cannot fetch live market data**
* Market context must be fetched **before** invoking the LLM
* Upgrade paths to real APIs are fully documented

See: **MARKET_DATA_API_GUIDE.md**

---

## 🏗️ Architecture

### Why ML + LLM (Not LLM-Only)

* **ML models** provide consistent, explainable numerical risk scoring
* **LLMs** excel at interpretation, explanation, and personalized guidance
* Separating responsibilities avoids hallucinated scores and improves trust

---

### System Overview

```
UI (HTML/JS)
     ↓
FastAPI Server
     ↓
Survey Mapper → ML Risk Model → Risk Score
     ↓
Market Context Provider (simulated or API-fed)
     ↓
LLM Profile Card Generator (Groq)
     ↓
User Dashboard / Persistence
```

---

### Data Flow

1. User completes survey (13 questions)
2. Answers mapped to engineered backend features
3. ML model outputs risk score, category, persona
4. Market context injected (simulated by default)
5. LLM generates personalized profile card
6. User may save profile via authentication system

---

## 👤 User Flow

### New User

1. Visit homepage
2. Complete survey (3–4 minutes)
3. Receive AI-generated profile card
4. Create account
5. View saved profile in dashboard

### Returning User

1. Sign in
2. View saved profile
3. Sign out

---

## 📡 API Documentation

### `POST /generate/profile-card`

Generates full investor profile.

Response includes:

* Risk score & category
* Persona & confidence
* Generated profile card
* Market context flag

---

## 📊 Market Data Integration

### Current State

* Market prices and rates are **estimated ranges**
* Clearly labeled as simulated
* Suitable for demos, testing, and MVP usage

### Upgrade Path

* NSE API (partnership required)
* Alpha Vantage / Finnhub
* Web scraping (with caching)
* Hybrid approach recommended

---

## 🗄️ Database Migration

### Current Storage

* File-based (`users_db.json`)
* Suitable for demos and <100 users

### Designed for Drop-In Migration

* PostgreSQL
* Supabase
* Firebase

Only `auth.py` needs replacement; no other services change.

---

## 🆓 Groq AI Setup (Free Tier)

Groq is used for:

* Fast LLM inference
* Dynamic profile generation
* Market-aware language (based on provided context)

> Free tier supports up to **14,400 requests/day**

---

## 🔐 Security Considerations

The current security setup is **appropriate for demos and controlled environments**, with production hardening steps clearly documented.

### Current

* Password hashing (SHA-256)
* Session tokens
* Session expiry
* Environment-based secrets

### Production Hardening (Planned)

* bcrypt password hashing
* Rate limiting
* HTTPS
* Token refresh
* Redis-backed sessions
* Real database

---

## 🎓 Technical Notes

### ML Model Details

* **Algorithms:** Random Forest Regressor & Classifier
* **Training Size:** 132 synthetic and anonymized investor profiles
* **Features:** 22 engineered features
* **R²:** 0.89 (regression)
* **Accuracy:** ~85% (classification)

> Data was curated to reflect realistic behavioral investing patterns.

---

## 🚀 Project Status

**✅ COMPLETE & MVP-READY**

* [x] Behavioral investor survey
* [x] ML-based risk profiling
* [x] LLM-generated profile cards
* [x] Market-context integration (simulated by default)
* [x] Authentication & persistence
* [x] Modular architecture with upgrade paths
* [x] Full API documentation

---

**Version:** 3.0
**Last Updated:** January 2026
**Market:** Kenya (with international exposure)
**Cost:** $0/month using free-tier services

```
```

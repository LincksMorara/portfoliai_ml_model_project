# 🛠️ Setup Notes & Common Issues

This document explains common setup issues and their solutions.

## 📋 Prerequisites Checklist

Before starting, verify you have:

- [ ] **Python 3.11+** installed (`python3 --version`)
- [ ] **Terminal** access (Terminal.app on macOS, PowerShell/CMD on Windows)
- [ ] **Internet connection** (for downloading dependencies)
- [ ] **~500MB disk space** (for dependencies)

## 🚀 Recommended Setup Method

Use the automated scripts for hassle-free setup:

```bash
# 1. Navigate to project
cd /Users/lincksmorara/Desktop/portfoliai_ml_model_project

# 2. Run setup (first time only)
./setup.sh

# 3. Start server
./start.sh

# 4. Open browser
# Visit: http://localhost:8000
```

## ⚠️ Common Issues & Solutions

### Issue 1: "ModuleNotFoundError: No module named 'fastapi'"

**Cause:** Dependencies not installed in virtual environment

**Solution:**
```bash
# Install dependencies directly using venv's Python
./venv/bin/python3 -m pip install -r requirements.txt
```

**Why this happens:**
- Virtual environment activation may not work correctly on some systems
- System Python might be used instead of venv Python
- Solution: Use venv's Python directly instead of relying on activation

---

### Issue 2: "source venv/bin/activate" doesn't activate venv properly

**Symptoms:**
- `which python3` still points to system Python
- Installed packages not found

**Solution:**
Don't rely on activation. Use direct Python path:
```bash
# Instead of:
source venv/bin/activate
uvicorn server:app --port 8000

# Use:
./venv/bin/python3 -m uvicorn server:app --host 0.0.0.0 --port 8000
```

**Why this happens:**
- Shell configuration issues
- Multiple Python installations
- Virtual environment path issues

---

### Issue 3: "Address already in use" or port 8000 blocked

**Symptoms:**
```
ERROR: [Errno 48] Address already in use
```

**Solution 1 - Kill existing process:**
```bash
# Find process on port 8000
lsof -ti:8000

# Kill it
pkill -f uvicorn

# Try again
./start.sh
```

**Solution 2 - Use different port:**
```bash
./venv/bin/python3 -m uvicorn server:app --host 0.0.0.0 --port 8001
# Then visit: http://localhost:8001
```

---

### Issue 4: scikit-learn version mismatch

**Symptoms:**
```
ValueError: The feature names should match those that were passed during fit.
```

**Solution:**
```bash
# Force reinstall correct version
./venv/bin/python3 -m pip install --force-reinstall scikit-learn==1.6.1
```

**Why this happens:**
- Different scikit-learn version than model was trained with
- Model files require specific version for compatibility

---

### Issue 5: Permission denied when running scripts

**Symptoms:**
```
bash: ./setup.sh: Permission denied
```

**Solution:**
```bash
# Make scripts executable
chmod +x setup.sh start.sh

# Now run
./setup.sh
```

---

### Issue 6: Virtual environment not found

**Symptoms:**
```
Error: Virtual environment not found
```

**Solution 1 - Use existing venv:**
```bash
# Check if venv directory exists
ls -la venv/

# If it exists, reinstall dependencies
./venv/bin/python3 -m pip install -r requirements.txt
```

**Solution 2 - Recreate venv:**
```bash
# Remove old venv
rm -rf venv

# Create new one
python3 -m venv venv

# Install dependencies
./venv/bin/python3 -m pip install -r requirements.txt
```

---

## 🔍 Diagnostic Commands

Run these to diagnose issues:

### Check Python Installation
```bash
# Python version
python3 --version  # Should be 3.11+

# Python location
which python3

# Venv Python
./venv/bin/python3 --version
```

### Check Dependencies
```bash
# List installed packages in venv
./venv/bin/python3 -m pip list

# Check specific packages
./venv/bin/python3 -c "import fastapi; print('✅ FastAPI')"
./venv/bin/python3 -c "import uvicorn; print('✅ Uvicorn')"
./venv/bin/python3 -c "import sklearn; print('✅ scikit-learn')"
```

### Check Server
```bash
# Test server health
curl http://localhost:8000/health

# Expected output:
# {"status":"healthy","service":"PortfoliAI ML Service"}

# Check if port is in use
lsof -ti:8000
```

### Check Files
```bash
# Check required files exist
ls -la server.py ml_service.py requirements.txt

# Check venv structure
ls -la venv/bin/python3
```

---

## 📦 Manual Dependency Installation

If `pip install -r requirements.txt` fails, install packages individually:

```bash
# Core packages
./venv/bin/python3 -m pip install fastapi uvicorn[standard]
./venv/bin/python3 -m pip install pydantic

# ML packages
./venv/bin/python3 -m pip install scikit-learn==1.6.1
./venv/bin/python3 -m pip install pandas numpy joblib

# AI packages (optional)
./venv/bin/python3 -m pip install groq openai

# Utilities
./venv/bin/python3 -m pip install python-dotenv requests
```

---

## 🐍 Python Version Issues

### If you have multiple Python versions:

```bash
# List all Python versions
ls -la /usr/local/bin/python*
ls -la /opt/homebrew/bin/python*

# Use specific version for venv
python3.11 -m venv venv
./venv/bin/python3 --version  # Verify version
```

### If Python version is too old:

**macOS:**
```bash
# Install Python 3.11+ with Homebrew
brew install python@3.11
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv
```

---

## 🎯 Verification Checklist

After setup, verify everything works:

- [ ] `./venv/bin/python3 --version` shows 3.11+
- [ ] `./venv/bin/python3 -c "import fastapi"` works
- [ ] `curl http://localhost:8000/health` returns healthy status
- [ ] `curl http://localhost:8000/` returns HTML
- [ ] Browser loads http://localhost:8000 successfully

---

## 💡 Tips for Smooth Setup

1. **Always use the setup script first** - It handles edge cases automatically
2. **Use direct Python paths** - More reliable than venv activation
3. **Check Python version** - Must be 3.11 or higher
4. **Keep dependencies updated** - But match scikit-learn version exactly
5. **Use the start script** - Handles port conflicts and checks

---

## 🆘 Still Having Issues?

If none of the above solutions work:

1. **Check system logs** for more detailed error messages
2. **Try creating fresh venv** in different location
3. **Verify no firewall/antivirus** blocking Python or ports
4. **Test with minimal dependencies** first (just fastapi + uvicorn)
5. **Check disk space** - Need ~500MB for all packages

---

## 📝 Platform-Specific Notes

### macOS
- Use Homebrew for Python installation
- May need Xcode command line tools: `xcode-select --install`
- Use Terminal.app or iTerm2

### Linux
- Install python3-venv: `sudo apt install python3-venv`
- May need build tools: `sudo apt install build-essential`

### Windows
- Use PowerShell or WSL (Windows Subsystem for Linux)
- Scripts need `.bat` or `.ps1` equivalents
- Forward slashes in paths become backslashes

---

## 🎓 Understanding the Setup

### What does setup.sh do?
1. Checks Python version
2. Creates/verifies virtual environment
3. Upgrades pip
4. Installs all dependencies from requirements.txt
5. Verifies installation
6. Creates .env file from template

### What does start.sh do?
1. Checks venv exists
2. Checks dependencies installed
3. Checks if port 8000 is in use
4. Starts uvicorn server with optimal settings

### Why direct Python path?
- `./venv/bin/python3` explicitly uses venv's Python
- Bypasses shell activation issues
- Works consistently across systems
- No PATH or environment variable conflicts

---

**Last Updated:** November 3, 2025  
**Tested On:** macOS 14.0+, Ubuntu 22.04+, Python 3.11-3.13



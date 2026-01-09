# 🤖 AI Chatbot Quick Start - Test Market Data APIs

## What This Is

A simple chatbot interface to test FMP and Finnhub API integrations. Type a stock symbol like "AAPL" and see real-time data from both APIs displayed side-by-side.

## 🚀 Setup (5 Minutes)

### Step 1: Get Your API Keys

#### FMP (Financial Modeling Prep)
1. Go to https://financialmodelingprep.com/developer/
2. Sign up for FREE account
3. Copy your API key
4. **Free tier**: 250 calls/day

#### Finnhub
1. Go to https://finnhub.io/register
2. Sign up for FREE account
3. Copy your API key
4. **Free tier**: 60 calls/minute

### Step 2: Add Keys to .env

```bash
cd /Users/lincksmorara/Desktop/portfoliai_ml_model_project

# If .env doesn't exist, create it from example
cp env.example .env

# Edit .env and add your keys:
# FMP_API_KEY=paste_your_fmp_key_here
# FINNHUB_API_KEY=paste_your_finnhub_key_here
```

### Step 3: Restart Server

```bash
# Stop existing server (if running)
pkill -f uvicorn

# Start server with new keys
./start.sh
```

Or manually:
```bash
./venv/bin/python3 -m uvicorn server:app --host 0.0.0.0 --port 8000
```

### Step 4: Test the Chatbot

1. **Login** to your account: http://localhost:8000
2. Click **"Open AI Chatbot →"** button on dashboard
3. Type a stock symbol: `AAPL`, `MSFT`, `TSLA`, `GOOGL`
4. See real-time data from both APIs!

## 📊 What You'll See

When you type `AAPL`, the chatbot will show:

### From FMP API:
- ✅ **Current Price** (e.g., $175.34)
- ✅ **Price Change** (e.g., +$1.20 / +0.69%)
- ✅ **Day High/Low**
- ✅ **Volume**
- ✅ **Market Cap**
- ✅ **Company Profile** (CEO, Industry, Sector, Website)

### From Finnhub API:
- ✅ **Current Price**
- ✅ **Price Change**
- ✅ **Open/Previous Close**
- ✅ **Recent News** (last 7 days, up to 3 articles)
  - Headlines
  - Source
  - Summary

## 🧪 Testing Different Symbols

Try these popular stocks:

**Tech:**
- `AAPL` - Apple
- `MSFT` - Microsoft
- `GOOGL` - Google
- `TSLA` - Tesla
- `NVDA` - NVIDIA

**Finance:**
- `JPM` - JPMorgan Chase
- `BAC` - Bank of America
- `GS` - Goldman Sachs

**Consumer:**
- `WMT` - Walmart
- `DIS` - Disney
- `NKE` - Nike

**Note:** NSE stocks (SCOM, EQTY, KCB) may not work with these APIs. For Kenya stocks, you'll need NSE-specific integration (web scraping).

## 🔍 Troubleshooting

### "FMP_API_KEY not configured"
- Check `.env` file exists
- Verify `FMP_API_KEY=your_key` (no quotes)
- Restart server

### "FINNHUB_API_KEY not configured"
- Check `.env` file
- Verify `FINNHUB_API_KEY=your_key`
- Restart server

### "No data found for symbol"
- Check symbol is valid (use uppercase)
- Try popular symbols first (AAPL, MSFT)
- Verify API key is working

### API returns errors
- Check you haven't exceeded free tier limits:
  - FMP: 250 calls/day
  - Finnhub: 60 calls/minute
- Wait a few minutes if rate limited
- Check API key is active

## 📁 Files Created

```
portfoliai_ml_model_project/
├── fmp_integration.py          # FMP API client
├── finnhub_integration.py      # Finnhub API client
├── chatbot.html                # Chatbot UI
├── server.py                   # Updated with /api/chatbot endpoint
├── dashboard.html              # Updated with chatbot link
└── env.example                 # Updated with API key placeholders
```

## 🎯 What This Proves

This chatbot demonstrates that:

1. ✅ **FMP API works** - You can fetch real stock prices
2. ✅ **Finnhub API works** - You can fetch news and quotes
3. ✅ **APIs return REAL data** - Not simulated
4. ✅ **Python integration works** - Backend successfully calls both APIs
5. ✅ **Ready for profile cards** - Can now integrate into investment profiles

## 📈 Next Steps

Once you've confirmed the APIs work:

### Option 1: Add to Profile Cards
Integrate real prices into the profile generation:
```python
# In profile_card_generator.py
fmp = get_fmp_client()
quote = fmp.get_quote('SCOM')
# Use real price instead of simulated
```

### Option 2: Build Market Dashboard
Create a dashboard with real-time prices:
```python
@app.get("/api/market-dashboard")
async def market_dashboard():
    return {
        'tech_stocks': [get_quote('AAPL'), get_quote('MSFT')],
        'news': get_news('AAPL'),
        'updated': datetime.now()
    }
```

### Option 3: Add NSE Integration
Combine FMP (for US stocks) with NSE scraping (for Kenya stocks):
```python
class HybridMarketData:
    def get_price(self, symbol):
        if symbol in ['SCOM', 'EQTY', 'KCB']:
            return scrape_nse(symbol)  # Kenya
        else:
            return fmp.get_quote(symbol)  # US/Global
```

## 💡 Pro Tips

1. **Cache responses** - APIs have rate limits, cache for 1-5 minutes
2. **Handle errors gracefully** - Show fallback data if API fails
3. **Batch requests** - Fetch multiple stocks at once when possible
4. **Monitor usage** - Track API call count to stay under limits
5. **Test extensively** - Try different symbols to ensure reliability

## 🎓 Understanding the Code

### FMP Integration (`fmp_integration.py`)
- Fetches quotes and company profiles
- Handles errors and timeouts
- Returns normalized data structure
- Logs all requests for debugging

### Finnhub Integration (`finnhub_integration.py`)
- Fetches news and quotes
- Filters and formats articles
- Sorts by date (newest first)
- Limits to 10 articles per request

### Chatbot Endpoint (`server.py`)
- Receives user message
- Extracts stock symbol
- Calls both APIs in parallel
- Returns combined results

### Chatbot UI (`chatbot.html`)
- Simple chat interface
- Real-time message display
- Formatted API responses
- Loading states and error handling

## 🔗 API Documentation

**FMP:**
- Docs: https://site.financialmodelingprep.com/developer/docs/
- Dashboard: https://site.financialmodelingprep.com/developer/
- Support: Contact through website

**Finnhub:**
- Docs: https://finnhub.io/docs/api
- Dashboard: https://finnhub.io/dashboard
- Support: https://finnhub.io/support

---

**Questions?** Check the logs: `grep "Chatbot\|FMP\|Finnhub" server.log`

**Ready to integrate?** See `MARKET_DATA_API_GUIDE.md` for production integration

🎉 **Happy Testing!**



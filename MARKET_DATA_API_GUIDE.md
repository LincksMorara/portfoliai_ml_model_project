# 📊 Market Data API Integration Guide

## 🚨 Current Status: SIMULATED DATA

**Important:** The current implementation uses **simulated/estimated market data**. Stock prices, T-Bill rates, and other financial data shown in profile cards are **approximations based on typical ranges**, not real-time data.

### What's Currently Simulated?

- ❌ NSE stock prices (Safaricom, Equity Group, KCB, etc.)
- ❌ T-Bill rates (estimated at 15-16% range)
- ❌ NSE 20 Index movements
- ❌ Specific company news and catalysts
- ❌ Week-over-week price changes

### Why Is This Happening?

The LLM (Groq or OpenAI) generates text based on the data you provide. Even though the prompts say "use LIVE data," the data being fed to it is simulated. **No LLM can fetch real market data** - it only works with what you give it.

---

## ✅ How to Get REAL Market Data

### Option 1: NSE Live Data API (Recommended for Kenya)

**Best Provider:** [NSE Kenya Official API](https://www.nse.co.ke)

1. **Register for API Access:**
   - Contact NSE for API partnership/developer access
   - Typical cost: Varies (may require institutional subscription)
   
2. **Integration Example:**
```python
# In market_data_fetcher.py
def _fetch_nse_price(self, ticker: str) -> Optional[Dict]:
    import requests
    
    # Replace with actual NSE API endpoint
    url = f"https://api.nse.co.ke/v1/stocks/{ticker}"
    headers = {"Authorization": f"Bearer {NSE_API_KEY}"}
    
    response = requests.get(url, headers=headers)
    data = response.json()
    
    return {
        'price': data['last_price'],
        'change_percent': data['change_percent'],
        'volume': data['volume'],
        'timestamp': data['timestamp']
    }
```

3. **Add to `.env`:**
```bash
NSE_API_KEY=your_nse_api_key_here
NSE_API_URL=https://api.nse.co.ke/v1
```

---

### Option 2: Third-Party Market Data Providers

#### A. **Alpha Vantage** (Global + Some African Markets)
- **Website:** https://www.alphavantage.co
- **Cost:** FREE tier (5 API calls/min), Premium from $49/month
- **Coverage:** Limited NSE coverage, good for US markets

**Setup:**
```bash
pip install alpha-vantage
```

```python
from alpha_vantage.timeseries import TimeSeries

def _fetch_price_alpha_vantage(self, symbol):
    ts = TimeSeries(key=ALPHA_VANTAGE_KEY, output_format='json')
    data, meta_data = ts.get_quote_endpoint(symbol=symbol)
    
    return {
        'price': float(data['05. price']),
        'change_percent': float(data['10. change percent'].strip('%'))
    }
```

#### B. **Finnhub** (Global Markets)
- **Website:** https://finnhub.io
- **Cost:** FREE tier (60 calls/min), Premium from $29/month
- **Coverage:** Good global coverage

```bash
pip install finnhub-python
```

```python
import finnhub

def _fetch_price_finnhub(self, symbol):
    finnhub_client = finnhub.Client(api_key=FINNHUB_KEY)
    quote = finnhub_client.quote(symbol)
    
    return {
        'price': quote['c'],  # Current price
        'change_percent': quote['dp']  # Percent change
    }
```

#### C. **Twelve Data** (Emerging Markets Focus)
- **Website:** https://twelvedata.com
- **Cost:** FREE tier (8 calls/min), Premium from $29/month
- **Coverage:** Better emerging market coverage

---

### Option 3: Web Scraping (Free but Fragile)

**⚠️ Warning:** Web scraping can break when websites update. Use only as fallback.

#### Scrape NSE Website

```python
def _scrape_nse_live(self, ticker: str):
    import requests
    from bs4 import BeautifulSoup
    
    # Example: Scrape from NSE live quotes page
    url = f"https://live.mystocks.co.ke/stock/{ticker}"
    
    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Find price element (inspect page to find correct selector)
    price_elem = soup.find('span', class_='stock-price')
    
    if price_elem:
        price = float(price_elem.text.replace('KSh', '').replace(',', '').strip())
        return {'price': price, 'source': 'scraped'}
    
    return None
```

**Websites to scrape (at your own risk):**
- https://live.mystocks.co.ke
- https://www.african-markets.com/en/stock-markets/nse
- https://www.investing.com/equities/kenya

---

### Option 4: Central Bank of Kenya (T-Bill Rates)

**For real T-Bill rates:**

```python
def _fetch_tbill_rates_real(self):
    import requests
    from bs4 import BeautifulSoup
    
    # Official CBK rates page
    url = "https://www.centralbank.go.ke/securities/treasury-bills/"
    
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Parse table of current rates
    # (Structure depends on CBK's actual page layout)
    rates_table = soup.find('table', class_='rates')
    
    rates = {}
    for row in rates_table.find_all('tr')[1:]:  # Skip header
        cols = row.find_all('td')
        tenor = cols[0].text.strip()  # e.g., "91-day"
        rate = cols[1].text.strip()   # e.g., "15.8%"
        rates[tenor] = rate
    
    return rates
```

---

## 🔧 Implementation Steps

### Step 1: Choose Your Data Provider

| Provider | Cost | NSE Coverage | Global Coverage | Ease of Use |
|----------|------|--------------|-----------------|-------------|
| **NSE Official API** | $$$ | ✅ Excellent | ❌ No | Medium |
| **Alpha Vantage** | $ | ⚠️ Limited | ✅ Good | Easy |
| **Finnhub** | $ | ⚠️ Limited | ✅ Excellent | Easy |
| **Twelve Data** | $ | ⚠️ Moderate | ✅ Good | Easy |
| **Web Scraping** | FREE | ⚠️ Fragile | ⚠️ Fragile | Hard |

**Recommendation:** 
- **For NSE data:** NSE Official API (if budget allows) or web scraping (fragile)
- **For global data:** Finnhub or Alpha Vantage
- **For T-Bills:** CBK website scraping

### Step 2: Update `market_data_fetcher.py`

Replace the simulated methods with real API calls:

```python
def __init__(self):
    self.nse_api_key = os.getenv('NSE_API_KEY')
    self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_KEY')
    self.use_real_data = bool(self.nse_api_key or self.alpha_vantage_key)
    logger.info(f"🔌 Real data enabled: {self.use_real_data}")
```

### Step 3: Add Error Handling & Fallbacks

```python
def get_live_stock_snippet(self, ticker: str, company: str) -> str:
    # Try Method 1: NSE Official API
    try:
        data = self._fetch_nse_api(ticker)
        if data:
            return f"{company} ({ticker}) at KSh {data['price']:.2f}, {data['change']:+.1f}% (LIVE from NSE)"
    except:
        pass
    
    # Try Method 2: Web scraping
    try:
        data = self._scrape_nse(ticker)
        if data:
            return f"{company} ({ticker}) at KSh {data['price']:.2f} (LIVE via scraping)"
    except:
        pass
    
    # Fallback: Simulated data with clear label
    return f"{company} ({ticker}) around KSh [typical range] ⚠️ SIMULATED DATA"
```

### Step 4: Update Environment Variables

```bash
# .env
NSE_API_KEY=your_key_here
ALPHA_VANTAGE_KEY=your_key_here
FINNHUB_KEY=your_key_here
```

### Step 5: Test Real Data Integration

```bash
python3 market_data_fetcher.py
```

Should log:
```
🔌 Real data enabled: True
✅ Fetched SCOM price: KSh 14.35 (NSE API)
✅ Fetched T-Bill rates: 15.8% (CBK)
```

---

## 📝 Production Checklist

- [ ] **Decide on data providers** (NSE API, third-party, or scraping)
- [ ] **Obtain API keys** and add to `.env`
- [ ] **Update `_fetch_nse_price()`** with real API calls
- [ ] **Update `_fetch_tbill_rates()`** with real rates
- [ ] **Add caching** (5-15 min for prices, 1 day for rates)
- [ ] **Add rate limiting** to avoid API throttling
- [ ] **Test error handling** (API down, rate limits, bad responses)
- [ ] **Add monitoring** to alert when data goes stale
- [ ] **Update profile cards** to show "Last updated: [time]"

---

## 🎯 Quick Win: Start with Global Data

While NSE integration is pending, start with global markets (easier):

```python
import yfinance as yf

def get_sp500_context(self):
    spy = yf.Ticker("SPY")
    hist = spy.history(period="5d")
    current_price = hist['Close'][-1]
    week_change = ((hist['Close'][-1] / hist['Close'][0]) - 1) * 100
    
    return f"S&P 500 at ${current_price:.2f}, {week_change:+.1f}% this week (LIVE DATA)"
```

---

## 🆘 Troubleshooting

### "Still seeing fake prices!"

1. Check logs: `grep "Real data enabled" server.log`
2. Verify API keys in `.env` are loaded
3. Test API call directly: `curl https://api.provider.com/test`
4. Check cache expiry: Old cached data may persist

### "API calls failing"

1. Check rate limits (most free tiers: 5-60 calls/min)
2. Verify API key is valid
3. Check network/firewall not blocking requests
4. Add retry logic with exponential backoff

### "Data is stale"

1. Reduce cache expiry time (5 min for prices)
2. Add "Last updated" timestamp to profile cards
3. Force cache refresh on demand

---

## 💡 Best Practices

1. **Cache aggressively** - Stock prices don't change every second
2. **Use fallbacks** - API down? Fall back to scraping or simulated
3. **Label data source** - Always tell users if data is live vs simulated
4. **Rate limit yourself** - Don't hammer APIs
5. **Monitor costs** - API calls add up on premium tiers

---

## 📚 Resources

- **NSE Kenya:** https://www.nse.co.ke
- **Central Bank of Kenya:** https://www.centralbank.go.ke
- **Alpha Vantage Docs:** https://www.alphavantage.co/documentation/
- **Finnhub Docs:** https://finnhub.io/docs/api
- **yfinance Docs:** https://pypi.org/project/yfinance/

---

**Last Updated:** November 3, 2025  
**Status:** Simulated data with API integration framework ready



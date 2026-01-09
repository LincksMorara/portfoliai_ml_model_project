# FMP (Financial Modeling Prep) API Testing Module

A standalone Express.js backend module for integrating FMP API into your project. Provides quote data, company profiles, and financial information.

## 📋 Overview

This module includes:
- Express.js server with rate limiting and caching
- Two main endpoints: Quote and Profile
- Automatic response normalization
- Error handling and logging
- Health check endpoint

## 🚀 Quick Start

### 1. Copy Files

Copy the entire `fmp-testing` folder to your project.

### 2. Install Dependencies

```bash
npm install express axios cors express-rate-limit node-cache dotenv
# or
yarn add express axios cors express-rate-limit node-cache dotenv
```

### 3. Set Environment Variable

Create or update your `.env` file in the backend directory:

```env
PORT=4000
FMP_API_KEY=your_fmp_api_key_here
```

**Get your API key:** https://site.financialmodelingprep.com/developer/docs/

### 4. Start the Server

```bash
cd fmp-testing
npm install
node server.js
```

The server will start on `http://localhost:4000`

### 5. Test the API

```bash
# Health check
curl http://localhost:4000/health

# Get quote
curl http://localhost:4000/api/quote/AAPL

# Get profile
curl http://localhost:4000/api/profile/AAPL
```

## 📁 File Structure

```
fmp-testing/
├── FMP_README.md          # This file
├── server.js              # Express server with FMP endpoints
└── package.json           # Dependencies
```

## 🔑 API Key Setup

1. **Sign up:** Go to https://site.financialmodelingprep.com/developer/
2. **Choose plan:** Free tier available with limits
3. **Get key:** Copy your API key from dashboard
4. **Add to `.env`:** `FMP_API_KEY=paste_key_here`

## 📊 API Endpoints

### 1. Health Check

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "ok"
}
```

**Use case:** Verify server is running

---

### 2. Quote Data

**Endpoint:** `GET /api/quote/:symbol`

**Parameters:**
- `:symbol` - Stock ticker (e.g., 'AAPL', 'MSFT')

**Response:**
```json
{
  "symbol": "AAPL",
  "price": 175.34,
  "change": -1.2,
  "volume": 45212000,
  "timestamp": 1694304000
}
```

**Headers:**
- `X-Cache: HIT` or `X-Cache: MISS`

**Example:**
```bash
curl http://localhost:4000/api/quote/AAPL
```

---

### 3. Company Profile

**Endpoint:** `GET /api/profile/:symbol`

**Parameters:**
- `:symbol` - Stock ticker (e.g., 'AAPL', 'MSFT')

**Response:**
```json
{
  "companyName": "Apple Inc.",
  "symbol": "AAPL",
  "image": "https://logo.clearbit.com/apple.com",
  "exchangeFullName": "NASDAQ",
  "industry": "Consumer Electronics",
  "sector": "Technology",
  "ceo": "Tim Cook",
  "price": 175.34,
  "changePercentage": -0.68,
  "marketCap": 2760000000000,
  "description": "Apple Inc. designs, manufactures, and markets...",
  "website": "https://www.apple.com"
}
```

**Headers:**
- `X-Cache: HIT` or `X-Cache: MISS`

**Example:**
```bash
curl http://localhost:4000/api/profile/MSFT
```

---

## ⚙️ Features

### Rate Limiting
- **120 requests/hour per IP**
- Configurable in `server.js`
- Returns 429 status when exceeded

### Caching
- **60-second TTL**
- Reduces API calls
- Cache status in headers

### Error Handling
- Comprehensive error messages
- HTTP status codes
- Detailed logging

### CORS Support
- Enabled for all origins
- Configure in `server.js` if needed

---

## 🔧 Configuration

Edit `server.js` to customize:

```javascript
// Change port
const PORT = process.env.PORT || 4000;

// Adjust rate limit
const limiter = rateLimit({
  windowMs: 60 * 60 * 1000, // 1 hour
  max: 120, // requests per hour
});

// Change cache TTL
const cache = new NodeCache({ stdTTL: 60 }); // seconds

// Modify CORS settings
app.use(cors({
  origin: 'http://localhost:3000' // specific origin
}));
```

---

## 🧪 Testing Guide

### Manual Testing

```bash
# 1. Health check
curl http://localhost:4000/health

# 2. Test quote
curl http://localhost:4000/api/quote/AAPL
curl http://localhost:4000/api/quote/TSLA

# 3. Test profile
curl http://localhost:4000/api/profile/MSFT
curl http://localhost:4000/api/profile/NVDA

# 4. Test caching (run twice quickly)
curl -v http://localhost:4000/api/quote/AAPL
# Second call should show X-Cache: HIT

# 5. Test error handling
curl http://localhost:4000/api/quote/INVALID
# Should return 404 error
```

### Using Postman

1. Import the collection from `examples/`
2. Set base URL: `http://localhost:4000`
3. Run requests

---

## 🔌 Integration Examples

### Frontend Integration (React/Next.js)

```typescript
// Fetch quote
const response = await fetch('http://localhost:4000/api/quote/AAPL');
const quote = await response.json();
console.log(`${quote.symbol}: $${quote.price}`);

// Fetch profile
const profileResponse = await fetch('http://localhost:4000/api/profile/AAPL');
const profile = await profileResponse.json();
console.log(profile.description);
```

### React Component Example

```tsx
import { useState, useEffect } from 'react';

function StockQuote({ symbol }: { symbol: string }) {
  const [quote, setQuote] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchQuote() {
      try {
        const response = await fetch(`http://localhost:4000/api/quote/${symbol}`);
        const data = await response.json();
        setQuote(data);
      } catch (error) {
        console.error('Error:', error);
      } finally {
        setLoading(false);
      }
    }
    
    fetchQuote();
  }, [symbol]);

  if (loading) return <div>Loading...</div>;
  
  return (
    <div>
      <h2>{quote.symbol}</h2>
      <p>Price: ${quote.price}</p>
      <p>Change: {quote.change}</p>
    </div>
  );
}
```

### Node.js Integration

```javascript
const axios = require('axios');

async function getQuote(symbol) {
  try {
    const response = await axios.get(`http://localhost:4000/api/quote/${symbol}`);
    return response.data;
  } catch (error) {
    console.error('Error:', error.response?.data);
    throw error;
  }
}

// Usage
getQuote('AAPL').then(quote => {
  console.log(`${quote.symbol}: $${quote.price}`);
});
```

---

## 📝 Response Formats

### Quote Response

```typescript
interface QuoteData {
  symbol: string;      // Stock ticker
  price: number;       // Current price
  change: number;      // Price change
  volume: number;      // Trading volume
  timestamp: number;   // Unix timestamp
}
```

### Profile Response

```typescript
interface ProfileData {
  companyName: string;        // Full company name
  symbol: string;             // Stock ticker
  image: string;              // Logo URL (Clearbit)
  exchangeFullName: string;   // Exchange name
  industry: string;           // Industry
  sector: string;             // Sector
  ceo: string;                // CEO name
  price: number;              // Current price
  changePercentage: number;   // Price change %
  marketCap: number;          // Market capitalization
  description: string;        // Company description
  website: string;            // Company website
}
```

### Error Response

```json
{
  "error": "Failed to fetch quote data",
  "message": "No data found for INVALID"
}
```

---

## ⚠️ Error Handling

### Common HTTP Status Codes

- **200:** Success
- **404:** Symbol not found
- **429:** Rate limit exceeded
- **500:** Server error

### Error Response Format

```json
{
  "error": "Error description",
  "message": "Detailed error message"
}
```

---

## 🔄 Migration Guide

### From This Project

1. **Copy files:** All files from `api_modules/fmp-testing/`
2. **Update URLs:** Change any hardcoded URLs
3. **Environment:** Add FMP_API_KEY to your `.env`
4. **Dependencies:** Run `npm install` to install packages
5. **Test:** Start server and test endpoints

### Deploying to Production

1. **Environment variables:** Use production API key
2. **Port:** Use process environment PORT
3. **CORS:** Restrict origins in production
4. **Rate limiting:** Adjust based on your needs
5. **HTTPS:** Use reverse proxy (nginx, etc.)

### Docker Deployment

```dockerfile
FROM node:18
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm install
COPY server.js ./
EXPOSE 4000
CMD ["node", "server.js"]
```

---

## 🧪 Advanced Testing

### Load Testing

```bash
# Install Apache Bench
brew install httpd # macOS
# apt-get install apache2-utils # Linux

# Test rate limiting
ab -n 200 -c 10 http://localhost:4000/api/quote/AAPL
```

### Cache Testing

```bash
# First request (cache MISS)
curl -v http://localhost:4000/api/quote/AAPL

# Second request within 60s (cache HIT)
curl -v http://localhost:4000/api/quote/AAPL
```

---

## 📚 Additional Resources

- **FMP Documentation:** https://site.financialmodelingprep.com/developer/docs/
- **FMP API Reference:** https://financialmodelingprep.com/developer/docs/
- **Rate Limits:** Check your plan's limits
- **Support:** Contact FMP support for API issues

---

## ⚡ Performance Tips

1. **Use caching:** Already implemented (60s TTL)
2. **Batch requests:** Group related API calls
3. **Monitor rate limits:** Don't exceed your plan
4. **Cache static data:** Company profiles rarely change
5. **Use CDN:** For production deployments

---

## 🐛 Troubleshooting

### "FMP_API_KEY is required"
- Check `.env` file exists in project root
- Verify variable name is `FMP_API_KEY`
- Restart server after changing `.env`

### "Rate limit exceeded"
- Upgrade your FMP plan
- Implement additional caching
- Reduce API call frequency

### "No data found"
- Check symbol is valid
- Verify API key has access to that data
- Some endpoints require premium subscriptions

### Connection refused
- Check server is running
- Verify port 4000 is available
- Check firewall settings

---

## 📄 License

This module is part of the PortfoliAI project and can be used freely for integration purposes.

## 🤝 Support

For issues:
1. Check server logs
2. Verify API key is valid
3. Review FMP API documentation
4. Check network connectivity


const express = require('express');
const axios = require('axios');
const cors = require('cors');
const rateLimit = require('express-rate-limit');
const NodeCache = require('node-cache');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 4000;

// Initialize cache with 60 second TTL
const cache = new NodeCache({ stdTTL: 60 });

// Rate limiter: 120 requests per hour per IP
const limiter = rateLimit({
  windowMs: 60 * 60 * 1000, // 1 hour
  max: 120, // limit each IP to 120 requests per windowMs
  message: {
    error: 'Too many requests from this IP, please try again later.',
    retryAfter: '1 hour'
  },
  standardHeaders: true,
  legacyHeaders: false,
});

// Middleware
app.use(cors());
app.use(express.json());
app.use(limiter);

// FMP API configuration
const FMP_BASE_URL = 'https://financialmodelingprep.com/api/v3';
const FMP_API_KEY = process.env.FMP_API_KEY;

if (!FMP_API_KEY) {
  console.error('❌ FMP_API_KEY is required. Please set it in your .env file');
  process.exit(1);
}

// Helper function to add cache headers
const addCacheHeader = (res, cacheHit) => {
  res.set('X-Cache', cacheHit ? 'HIT' : 'MISS');
};

// Helper function to get cached data or fetch from API
const getCachedOrFetch = async (cacheKey, fetchFunction) => {
  const cached = cache.get(cacheKey);
  if (cached) {
    return { data: cached, fromCache: true };
  }
  
  const data = await fetchFunction();
  cache.set(cacheKey, data);
  return { data, fromCache: false };
};

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

// Quote endpoint
app.get('/api/quote/:symbol', async (req, res) => {
  try {
    const { symbol } = req.params;
    const upperSymbol = symbol.toUpperCase();
    
    const cacheKey = `quote_${upperSymbol}`;
    
    const { data, fromCache } = await getCachedOrFetch(cacheKey, async () => {
      const response = await axios.get(`${FMP_BASE_URL}/quote/${upperSymbol}?apikey=${FMP_API_KEY}`);
      
      if (!response.data || response.data.length === 0) {
        throw new Error(`No data found for ${upperSymbol}`);
      }
      
      const quote = response.data[0];
      
      // Normalize response
      return {
        symbol: quote.symbol,
        price: quote.price,
        change: quote.change,
        volume: quote.volume,
        timestamp: Math.floor(Date.now() / 1000)
      };
    });
    
    addCacheHeader(res, fromCache);
    res.json(data);
    
  } catch (error) {
    console.error('Quote API error:', error.message);
    if (error.response?.data) {
      console.error('API Response:', error.response.data);
    }
    
    if (error.message.includes('No data found')) {
      return res.status(404).json({ 
        error: `No data found for ${req.params.symbol.toUpperCase()}`
      });
    }
    
    res.status(500).json({ 
      error: 'Failed to fetch quote data',
      message: error.message 
    });
  }
});

// Profile endpoint
app.get('/api/profile/:symbol', async (req, res) => {
  try {
    const { symbol } = req.params;
    const upperSymbol = symbol.toUpperCase();
    
    const cacheKey = `profile_${upperSymbol}`;
    
    const { data, fromCache } = await getCachedOrFetch(cacheKey, async () => {
      const response = await axios.get(`${FMP_BASE_URL}/profile/${upperSymbol}?apikey=${FMP_API_KEY}`);
      
      if (!response.data || response.data.length === 0) {
        throw new Error(`No data found for ${upperSymbol}`);
      }
      
      const profile = response.data[0];
      
      // Normalize response
      return {
        companyName: profile.companyName,
        symbol: profile.symbol,
        image: `https://logo.clearbit.com/${profile.website || profile.companyName.toLowerCase().replace(/\s+/g, '')}.com`,
        exchangeFullName: profile.exchangeShortName,
        industry: profile.industry,
        sector: profile.sector,
        ceo: profile.ceo,
        price: profile.price,
        changePercentage: profile.changesPercentage,
        marketCap: profile.mktCap,
        description: profile.description,
        website: profile.website
      };
    });
    
    addCacheHeader(res, fromCache);
    res.json(data);
    
  } catch (error) {
    console.error('Profile API error:', error.message);
    if (error.response?.data) {
      console.error('API Response:', error.response.data);
    }
    
    if (error.message.includes('No data found')) {
      return res.status(404).json({ 
        error: `No data found for ${req.params.symbol.toUpperCase()}`
      });
    }
    
    res.status(500).json({ 
      error: 'Failed to fetch profile data',
      message: error.message 
    });
  }
});

// Error handler
app.use((error, req, res, next) => {
  console.error('Server error:', error);
  res.status(500).json({ 
    error: 'Internal server error',
    message: error.message 
  });
});

// Start server
app.listen(PORT, () => {
  console.log(`🚀 FMP API Server running on port ${PORT}`);
  console.log(`📊 Health check: http://localhost:${PORT}/health`);
  console.log(`📈 Quote API: http://localhost:${PORT}/api/quote/AAPL`);
  console.log(`🏢 Profile API: http://localhost:${PORT}/api/profile/AAPL`);
  console.log(`⚡ Rate limit: 120 requests/hour per IP`);
  console.log(`💾 Cache TTL: 60 seconds`);
});

module.exports = app;


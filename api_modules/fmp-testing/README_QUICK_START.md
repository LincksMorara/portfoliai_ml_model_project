# 🚀 FMP API Quick Start

Get up and running in 5 minutes!

## Step 1: Setup

```bash
# Copy the fmp-testing folder to your project
# Then install dependencies
cd fmp-testing
npm install
```

## Step 2: Configure

```bash
# Copy the example env file
cp example.env .env

# Edit .env and add your API key
# FMP_API_KEY=your_key_here
```

**Get your free API key:** https://financialmodelingprep.com/developer/

## Step 3: Run

```bash
# Start the server
npm start

# You should see:
# 🚀 FMP API Server running on port 4000
```

## Step 4: Test

```bash
# In another terminal, run the test client
node test-client.js

# Or test manually with curl:
curl http://localhost:4000/api/quote/AAPL
```

## Done! ✅

Your FMP API server is running. Use it in your projects!

## Next Steps

- Read `FMP_README.md` for detailed documentation
- Check `test-client.js` for usage examples
- Integrate into your frontend/backend


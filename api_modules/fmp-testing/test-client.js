/**
 * FMP API Test Client
 * 
 * Simple Node.js client to test the FMP API server
 * Usage: node test-client.js
 */

const axios = require('axios');

const BASE_URL = 'http://localhost:4000';

// Color codes for terminal output
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[36m',
  gray: '\x1b[90m'
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

async function testHealth() {
  log('\n=== Testing Health Check ===', 'blue');
  try {
    const response = await axios.get(`${BASE_URL}/health`);
    log(`✓ Health check passed: ${response.data.status}`, 'green');
    return true;
  } catch (error) {
    log(`✗ Health check failed: ${error.message}`, 'red');
    return false;
  }
}

async function testQuote(symbol) {
  log(`\n=== Testing Quote API for ${symbol} ===`, 'blue');
  try {
    const startTime = Date.now();
    const response = await axios.get(`${BASE_URL}/api/quote/${symbol}`);
    const duration = Date.now() - startTime;
    
    const cacheStatus = response.headers['x-cache'];
    log(`✓ Quote fetched successfully (${duration}ms, ${cacheStatus})`, 'green');
    log(`  Symbol: ${response.data.symbol}`, 'gray');
    log(`  Price: $${response.data.price}`, 'gray');
    log(`  Change: ${response.data.change >= 0 ? '+' : ''}${response.data.change}`, 'gray');
    log(`  Volume: ${response.data.volume.toLocaleString()}`, 'gray');
    return true;
  } catch (error) {
    log(`✗ Quote fetch failed: ${error.response?.data?.error || error.message}`, 'red');
    return false;
  }
}

async function testProfile(symbol) {
  log(`\n=== Testing Profile API for ${symbol} ===`, 'blue');
  try {
    const startTime = Date.now();
    const response = await axios.get(`${BASE_URL}/api/profile/${symbol}`);
    const duration = Date.now() - startTime;
    
    const cacheStatus = response.headers['x-cache'];
    log(`✓ Profile fetched successfully (${duration}ms, ${cacheStatus})`, 'green');
    log(`  Company: ${response.data.companyName}`, 'gray');
    log(`  Industry: ${response.data.industry}`, 'gray');
    log(`  Sector: ${response.data.sector}`, 'gray');
    log(`  Market Cap: $${(response.data.marketCap / 1e9).toFixed(2)}B`, 'gray');
    return true;
  } catch (error) {
    log(`✗ Profile fetch failed: ${error.response?.data?.error || error.message}`, 'red');
    return false;
  }
}

async function testCaching() {
  log('\n=== Testing Cache ===', 'blue');
  try {
    const symbol = 'AAPL';
    
    log('First request (should be MISS)...', 'yellow');
    const response1 = await axios.get(`${BASE_URL}/api/quote/${symbol}`);
    const cache1 = response1.headers['x-cache'];
    log(`Cache status: ${cache1}`, 'gray');
    
    log('Second request immediately after (should be HIT)...', 'yellow');
    const response2 = await axios.get(`${BASE_URL}/api/quote/${symbol}`);
    const cache2 = response2.headers['x-cache'];
    log(`Cache status: ${cache2}`, 'gray');
    
    if (cache1 === 'MISS' && cache2 === 'HIT') {
      log('✓ Cache working correctly', 'green');
      return true;
    } else {
      log('✗ Cache not working as expected', 'red');
      return false;
    }
  } catch (error) {
    log(`✗ Cache test failed: ${error.message}`, 'red');
    return false;
  }
}

async function testErrorHandling() {
  log('\n=== Testing Error Handling ===', 'blue');
  try {
    log('Testing invalid symbol...', 'yellow');
    const response = await axios.get(`${BASE_URL}/api/quote/INVALID_SYMBOL_12345`, {
      validateStatus: () => true // Don't throw on non-2xx
    });
    
    if (response.status === 404) {
      log(`✓ Error handling working (404 for invalid symbol)`, 'green');
      return true;
    } else {
      log(`✗ Unexpected status: ${response.status}`, 'red');
      return false;
    }
  } catch (error) {
    log(`✗ Error test failed: ${error.message}`, 'red');
    return false;
  }
}

async function runAllTests() {
  log('='.repeat(60), 'blue');
  log('FMP API Server Test Suite', 'blue');
  log('='.repeat(60), 'blue');
  
  const results = {
    passed: 0,
    failed: 0
  };
  
  // Health check
  const healthOK = await testHealth();
  results[healthOK ? 'passed' : 'failed']++;
  
  if (!healthOK) {
    log('\n❌ Server is not running. Please start the server first.', 'red');
    log('Run: node server.js', 'yellow');
    return;
  }
  
  // Wait a bit before continuing
  await new Promise(resolve => setTimeout(resolve, 500));
  
  // Test quotes
  const quote1 = await testQuote('AAPL');
  results[quote1 ? 'passed' : 'failed']++;
  
  await new Promise(resolve => setTimeout(resolve, 500));
  
  const quote2 = await testQuote('MSFT');
  results[quote2 ? 'passed' : 'failed']++;
  
  await new Promise(resolve => setTimeout(resolve, 500));
  
  // Test profiles
  const profile1 = await testProfile('TSLA');
  results[profile1 ? 'passed' : 'failed']++;
  
  await new Promise(resolve => setTimeout(resolve, 500));
  
  // Test caching
  const cacheOK = await testCaching();
  results[cacheOK ? 'passed' : 'failed']++;
  
  await new Promise(resolve => setTimeout(resolve, 500));
  
  // Test error handling
  const errorOK = await testErrorHandling();
  results[errorOK ? 'passed' : 'failed']++;
  
  // Summary
  log('\n' + '='.repeat(60), 'blue');
  log('Test Summary', 'blue');
  log('='.repeat(60), 'blue');
  log(`Total Tests: ${results.passed + results.failed}`, 'yellow');
  log(`Passed: ${results.passed}`, 'green');
  log(`Failed: ${results.failed}`, 'red');
  log('='.repeat(60), 'blue');
  
  if (results.failed === 0) {
    log('\n🎉 All tests passed!', 'green');
  } else {
    log('\n⚠️  Some tests failed. Check the output above.', 'yellow');
  }
}

// Run tests
runAllTests().catch(error => {
  log(`\n✗ Test suite failed: ${error.message}`, 'red');
  process.exit(1);
});


"""
FMP (Financial Modeling Prep) API Integration
Provides real-time stock quotes and company profiles
"""

import requests
import os
import logging
from typing import Dict, Optional
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class FMPClient:
    """Client for Financial Modeling Prep API"""
    
    def __init__(self):
        self.api_key = os.getenv('FMP_API_KEY')
        # Use the /stable endpoints because /api/v3 requires paid plans
        self.base_url = 'https://financialmodelingprep.com/stable'
        
        if not self.api_key:
            logger.warning("FMP_API_KEY not found in environment variables")
        else:
            logger.info("✅ FMP Client initialized")
    
    def get_quote(self, symbol: str) -> Optional[Dict]:
        """
        Get real-time stock quote
        
        Args:
            symbol: Stock ticker (e.g., 'AAPL', 'MSFT')
            
        Returns:
            Dict with price data or None if error
        """
        if not self.api_key:
            return {"error": "FMP_API_KEY not configured"}
        
        try:
            symbol = symbol.upper()
            url = f"{self.base_url}/quote"
            
            logger.info(f"📊 Fetching quote for {symbol} from FMP stable endpoint...")
            
            response = requests.get(
                url,
                params={'symbol': symbol, 'apikey': self.api_key},
                timeout=10
            )
            
            response.raise_for_status()
            data = response.json()
            
            if not data or len(data) == 0:
                return {
                    "error": f"No data found for symbol {symbol}",
                    "symbol": symbol
                }
            
            quote = data[0]
            
            result = {
                "source": "FMP",
                "symbol": quote.get('symbol'),
                "name": quote.get('name'),
                "price": quote.get('price'),
                "change": quote.get('change'),
                "change_percent": quote.get('changesPercentage') if quote.get('changesPercentage') is not None else quote.get('changePercentage'),
                "day_high": quote.get('dayHigh'),
                "day_low": quote.get('dayLow'),
                "year_high": quote.get('yearHigh'),
                "year_low": quote.get('yearLow'),
                "volume": quote.get('volume'),
                "market_cap": quote.get('marketCap'),
                "timestamp": datetime.now().isoformat(),
                "raw_data": quote  # Include full response for debugging
            }
            
            logger.info(f"✅ Got quote for {symbol}: ${result['price']}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ FMP API error: {e}")
            return {
                "error": f"Failed to fetch data: {str(e)}",
                "symbol": symbol
            }
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            return {
                "error": f"Unexpected error: {str(e)}",
                "symbol": symbol
            }
    
    def get_profile(self, symbol: str) -> Optional[Dict]:
        """
        Get company profile information
        
        Args:
            symbol: Stock ticker
            
        Returns:
            Dict with company info or None if error
        """
        if not self.api_key:
            return {"error": "FMP_API_KEY not configured"}
        
        try:
            symbol = symbol.upper()
            url = f"{self.base_url}/profile"
            
            logger.info(f"🏢 Fetching profile for {symbol} from FMP stable endpoint...")
            
            response = requests.get(
                url,
                params={'symbol': symbol, 'apikey': self.api_key},
                timeout=10
            )
            
            response.raise_for_status()
            data = response.json()
            
            if not data or len(data) == 0:
                return {
                    "error": f"No profile found for symbol {symbol}",
                    "symbol": symbol
                }
            
            profile = data[0]
            
            result = {
                "source": "FMP",
                "symbol": profile.get('symbol'),
                "company_name": profile.get('companyName'),
                "price": profile.get('price'),
                "ceo": profile.get('ceo'),
                "industry": profile.get('industry'),
                "sector": profile.get('sector'),
                "website": profile.get('website'),
                "description": profile.get('description'),
                "exchange": profile.get('exchangeShortName'),
                "market_cap": profile.get('mktCap'),
                "timestamp": datetime.now().isoformat(),
                "raw_data": profile
            }
            
            logger.info(f"✅ Got profile for {symbol}: {result['company_name']}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ FMP API error: {e}")
            return {
                "error": f"Failed to fetch profile: {str(e)}",
                "symbol": symbol
            }
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            return {
                "error": f"Unexpected error: {str(e)}",
                "symbol": symbol
            }


# Global instance
_fmp_client = None

def get_fmp_client() -> FMPClient:
    """Get or create FMP client singleton"""
    global _fmp_client
    if _fmp_client is None:
        _fmp_client = FMPClient()
    return _fmp_client


if __name__ == "__main__":
    # Test the client
    client = FMPClient()
    
    print("\n🧪 Testing FMP Integration\n")
    
    # Test quote
    print("📊 Testing Quote API (AAPL)...")
    quote = client.get_quote('AAPL')
    print(f"Result: {quote}\n")
    
    # Test profile
    print("🏢 Testing Profile API (AAPL)...")
    profile = client.get_profile('AAPL')
    print(f"Result: {profile}\n")



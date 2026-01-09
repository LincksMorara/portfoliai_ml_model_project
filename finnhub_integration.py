"""
Finnhub API Integration
Provides company news and market data
"""

import requests
import os
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class FinnhubClient:
    """Client for Finnhub API"""
    
    def __init__(self):
        self.api_key = os.getenv('FINNHUB_API_KEY')
        self.base_url = 'https://finnhub.io/api/v1'
        
        if not self.api_key:
            logger.warning("FINNHUB_API_KEY not found in environment variables")
        else:
            logger.info("✅ Finnhub Client initialized")
    
    def get_company_news(self, symbol: str, days_back: int = 7) -> Optional[Dict]:
        """
        Get company news articles
        
        Args:
            symbol: Stock ticker (e.g., 'AAPL')
            days_back: Number of days to look back (default 7)
            
        Returns:
            Dict with news articles or error
        """
        if not self.api_key:
            return {"error": "FINNHUB_API_KEY not configured"}
        
        try:
            symbol = symbol.upper()
            
            # Calculate date range
            today = datetime.now()
            from_date = (today - timedelta(days=days_back)).strftime('%Y-%m-%d')
            to_date = today.strftime('%Y-%m-%d')
            
            url = f"{self.base_url}/company-news"
            
            logger.info(f"📰 Fetching news for {symbol} from {from_date} to {to_date}...")
            
            response = requests.get(
                url,
                params={
                    'symbol': symbol,
                    'from': from_date,
                    'to': to_date,
                    'token': self.api_key
                },
                timeout=10
            )
            
            response.raise_for_status()
            articles = response.json()
            
            if not articles or len(articles) == 0:
                return {
                    "source": "Finnhub",
                    "symbol": symbol,
                    "articles": [],
                    "count": 0,
                    "message": f"No news found for {symbol} in the last {days_back} days",
                    "from_date": from_date,
                    "to_date": to_date
                }
            
            # Format articles
            formatted_articles = []
            for article in articles[:10]:  # Limit to 10 most recent
                formatted_articles.append({
                    "headline": article.get('headline', 'No headline'),
                    "summary": article.get('summary', 'No summary'),
                    "source": article.get('source', 'Unknown'),
                    "url": article.get('url', ''),
                    "datetime": datetime.fromtimestamp(article.get('datetime', 0)).isoformat(),
                    "related": article.get('related', '')
                })
            
            result = {
                "source": "Finnhub",
                "symbol": symbol,
                "articles": formatted_articles,
                "count": len(formatted_articles),
                "from_date": from_date,
                "to_date": to_date,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"✅ Got {len(formatted_articles)} news articles for {symbol}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Finnhub API error: {e}")
            return {
                "error": f"Failed to fetch news: {str(e)}",
                "symbol": symbol
            }
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            return {
                "error": f"Unexpected error: {str(e)}",
                "symbol": symbol
            }
    
    def get_quote(self, symbol: str) -> Optional[Dict]:
        """
        Get real-time quote from Finnhub
        
        Args:
            symbol: Stock ticker
            
        Returns:
            Dict with quote data or error
        """
        if not self.api_key:
            return {"error": "FINNHUB_API_KEY not configured"}
        
        try:
            symbol = symbol.upper()
            url = f"{self.base_url}/quote"
            
            logger.info(f"📊 Fetching quote for {symbol} from Finnhub...")
            
            response = requests.get(
                url,
                params={
                    'symbol': symbol,
                    'token': self.api_key
                },
                timeout=10
            )
            
            response.raise_for_status()
            data = response.json()
            
            if not data or data.get('c') == 0:
                return {
                    "error": f"No quote data for {symbol}",
                    "symbol": symbol
                }
            
            result = {
                "source": "Finnhub",
                "symbol": symbol,
                "current_price": data.get('c'),  # Current price
                "change": data.get('d'),  # Change
                "percent_change": data.get('dp'),  # Percent change
                "high": data.get('h'),  # High
                "low": data.get('l'),  # Low
                "open": data.get('o'),  # Open
                "previous_close": data.get('pc'),  # Previous close
                "timestamp": datetime.now().isoformat(),
                "raw_data": data
            }
            
            logger.info(f"✅ Got quote for {symbol}: ${result['current_price']}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Finnhub API error: {e}")
            return {
                "error": f"Failed to fetch quote: {str(e)}",
                "symbol": symbol
            }
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            return {
                "error": f"Unexpected error: {str(e)}",
                "symbol": symbol
            }


# Global instance
_finnhub_client = None

def get_finnhub_client() -> FinnhubClient:
    """Get or create Finnhub client singleton"""
    global _finnhub_client
    if _finnhub_client is None:
        _finnhub_client = FinnhubClient()
    return _finnhub_client


if __name__ == "__main__":
    # Test the client
    client = FinnhubClient()
    
    print("\n🧪 Testing Finnhub Integration\n")
    
    # Test news
    print("📰 Testing News API (AAPL)...")
    news = client.get_company_news('AAPL', days_back=7)
    print(f"Found {news.get('count', 0)} articles\n")
    if news.get('articles'):
        print(f"Latest headline: {news['articles'][0]['headline']}\n")
    
    # Test quote
    print("📊 Testing Quote API (AAPL)...")
    quote = client.get_quote('AAPL')
    print(f"Result: {quote}\n")



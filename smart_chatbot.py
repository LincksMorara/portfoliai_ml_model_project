"""
Smart Investment Research Chatbot
Provides personalized, context-aware investment analysis using user's profile and conversation history
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import os
from dotenv import load_dotenv

from fmp_integration import get_fmp_client
from finnhub_integration import get_finnhub_client

# Try to import Groq
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

load_dotenv()
logger = logging.getLogger(__name__)

class SmartChatbot:
    """
    Intelligent investment research assistant that provides personalized analysis
    based on user's investor profile and conversation history
    """
    
    def __init__(self):
        self.fmp = get_fmp_client()
        self.finnhub = get_finnhub_client()
        
        # Initialize Groq for analysis
        self.groq_key = os.getenv('GROQ_API_KEY')
        if self.groq_key and GROQ_AVAILABLE:
            self.groq = Groq(api_key=self.groq_key)
            self.llm_available = True
            logger.info("✅ Smart Chatbot initialized with Groq")
        else:
            self.groq = None
            self.llm_available = False
            logger.warning("⚠️ Groq not available - using basic responses")
        
        # In-memory conversation storage (in production, use Redis/database)
        self.conversations = {}
    
    def extract_symbols(self, message: str) -> List[str]:
        """Extract stock symbols from user message"""
        # Common stock symbols (can be enhanced with NLP)
        import re
        
        # Look for uppercase words that might be symbols
        potential_symbols = re.findall(r'\b[A-Z]{1,5}\b', message.upper())
        
        # Common symbols for reference
        common_symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 
                         'META', 'JPM', 'BAC', 'WMT', 'DIS', 'NFLX']
        
        # Filter to likely symbols
        symbols = [s for s in potential_symbols if s in common_symbols or len(s) <= 5]
        
        return symbols[:3]  # Limit to 3 symbols max
    
    def fetch_market_data(self, symbols: List[str]) -> Dict[str, Any]:
        """Fetch comprehensive market data for given symbols"""
        data = {}
        
        for symbol in symbols:
            try:
                # Get quote and profile from FMP
                quote = self.fmp.get_quote(symbol)
                profile = self.fmp.get_profile(symbol)
                
                # Get news from Finnhub
                news = self.finnhub.get_company_news(symbol, days_back=7)
                
                data[symbol] = {
                    'quote': quote,
                    'profile': profile,
                    'news': news,
                    'timestamp': datetime.now().isoformat()
                }
                
                logger.info(f"✅ Fetched data for {symbol}")
                
            except Exception as e:
                logger.error(f"❌ Error fetching data for {symbol}: {e}")
                data[symbol] = {'error': str(e)}
        
        return data
    
    def build_analysis_prompt(self, 
                             user_message: str,
                             user_profile: Dict[str, Any],
                             market_data: Dict[str, Any],
                             conversation_history: List[Dict]) -> str:
        """
        Build comprehensive prompt for LLM analysis
        """
        
        # Extract user profile details
        risk_score = user_profile.get('risk_score', 0.5)
        risk_category = user_profile.get('risk_category', 'Comfortable')
        persona = user_profile.get('persona', 'Strategic Balancer')
        
        # Build context about user
        user_context = f"""
USER'S INVESTOR PROFILE:
━━━━━━━━━━━━━━━━━━━━
Risk Score: {risk_score:.2f}/1.0 ({risk_category})
Investor Persona: {persona}
Risk Tolerance: {"High - can handle volatility" if risk_score > 0.7 else "Moderate - balanced approach" if risk_score > 0.4 else "Low - prefers stability"}
Investment Horizon: {"Long-term (5+ years)" if risk_score > 0.6 else "Medium-term (3-5 years)" if risk_score > 0.4 else "Short-term (1-3 years)"}
Profile Type: {"Growth-focused, can stomach 20-30% drawdowns" if risk_score > 0.7 else "Balanced, seeking steady growth with manageable risk" if risk_score > 0.4 else "Conservative, prioritizing capital preservation"}
        """
        
        # Format market data for context
        market_context = "\n\nLIVE MARKET DATA:\n━━━━━━━━━━━━━━━━━━━━\n"
        
        for symbol, data in market_data.items():
            if 'error' in data:
                continue
            
            quote = data.get('quote', {})
            profile = data.get('profile', {})
            news = data.get('news', {})
            
            if quote and not quote.get('error'):
                market_context += f"""
{symbol} ({profile.get('company_name', symbol)}):
• Current Price: ${quote.get('price', 0):.2f}
• Change: ${quote.get('change', 0):.2f} ({quote.get('change_percent', 0):.2f}%)
• Day Range: ${quote.get('day_low', 0):.2f} - ${quote.get('day_high', 0):.2f}
• 52-Week Range: ${quote.get('year_low', 0):.2f} - ${quote.get('year_high', 0):.2f}
• Volume: {quote.get('volume', 0):,}
• Market Cap: ${(quote.get('market_cap', 0) / 1e9):.2f}B
• P/E Ratio: {quote.get('raw_data', {}).get('pe', 'N/A')}

Company Info:
• CEO: {profile.get('ceo', 'N/A')}
• Industry: {profile.get('industry', 'N/A')}
• Sector: {profile.get('sector', 'N/A')}
"""
            
            # Add key news headlines
            if news and news.get('articles') and len(news['articles']) > 0:
                market_context += f"\nRecent News ({news.get('count', 0)} articles):\n"
                for i, article in enumerate(news['articles'][:3], 1):
                    market_context += f"{i}. {article.get('headline', 'No headline')}\n"
        
        # Format conversation history
        history_context = ""
        if conversation_history:
            history_context = "\n\nCONVERSATION HISTORY:\n━━━━━━━━━━━━━━━━━━━━\n"
            for msg in conversation_history[-5:]:  # Last 5 messages
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                history_context += f"{role.upper()}: {content[:200]}...\n"
        
        # Build the complete prompt
        prompt = f"""
You are a highly skilled investment research assistant helping an investor make informed decisions. 

{user_context}

{history_context}

{market_context}

USER'S CURRENT QUESTION:
━━━━━━━━━━━━━━━━━━━━
{user_message}

YOUR TASK:
━━━━━━━━━━━━━━━━━━━━
Provide a comprehensive, personalized analysis that:

1. **Directly answers their question** - Be conversational and insightful

2. **Analyzes the data in context of THEIR profile**:
   - How does this stock fit their risk tolerance?
   - Is the valuation appropriate for their goals?
   - Should they be aggressive or cautious?

3. **Provides deep analysis**:
   - Price context (near highs/lows? trending?)
   - Valuation (P/E reasonable? Growth justified?)
   - Recent catalysts (earnings, news driving price?)
   - Risk factors (volatility, sector risks?)
   
4. **Gives actionable insights**:
   - Clear recommendation (Strong Buy / Buy / Hold / Avoid)
   - Position sizing based on their risk profile
   - Entry strategy (all at once vs dollar-cost-average?)
   - What to watch (metrics, news, events)

5. **Educates as you explain**:
   - Explain jargon in simple terms
   - Show why metrics matter
   - Connect theory to practice

6. **Be their research partner**:
   - Friendly but professional tone
   - Acknowledge their situation
   - Proactive suggestions for next steps

RESPONSE FORMAT:
━━━━━━━━━━━━━━━━━━━━

**Quick Take:** [2-3 sentence summary]

**Detailed Analysis:**

[Comprehensive breakdown - 3-4 paragraphs covering valuation, momentum, risks, opportunities]

**For Your Profile ({risk_category}):**

[Specific guidance on how this fits THEIR risk profile, goals, and investment style]

**My Recommendation:**

[Clear action: Buy/Hold/Avoid, position size %, entry strategy]

**What to Watch:**

• [Key metric or event #1]
• [Key metric or event #2]
• [Key metric or event #3]

**Want to explore further?** [Suggest 2-3 follow-up questions]

---

Remember: You're analyzing for a **{risk_category} investor ({persona})**. Tailor everything to THEIR situation.
Be insightful, be practical, be their smart research partner.
        """
        
        return prompt.strip()
    
    def analyze_with_llm(self, prompt: str) -> str:
        """Send prompt to Groq for analysis"""
        if not self.llm_available:
            return "LLM analysis not available. Please add GROQ_API_KEY to .env"
        
        try:
            response = self.groq.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert investment research assistant. Provide thorough, personalized analysis that helps investors make informed decisions."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            analysis = response.choices[0].message.content
            logger.info(f"✅ Generated analysis ({len(analysis)} chars)")
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Error calling Groq: {e}")
            return f"Error generating analysis: {str(e)}"
    
    def get_conversation_history(self, user_id: str) -> List[Dict]:
        """Get conversation history for user"""
        return self.conversations.get(user_id, [])
    
    def save_to_history(self, user_id: str, role: str, content: str):
        """Save message to conversation history"""
        if user_id not in self.conversations:
            self.conversations[user_id] = []
        
        self.conversations[user_id].append({
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep only last 20 messages
        self.conversations[user_id] = self.conversations[user_id][-20:]
    
    def chat(self, 
             user_message: str,
             user_profile: Dict[str, Any],
             user_id: str = "default") -> Dict[str, Any]:
        """
        Main chat interface - processes user message and returns intelligent response
        """
        try:
            logger.info(f"💬 Processing message from user {user_id}: {user_message[:50]}...")
            
            # Save user message to history
            self.save_to_history(user_id, 'user', user_message)
            
            # Extract symbols from message
            symbols = self.extract_symbols(user_message)
            
            # If no symbols found, check if it's a general question
            if not symbols:
                # Check for common questions without symbols
                if any(word in user_message.lower() for word in ['what', 'how', 'should', 'can', 'tell me', 'explain']):
                    symbols = []  # General question
                else:
                    return {
                        'type': 'clarification',
                        'response': "I'd love to help! Could you mention a specific stock ticker? For example: 'What do you think about AAPL?' or 'Should I buy Tesla (TSLA)?'",
                        'suggestions': ['Tell me about Apple (AAPL)', 'Should I invest in Microsoft (MSFT)?', 'Compare GOOGL vs AMZN']
                    }
            
            # Fetch market data if symbols present
            market_data = {}
            if symbols:
                market_data = self.fetch_market_data(symbols)
            
            # Get conversation history
            conversation_history = self.get_conversation_history(user_id)
            
            # Build analysis prompt
            prompt = self.build_analysis_prompt(
                user_message,
                user_profile,
                market_data,
                conversation_history
            )
            
            # Get LLM analysis
            analysis = self.analyze_with_llm(prompt)
            
            # Save assistant response to history
            self.save_to_history(user_id, 'assistant', analysis)
            
            return {
                'type': 'analysis',
                'response': analysis,
                'symbols_analyzed': symbols,
                'market_data': market_data,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error in chat: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                'type': 'error',
                'response': f"I encountered an error while analyzing. Please try again. Error: {str(e)}"
            }


# Global instance
_smart_chatbot = None

def get_smart_chatbot() -> SmartChatbot:
    """Get or create smart chatbot singleton"""
    global _smart_chatbot
    if _smart_chatbot is None:
        _smart_chatbot = SmartChatbot()
    return _smart_chatbot


if __name__ == "__main__":
    # Test the smart chatbot
    chatbot = SmartChatbot()
    
    # Mock user profile
    test_profile = {
        'risk_score': 0.65,
        'risk_category': 'Comfortable',
        'persona': 'Strategic Balancer'
    }
    
    print("\n🤖 Testing Smart Investment Chatbot\n")
    
    # Test question
    response = chatbot.chat(
        "What do you think about Apple right now? Should I invest?",
        test_profile,
        user_id="test_user"
    )
    
    print(f"Response Type: {response['type']}")
    print(f"\n{response['response']}\n")



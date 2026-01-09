"""
Adaptive Investment Intelligence Chatbot
Refined conversational system with dynamic depth, natural tone, and smart interactivity
"""

import logging
from typing import Dict, List, Optional, Any, Literal
from datetime import datetime
import re
import os
from dotenv import load_dotenv

from fmp_integration import get_fmp_client
from finnhub_integration import get_finnhub_client

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

load_dotenv()
logger = logging.getLogger(__name__)

ResponseMode = Literal['quick', 'balanced', 'deep']

class AdaptiveChatbot:
    """
    Intelligent chatbot with adaptive response depth, natural persona integration,
    and dynamic conversation flow
    """
    
    def __init__(self):
        self.fmp = get_fmp_client()
        self.finnhub = get_finnhub_client()
        
        # Initialize Groq
        self.groq_key = os.getenv('GROQ_API_KEY')
        if self.groq_key and GROQ_AVAILABLE:
            self.groq = Groq(api_key=self.groq_key)
            self.llm_available = True
            logger.info("✅ Adaptive Chatbot initialized with Groq")
        else:
            self.groq = None
            self.llm_available = False
        
        # Conversation storage
        self.conversations = {}
        self.user_preferences = {}  # Track learned preferences
    
    def detect_response_mode(self, 
                            message: str, 
                            conversation_history: List[Dict],
                            user_preference: Optional[ResponseMode] = None) -> ResponseMode:
        """
        Intelligently detect appropriate response depth
        
        Returns: 'quick', 'balanced', or 'deep'
        """
        # User explicitly requested mode
        if user_preference:
            return user_preference
        
        # Check for explicit depth requests in message
        message_lower = message.lower()
        if any(word in message_lower for word in ['quick', 'briefly', 'summary', 'tldr', 'short']):
            return 'quick'
        
        if any(word in message_lower for word in ['detail', 'deep', 'comprehensive', 'full analysis', 'explain']):
            return 'deep'
        
        # Simple questions → quick
        simple_patterns = [
            r'^what is ',
            r'^what\'s ',
            r'^how much ',
            r'^current price',
            r'^price of ',
            r'trading at',
        ]
        
        for pattern in simple_patterns:
            if re.search(pattern, message_lower):
                return 'quick'
        
        # Complex questions → deep
        complex_keywords = ['should i', 'compare', 'vs', 'better', 'worth', 'invest', 
                           'portfolio', 'strategy', 'risk', 'pros and cons']
        
        if any(keyword in message_lower for keyword in complex_keywords):
            return 'deep'
        
        # Default: balanced for most queries
        return 'balanced'
    
    def detect_user_intent(self, message: str) -> str:
        """
        Categorize user's intent for better response targeting
        
        Returns: 'price_check', 'analysis', 'comparison', 'education', 'general'
        """
        message_lower = message.lower()
        
        # Price check
        if any(word in message_lower for word in ['price', 'trading at', 'current', 'quote']):
            return 'price_check'
        
        # Comparison
        if 'vs' in message_lower or 'versus' in message_lower or 'compare' in message_lower:
            return 'comparison'
        
        # Education
        if any(word in message_lower for word in ['what is', 'what does', 'explain', 'how does', 'why']):
            return 'education'
        
        # Investment decision
        if any(word in message_lower for word in ['should i', 'recommend', 'invest', 'buy', 'sell']):
            return 'analysis'
        
        return 'general'
    
    def extract_symbols(self, message: str) -> List[str]:
        """Extract stock symbols from message"""
        # Look for uppercase words that could be symbols
        potential_symbols = re.findall(r'\b[A-Z]{1,5}\b', message.upper())
        
        # Common stocks
        known_symbols = ['AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'TSLA', 'NVDA', 
                        'META', 'JPM', 'BAC', 'WMT', 'DIS', 'NFLX', 'AMD', 'INTC']
        
        # Also check for company names
        company_map = {
            'apple': 'AAPL', 'microsoft': 'MSFT', 'google': 'GOOGL', 
            'amazon': 'AMZN', 'tesla': 'TSLA', 'nvidia': 'NVDA',
            'meta': 'META', 'facebook': 'META', 'netflix': 'NFLX',
            'disney': 'DIS', 'walmart': 'WMT'
        }
        
        message_lower = message.lower()
        symbols = []
        
        # Check company names
        for company, symbol in company_map.items():
            if company in message_lower:
                symbols.append(symbol)
        
        # Add explicit symbols
        for symbol in potential_symbols:
            if symbol in known_symbols and symbol not in symbols:
                symbols.append(symbol)
        
        return symbols[:3]  # Max 3 symbols
    
    def fetch_smart_data(self, 
                        symbols: List[str], 
                        intent: str, 
                        mode: ResponseMode) -> Dict[str, Any]:
        """
        Fetch only the data needed for this specific query
        Optimizes for speed and relevance
        """
        data = {}
        
        for symbol in symbols:
            try:
                symbol_data = {}
                
                # Always fetch quote (it's fast)
                quote = self.fmp.get_quote(symbol)
                symbol_data['quote'] = quote
                
                # Fetch profile only for deep analysis or comparisons
                if mode in ['deep', 'balanced'] or intent in ['analysis', 'comparison']:
                    profile = self.fmp.get_profile(symbol)
                    symbol_data['profile'] = profile
                
                # Fetch news only for deep analysis
                if mode == 'deep' or intent == 'analysis':
                    news = self.finnhub.get_company_news(symbol, days_back=7)
                    symbol_data['news'] = news
                
                data[symbol] = symbol_data
                
            except Exception as e:
                logger.error(f"Error fetching data for {symbol}: {e}")
                data[symbol] = {'error': str(e)}
        
        return data
    
    def get_persona_context(self, 
                           user_profile: Dict[str, Any], 
                           conversation_history: List[Dict],
                           first_mention: bool = False) -> str:
        """
        Generate natural persona reference
        Only include full context on first mention or when directly relevant
        """
        risk_score = user_profile.get('risk_score', 0.5)
        category = user_profile.get('risk_category', 'Comfortable')
        
        # First time or when directly relevant
        if first_mention or len(conversation_history) < 2:
            return f"""
USER PROFILE:
Risk: {category} ({risk_score:.2f})
Tolerance: {"High volatility OK" if risk_score > 0.7 else "Moderate, balanced" if risk_score > 0.4 else "Low, stability-focused"}
"""
        
        # Subsequent mentions - natural reference
        return f"(User: {category} risk profile, score {risk_score:.2f})"
    
    def build_adaptive_prompt(self,
                             user_message: str,
                             user_profile: Dict[str, Any],
                             market_data: Dict[str, Any],
                             conversation_history: List[Dict],
                             mode: ResponseMode,
                             intent: str) -> str:
        """
        Build adaptive prompt based on mode, intent, and context
        """
        # Get compact persona context
        first_interaction = len(conversation_history) < 2
        persona_context = self.get_persona_context(user_profile, conversation_history, first_interaction)
        
        # Format market data concisely
        market_summary = self._format_market_data(market_data, mode)
        
        # Build mode-specific instructions
        mode_instructions = {
            'quick': {
                'length': '2-3 sentences max (50-80 words)',
                'structure': 'Single quick insight or answer',
                'tone': 'Concise and direct',
                'example': '**Quick Take:** AAPL at $270 near highs. Solid for moderate risk (your profile). Consider 5-8% allocation. 📈'
            },
            'balanced': {
                'length': '3-5 sentences (100-150 words)',
                'structure': 'Brief insight + key point + recommendation',
                'tone': 'Conversational but informative',
                'example': '**Brief:** [2 sentences]\n**Key:** [1-2 bullets]\n**For You:** [fit assessment]\n**Next:** [1 follow-up question]'
            },
            'deep': {
                'length': '300-400 words max',
                'structure': 'Structured analysis with clear sections',
                'tone': 'Analytical yet accessible',
                'example': '**Take:** [2-3 lines]\n**Analysis:** [2-3 paragraphs]\n**For You:** [fit]\n**Action:** [recommendation]\n**Watch:** [2-3 bullets]'
            }
        }
        
        current_mode = mode_instructions[mode]
        
        # Build the prompt
        prompt = f"""You are an adaptive investment advisor. Respond to this query with the RIGHT level of detail.

{persona_context}

{market_summary}

USER QUERY: "{user_message}"

RESPONSE MODE: {mode.upper()}
- Length: {current_mode['length']}
- Structure: {current_mode['structure']}
- Tone: {current_mode['tone']}

CRITICAL GUIDELINES:
1. **Be appropriately concise** - Don't over-explain in quick/balanced modes
2. **Natural persona reference** - Say "for your moderate risk profile" not "As a Strategic Balancer..."
3. **Data-driven** - Use the LIVE market data provided
4. **Actionable** - Always end with clear next step or insight
5. **Interactive** - Suggest 1-2 follow-up options naturally

RESPONSE FORMAT FOR {mode.upper()} MODE:
{current_mode['example']}

Remember: {mode} mode = {current_mode['length']}. Stick to it!
"""
        
        return prompt.strip()
    
    def _format_market_data(self, market_data: Dict[str, Any], mode: ResponseMode) -> str:
        """Format market data based on response mode"""
        if not market_data:
            return ""
        
        output = "LIVE DATA:\n"
        
        for symbol, data in market_data.items():
            if 'error' in data:
                continue
            
            quote = data.get('quote', {})
            if not quote or quote.get('error'):
                continue
            
            # Always show price
            output += f"• {symbol}: ${quote.get('price', 0):.2f}"
            
            # Add details based on mode
            if mode in ['balanced', 'deep']:
                change = quote.get('change', 0)
                change_pct = quote.get('change_percent', 0)
                output += f" ({change:+.2f}, {change_pct:+.2f}%)"
            
            if mode == 'deep':
                pe = quote.get('raw_data', {}).get('pe')
                if pe:
                    output += f", P/E {pe:.1f}"
            
            output += "\n"
        
        return output
    
    def generate_follow_ups(self, 
                           user_message: str, 
                           symbols: List[str], 
                           intent: str) -> List[str]:
        """Generate contextual follow-up suggestions"""
        suggestions = []
        
        if intent == 'price_check' and symbols:
            suggestions = [
                f"Should I invest in {symbols[0]}?",
                f"What are the risks with {symbols[0]}?",
                "Show me a detailed analysis"
            ]
        
        elif intent == 'analysis' and symbols:
            if len(symbols) == 1:
                suggestions = [
                    f"Compare {symbols[0]} with similar stocks",
                    f"What's driving {symbols[0]}'s price?",
                    f"Quick summary of {symbols[0]}"
                ]
            else:
                suggestions = [
                    f"Give me more detail on {symbols[0]}",
                    "Which better fits my profile?",
                    "Show me a comparison table"
                ]
        
        elif intent == 'education':
            suggestions = [
                "Show me an example with real stocks",
                "How does this apply to my portfolio?",
                "Explain it more simply"
            ]
        
        return suggestions[:2]  # Max 2 suggestions
    
    def analyze_with_groq(self, prompt: str, mode: ResponseMode) -> str:
        """Call Groq with mode-appropriate parameters"""
        if not self.llm_available:
            return "Analysis unavailable (Groq not configured)"
        
        try:
            # Adjust LLM parameters based on mode
            params = {
                'quick': {'temperature': 0.6, 'max_tokens': 150},
                'balanced': {'temperature': 0.7, 'max_tokens': 400},
                'deep': {'temperature': 0.7, 'max_tokens': 800}
            }
            
            response = self.groq.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a concise, adaptive investment advisor. Match your response length to what's requested."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                **params[mode]
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Groq error: {e}")
            return f"Error generating analysis: {str(e)}"
    
    def chat(self,
             user_message: str,
             user_profile: Dict[str, Any],
             user_id: str = "default",
             preferred_mode: Optional[ResponseMode] = None) -> Dict[str, Any]:
        """
        Main chat interface with adaptive intelligence
        """
        try:
            # Get conversation history
            history = self.conversations.get(user_id, [])
            
            # Detect intent and mode
            intent = self.detect_user_intent(user_message)
            mode = self.detect_response_mode(user_message, history, preferred_mode)
            
            logger.info(f"💬 Query: '{user_message[:50]}...' | Intent: {intent} | Mode: {mode}")
            
            # Extract symbols
            symbols = self.extract_symbols(user_message)
            
            # Fetch smart data (only what's needed)
            market_data = {}
            if symbols:
                market_data = self.fetch_smart_data(symbols, intent, mode)
            
            # Build adaptive prompt
            prompt = self.build_adaptive_prompt(
                user_message,
                user_profile,
                market_data,
                history,
                mode,
                intent
            )
            
            # Generate response
            analysis = self.analyze_with_groq(prompt, mode)
            
            # Generate follow-ups
            follow_ups = self.generate_follow_ups(user_message, symbols, intent)
            
            # Save to history
            if user_id not in self.conversations:
                self.conversations[user_id] = []
            
            self.conversations[user_id].append({
                'role': 'user',
                'content': user_message,
                'timestamp': datetime.now().isoformat()
            })
            
            self.conversations[user_id].append({
                'role': 'assistant',
                'content': analysis,
                'mode': mode,
                'intent': intent,
                'timestamp': datetime.now().isoformat()
            })
            
            # Keep last 20 messages
            self.conversations[user_id] = self.conversations[user_id][-20:]
            
            return {
                'type': 'analysis',
                'response': analysis,
                'mode': mode,
                'intent': intent,
                'symbols': symbols,
                'follow_ups': follow_ups,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Chat error: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                'type': 'error',
                'response': f"I encountered an error: {str(e)}"
            }


# Global instance
_adaptive_chatbot = None

def get_adaptive_chatbot() -> AdaptiveChatbot:
    """Get or create adaptive chatbot singleton"""
    global _adaptive_chatbot
    if _adaptive_chatbot is None:
        _adaptive_chatbot = AdaptiveChatbot()
    return _adaptive_chatbot


if __name__ == "__main__":
    # Test adaptive chatbot
    chatbot = AdaptiveChatbot()
    
    test_profile = {
        'risk_score': 0.65,
        'risk_category': 'Comfortable',
        'persona': 'Strategic Balancer'
    }
    
    print("\n🧪 Testing Adaptive Chatbot\n")
    
    # Test quick mode
    print("=" * 60)
    print("TEST 1: Quick mode (price check)")
    response = chatbot.chat(
        "What's Apple trading at?",
        test_profile,
        "test_user"
    )
    print(f"Mode: {response['mode']}")
    print(f"Response:\n{response['response']}\n")
    
    # Test balanced mode
    print("=" * 60)
    print("TEST 2: Balanced mode (general question)")
    response = chatbot.chat(
        "What do you think about Tesla?",
        test_profile,
        "test_user"
    )
    print(f"Mode: {response['mode']}")
    print(f"Response:\n{response['response']}\n")
    
    # Test deep mode
    print("=" * 60)
    print("TEST 3: Deep mode (investment decision)")
    response = chatbot.chat(
        "Should I invest in Apple? Give me a detailed analysis.",
        test_profile,
        "test_user"
    )
    print(f"Mode: {response['mode']}")
    print(f"Response:\n{response['response']}\n")



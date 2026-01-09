"""
Human-Centered Investment Chatbot
100% LLM-powered with real API data - NO TEMPLATES, EVER
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import re
import os
import time
import json
import threading
from dotenv import load_dotenv

from fmp_integration import get_fmp_client
from finnhub_integration import get_finnhub_client
from portfolio_manager import get_portfolio_manager
from withdrawal_planner import get_withdrawal_planner
from conversation_manager import get_conversation_manager
from tax_calculator import get_tax_calculator
from app.services.portfolio_context import build_portfolio_context

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

load_dotenv()

USE_PORTFOLIO_CONTEXT = os.getenv("USE_PORTFOLIO_CONTEXT", "false").lower() == "true"
logger = logging.getLogger(__name__)

class ConversationalChatbot:
    """
    Natural investment advisor - feels like talking to a smart friend
    Uses LLM for ALL responses with real market data when available
    """
    
    def __init__(self):
        self.fmp = get_fmp_client()
        self.finnhub = get_finnhub_client()
        
        self.groq_key = os.getenv('GROQ_API_KEY')
        if self.groq_key and GROQ_AVAILABLE:
            self.groq = Groq(api_key=self.groq_key)
            self.llm_available = True
            logger.info("✅ Conversational Chatbot with Groq LLM")
        else:
            self.groq = None
            self.llm_available = False
            logger.warning("⚠️ Groq not available - chatbot disabled")
        
        self.conversations = {}
        
        # News cache infrastructure
        # Format: { cache_key: {'timestamp': float, 'data': {...}, 'summary': {...}} }
        self._news_cache = {}
        self._news_cache_lock = threading.Lock()
        self.NEWS_TTL_SECONDS = 30 * 60  # 30 minutes
        
        logger.info("🗞️ News cache initialized (TTL: 30min)")
    
    def detect_query_style(self, message: str, history: List[Dict]) -> Dict[str, Any]:
        """Detect depth, intent, and tone from user message"""
        msg_lower = message.lower()
        word_count = len(message.split())
        
        # Depth
        if any(w in msg_lower for w in ['quick', 'briefly', 'tldr', 'short']):
            depth = 'quick'
        elif any(w in msg_lower for w in ['detail', 'deep', 'comprehensive', 'explain']):
            depth = 'deep'
        elif word_count < 5:
            depth = 'quick'
        elif any(w in msg_lower for w in ['should i', 'compare', 'worth investing']):
            depth = 'deep'
        else:
            depth = 'balanced'
        
        # Intent
        if any(w in msg_lower for w in ['summarize', 'summary', 'recap', 'everything we discussed']):
            intent = 'summary_request'
        elif any(w in msg_lower for w in [
            'my portfolio', 'how am i doing', 'my holdings', 'my positions', 'portfolio health',
            'cash balance', 'deploy cash', 'allocation plan', 'build my portfolio',
            'design a portfolio', 'liquidated all my positions', 'full allocation plan',
            'buy apple stock', 'rebalance my portfolio', 'invest my cash', 'portfolio strategy'
        ]):
            intent = 'portfolio_analysis'
        elif any(w in msg_lower for w in ['should i sell', 'trim', 'reduce', 'too much', 'over-concentrated']):
            intent = 'voice_of_reason'  # Prevent emotional decisions
        elif any(w in msg_lower for w in ['withdraw', 'withdrawal', 'safe to withdraw', 'can i take']):
            intent = 'withdrawal_planning'
        elif any(w in msg_lower for w in ['what if', 'scenario', 'simulation']):
            intent = 'scenario_analysis'
        elif 'compare' in msg_lower or ' vs ' in msg_lower:
            intent = 'comparison'
        elif any(w in msg_lower for w in ['should i', 'invest', 'buy', 'worth']):
            intent = 'investment_decision'
        elif any(w in msg_lower for w in ['what is', 'explain', 'how does', 'why']):
            intent = 'education'
        elif any(w in msg_lower for w in ['price', 'trading at', 'current']):
            intent = 'price_check'
        else:
            intent = 'general_research'
        
        # Tone
        tone = 'welcoming' if len(history) < 2 else 'conversational'
        if intent == 'education':
            tone = 'teaching'
        elif intent in ['investment_decision', 'comparison']:
            tone = 'advisory'
        
        return {
            'depth': depth,
            'intent': intent,
            'tone': tone,
            'is_follow_up': len(history) > 0
        }
    
    def extract_symbols_and_context(self, message: str) -> Dict[str, Any]:
        """Extract symbols and determine if Kenya-focused"""
        # US stock symbols
        company_map = {
            'apple': 'AAPL', 'microsoft': 'MSFT', 'google': 'GOOGL', 'alphabet': 'GOOGL',
            'amazon': 'AMZN', 'tesla': 'TSLA', 'nvidia': 'NVDA', 'meta': 'META',
            'facebook': 'META', 'netflix': 'NFLX', 'disney': 'DIS', 'walmart': 'WMT',
            'amd': 'AMD', 'intel': 'INTC', 'jpmorgan': 'JPM'
        }
        
        symbols = []
        msg_lower = message.lower()
        
        # Check company names
        for company, symbol in company_map.items():
            if company in msg_lower:
                symbols.append(symbol)
        
        # Check explicit symbols
        explicit = re.findall(r'\b[A-Z]{2,5}\b', message.upper())
        known = list(company_map.values())
        symbols.extend([s for s in explicit if s in known and s not in symbols])
        
        # Check if Kenya-focused
        kenya_keywords = ['kenya', 'kenyan', 'nse', 'nairobi', 'safaricom', 'equity bank', 
                         'kcb', 'mutual fund', 'money market', 'sacco', 'm-akiba', 'cic', 'britam']
        is_kenya = any(k in msg_lower for k in kenya_keywords)
        
        return {
            'us_symbols': symbols[:3],
            'is_kenya_query': is_kenya and not symbols  # Kenya query without US stocks
        }
    
    # ========== NEWS ENRICHMENT PIPELINE ==========
    
    def _fetch_news_with_cache(self, symbol: str, limit: int = 5) -> Dict[str, Any]:
        """
        Fetch news with in-memory cache (30min TTL)
        Returns: {'articles': [...], 'source': 'fmp'/'finnhub', 'fetched_at': ISO}
        """
        cache_key = f"news::{symbol}"
        now = time.time()
        
        # Check cache
        with self._news_cache_lock:
            cached = self._news_cache.get(cache_key)
            if cached and (now - cached['timestamp'] < self.NEWS_TTL_SECONDS):
                logger.info(f"📰 Cache HIT for {symbol} news")
                return {
                    'articles': cached['data']['articles'],
                    'fetched_at': cached['data']['fetched_at'],
                    'source': 'cache'
                }
        
        # Cache miss - fetch fresh news
        logger.info(f"📰 Cache MISS for {symbol} - fetching fresh news")
        articles = []
        fetched_at = datetime.utcnow().isoformat() + "Z"
        source = 'none'
        
        try:
            # Try FMP first (if method exists)
            if hasattr(self.fmp, 'get_company_news'):
                try:
                    fmp_resp = self.fmp.get_company_news(symbol, limit=limit)
                    if fmp_resp and 'articles' in fmp_resp and fmp_resp['articles']:
                        articles = fmp_resp['articles'][:limit]
                        source = 'fmp'
                        logger.info(f"✅ FMP: Fetched {len(articles)} articles for {symbol}")
                    else:
                        # FMP returned no articles, try Finnhub
                        raise AttributeError("FMP returned no articles")
                except (AttributeError, TypeError) as e:
                    # FMP doesn't have news method or returned nothing, use Finnhub
                    logger.debug(f"FMP news not available, using Finnhub: {e}")
                    fh_resp = self.finnhub.get_company_news(symbol)
                    if fh_resp and 'articles' in fh_resp and fh_resp['articles']:
                        articles = fh_resp['articles'][:limit]
                        source = 'finnhub'
                        logger.info(f"✅ Finnhub: Fetched {len(articles)} articles for {symbol}")
                    else:
                        logger.warning(f"No news found from Finnhub for {symbol}")
            else:
                # FMP doesn't have news method, use Finnhub directly
                fh_resp = self.finnhub.get_company_news(symbol)
                if fh_resp and 'articles' in fh_resp and fh_resp['articles']:
                    articles = fh_resp['articles'][:limit]
                    source = 'finnhub'
                    logger.info(f"✅ Finnhub: Fetched {len(articles)} articles for {symbol}")
                else:
                    logger.warning(f"No news found from Finnhub for {symbol}")
        except Exception as e:
            logger.error(f"News fetch error for {symbol}: {e}")
            source = 'error'
        
        data = {
            'articles': articles,
            'fetched_at': fetched_at,
            'source': source
        }
        
        # Cache it
        with self._news_cache_lock:
            self._news_cache[cache_key] = {
                'timestamp': now,
                'data': data,
                'summary': None  # Will be populated on first summarization
            }
        
        return data
    
    def _add_recency_badges(self, articles: List[Dict]) -> List[Dict]:
        """Add recency badges to articles (BREAKING, Today, This week, Older)"""
        now = datetime.now()
        
        for art in articles:
            published_str = art.get('publishedDate') or art.get('datetime') or ''
            
            try:
                # Handle different date formats
                if isinstance(published_str, int):
                    # Unix timestamp (Finnhub)
                    pub_dt = datetime.fromtimestamp(published_str)
                else:
                    # ISO string (FMP)
                    pub_dt = datetime.fromisoformat(published_str.replace('Z', '+00:00'))
                
                hours_ago = (now - pub_dt).total_seconds() / 3600
                
                if hours_ago < 2:
                    art['recency_badge'] = '🔴 BREAKING'
                    art['urgency'] = 'critical'
                elif hours_ago < 24:
                    art['recency_badge'] = '🆕 Today'
                    art['urgency'] = 'high'
                elif hours_ago < 168:  # 7 days
                    art['recency_badge'] = '📰 This week'
                    art['urgency'] = 'medium'
                else:
                    art['recency_badge'] = '📅 Older'
                    art['urgency'] = 'low'
                
                art['hours_ago'] = hours_ago
            except Exception as e:
                art['recency_badge'] = ''
                art['urgency'] = 'unknown'
                art['hours_ago'] = 999
        
        return articles
    
    def _filter_relevant_articles(self, articles: List[Dict], symbol: str) -> List[Dict]:
        """Filter articles to keep only those actually ABOUT the company"""
        
        # Company name mappings
        company_keywords = {
            'AAPL': ['apple', 'iphone', 'ipad', 'macbook', 'tim cook', 'app store'],
            'MSFT': ['microsoft', 'windows', 'azure', 'office', 'satya nadella', 'xbox'],
            'GOOGL': ['google', 'alphabet', 'android', 'youtube', 'sundar pichai', 'chrome'],
            'AMZN': ['amazon', 'aws', 'prime', 'bezos', 'alexa'],
            'TSLA': ['tesla', 'elon musk', 'model 3', 'model y', 'cybertruck'],
            'META': ['meta', 'facebook', 'instagram', 'whatsapp', 'zuckerberg'],
            'NVDA': ['nvidia', 'gpu', 'jensen huang', 'cuda', 'ai chip']
        }
        
        keywords = company_keywords.get(symbol, [symbol.lower()])
        relevant = []
        
        for art in articles:
            headline = (art.get('title') or art.get('headline') or '').lower()
            text = (art.get('text') or art.get('summary') or '').lower()
            
            # Article is relevant if headline contains keyword
            if any(kw in headline for kw in keywords):
                relevant.append(art)
            # Or if text heavily features it (2+ mentions)
            elif sum(text.count(kw) for kw in keywords) >= 2:
                relevant.append(art)
        
        logger.info(f"🔍 Filtered {len(relevant)}/{len(articles)} relevant articles for {symbol}")
        return relevant
    
    def _detect_breaking_news(self, articles: List[Dict]) -> Optional[Dict]:
        """Check if any news is <2 hours old (breaking)"""
        breaking = [art for art in articles if art.get('urgency') == 'critical']
        
        if breaking:
            return {
                'count': len(breaking),
                'headline': breaking[0].get('title') or breaking[0].get('headline', ''),
                'hours_ago': breaking[0].get('hours_ago', 0)
            }
        
        return None
    
    def _summarize_news_batch(self, symbols_and_articles: Dict[str, List]) -> Dict[str, Dict]:
        """
        Summarize news for MULTIPLE symbols in ONE LLM call (cost optimization)
        
        Args:
            symbols_and_articles: {'AAPL': [articles], 'MSFT': [articles], ...}
        
        Returns:
            {'AAPL': {'bullets': [...], 'sentiment': 'positive'}, ...}
        """
        if not symbols_and_articles or not self.llm_available:
            return {}
        
        # Build batch prompt
        articles_text = ""
        for symbol, articles in symbols_and_articles.items():
            if not articles:
                continue
            
            articles_text += f"\n\n### {symbol}:\n"
            for i, art in enumerate(articles[:3], 1):
                headline = art.get('title') or art.get('headline') or ''
                text = art.get('text') or art.get('summary') or ''
                text_snippet = (text[:400] + '...') if len(text) > 400 else text
                badge = art.get('recency_badge', '')
                
                articles_text += f"{i}. {badge} {headline}\n   {text_snippet}\n"
        
        # Compose batch summarization prompt
        system_prompt = """You are a financial news summarizer. Analyze news for multiple companies.

Return ONLY valid JSON (no extra text) with this structure:
{
  "AAPL": {
    "bullets": ["Short insight 1", "Short insight 2"],
    "sentiment": "positive",
    "confidence": 0.85
  },
  "MSFT": {
    "bullets": ["Insight 1", "Insight 2"],
    "sentiment": "neutral",
    "confidence": 0.75
  }
}

Rules:
- Each bullet: ≤80 characters, actionable fact
- Sentiment: 'positive', 'neutral', or 'negative'
- Confidence: 0-1 (how certain you are)
- Include only companies that have news
"""
        
        user_prompt = f"Summarize news for these companies:{articles_text}\n\nReturn JSON only:"
        
        try:
            completion = self.groq.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.0,  # Deterministic
                max_tokens=300,  # Enough for multi-symbol summary
                top_p=1.0
            )
            
            raw = completion.choices[0].message.content.strip()
            logger.info(f"✅ Batch summarized {len(symbols_and_articles)} symbols")
            
            # Parse JSON
            try:
                parsed = json.loads(raw)
                return parsed
            except json.JSONDecodeError:
                # Try to extract JSON substring
                start = raw.index('{')
                end = raw.rindex('}') + 1
                parsed = json.loads(raw[start:end])
                return parsed
        
        except Exception as e:
            logger.error(f"Batch summarization error: {e}")
            
            # Fallback: extractive summary per symbol
            fallback = {}
            for symbol, articles in symbols_and_articles.items():
                if articles:
                    headlines = [art.get('title') or art.get('headline', '') for art in articles[:2]]
                    fallback[symbol] = {
                        'bullets': headlines,
                        'sentiment': 'neutral',
                        'confidence': 0.5
                    }
            return fallback
    
    def chat(self,
             user_message: str,
             user_profile: Dict[str, Any],
             user_id: str = "default",
             portfolio_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Main conversational interface
        EVERYTHING uses LLM - no templates!
        """
        
        if not self.llm_available:
            return {
                'type': 'error',
                'response': "Chatbot unavailable. Please add GROQ_API_KEY to .env file."
            }
        
        try:
            # Get history
            history = self.conversations.get(user_id, [])
            
            # Detect query style
            query_style = self.detect_query_style(user_message, history)
            
            logger.info(f"💬 Intent: {query_style['intent']} | Depth: {query_style['depth']}")
            
            # Conversation summary requests
            if query_style['intent'] == 'summary_request':
                response = self._summarize_conversation(user_message, user_profile, history, portfolio_data)
                self._save_to_history(user_id, user_message, response['response'])
                return response
            
            # Handle portfolio-specific queries
            if query_style['intent'] in ['portfolio_analysis', 'voice_of_reason', 'withdrawal_planning', 'scenario_analysis']:
                response = self._handle_portfolio_query(user_message, user_profile, user_id, query_style, portfolio_data)
                self._save_to_history(user_id, user_message, response['response'])
                return response
            
            # Extract symbols for stock queries
            context = self.extract_symbols_and_context(user_message)
            
            # Build comprehensive prompt
            if context['is_kenya_query']:
                # Kenya query - use knowledge base + LLM
                prompt = self._build_kenya_prompt(user_message, user_profile, query_style, history)
            elif context['us_symbols']:
                # US stocks - fetch real API data + LLM
                market_data = self._fetch_smart_data(context['us_symbols'], query_style)
                prompt = self._build_us_stocks_prompt(user_message, user_profile, market_data, query_style, history)
            else:
                # General question - LLM only
                prompt = self._build_general_prompt(user_message, user_profile, query_style, history)
            
            # Call Groq LLM
            response_text = self._call_groq(prompt, query_style)
            
            # Save to history
            self._save_to_history(user_id, user_message, response_text)
            
            return {
                'type': 'analysis',
                'response': response_text,
                'query_style': query_style,
                'symbols': context['us_symbols'],
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Chat error: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                'type': 'error',
                'response': f"Sorry, hit a snag: {str(e)}. Mind rephrasing?"
            }
    
    def _summarize_conversation(self,
                                user_message: str,
                                user_profile: Dict[str, Any],
                                history: List[Dict[str, Any]],
                                portfolio_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate a conversation summary."""
        summary_style = {
            'depth': 'quick',
            'intent': 'summary_request',
            'tone': 'advisory',
            'is_follow_up': True
        }

        if not history:
            return {
                'type': 'summary',
                'response': "We haven't covered much yet, so there's nothing meaningful to summarize.",
                'query_style': summary_style
            }

        # Limit to last 12 exchanges
        recent_history = history[-12:]
        formatted_history = []
        for idx, msg in enumerate(recent_history, start=1):
            role = "You" if msg.get('role') == 'user' else "Advisor"
            content = msg.get('content', '')
            if len(content) > 400:
                content = content[:397] + "..."
            formatted_history.append(f"{idx}. {role}: {content}")

        portfolio_snapshot = ""
        if portfolio_data:
            cash = float(portfolio_data.get('cash_balance', 0) or 0)
            total_value = float(portfolio_data.get('portfolio_value', 0) or 0)
            allocation = portfolio_data.get('allocation', [])
            top_alloc = sorted(allocation, key=lambda x: x.get('percent', 0), reverse=True)[:3]
            top_lines = "\n".join(
                f"  - {alloc['symbol']}: {alloc.get('percent', 0):.1f}% (${alloc.get('value', 0):,.0f})"
                for alloc in top_alloc
            )
            portfolio_snapshot = (
                f"Portfolio Value ≈ ${total_value:,.0f}\n"
                f"Cash Balance ≈ ${cash:,.0f}\n"
                f"Top Weights:\n{top_lines or '  - No positions logged'}"
            )

        prompt = f"""
You are PortfoliAI, an AI portfolio analyst. Provide a concise recap with the following sections:
1. Conversation Recap (bullet list)
2. Portfolio Snapshot (if provided)
3. Next Recommended Actions

User risk score: {user_profile.get('risk_score', 'N/A')}

Conversation Log:
{os.linesep.join(formatted_history)}

Portfolio Context:
{portfolio_snapshot or 'No portfolio data available.'}

Write in a professional, numbers-first tone. Keep it under 180 words.
"""

        try:
            summary_text = self._call_groq(prompt, summary_style)
        except Exception as e:
            logger.error(f"Summary generation error: {e}")
            summary_text = None

        if not summary_text:
            summary_text = "Quick recap unavailable right now, but we can revisit this once more messages are logged."

        return {
            'type': 'summary',
            'response': summary_text,
            'query_style': summary_style
        }

    def _handle_portfolio_query(self, 
                                message: str,
                                user_profile: Dict[str, Any],
                                user_id: str,
                                query_style: Dict,
                                portfolio_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Handle portfolio-related queries with real portfolio data + LLM analysis
        """
        try:
            # Check if portfolio data was provided
            if not portfolio_data or (portfolio_data.get('positions_count', 0) == 0 and not portfolio_data.get('withdrawals')):
                return {
                    'type': 'info',
                    'response': "You don't have any positions in your portfolio yet. Head over to the Portfolio page to add your first position, then I can help you analyze it! 📊",
                    'query_style': query_style
                }
            
            # Build portfolio context for LLM from provided data
            portfolio_context = self._format_portfolio_data_for_llm(portfolio_data, query_style['intent'])
            
            # Build prompt based on specific intent
            prompt = self._build_portfolio_query_prompt(
                message,
                user_profile,
                portfolio_context,
                query_style
            )
            
            # Get LLM analysis
            response_text = self._call_groq(prompt, query_style)
            
            # Check if NSE stocks need price updates from portfolio data
            nse_update_prompt = self._check_nse_price_updates_from_data(portfolio_data)
            if nse_update_prompt:
                response_text += f"\n\n{nse_update_prompt}"
            
            return {
                'type': 'analysis',
                'response': response_text,
                'query_style': query_style,
                'portfolio_data': portfolio_data
            }
            
        except Exception as e:
            logger.error(f"Portfolio query error: {e}")
            import traceback
            traceback.print_exc()
            return {
                'type': 'error',
                'response': f"Error analyzing portfolio: {str(e)}"
            }
    
    def _format_portfolio_data_for_llm(self, portfolio_data: Dict, intent: str) -> str:
        """Format portfolio data from Supabase for LLM consumption with tax analysis"""
        positions = portfolio_data.get('positions', [])
        cash_balance = float(portfolio_data.get('cash_balance', 0) or 0)
        total_value = float(portfolio_data.get('portfolio_value', 0) or 0)
        withdrawals = portfolio_data.get('withdrawals', [])
        withdrawal_stats = portfolio_data.get('withdrawal_stats', {})
        withdrawal_projection = portfolio_data.get('withdrawal_projection', {})
        risk_metrics = portfolio_data.get('risk_metrics', {})
        scenario_options = portfolio_data.get('scenario_options', [])
        withdrawal_projection = portfolio_data.get('withdrawal_projection', {})
        allocation = portfolio_data.get('allocation', [])
        concentration_alert = portfolio_data.get('concentration_alert')
        
        context = f"📊 User's Portfolio ({len(positions)} positions):\n"
        context += f"• Portfolio Value (est.): ${total_value:,.2f}\n"
        context += f"• Cash Available: ${cash_balance:,.2f}\n\n"

        if risk_metrics:
            context += "Risk Metrics:\n"
            context += f"• Portfolio beta: {risk_metrics.get('portfolio_beta', 0):.2f}\n"
            context += f"• Estimated volatility proxy: {risk_metrics.get('estimated_volatility', 0)*100:.1f}%\n"
            context += f"• Equity vs Cash: {risk_metrics.get('equity_percent', 0):.1f}% / {risk_metrics.get('cash_percent', 0):.1f}%\n"
            warnings = risk_metrics.get('correlation_warnings', [])
            tips = risk_metrics.get('diversification_tips', [])
            if warnings:
                context += "• Correlation warnings:\n"
                for w in warnings:
                    context += f"  - {w}\n"
            if tips:
                context += "• Diversification nudges:\n"
                for tip in tips:
                    context += f"  - {tip}\n"
            context += "\n"
        
        if allocation:
            context += "Top Concentrations:\n"
            top_alloc = sorted(allocation, key=lambda x: x.get('percent', 0), reverse=True)[:3]
            for alloc in top_alloc:
                context += f"• {alloc['symbol']}: {alloc.get('percent', 0):.1f}% (${alloc.get('value', 0):,.2f})\n"
            context += "\n"
        
        if concentration_alert:
            context += (
                "Concentration Alert:\n"
                f"• {concentration_alert['symbol']} = {concentration_alert['current_percent']:.1f}% of portfolio.\n"
                f"• Suggest trimming ${concentration_alert['suggested_sell_amount']:,.2f} to reach {concentration_alert['target_percent']}% target.\n\n"
            )
        
        # Get tax calculator (Kenya by default, can be configured)
        tax_calc = get_tax_calculator('kenya')
        
        if positions:
            context += "Positions Detail:\n"
        else:
            context += "Positions Detail:\n"
        
        for pos in positions:
            symbol = pos.get('symbol', 'N/A')
            quantity = pos.get('total_quantity', 0)
            avg_cost = pos.get('average_cost', 0)
            current_price = pos.get('current_price', avg_cost)
            total_invested = pos.get('total_invested', 0)
            current_value = quantity * current_price
            pl = current_value - total_invested
            pl_pct = (pl / total_invested * 100) if total_invested > 0 else 0
            
            # Basic position info
            context += f"- {symbol}: {quantity} shares @ ${avg_cost:.2f} avg cost\n"
            context += f"  Current: ${current_price:.2f} | Value: ${current_value:.2f}\n"
            context += f"  P/L: ${pl:+.2f} ({pl_pct:+.1f}%)\n"
            
            # Add tax analysis if position is in profit
            if pl > 0:
                try:
                    # Get purchase date from entries (use first entry if multiple)
                    entries = pos.get('entries', [])
                    if entries and len(entries) > 0:
                        first_entry = entries[0]
                        purchase_date_str = first_entry.get('date')
                        if purchase_date_str:
                            purchase_date = datetime.fromisoformat(purchase_date_str.replace('Z', '+00:00'))
                            
                            # Calculate tax for both Kenya and US (show comparison)
                            kenya_tax = tax_calc.calculate_capital_gains_tax(
                                purchase_price=avg_cost,
                                sale_price=current_price,
                                quantity=quantity,
                                purchase_date=purchase_date,
                                jurisdiction='kenya'
                            )
                            
                            us_tax = tax_calc.calculate_capital_gains_tax(
                                purchase_price=avg_cost,
                                sale_price=current_price,
                                quantity=quantity,
                                purchase_date=purchase_date,
                                jurisdiction='us'
                            )
                            
                            holding_days = kenya_tax['holding_period_days']
                            context += f"  Tax (if sold now):\n"
                            context += f"    Kenya: ${kenya_tax['tax_owed']:.2f} (5% flat) → Net: ${kenya_tax['net_gain']:.2f}\n"
                            context += f"    US: ${us_tax['tax_owed']:.2f} ({us_tax['tax_rate']*100:.0f}% {us_tax.get('tax_type', '').replace('_', ' ')}) → Net: ${us_tax['net_gain']:.2f}\n"
                            
                            # Add recommendation if relevant
                            if us_tax.get('recommendation'):
                                context += f"    💡 {us_tax['recommendation']}\n"
                except Exception as e:
                    logger.warning(f"Could not calculate tax for {symbol}: {e}")
            
            context += "\n"
        
        return context
    
    def _check_nse_price_updates_from_data(self, portfolio_data: Dict) -> str:
        """Check if NSE stocks need price updates"""
        positions = portfolio_data.get('positions', [])
        nse_stocks = [p for p in positions if p.get('manual_price', False)]
        
        if nse_stocks:
            symbols = ', '.join([p.get('symbol', '') for p in nse_stocks])
            return f"💡 Reminder: Update prices manually for NSE stocks ({symbols}) on the Portfolio page for accurate analysis."
        
        return ""
    
    def _format_portfolio_for_llm(self, summary: Dict, intent: str) -> str:
        """Format portfolio data for LLM consumption"""
        
        overview = summary['overview']
        health = summary.get('health', {})
        withdrawal = summary.get('withdrawal', {})
        
        context = f"""
USER'S ACTUAL PORTFOLIO DATA:
━━━━━━━━━━━━━━━━━━━━━━━━━━

Portfolio Overview:
• Total Value: ${overview['total_value']:,.2f}
• Total P/L: ${overview['total_pl']:+,.2f} ({overview['total_pl_percent']:+.2f}%)
• Positions: {overview['positions_count']}
• Cash: ${overview['cash_balance']:,.2f}

Health Score: {health.get('total_score', 'N/A')}/100 ({health.get('health_rating', 'N/A')})
• Diversification: {health.get('scores', {}).get('diversification', 0)}/25
• Risk Alignment: {health.get('scores', {}).get('risk_alignment', 0)}/25
• Performance: {health.get('scores', {}).get('performance', 0)}/25
• Sustainability: {health.get('scores', {}).get('sustainability', 0)}/25

Insights:
{chr(10).join('• ' + insight for insight in health.get('insights', []))}

Top Holdings:
"""
        
        for holding in summary.get('top_holdings', [])[:5]:
            pl_sign = '+' if holding['total_pl'] >= 0 else ''
            context += f"""
• {holding['symbol']}: {holding['total_quantity']} shares
  Current: ${holding['current_price']:.2f} | Avg Cost: ${holding['average_cost']:.2f}
  Value: ${holding['current_value']:,.2f}
  P/L: {pl_sign}${holding['total_pl']:.2f} ({pl_sign}{holding['total_pl_percent']:.2f}%)
  Entries: {holding.get('entry_count', 1)}
"""
        
        if withdrawals:
            context += "\nRecent Withdrawals:\n"
            for withdrawal in withdrawals[:5]:
                amount = float(withdrawal.get('amount', 0) or 0)
                date_str = withdrawal.get('withdrawal_date', 'N/A')
                w_type = withdrawal.get('withdrawal_type', 'general')
                notes = withdrawal.get('notes', '')
                notes_text = f" – {notes}" if notes else ""
                context += f"• {date_str}: ${amount:,.2f} ({w_type}){notes_text}\n"
            
            context += f"""

Withdrawal Stats:
• Year-to-date: {withdrawal_stats.get('ytd_count', 0)} withdrawals totaling ${withdrawal_stats.get('ytd_amount', 0):,.2f}
• Last 90 days: ${withdrawal_stats.get('last_90d_amount', 0):,.2f}
• Last withdrawal date: {withdrawal_stats.get('last_withdrawal', 'N/A')}
• Safe Annual: ${withdrawal_stats.get('safe_annual', 0):,.2f} | Quarterly: ${withdrawal_stats.get('safe_quarterly', 0):,.2f}
• Safe Monthly: ${withdrawal_stats.get('safe_monthly', 0):,.2f}
"""
        else:
            context += "\nWithdrawals: None recorded recently.\n"
        
        if withdrawal_projection:
            runway = withdrawal_projection.get('runway_months')
            runway_text = f"{runway:.1f} months" if runway else "N/A"
            context += f"""

Withdrawal Projection:
• Avg Monthly Withdrawal: ${withdrawal_projection.get('avg_monthly_withdrawal', 0):,.2f}
• Runway (cash ÷ avg withdrawal): {runway_text}
• Annualized Withdrawal Rate: {withdrawal_projection.get('annualized_withdraw_pct', 0):.1f}%
• Projected Value in 12 months (if behavior persists): ${withdrawal_projection.get('projected_value_one_year', 0):,.2f}
"""
        else:
            context += "\nWithdrawal Projection: insufficient data.\n"
        
        if intent in ['withdrawal_planning', 'scenario_analysis']:
            context += f"""

Withdrawal Planning:
• Safe Annual (4% rule): ${withdrawal.get('safe_annual', 0):,.2f}
• Safe Monthly: ${withdrawal.get('safe_monthly', 0):,.2f}
• YTD Withdrawn: ${withdrawal.get('ytd_withdrawn', 0):,.2f}
• Remaining This Year: ${withdrawal.get('remaining_this_year', 0):,.2f}
"""
        
        if scenario_options:
            context += "\nScenario Options:\n"
            for opt in scenario_options:
                context += f"• {opt.get('name')}: {opt.get('summary')}\n"
                for action in opt.get('actions', []):
                    context += f"   - {action}\n"
        else:
            context += "\nScenario Options: Provide multiple paths (trim, diversify, pause) referencing their risk profile."
        
        return context.strip()
    
    def _build_portfolio_query_prompt(self,
                                     message: str,
                                     user_profile: Dict,
                                     portfolio_context: str,
                                     query_style: Dict) -> str:
        """Build prompt for portfolio-specific queries"""
        
        risk_score = user_profile.get('risk_score', 0.5)
        category = user_profile.get('risk_category', 'Comfortable')
        
        intent_guides = {
            'portfolio_analysis': """
Analyze their ACTUAL portfolio with numbers:
- Cite concentration metrics (e.g., "AAPL = 83%")
- Quantify trim/buy suggestions in dollars and percentages
- Reference health/diversification scores
- Include concrete next steps (e.g., "sell $460 of AAPL, redeploy $230 into ETF, $230 into T-bills")
            """,
            'voice_of_reason': """
They're considering an emotional decision (selling/buying impulsively).
BE THEIR VOICE OF REASON:
- Challenge the decision respectfully
- Show tax implications, concentration risk
- Reference their risk profile  
- Suggest more measured approach
- Ask clarifying questions
            """,
            'withdrawal_planning': """
Help them plan withdrawals safely:
- Use provided withdrawal stats (YTD amount, runway, safe monthly)
- State sustainability verdict with numbers ("current pace = 9%/yr, safe = 4%")
- Provide concrete plan (pause X months, resume ≤Y% per quarter)
- Warn about sequence risk if relevant
            """,
            'scenario_analysis': """
Run the scenario they're asking about:
- Calculate outcomes clearly
- Compare to baseline
- Show trade-offs with actual dollar outcomes
- Include best/worst-case or projected value at 12 months
- Give clear recommendation (do / don't, with thresholds)
            """
        }
        
        intent_guide = intent_guides.get(query_style['intent'], "Respond helpfully and naturally")
        
        word_limits = {
            'quick': '40-80 words',
            'balanced': '150-250 words',
            'deep': '300-450 words'
        }
        
        return f"""You're analyzing the user's ACTUAL portfolio using multi-perspective reasoning.

{self._get_multi_expert_framework()}

User Profile: {category} ({risk_score:.2f})

{portfolio_context}

USER ASKS: "{message}"

{intent_guide}

ANALYZE using all three expert perspectives:
📊 Quantitative - Performance numbers, allocation percentages, concentration risk
📰 Market Strategist - Sector trends, market timing, external factors affecting holdings
💬 Personal Advisor - Risk alignment, tax efficiency, behavioral factors, goal fit

RESPOND USING THIS STRUCTURE:
1. **Snapshot** – 2 bullets covering cash + top positions (with actual values/percentages)
2. **Allocation Plan** – numbered list with target % per sleeve (e.g., Core ETF, Apple, T-Bills) and KSh/USD amounts
3. **Action Steps (Next 7 Days)** – 3 concrete tasks (trade ticket style: "Buy X shares of Apple = KSh ___")
4. **Risk Watch** – 1-2 bullets on what to monitor (concentration, cash runway, tax)

- Use their actual numbers (don't make up data!)
- Be conversational ("Your Apple position is up 12%" not "Analysis indicates...")
- Reference specific holdings by name
- Weave in insights from all three perspectives naturally
- Keep it focused on execution and what to do next

LENGTH: {word_limits[query_style['depth']]}

Respond now:"""
    
    def _check_nse_price_updates(self, pm: Any) -> Optional[str]:
        """Check if NSE stocks need price updates and prompt user"""
        
        # Get NSE positions
        nse_symbols = []
        for pos in pm.get_all_positions():
            if pos.get('market') == 'NSE':
                symbol = pos['symbol']
                if symbol not in nse_symbols:
                    nse_symbols.append(symbol)
        
        if not nse_symbols:
            return None
        
        # Check which ones need updates
        needs_update = []
        for symbol in nse_symbols:
            if pm.needs_price_update(symbol):
                needs_update.append(symbol)
        
        if not needs_update:
            return None
        
        # Prompt for updates
        symbols_str = ", ".join(needs_update)
        return f"\n\n📊 **Price Update Needed:** Your NSE stocks ({symbols_str}) haven't been updated in 24+ hours. Head to the Portfolio page to update current prices for accurate P/L."
    
    def _build_us_stocks_prompt(self, message: str, profile: Dict, market_data: Dict, style: Dict, history: List) -> str:
        """Build prompt for US stocks with REAL API data"""
        
        risk_score = profile.get('risk_score', 0.5)
        category = profile.get('risk_category', 'Comfortable')
        
        # Profile context (compact if follow-up)
        if style['is_follow_up']:
            profile_ctx = f"User: {category} risk ({risk_score:.2f})"
        else:
            profile_ctx = f"User Profile: {category} - {risk_score:.2f}/1.0 risk tolerance"
        
        # Format REAL market data
        market_ctx = "LIVE MARKET DATA:\n"
        for symbol, data in market_data.items():
            if 'error' in data:
                continue
            
            quote = data.get('quote', {})
            if quote and not quote.get('error'):
                price = quote.get('price', 0)
                change = quote.get('change', 0)
                change_pct = quote.get('change_percent', 0)
                pe = quote.get('raw_data', {}).get('pe')
                year_high = quote.get('year_high', 0)
                year_low = quote.get('year_low', 0)
                
                market_ctx += f"\n{symbol}: ${price:.2f} ({change:+.2f}, {change_pct:+.2f}%)"
                if pe:
                    market_ctx += f", P/E {pe:.1f}"
                if year_high and year_low:
                    range_pct = ((price - year_low) / (year_high - year_low)) * 100
                    market_ctx += f", at {range_pct:.0f}% of 52-week range"
            
            # Add company info if available
            if 'profile' in data and not data['profile'].get('error'):
                prof = data['profile']
                market_ctx += f"\n  Company: {prof.get('company_name')}, CEO: {prof.get('ceo')}"
                market_ctx += f"\n  Sector: {prof.get('sector')} | Industry: {prof.get('industry')}"
            
            # Add enriched news (with summary, sentiment, breaking alerts)
            breaking_alert = ""
            
            # Check for breaking news first
            if 'breaking_news' in data:
                breaking = data['breaking_news']
                breaking_alert = f"\n  🚨 BREAKING ({breaking['hours_ago']:.0f}h ago): {breaking['headline']}"
                market_ctx = market_ctx + breaking_alert
            
            # Add news summary (LLM-generated)
            if 'news_summary' in data and data['news_summary']:
                summary = data['news_summary']
                sentiment = summary.get('sentiment', 'neutral')
                bullets = summary.get('bullets', [])
                confidence = summary.get('confidence', 0.5)
                
                # Sentiment indicator
                sentiment_emoji = {
                    'positive': '📈 Positive',
                    'negative': '📉 Negative',
                    'neutral': '➖ Neutral'
                }
                sentiment_label = sentiment_emoji.get(sentiment, '➖ Neutral')
                
                # Contrarian signal detection
                price_change_pct = data.get('quote', {}).get('change_percent', 0)
                contrarian = ""
                if sentiment == 'negative' and price_change_pct > 1:
                    contrarian = "\n    ⚠️ CONTRARIAN: Negative news but price rising!"
                elif sentiment == 'positive' and price_change_pct < -2:
                    contrarian = "\n    ⚠️ CONTRARIAN: Positive news but price falling!"
                
                market_ctx += f"\n  News Summary ({sentiment_label}, confidence: {confidence:.0%}):"
                for bullet in bullets:
                    market_ctx += f"\n    • {bullet}"
                if contrarian:
                    market_ctx += contrarian
            
            # Fallback: raw headlines if no summary
            elif 'news_raw' in data:
                articles = data['news_raw'][:3]
                if articles:
                    market_ctx += f"\n  Recent headlines:"
                    for art in articles:
                        badge = art.get('recency_badge', '')
                        headline = art.get('title') or art.get('headline', '')
                        market_ctx += f"\n    • {badge} {headline[:70]}"
        
        # Word limits by mode
        word_limits = {
            'quick': '40-80 words (2-3 sentences)',
            'balanced': '150-250 words',
            'deep': '300-450 words'
        }
        
        return f"""You're a natural investment advisor using multi-perspective reasoning.

{self._get_multi_expert_framework()}

{profile_ctx}

{market_ctx}

USER: "{message}"

ANALYZE using all three expert perspectives:
📊 Quantitative Analyst - Look at the numbers (price, P/E, 52-week position, changes)
📰 Market Strategist - Consider the news, sector context, market sentiment
💬 Personal Advisor - Match to user's {risk_score:.2f} risk profile and investment goals

CRITICAL RULES:
1. **VARY OPENINGS**: Use "Good question", "Interesting!", "Let's look at this", "Here's what I see"
2. **NO TEMPLATES**: Don't always follow same structure (Take/Analysis/For You/Action/Watch)
3. **BE NATURAL**: Sound like a friend, not a report ("Apple's doing well" not "Analysis indicates positive momentum")
4. **SHORT PARAGRAPHS**: 2-3 sentences max, then break or use bullets
5. **WEAVE IN PROFILE**: "for your moderate risk comfort" not "For Your Profile (Comfortable):"
6. **USE REAL DATA**: Reference the actual prices, news, P/E ratios provided above!
7. **SHOW REASONING**: Naturally weave in insights from all three perspectives
8. **END NATURALLY**: Vary your closers - not always same question

LENGTH: {word_limits[style['depth']]} ({style['depth']} mode)
TONE: {style['tone']}

Respond naturally now:"""
    
    def _build_kenya_prompt(self, message: str, profile: Dict, style: Dict, history: List) -> str:
        """Build prompt for Kenya queries using knowledge base + LLM (NO live API data available)"""
        
        risk_score = profile.get('risk_score', 0.5)
        category = profile.get('risk_category', 'Comfortable')
        
        profile_ctx = f"User: {category} risk ({risk_score:.2f})" if style['is_follow_up'] else f"User Profile: {category} ({risk_score:.2f})"
        
        kenya_knowledge = """
KENYA MARKET INFO (Use this but respond naturally - prices from live web search):

NSE Stocks Worth Considering:
• Safaricom (SCOM): KSh 29.65 (LIVE via DuckDuckGo web search), telco + M-Pesa dominant, 60%+ market share, 4-5% dividend
• Equity Bank (EQTY): KSh 63.25 (LIVE via DuckDuckGo web search), regional fintech, 6 countries, good dividend
• KCB Group: KSh 61.00 (LIVE via DuckDuckGo web search), largest bank, stable, 6-7% dividend yield
• EABL: ~KSh 140-150, consumer staples, defensive
• Bamburi Cement: ~KSh 25-30, infrastructure play

Mutual Funds:
Money Market (Low Risk, 8-10% returns):
- CIC Money Market Fund (very liquid, low fees, min KSh 5,000)
- Britam Money Market (strong reputation, similar returns)
- NCBA Money Market (competitive, sometimes 9-11%)

Balanced Funds (Moderate Risk, 12-15% returns):
- ICEA LION Balanced (60/40 stocks/bonds, ±10% volatility)
- CIC Balanced (conservative, beginner-friendly)
- Sanlam Balanced (70% equity, aggressive)

Key Insights:
• NSE liquidity is LIMITED (hard to sell quickly)
• Mutual funds are MORE LIQUID than individual stocks
• Currency risk (all KSh, dollar value fluctuates)
• T-Bills: 15-16% currently (good for conservative investors)
• Access: CDS account for stocks, direct for mutual funds
• Minimum: KSh 50k-100k for stocks, KSh 5k+ for funds
        """
        
        word_limits = {
            'quick': '40-80 words',
            'balanced': '150-250 words',
            'deep': '300-450 words'
        }
        
        return f"""You're advising on Kenya investments using multi-perspective reasoning.

{self._get_multi_expert_framework()}

{profile_ctx}

{kenya_knowledge}

USER: "{message}"

ANALYZE using all three perspectives:
📊 Quantitative - Yields, liquidity, historical returns, fees
📰 Market Strategist - NSE trends, M-Pesa dominance, regional expansion, infrastructure
💬 Personal Advisor - Match to user's {risk_score:.2f} risk profile, Kenya-specific considerations

RESPOND NATURALLY:
- Use the Kenya data but don't just list it
- Analyze FOR THIS SPECIFIC USER (their risk level matters!)
- Mix structure (sometimes bullets first, sometimes explanation first)
- Be conversational ("Here's the thing about Kenyan stocks..." not "Analysis: The Kenyan market...")
- Reference their profile naturally ("given you prefer moderate risk" not "For Your Profile:")
- Weave in insights from all three expert angles naturally

LENGTH: {word_limits[style['depth']]} ({style['depth']} mode)

⚠️ NOTE: This is general Kenya market knowledge, not live API data. Be helpful but mention this reality when relevant.

Respond naturally now:"""
    
    def _get_multi_expert_framework(self) -> str:
        """Multi-perspective reasoning framework for all prompts"""
        return """
🧠 MULTI-EXPERT REASONING:
Think as THREE experts before responding:

1️⃣ 📊 QUANTITATIVE ANALYST - Numbers, ratios, valuations, risk metrics
2️⃣ 📰 MARKET STRATEGIST - Macro trends, sentiment, news, market context  
3️⃣ 💬 PERSONAL ADVISOR - User fit, risk alignment, tax efficiency, behavioral factors

Synthesize all three perspectives into ONE natural, conversational response.
"""
    
    def _build_general_prompt(self, message: str, profile: Dict, style: Dict, history: List) -> str:
        """Build prompt for general questions (no specific stock/market)"""
        
        risk_score = profile.get('risk_score', 0.5)
        category = profile.get('risk_category', 'Comfortable')
        
        word_limits = {
            'quick': '40-80 words',
            'balanced': '150-250 words',
            'deep': '300-450 words'
        }
        
        return f"""You're an AI investment advisor using multi-perspective reasoning.

{self._get_multi_expert_framework()}

User: {category} risk tolerance ({risk_score:.2f}/1.0)

USER ASKS: "{message}"

Respond naturally by combining insights from all three expert perspectives:
- Teach clearly if it's an education question
- Give practical advice tied to THEIR risk profile
- Use real examples when helpful
- Be conversational, not textbook-y
- Show reasoning from multiple angles naturally

LENGTH: {word_limits[style['depth']]}

Respond now:"""
    
    def _fetch_smart_data(self, symbols: List[str], style: Dict) -> Dict[str, Any]:
        """Fetch data with enriched news pipeline (cache + summarization)"""
        data = {}
        depth = style['depth']
        intent = style['intent']
        
        # Step 1: Fetch quotes and profiles for all symbols
        for symbol in symbols:
            try:
                # Always get quote (fast, essential)
                symbol_data = {'quote': self.fmp.get_quote(symbol)}
                
                # Profile for balanced/deep or comparisons
                if depth in ['balanced', 'deep'] or intent == 'comparison':
                    symbol_data['profile'] = self.fmp.get_profile(symbol)
                
                data[symbol] = symbol_data
                
            except Exception as e:
                logger.error(f"Error fetching {symbol}: {e}")
                data[symbol] = {'error': str(e)}
        
        # Step 2: Fetch news with cache (only for balanced/deep)
        symbols_with_news = {}
        if depth in ['balanced', 'deep']:
            for symbol in symbols:
                if 'error' not in data[symbol]:
                    news_resp = self._fetch_news_with_cache(symbol, limit=5)
                    raw_articles = news_resp.get('articles', [])
                    
                    if raw_articles:
                        # Add recency badges
                        raw_articles = self._add_recency_badges(raw_articles)
                        
                        # Filter for relevance
                        relevant_articles = self._filter_relevant_articles(raw_articles, symbol)
                        
                        if relevant_articles:
                            symbols_with_news[symbol] = relevant_articles
                            data[symbol]['news_raw'] = relevant_articles
        
        # Step 3: Batch summarize all news in ONE LLM call
        news_summaries = {}
        if symbols_with_news:
            # Check cache for existing summaries first
            needs_summarization = {}
            for symbol, articles in symbols_with_news.items():
                cache_key = f"news::{symbol}"
                with self._news_cache_lock:
                    cached = self._news_cache.get(cache_key)
                    if cached and cached.get('summary'):
                        # Use cached summary
                        news_summaries[symbol] = cached['summary']
                        logger.info(f"📰 Using cached summary for {symbol}")
                    else:
                        # Needs fresh summarization
                        needs_summarization[symbol] = articles
            
            # Summarize symbols that need it (batch call)
            if needs_summarization:
                logger.info(f"🤖 Batch summarizing {len(needs_summarization)} symbols...")
                batch_summaries = self._summarize_news_batch(needs_summarization)
                
                # Cache the summaries
                for symbol, summary in batch_summaries.items():
                    cache_key = f"news::{symbol}"
                    with self._news_cache_lock:
                        if cache_key in self._news_cache:
                            self._news_cache[cache_key]['summary'] = summary
                    
                    news_summaries[symbol] = summary
        
        # Step 4: Attach summaries to symbol data
        for symbol, summary in news_summaries.items():
            if symbol in data:
                data[symbol]['news_summary'] = summary
                
                # Detect breaking news
                if 'news_raw' in data[symbol]:
                    breaking = self._detect_breaking_news(data[symbol]['news_raw'])
                    if breaking:
                        data[symbol]['breaking_news'] = breaking
        
        return data
    
    def _call_groq(self, prompt: str, style: Dict) -> str:
        """Call Groq LLM with style-appropriate parameters"""
        
        params = {
            'quick': {'max_tokens': 150, 'temperature': 0.7},
            'balanced': {'max_tokens': 500, 'temperature': 0.7},
            'deep': {'max_tokens': 900, 'temperature': 0.7}
        }
        
        try:
            response = self.groq.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a natural, engaging investment advisor. Vary your style, be human, avoid robotic templates. Sound like a knowledgeable friend."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                **params[style['depth']]
            )
            
            text = response.choices[0].message.content
            logger.info(f"✅ Generated {style['depth']} response ({len(text)} chars)")
            return text
            
        except Exception as e:
            logger.error(f"Groq error: {e}")
            return f"Error generating response: {str(e)}"
    
    def _save_to_history(self, user_id: str, message: str, response: str):
        """Save conversation to history"""
        if user_id not in self.conversations:
            self.conversations[user_id] = []
        
        self.conversations[user_id].extend([
            {'role': 'user', 'content': message, 'timestamp': datetime.now().isoformat()},
            {'role': 'assistant', 'content': response, 'timestamp': datetime.now().isoformat()}
        ])
        
        self.conversations[user_id] = self.conversations[user_id][-20:]


# Global instance
_conversational_chatbot = None

def get_conversational_chatbot() -> ConversationalChatbot:
    """Get or create conversational chatbot singleton"""
    global _conversational_chatbot
    if _conversational_chatbot is None:
        _conversational_chatbot = ConversationalChatbot()
    return _conversational_chatbot


if __name__ == "__main__":
    # Test all modes
    chatbot = ConversationalChatbot()
    
    test_profile = {
        'risk_score': 0.65,
        'risk_category': 'Comfortable',
        'persona': 'Strategic Balancer'
    }
    
    print("\n🧪 Testing Conversational Chatbot (All LLM-Powered)\n")
    
    # Test 1: Quick US stock
    print("=" * 70)
    print("TEST 1: Quick mode - US Stock")
    r = chatbot.chat("What's Apple trading at?", test_profile, "test1")
    print(f"Mode: {r['query_style']['depth']}")
    print(f"\n{r['response']}\n")
    
    # Test 2: Kenya funds (NO API, but still LLM!)
    print("=" * 70)
    print("TEST 2: Kenya mutual funds (LLM + knowledge base, NO templates)")
    r = chatbot.chat("Tell me about Kenyan mutual funds I can invest in", test_profile, "test2")
    print(f"Mode: {r['query_style']['depth']}")
    print(f"\n{r['response']}\n")
    
    # Test 3: Deep US analysis
    print("=" * 70)
    print("TEST 3: Deep mode - Investment decision")
    r = chatbot.chat("Should I invest in Tesla? Give me details.", test_profile, "test3")
    print(f"Mode: {r['query_style']['depth']}")
    print(f"\n{r['response'][:500]}...\n")


"""
Profile Card Generator - LLM-powered investor personality insights
Generates personalized investment profiles and strategies using OpenAI GPT-4
"""

import os
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Try Groq first (free), fallback to OpenAI
try:
    from groq import Groq
    LLM_PROVIDER = 'groq'
except ImportError:
    try:
        from openai import OpenAI
        LLM_PROVIDER = 'openai'
    except ImportError:
        LLM_PROVIDER = None

from market_data_fetcher import get_market_data_fetcher

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class ProfileCardGenerator:
    """Generates personalized investor profile cards using LLM."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize with LLM API key (Groq or OpenAI).
        
        Args:
            api_key: API key. If None, tries GROQ_API_KEY then OPENAI_API_KEY from env.
        """
        # Try Groq first (free!), then OpenAI
        self.api_key = api_key or os.getenv('GROQ_API_KEY') or os.getenv('OPENAI_API_KEY')
        self.provider = None
        self.market_data = get_market_data_fetcher()
        
        if not self.api_key:
            logger.warning("No LLM API key found. Using enhanced fallback templates.")
            self.client = None
        elif LLM_PROVIDER == 'groq' and os.getenv('GROQ_API_KEY'):
            self.client = Groq(api_key=self.api_key)
            self.provider = 'groq'
            logger.info("✨ Groq client initialized (FREE, real-time enhanced)")
        elif LLM_PROVIDER == 'openai' and os.getenv('OPENAI_API_KEY'):
            self.client = OpenAI(api_key=self.api_key)
            self.provider = 'openai'
            logger.info("OpenAI client initialized successfully")
        else:
            logger.warning("LLM provider not available. Using enhanced fallback templates.")
            self.client = None
    
    def generate_profile_card(self, 
                             risk_data: Dict[str, Any],
                             survey_answers: Dict[str, Any] = None,
                             use_kenyan_context: bool = True) -> Dict[str, Any]:
        """
        Generate a personalized investor profile card.
        
        Args:
            risk_data: Output from ml_service.predict_survey_risk()
            survey_answers: Original survey answers for context
            use_kenyan_context: Include Kenya-specific investment recommendations
            
        Returns:
            Dict with profile card sections
        """
        # Check if using real market data
        market_data_status = "SIMULATED (typical ranges)" if not self.market_data.use_real_data else "LIVE (API)"
        logger.info(f"📊 Market data mode: {market_data_status}")
        
        if not self.client:
            logger.warning("Using fallback profile card (no API key)")
            return self._generate_fallback_card(risk_data, survey_answers, use_kenyan_context)
        
        logger.info(f"🚀 Calling {self.provider} to generate Living Profile Card...")
        
        try:
            # Build comprehensive context for LLM
            prompt = self._build_prompt(risk_data, survey_answers, use_kenyan_context)
            logger.info(f"📝 Prompt built ({len(prompt)} chars), calling LLM...")
            
            # Call LLM API (Groq or OpenAI)
            # Groq models: llama-3.3-70b-versatile, llama-3.1-8b-instant, mixtral-8x7b-32768
            model_name = "llama-3.3-70b-versatile" if self.provider == 'groq' else "gpt-4"
            
            response = self.client.chat.completions.create(
                model=model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional financial advisor in Kenya specializing in investor psychology and personalized portfolio strategy. You create warm, insightful investor profiles that make people feel deeply understood while providing actionable investment guidance. You use REAL-TIME market data to make recommendations feel current and alive."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            # Parse LLM response
            profile_text = response.choices[0].message.content
            logger.info(f"✅ {self.provider} generated profile card ({len(profile_text)} chars)")
            
            # Structure the response
            return self._structure_profile_card(profile_text, risk_data)
            
        except Exception as e:
            import traceback
            logger.error(f"❌ Error generating profile card with {self.provider}: {e}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            logger.warning("⚠️ Falling back to enhanced templates")
            return self._generate_fallback_card(risk_data, survey_answers, use_kenyan_context)
    
    def _build_prompt(self, risk_data: Dict[str, Any], survey_answers: Dict[str, Any], use_kenyan: bool) -> str:
        """Build the LLM prompt with all context."""
        
        # Extract key data
        risk_score = risk_data.get('risk_score', 0.5)
        category = risk_data.get('risk_category', 'Comfortable')
        persona = risk_data.get('persona', 'Strategic Balancer')
        backend = risk_data.get('backend_features', {})
        
        # Get REAL-TIME market context for "Living Profile Card"
        nse_context = self.market_data.get_nse_context() if use_kenyan else ""
        global_context = self.market_data.get_global_market_context()
        kenya_news = self.market_data.get_kenya_investment_news() if use_kenyan else []
        allocations = self.market_data.get_recommended_allocations(risk_score, use_kenyan)
        date_context = self.market_data.get_current_date_context()
        
        # LIVING CARD ENHANCEMENTS
        market_mood = self.market_data.get_market_mood_pulse(category)
        volatility_context = self.market_data.get_volatility_context(risk_score)
        quarterly_outlook = self.market_data.get_quarterly_outlook()
        weekly_opportunity = self.market_data.get_weekly_opportunity(risk_score)
        
        # Live stock snippets for major holdings
        # Clear cache to ensure fresh prices
        self.market_data.cache = {}
        self.market_data.cache_expiry = {}
        
        # Extract exact prices first
        scom_price = self.market_data._fetch_nse_price('SCOM')
        eqty_price = self.market_data._fetch_nse_price('EQTY')
        kcb_price = self.market_data._fetch_nse_price('KCB')
        
        scom_exact = scom_price['price'] if scom_price else 29.65
        eqty_exact = eqty_price['price'] if eqty_price else 63.25
        kcb_exact = kcb_price['price'] if kcb_price else 61.00
        
        # Generate live snippets with exact prices
        scom_live = f"Safaricom (SCOM) trading at KSh {scom_exact:.2f} (LIVE via DuckDuckGo web search)"
        eqty_live = f"Equity Group (EQTY) trading at KSh {eqty_exact:.2f} (LIVE via DuckDuckGo web search)"
        kcb_live = f"KCB Group (KCB) trading at KSh {kcb_exact:.2f} (LIVE via DuckDuckGo web search)"
        
        # Build context
        context_parts = []
        
        # Basic profile
        age = backend.get('age', 35)
        occupation = backend.get('occupation', 'Salaried')
        experience = 'experienced' if backend.get('invests', True) else 'new to investing'
        
        context_parts.append(f"Age: {age}, Occupation: {occupation}, Experience: {experience}")
        
        # Investment preferences
        main_avenue = backend.get('main_avenue', 'Mutual Funds')
        expected_return = backend.get('expected_return', '10% - 15%')
        horizon = backend.get('investment_horizon', '3-5 years')
        
        context_parts.append(f"Prefers: {main_avenue}, Expects: {expected_return}, Horizon: {horizon}")
        
        # Behavioral indicators
        equity_rank = backend.get('equity_rank', 4)
        fund_rank = backend.get('fund_rank', 4)
        monitoring = backend.get('monitoring_frequency', 'Monthly')
        
        context_parts.append(f"Equity preference: {equity_rank}/7, Fund preference: {fund_rank}/7, Monitors: {monitoring}")
        
        # Survey-specific insights
        if survey_answers:
            if 'market_reaction' in survey_answers:
                reaction_map = {
                    'a': 'Would sell during 15% drop (risk-averse)',
                    'b': 'Would wait during 15% drop (patient)',
                    'c': 'Would buy more during 15% drop (contrarian/aggressive)'
                }
                context_parts.append(f"Market behavior: {reaction_map.get(survey_answers['market_reaction'], 'Unknown')}")
            
            if 'goal' in survey_answers:
                goal_map = {
                    'a': 'Preserve wealth',
                    'b': 'Grow steadily',
                    'c': 'Maximize returns'
                }
                context_parts.append(f"Primary goal: {goal_map.get(survey_answers['goal'], 'Unknown')}")
        
        # Build full prompt with REAL-TIME market data for "Living Card"
        kenyan_context = f"""
🌐 REAL-TIME MARKET DATA ({date_context}):

LIVE STOCK QUOTES:
• {scom_live}
• {eqty_live}
• {kcb_live}

NSE MARKET PULSE:
{nse_context}

GLOBAL MARKETS:
{global_context}

KENYA INVESTMENT NEWS (This Week):
{chr(10).join('• ' + news for news in kenya_news)}

DYNAMIC INSIGHTS FOR THIS INVESTOR:
• Market Mood Pulse: "{market_mood}"
• Quarterly Outlook: {quarterly_outlook}
• This Week's Opportunity: {weekly_opportunity}
{f'• Volatility Alert: {volatility_context}' if volatility_context else ''}

RECOMMENDED ALLOCATIONS:
{allocations}

⚡ CRITICAL INSTRUCTIONS FOR "LIVING PROFILE CARD":
1. **MUST USE EXACT PRICES PROVIDED** - Use these EXACT prices in Portfolio Blueprint:
   - Safaricom (SCOM): KSh {scom_exact:.2f} (LIVE via DuckDuckGo web search)
   - Equity Group (EQTY): KSh {eqty_exact:.2f} (LIVE via DuckDuckGo web search)
   - KCB Group (KCB): KSh {kcb_exact:.2f} (LIVE via DuckDuckGo web search)
   DO NOT generate or estimate different prices. Use ONLY these exact prices: {scom_exact:.2f}, {eqty_exact:.2f}, {kcb_exact:.2f}
2. Add Market Mood Pulse after intro persona
3. Use current T-Bill rates, stock prices, and news in examples
4. Make Quick Wins reference THIS WEEK's specific opportunities
5. Add quarterly timing to Level-Up Tip
6. Mention recent company developments (Ethiopia expansion, fintech growth, etc.)
7. This should feel ALIVE and CURRENT, not a static template!
        """ if use_kenyan else f"{global_context}"
        
        prompt = f"""
Create a personalized investor profile card for this investor using REAL-TIME market data:

PROFILE DATA:
- Risk Score: {risk_score:.2f} (0=conservative, 1=aggressive)
- Category: {category}
- Persona: {persona}
- {chr(10).join(context_parts)}

{kenyan_context}

Generate a LIVING INVESTOR PROFILE CARD using THIS EXACT STRUCTURE:

**WHO YOU ARE** (2-3 sentences)
   - Conversational, empowering tone like "You've got the courage most investors wish they had"
   - Make them feel deeply understood
   - Use phrases like "That's your edge" or "You're built for this"
   
   **Market Mood Pulse:** Add one line reflecting current market conditions, like:
   "{market_mood}"

**PORTFOLIO BLUEPRINT**

You invest best when [complete this based on their profile]

**Layer System:**

🟩 **Core (X%)** — [What this layer means for them]
   • INJECT LIVE EXAMPLES: Use these EXACT prices - DO NOT change or estimate:
     - Safaricom (SCOM) trading at KSh {scom_exact:.2f} (LIVE via DuckDuckGo web search)
     - Equity Group (EQTY) trading at KSh {eqty_exact:.2f} (LIVE via DuckDuckGo web search)
     - KCB Group (KCB) trading at KSh {kcb_exact:.2f} (LIVE via DuckDuckGo web search)
   • CRITICAL: Use EXACTLY these prices: {scom_exact:.2f}, {eqty_exact:.2f}, {kcb_exact:.2f}. Do not generate different prices.
   • Add WHY each is in core right now (recent performance, catalysts)

🟦 **Growth/Stability (X%)** — [Second layer purpose]
   • Reference CURRENT market trends from global context
   • Mention specific performance (e.g., "S&P 500 up 20% YTD")

🟨 **Safety/International (X%)** — [Third layer purpose]
   • Include CURRENT T-Bill rates (15.5%, 15.8%)
   • Mention recent bond market movements

**Strategy Snapshot:**

**Kenyan Focus (X%):**
• [List with CURRENT market context - mention recent news, current prices, trends]

**Global Expansion (X%):**
• [Reference current global market trends from the data provided]

**Mixed Strategy:**
[Specific guidance on combining Kenya + International. Mention CURRENT market conditions]

**Your Superpower:** [Their unique investing strength]
{f'   💡 {volatility_context}' if volatility_context else ''}

**Level-Up Tip:**
[Actionable advice] MUST INCLUDE: {quarterly_outlook}

**Watch Out For:**
[Specific pitfall with CURRENT market example from live data]

**Quick Wins This Week:**
CRITICAL - Make these TIME-SENSITIVE and reference THIS WEEK:
1. {weekly_opportunity}
2. [Second action using live stock prices provided]
3. [Third action with specific current rate/opportunity]

**Expected Return:** X-Y% annually
   💭 Current Environment: [Mention if rates are high/low, markets trending up/down]

CRITICAL: Use the REAL-TIME market data provided (current prices, recent news, T-Bill rates). Make it feel ALIVE and CURRENT, not templated. Reference specific developments like "with Safaricom's recent expansion to Ethiopia" or "given current T-Bill rates at 15.5%"

TONE: Confident, warm, empowering. Use "You've got", "That's your edge", "You're built for this"
LENGTH: Comprehensive but scannable (300-400 words)
"""
        
        return prompt
    
    def _structure_profile_card(self, llm_text: str, risk_data: Dict[str, Any]) -> Dict[str, Any]:
        """Structure the LLM response into card sections."""
        
        # Try to parse sections from LLM response
        sections = {}
        
        # Simple parsing - look for section headers
        lines = llm_text.split('\n')
        current_section = 'full_text'
        current_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Detect section headers
            if 'WHO YOU ARE' in line.upper() or 'YOUR PERSONALITY' in line.upper():
                if current_content:
                    sections[current_section] = '\n'.join(current_content)
                current_section = 'personality'
                current_content = []
            elif 'INVESTMENT STRATEGY' in line.upper() or 'YOUR STRATEGY' in line.upper():
                if current_content:
                    sections[current_section] = '\n'.join(current_content)
                current_section = 'strategy'
                current_content = []
            elif 'WHY THIS WORKS' in line.upper() or 'WHY IT WORKS' in line.upper():
                if current_content:
                    sections[current_section] = '\n'.join(current_content)
                current_section = 'rationale'
                current_content = []
            elif not line.startswith('#') and not line.startswith('**') or line.count('**') == 2:
                current_content.append(line)
        
        # Add last section
        if current_content:
            sections[current_section] = '\n'.join(current_content)
        
        # Add data quality warning if using simulated data
        data_quality_note = None
        if not self.market_data.use_real_data:
            data_quality_note = "⚠️ Market prices shown are typical ranges (SIMULATED). For production use, integrate real-time API - see MARKET_DATA_API_GUIDE.md"
        
        # Return structured card
        return {
            'risk_score': risk_data.get('risk_score'),
            'risk_category': risk_data.get('risk_category'),
            'persona': risk_data.get('persona'),
            'confidence': risk_data.get('confidence'),
            'profile_card': {
                'personality': sections.get('personality', ''),
                'strategy': sections.get('strategy', ''),
                'rationale': sections.get('rationale', ''),
                'full_text': llm_text
            },
            'generated_by': f'{self.provider}_realtime' if self.provider else 'openai_gpt4',
            'market_data_included': True,
            'market_data_quality': 'simulated' if not self.market_data.use_real_data else 'live',
            'data_quality_note': data_quality_note,
            'generated_at': self.market_data.get_current_date_context()
        }
    
    def _generate_fallback_card(self, risk_data: Dict[str, Any], survey_answers: Dict[str, Any], use_kenyan: bool) -> Dict[str, Any]:
        """Generate a rule-based profile card when LLM is not available."""
        
        risk_score = risk_data.get('risk_score', 0.5)
        category = risk_data.get('risk_category', 'Comfortable')
        persona = risk_data.get('persona', 'Strategic Balancer')
        backend = risk_data.get('backend_features', {})
        
        # Template-based generation
        if risk_score < 0.3:
            personality = f"You invest with your head, not your heart. While others chase trends, you build wealth the old-fashioned way—steadily, safely, predictably. You've learned that protecting what you have matters more than reaching for what you might never get. Sleep comes easy when your money is tucked into safe harbors."
            
            if use_kenyan:
                strategy = """
**Portfolio Blueprint**

You invest best when your portfolio feels like a fortress — unshakeable, reliable, and growing quietly in the background.

**Layer System:**

🟩 **Foundation (75%)** — Your bedrock. These never surprise you, and that's exactly the point.
   • Kenyan Treasury Bills (91-day, 182-day, 364-day) — 40%
   • M-Akiba mobile bonds — 15%
   • Equity Bank / KCB Fixed Deposits (12-month) — 20%

🟦 **Gentle Growth (20%)** — A little equity exposure for inflation protection, but only the safest kind.
   • NCBA Money Market Fund — 10%
   • CIC Conservative Balanced Fund — 10%

🟨 **Safety Net (5%)** — Ultra-liquid cushion for emergencies.
   • High-interest SACCO savings account

**International Diversification (Optional 10-15%):**
   • Vanguard Total Bond Market ETF (BND) — 8%
   • US Treasury Bills for dollar safety — 7%

**Mixed Strategy:**
Start 100% Kenyan for the first year—you'll sleep better with what you know. Once comfortable, add 10-15% international bonds for currency hedging. Think of it as insurance against KES swings, not a growth play.

**Strategy Snapshot:**
• **Kenyan Focus**: 85-90% (T-Bills, M-Akiba, FDs, Money Market)
• **Global Buffer**: 10-15% (International bonds, US Treasuries)

**Your Superpower:** Patience. You don't panic when others do, and that discipline compounds over decades.

**Level-Up Tip:**
Set up automatic monthly investments in T-Bills (M-Akiba makes this easy). Reinvest interest payments. Review quarterly—not daily.

**Watch Out For:**
Inflation eating your returns. With 8-12% returns and ~7% inflation, you're barely growing real wealth. Consider adding 5% more equity exposure if inflation stays high.

**Quick Wins This Week:**
1. Open M-Akiba account (mobile-friendly govt bonds)
2. Lock KSh 500,000 in a 12-month Equity Bank FD
3. Start auto-investing KSh 20,000/month in NCBA Money Market

**Expected Return:** 8-12% annually with minimal volatility
                """.strip()
            else:
                strategy = """
• **Asset Allocation**: 70% Bonds/Fixed Deposits, 30% Conservative Balanced Funds
• **Specific Investments**: Government bonds, High-grade corporate bonds, Conservative index funds
• **Timeline**: Review quarterly, rebalance annually
• **Expected Return**: 6-10% annually with low volatility
                """.strip()
            
            rationale = "This fortress strategy protects your capital while generating steady returns. The heavy Kenyan fixed-income allocation (75%) ensures stability and familiarity, while a small equity exposure (20%) fights inflation. The optional international component (10-15%) adds currency diversification without overwhelming complexity. Perfect for your low risk tolerance and need for predictability. You're building wealth the way it was meant to be built—slowly, surely, safely."
        
        elif risk_score < 0.6:
            personality = f"You're the investor who gets it—growth matters, but not at the cost of sleepless nights. You know the difference between smart risk and reckless gambling. You're patient enough to let compound interest work its magic, but ambitious enough to capture real market growth. That balance is your edge."
            
            if use_kenyan:
                strategy = """
**Portfolio Blueprint**

You invest best when your portfolio has rhythm—steady income from bonds, upside from stocks, and just enough global exposure to feel diversified.

**Layer System:**

🟩 **Core (50%)** — Your anchor. Kenyan blue chips and quality funds you can hold through any storm.
   • Safaricom (SCOM), Equity Group (EQTY), KCB — 25%
   • CIC Balanced Fund, ICEA LION Balanced — 15%
   • NSE Index Fund — 10%

🟦 **Stability (25%)** — Income generators that smooth out the bumps.
   • Kenya Government Bonds (5-10 year) — 15%
   • M-Akiba bonds — 5%
   • Corporate Bonds (Equity, KCB) — 5%

🟨 **Growth (20%)** — International exposure for diversification and dollar strength.
   • S&P 500 / Nasdaq index funds — 15%
   • Emerging markets ETF (India, Vietnam) — 5%

🟧 **Flexibility (5%)** — Quick-access money for opportunities or emergencies.
   • NCBA Money Market Fund

**Strategy Snapshot:**

**Kenyan Focus (65-70%):**
• **Blue Chips**: Safaricom, Equity Group, KCB, EABL
• **Balanced Funds**: CIC, ICEA LION, Britam
• **Fixed Income**: Govt Bonds, M-Akiba, NSE Index
• **Alternative**: SACCO shares, Fahari I-REIT

**Global Expansion (25-35%):**
• **Developed Markets (20%)** — S&P 500, Nasdaq (US tech & innovation)
• **Emerging Markets (10%)** — India, Vietnam, Nigeria ETFs
• **Thematic (5%)** — Global balanced funds, sector plays

**Mixed Strategy:**
Build your Kenyan core first (65-70%)—these are companies you understand and can track. Then layer in international (25-35%) for geographic diversification and dollar exposure. The 50/25/20/5 split gives you growth, income, safety, and flexibility all at once. Rebalance when any layer drifts more than 10% from target.

**Your Superpower:** Emotional stability. Markets swing, but you don't. You can hold through corrections because you've built a portfolio that matches your temperament.

**Level-Up Tip:**
Review monthly to stay engaged, but only rebalance semi-annually. Watching too closely breeds overtrading. Trust the strategy and let time work.

**Watch Out For:**
Chasing performance. When NSE is hot, you'll be tempted to go all-in. When international is hot, you'll want to abandon Kenya. Resist both. Your 65/35 split is your compass—don't abandon it for short-term noise.

**Quick Wins This Week:**
1. Buy 100 shares each of SCOM, EQTY, KCB (diversified NSE exposure)
2. Set up monthly auto-invest in CIC Balanced Fund (KSh 30,000)
3. Open international brokerage account (Interactive Brokers Kenya) for S&P 500 access

**Expected Return:** 13-18% annually with moderate volatility
                """.strip()
            else:
                strategy = """
• **Asset Allocation**: 60% Stocks/Equity Funds, 35% Bonds, 5% Cash
• **Specific Investments**: Index funds (S&P 500), Balanced mutual funds, Corporate bonds
• **Timeline**: Review monthly, rebalance semi-annually
• **Expected Return**: 10-14% annually with moderate volatility
                """.strip()
            
            rationale = f"This balanced portfolio matches your psychology perfectly. The Kenyan core (65-70%) keeps you grounded in companies you understand—Safaricom's M-Pesa ecosystem, Equity Group's fintech expansion, KCB's regional dominance. You can follow their quarterly earnings and feel connected. International exposure (25-35%) hedges currency risk and taps into US innovation (Apple, Google, Microsoft via S&P 500). Your {backend.get('monitoring_frequency', 'monthly')} monitoring frequency shows you're engaged but not obsessive—perfect for this rhythm. You're building real, lasting wealth without losing sleep or chasing every shiny trend."
        
        else:  # Aggressive
            personality = f"You've got the courage most investors wish they had. You see market swings not as threats but as opportunities to grow faster. You understand that volatility is part of the game—and you've got the time horizon and confidence to play the long one. When others panic, you stay cool. When markets dip, you get excited. That's the mindset of wealth builders."
            
            if use_kenyan:
                strategy = """
**Portfolio Blueprint**

You invest best when your portfolio feels alive—a mix of bold moves and smart anchors.

**Layer System:**

🟩 **Core (60%)** — Your foundation. Steady Kenyan companies you know and trust. These keep your portfolio grounded while everything else moves.
   • Safaricom (SCOM), Equity Group (EQTY), KCB — 30%
   • Britam Equity Fund, GenAfrica Equity Fund — 15%
   • NSE small-caps & emerging plays — 10%
   • Fahari I-REIT — 5%

🟦 **Growth (35%)** — The fun zone. Fast-moving opportunities that can supercharge returns. Global tech ETFs, emerging markets, and innovative sectors fit here.
   • U.S. tech (Nasdaq, S&P 500) — 20%
   • Emerging markets ETFs (India, Vietnam, Nigeria) — 10%
   • Thematic funds (clean energy, fintech, AI) — 5%

🟨 **Safety (5%)** — Your calm corner. A small cushion for peace of mind when markets dip. Think infrastructure bonds or money markets.
   • Kenyan Infrastructure Bonds or Money Market Fund

**Strategy Snapshot:**

**Kenyan Focus (60%):**
• **Growth Leaders**: Safaricom, Equity Group, KCB, EABL, Bamburi
• **Equity Funds**: Britam, CIC, GenAfrica
• **Small-Caps & REITs**: Fahari I-REIT, emerging NSE plays
• **Regional**: East African Community stocks (Uganda, Tanzania)

**Global Expansion (40%):**
• **U.S. Tech & Innovation (20%)** — Nasdaq & S&P 500 exposure
• **Emerging Markets (10%)** — India, Vietnam, Nigeria ETFs
• **Thematic (10%)** — fintech, clean energy, frontier markets

**Mixed Strategy:**
Anchor with 60% Kenyan equity you can research and understand (NSE financials, telco, industrials), then overlay 30-40% international for exposure to global tech, US growth, and emerging market dynamism. This gives you the explosive growth potential of African markets PLUS the stability and innovation of developed markets. Rebalance quarterly or when Kenya/international split moves beyond 15% from target.

**Your Superpower:** Emotional discipline. You can stomach short-term swings to chase long-term growth. While others sell in panic, you buy the dip. That conviction is worth more than any stock pick.

**Level-Up Tip:**
Check your portfolio weekly, rebalance quarterly. Don't react to noise—refine your edge. Set calendar reminders to rebalance, not to check prices. Consistency beats intensity in investing.

**Watch Out For:**
Over-concentration in one stock (even Safaricom). No single position should exceed 10% of your portfolio. Also, don't abandon your 60/40 Kenya/International split during hot streaks—that's when discipline pays most.

**Quick Wins This Week:**
1. Buy Safaricom, Equity Group, KCB (200 shares each) — KSh 200,000
2. Open Interactive Brokers Kenya account for S&P 500 access
3. Set up quarterly auto-rebalance alerts (Google Calendar)

**Expected Return:** 18-28% annually with high volatility (be prepared for 20-30% drawdowns). You're built for it.
                """.strip()
            else:
                strategy = """
• **Asset Allocation**: 85% Stocks, 10% Growth Funds, 5% Cash
• **Specific Investments**: Growth stocks, Small-cap funds, Sector ETFs, Individual stock picks
• **Timeline**: Review weekly, rebalance quarterly
• **Expected Return**: 15-20%+ annually with high volatility
                """.strip()
            
            rationale = f"Your portfolio thrives on momentum and conviction. You like staying close to what you understand—strong Kenyan companies you can research (Safaricom's M-Pesa dominance, Equity's fintech empire, KCB's regional expansion)—but also reaching out to global opportunities that move fast (US tech, emerging market rockets). The 60/40 Kenya/International mix gives you control, variety, and upside. Your superpower is emotional discipline—you can stomach 20-30% drawdowns to chase 25%+ annualized gains. With {backend.get('monitoring_frequency', 'daily')} monitoring, you can actively manage both markets and catch opportunities others miss. You're built for this game."
        
        # Add data quality warning
        data_quality_note = "⚠️ Market prices shown are typical ranges (SIMULATED). For production use, integrate real-time API - see MARKET_DATA_API_GUIDE.md"
        
        return {
            'risk_score': risk_score,
            'risk_category': category,
            'persona': persona,
            'confidence': risk_data.get('confidence', 0.7),
            'profile_card': {
                'personality': personality,
                'strategy': strategy,
                'rationale': rationale,
                'full_text': f"{personality}\n\n**YOUR INVESTMENT STRATEGY**\n{strategy}\n\n**WHY THIS WORKS FOR YOU**\n{rationale}"
            },
            'generated_by': 'fallback_template',
            'market_data_quality': 'simulated',
            'data_quality_note': data_quality_note
        }
    
    def generate_kenyan_specific_insights(self, risk_data: Dict[str, Any]) -> Dict[str, str]:
        """Generate Kenya-specific investment recommendations."""
        
        risk_score = risk_data.get('risk_score', 0.5)
        backend = risk_data.get('backend_features', {})
        
        insights = {
            'nse_stocks': [],
            'bonds': [],
            'funds': [],
            'alternatives': []
        }
        
        # Conservative
        if risk_score < 0.3:
            insights['bonds'] = ['Kenya Treasury Bills (91-day, 182-day)', 'M-Akiba (mobile bond)', 'Infrastructure Bonds']
            insights['funds'] = ['NCBA Money Market Fund', 'CIC Money Market Fund']
            insights['alternatives'] = ['SACCO Fixed Deposits', 'Equity Bank FD']
        
        # Moderate
        elif risk_score < 0.6:
            insights['nse_stocks'] = ['Safaricom (SCOM)', 'Equity Group (EQTY)', 'KCB Group (KCB)']
            insights['bonds'] = ['Kenya Government Bonds (5-10 year)', 'M-Akiba']
            insights['funds'] = ['CIC Balanced Fund', 'ICEA LION Balanced Fund']
            insights['alternatives'] = ['NSE Index Fund', 'SACCO shares']
        
        # Aggressive
        else:
            insights['nse_stocks'] = ['Safaricom (SCOM)', 'Equity Group (EQTY)', 'Bamburi Cement (BMBC)', 'Kenya Airways (KQ)']
            insights['funds'] = ['Britam Equity Fund', 'CIC Equity Fund', 'GenAfrica Equity Fund']
            insights['alternatives'] = ['REITs (Fahari I-REIT)', 'East Africa growth funds', 'Select small-cap NSE stocks']
            insights['bonds'] = ['Infrastructure Bonds (long-term)']
        
        return insights


# Global instance
profile_generator = None

def get_profile_generator() -> ProfileCardGenerator:
    """Get global profile card generator instance."""
    global profile_generator
    if profile_generator is None:
        profile_generator = ProfileCardGenerator()
    return profile_generator


if __name__ == "__main__":
    # Test the generator
    from ml_service import PortfoliAIMLService
    
    service = PortfoliAIMLService()
    generator = ProfileCardGenerator()
    
    # Test with sample survey data
    survey_data = {
        'age': 30,
        'occupation': 'Salaried',
        'invests': True,
        'investment_proportion': '20% - 30%',
        'expected_return': '10% - 15%',
        'investment_horizon': '5+ years',
        'monitoring_frequency': 'Weekly',
        'equity_rank': 5,
        'fund_rank': 4,
        'invests_stock': True,
        'main_avenue': 'Equity'
    }
    
    # Get risk prediction
    risk_result = service.predict_survey_risk(survey_data)
    
    # Generate profile card
    survey_answers = {
        'market_reaction': 'b',
        'goal': 'b'
    }
    
    profile_card = generator.generate_profile_card(risk_result, survey_answers, use_kenyan_context=True)
    
    print("=" * 60)
    print("INVESTOR PROFILE CARD")
    print("=" * 60)
    print(f"\nRisk Score: {profile_card['risk_score']:.2f}")
    print(f"Category: {profile_card['risk_category']}")
    print(f"Persona: {profile_card['persona']}\n")
    print(profile_card['profile_card']['full_text'])
    print("\n" + "=" * 60)


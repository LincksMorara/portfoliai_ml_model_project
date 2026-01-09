"""
FastAPI server for PortfoliAI ML Service
Provides HTTP endpoints for ML predictions
"""

from fastapi import FastAPI, HTTPException, Response, Cookie, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
import os
from datetime import datetime
from ml_service import get_ml_service
from survey_mapper import map_redesigned_survey_to_backend
from profile_card_generator import get_profile_generator

# Supabase integration
from app.database import supabase, supabase_admin
from app.services.auth_service import get_auth_service
from app.schemas.user import UserSignup, UserLogin, InvestorProfileCreate

# Fallback auth system
try:
    from auth import get_auth_system
    FALLBACK_AUTH_AVAILABLE = True
except ImportError:
    FALLBACK_AUTH_AVAILABLE = False

from fmp_integration import get_fmp_client
from finnhub_integration import get_finnhub_client
from conversational_chatbot import get_conversational_chatbot
from event_detector import get_event_detector
from portfolio_manager import get_portfolio_manager
from withdrawal_planner import get_withdrawal_planner
from conversation_manager import get_conversation_manager
from app.services.portfolio_context import build_portfolio_context
from app.services.currency import (
    normalize_currency,
    convert_portfolio_summary,
    convert_transactions,
    convert_withdrawals,
    convert_withdrawal_plan,
    convert_portfolio_data,
    get_currency_symbol,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="PortfoliAI ML Service", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static symbol metadata for risk calculations
SYMBOL_METADATA = {
    'AAPL': {'beta': 1.20, 'sector': 'Technology', 'region': 'US'},
    'TSLA': {'beta': 1.60, 'sector': 'Technology', 'region': 'US'},
    'AMZN': {'beta': 1.15, 'sector': 'Technology', 'region': 'US'},
    'MSFT': {'beta': 1.00, 'sector': 'Technology', 'region': 'US'},
    'SCOM': {'beta': 0.80, 'sector': 'Telecom', 'region': 'Kenya'},
    'EQTY': {'beta': 0.70, 'sector': 'Financials', 'region': 'Kenya'},
    'KCB': {'beta': 0.75, 'sector': 'Financials', 'region': 'Kenya'},
    'EABL': {'beta': 0.65, 'sector': 'Consumer Staples', 'region': 'Kenya'},
    'T-BILLS': {'beta': 0.05, 'sector': 'Fixed Income', 'region': 'Kenya'},
    'ETF_US_TOTAL': {'beta': 1.00, 'sector': 'Multi', 'region': 'US'},
    'ETF_GLOBAL': {'beta': 0.95, 'sector': 'Multi', 'region': 'Global'},
}

USE_PORTFOLIO_CONTEXT = os.getenv("USE_PORTFOLIO_CONTEXT", "false").lower() == "true"

# Initialize ML service, profile generator, auth service, and FMP client
ml_service = get_ml_service()
profile_generator = get_profile_generator()
auth_service = get_auth_service()
fmp_client = get_fmp_client()


def ensure_portfolio(user_id: str) -> Dict[str, Any]:
    """
    Fetch portfolio for a user or create a default one if missing.
    Ensures new or migrated accounts always have a portfolio row.
    """
    if supabase is None or supabase_admin is None:
        raise HTTPException(
            status_code=503,
            detail="Portfolio service unavailable - Supabase not configured"
        )
    
    try:
        response = supabase.table("portfolios")\
            .select("*")\
            .eq("user_id", user_id)\
            .execute()
        
        if response.data:
            return response.data[0]
        
        default_portfolio = {
            "user_id": user_id,
            "name": "My Portfolio",
            "currency": "USD",
            "cash_balance": 0.0,
            "total_invested": 0.0,
            "current_value": 0.0,
            "total_profit_loss": 0.0
        }
        
        insert_response = supabase_admin.table("portfolios")\
            .insert(default_portfolio)\
            .execute()
        
        if insert_response.data:
            logger.info(f"✅ Created default portfolio for user {user_id}")
            return insert_response.data[0]
        
        # Fallback: try fetching again (some drivers return no data on insert)
        response = supabase.table("portfolios")\
            .select("*")\
            .eq("user_id", user_id)\
            .execute()
        if response.data:
            return response.data[0]
        
        raise HTTPException(status_code=500, detail="Failed to create portfolio")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Portfolio initialization error for {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Could not initialize portfolio")

# Fallback portfolio builder (file-based auth/portfolio)
def build_local_portfolio_context(user_id: str, target_currency: str = 'USD') -> Optional[Dict[str, Any]]:
    """
    Build portfolio context from the file-based portfolio manager when Supabase is unavailable.
    """
    pm = get_portfolio_manager(user_id)
    portfolio = pm.portfolio or {}
    positions_raw = portfolio.get('positions', [])
    cash_balance = float(portfolio.get('cash_balance', 0) or 0)
    
    if not positions_raw and cash_balance <= 0:
        return None
    
    holdings_map: Dict[str, Dict[str, Any]] = {}
    total_position_value = 0.0
    
    for pos in positions_raw:
        symbol = (pos.get('symbol') or 'N/A').upper()
        quantity = float(pos.get('quantity', 0) or 0)
        if quantity <= 0:
            continue
        
        market = pos.get('market', 'US')
        current_price = pm.get_current_price(symbol, market)
        if current_price is None:
            current_price = float(pos.get('purchase_price', 0) or 0)
        if current_price is None:
            current_price = 0.0
        
        entry_pl = pm.calculate_position_pl(pos, current_price)
        
        holding = holdings_map.setdefault(symbol, {
            'symbol': symbol,
            'total_quantity': 0.0,
            'total_cost_basis': 0.0,
            'current_value': 0.0,
            'entries': [],
            'entry_count': 0
        })
        
        holding['entries'].append(entry_pl)
        holding['entry_count'] += 1
        holding['total_quantity'] += entry_pl['quantity']
        holding['total_cost_basis'] += entry_pl['cost_basis']
        holding['current_value'] += entry_pl['current_value']
    
    fallback_positions = []
    allocation = []
    
    for holding in holdings_map.values():
        if holding['total_quantity'] <= 0:
            continue
        
        average_cost = holding['total_cost_basis'] / holding['total_quantity'] if holding['total_quantity'] > 0 else 0
        current_price = holding['current_value'] / holding['total_quantity'] if holding['total_quantity'] > 0 else 0
        total_pl = holding['current_value'] - holding['total_cost_basis']
        total_pl_percent = (total_pl / holding['total_cost_basis'] * 100) if holding['total_cost_basis'] > 0 else 0
        
        fallback_positions.append({
            'symbol': holding['symbol'],
            'total_quantity': holding['total_quantity'],
            'average_cost': average_cost,
            'current_price': current_price,
            'current_value': holding['current_value'],
            'total_invested': holding['total_cost_basis'],
            'total_pl': total_pl,
            'total_pl_percent': total_pl_percent,
            'entries': holding['entries'],
            'entry_count': holding['entry_count'],
            'price_source': 'api'
        })
        
        total_position_value += holding['current_value']
    
    total_portfolio_value = cash_balance + total_position_value
    
    for holding in fallback_positions:
        percent = (holding['current_value'] / total_portfolio_value * 100) if total_portfolio_value > 0 else 0
        meta = SYMBOL_METADATA.get(holding['symbol'].upper(), {})
        allocation.append({
            'symbol': holding['symbol'],
            'value': holding['current_value'],
            'percent': percent,
            'sector': meta.get('sector', 'General'),
            'region': meta.get('region', 'Global'),
            'beta': meta.get('beta', 1.0)
        })
    
    equity_percent = (total_position_value / total_portfolio_value * 100) if total_portfolio_value > 0 else 0
    cash_percent = (cash_balance / total_portfolio_value * 100) if total_portfolio_value > 0 else 0
    portfolio_beta = 0.0
    for alloc in allocation:
        portfolio_beta += (alloc['percent'] / 100) * alloc.get('beta', 1.0)
    
    risk_metrics = {
        'portfolio_beta': round(portfolio_beta, 2),
        'estimated_volatility': round(0.18 * portfolio_beta, 4) if total_portfolio_value > 0 else 0,
        'equity_percent': round(equity_percent, 1),
        'cash_percent': round(cash_percent, 1),
        'correlation_warnings': [],
        'diversification_tips': []
    }
    
    withdrawals = portfolio.get('withdrawals', []) or []
    withdrawal_stats = {
        'total_count': len(withdrawals),
        'ytd_count': 0,
        'ytd_amount': 0.0,
        'last_withdrawal': withdrawals[0].get('date') if withdrawals and isinstance(withdrawals[0], dict) else None
    }
    
    portfolio_context = {
        'source': 'file',
        'positions_count': len(fallback_positions),
        'positions': fallback_positions,
        'cash_balance': cash_balance,
        'portfolio_value': total_portfolio_value,
        'withdrawals': withdrawals,
        'withdrawal_stats': withdrawal_stats,
        'withdrawal_projection': {
            'current_value': total_portfolio_value,
            'cash_balance': cash_balance
        },
        'allocation': allocation,
        'concentration_alert': None,
        'risk_metrics': risk_metrics,
        'scenario_options': []
    }
    return convert_portfolio_data(portfolio_context, target_currency)

# NEW: Redesigned Survey Model
class RedesignedSurveyData(BaseModel):
    happiness_outcome: str  # a, b, c
    horizon: str  # a, b, c
    risk_slider: int  # 1-10
    market_reaction: str  # a, b, c
    knowledge_slider: int  # 1-10
    income_stability: str  # a, b, c
    experience: str  # a, b, c
    age_group: str  # a, b, c
    goal: str  # a, b, c
    loss_tolerance: str  # a, b, c, d
    liquidity: str  # a, b, c
    diversification: str  # a, b, c
    monitoring: str  # a, b, c, d, e

# OLD: Original Survey Model (kept for backwards compatibility)
class SurveyData(BaseModel):
    age: int
    gender: Optional[str] = "male"
    education_level: Optional[int] = 3
    occupation: Optional[str] = "Salaried"
    invests: Optional[bool] = True
    investment_proportion: str
    expected_return: str
    investment_horizon: str
    monitoring_frequency: str
    equity_rank: int
    fund_rank: int
    invests_stock: Optional[bool] = True
    main_avenue: Optional[str] = "Equity"

class TransactionData(BaseModel):
    amount: float
    asset_id: str
    asset_type: str
    trade_type: str
    timestamp: str

class MetaRiskRequest(BaseModel):
    survey_data: SurveyData
    transaction_data: Optional[List[TransactionData]] = None
    survey_weight: float = 0.5

# Home page with Login/Survey options
@app.get("/", response_class=HTMLResponse)
async def root_page():
    """Homepage with login or take survey options"""
    return open('home.html', 'r').read()

# Survey page
@app.get("/survey", response_class=HTMLResponse)
async def survey_page():
    """Main user-friendly survey interface"""
    return open('redesigned_survey.html', 'r').read()

# Keep v2 route for backwards compatibility
@app.get("/v2", response_class=HTMLResponse)
async def redesigned_survey_page():
    """Redesigned user-friendly survey interface (same as root)"""
    return open('redesigned_survey.html', 'r').read()

# Original technical UI at /legacy
@app.get("/legacy", response_class=HTMLResponse)
async def legacy_page():
    return """
<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
  <title>PortfoliAI Demo</title>
  <style>
    body { font-family: -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif; margin: 24px; line-height: 1.4; }
    h1 { margin-bottom: 8px; }
    fieldset { border: 1px solid #ddd; padding: 16px; margin-bottom: 16px; }
    legend { font-weight: 600; }
    label { display: block; margin: 8px 0 4px; }
    input, select { width: 100%; max-width: 360px; padding: 8px; }
    button { margin-top: 12px; padding: 8px 12px; cursor: pointer; }
    .row { display: flex; gap: 24px; flex-wrap: wrap; }
    .card { flex: 1 1 360px; border: 1px solid #eee; padding: 16px; border-radius: 8px; }
    pre { background: #0b1021; color: #e6e6e6; padding: 12px; border-radius: 6px; overflow: auto; }
  </style>
  <script>
    async function postJSON(url, data) {
      const res = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
      if (!res.ok) { throw new Error(await res.text()); }
      return res.json();
    }

    async function submitSurvey(e) {
      e.preventDefault();
      const payload = {
        age: parseInt(document.getElementById('age').value || '35'),
        gender: document.getElementById('gender').value,
        education_level: parseInt(document.getElementById('education_level').value || '3'),
        occupation: document.getElementById('occupation').value,
        invests: document.getElementById('invests').value === 'true',
        investment_proportion: document.getElementById('investment_proportion').value,
        expected_return: document.getElementById('expected_return').value,
        investment_horizon: document.getElementById('investment_horizon').value,
        monitoring_frequency: document.getElementById('monitoring_frequency').value,
        equity_rank: parseInt(document.getElementById('equity_rank').value || '3'),
        fund_rank: parseInt(document.getElementById('fund_rank').value || '2'),
        invests_stock: document.getElementById('invests_stock').value === 'true',
        main_avenue: document.getElementById('main_avenue').value
      };
      try {
        const result = await postJSON('/predict/survey-risk', payload);
        document.getElementById('survey_result').textContent = JSON.stringify(result, null, 2);
      } catch (err) {
        document.getElementById('survey_result').textContent = 'Error: ' + err.message;
      }
    }

    async function submitMeta(e) {
      e.preventDefault();
      const survey = {
        age: parseInt(document.getElementById('age').value || '35'),
        gender: document.getElementById('gender').value,
        education_level: parseInt(document.getElementById('education_level').value || '3'),
        occupation: document.getElementById('occupation').value,
        invests: document.getElementById('invests').value === 'true',
        investment_proportion: document.getElementById('investment_proportion').value,
        expected_return: document.getElementById('expected_return').value,
        investment_horizon: document.getElementById('investment_horizon').value,
        monitoring_frequency: document.getElementById('monitoring_frequency').value,
        equity_rank: parseInt(document.getElementById('equity_rank').value || '3'),
        fund_rank: parseInt(document.getElementById('fund_rank').value || '2'),
        invests_stock: document.getElementById('invests_stock').value === 'true',
        main_avenue: document.getElementById('main_avenue').value
      };
      const txText = document.getElementById('transactions').value.trim();
      let tx = undefined;
      if (txText) {
        try { tx = JSON.parse(txText); } catch (_) { alert('Transactions must be valid JSON array'); return; }
      }
      const payload = { survey_data: survey, transaction_data: tx, survey_weight: parseFloat(document.getElementById('survey_weight').value || '0.5') };
      try {
        const result = await postJSON('/predict/meta-risk', payload);
        document.getElementById('meta_result').textContent = JSON.stringify(result, null, 2);
      } catch (err) {
        document.getElementById('meta_result').textContent = 'Error: ' + err.message;
      }
    }
  </script>
  </head>
  <body>
    <h1>PortfoliAI Demo</h1>
    <p>Quickly test survey and meta risk predictions.</p>

    <div class=\"row\">
      <div class=\"card\">
        <form onsubmit=\"submitSurvey(event)\">
          <fieldset>
            <legend>Survey Inputs</legend>
            <label>Age</label>
            <input id=\"age\" type=\"number\" value=\"35\" />
            <label>Gender</label>
            <select id=\"gender\">
              <option value=\"male\">Male</option>
              <option value=\"female\">Female</option>
            </select>
            <label>Education Level</label>
            <select id=\"education_level\">
              <option value=\"1\">Below High School</option>
              <option value=\"2\">High School</option>
              <option value=\"3\" selected>Bachelor's Degree</option>
              <option value=\"4\">Master's Degree</option>
              <option value=\"5\">Doctorate</option>
            </select>
            <label>Occupation</label>
            <select id=\"occupation\">
              <option value=\"Salaried\" selected>Salaried</option>
              <option value=\"Self-employed\">Self-employed</option>
              <option value=\"Student\">Student</option>
              <option value=\"Others\">Others</option>
            </select>
            <label>Do you currently invest?</label>
            <select id=\"invests\">
              <option value=\"true\">Yes</option>
              <option value=\"false\">No</option>
            </select>
            <label>Investment Proportion</label>
            <select id=\"investment_proportion\">
              <option>10% - 20%</option>
              <option>20% - 30%</option>
              <option>30% - 40%</option>
              <option>40% and above</option>
            </select>
            <label>Expected Return</label>
            <select id=\"expected_return\">
              <option>5% - 10%</option>
              <option>10% - 15%</option>
              <option>15% and above</option>
            </select>
            <label>Investment Horizon</label>
            <select id=\"investment_horizon\">
              <option>1-3 years</option>
              <option selected>3-5 years</option>
              <option>5+ years</option>
            </select>
            <label>Monitoring Frequency</label>
            <select id=\"monitoring_frequency\">
              <option>Monthly</option>
              <option>Weekly</option>
              <option>Daily</option>
            </select>
            <label>Equity Preference Rank (1-7)</label>
            <small style=\"color: #666;\">How much do you prefer equity investments? (1=lowest, 7=highest)</small>
            <input id=\"equity_rank\" type=\"number\" min=\"1\" max=\"7\" value=\"3\" />
            <label>Mutual Fund Preference Rank (1-7)</label>
            <small style=\"color: #666;\">How much do you prefer mutual funds? (1=lowest, 7=highest)</small>
            <input id=\"fund_rank\" type=\"number\" min=\"1\" max=\"7\" value=\"2\" />
            <label>Do you invest in stocks/equity?</label>
            <select id=\"invests_stock\">
              <option value=\"true\">Yes</option>
              <option value=\"false\">No</option>
            </select>
            <label>Main Investment Avenue</label>
            <select id=\"main_avenue\">
              <option value=\"Equity\" selected>Equity</option>
              <option value=\"Mutual Funds\">Mutual Funds</option>
              <option value=\"Fixed Deposits\">Fixed Deposits</option>
              <option value=\"Bonds\">Bonds</option>
              <option value=\"Gold / SGBs\">Gold / SGBs</option>
              <option value=\"PPF - Public Provident Fund\">PPF - Public Provident Fund</option>
            </select>
            <button type=\"submit\">Predict Survey Risk</button>
          </fieldset>
        </form>
        <pre id=\"survey_result\"></pre>
      </div>

      <div class=\"card\">
        <form onsubmit=\"submitMeta(event)\">
          <fieldset>
            <legend>Meta Risk (Optional Transactions)</legend>
            <label>Survey Weight (0-1)</label>
            <input id=\"survey_weight\" type=\"number\" step=\"0.1\" min=\"0\" max=\"1\" value=\"0.5\" />
            <label>Transactions JSON Array</label>
            <textarea id=\"transactions\" rows=\"10\" style=\"width:100%;\" placeholder='[
  {"amount": 5000, "asset_id": "AAPL", "asset_type": "Stock", "trade_type": "buy", "timestamp": "2024-01-15"}
]'></textarea>
            <button type=\"submit\">Predict Meta Risk</button>
          </fieldset>
        </form>
        <pre id=\"meta_result\"></pre>
      </div>
    </div>
  </body>
</html>
"""

# Authentication Pages
@app.get("/login", response_class=HTMLResponse)
async def login_page():
    """Login page"""
    return open('login.html', 'r').read()

@app.get("/signup", response_class=HTMLResponse)
async def signup_page():
    """Signup page"""
    return open('signup.html', 'r').read()

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page():
    """Dashboard page (requires authentication)"""
    return open('dashboard.html', 'r').read()

@app.get("/chatbot", response_class=HTMLResponse)
async def chatbot_page():
    """AI Chatbot page with conversation management"""
    return open('chatbot_v2.html', 'r').read()

@app.get("/chatbot/simple", response_class=HTMLResponse)
async def chatbot_simple_page():
    """Simple chatbot (old version without conversations)"""
    return open('chatbot.html', 'r').read()

@app.get("/chatbot/test", response_class=HTMLResponse)
async def chatbot_test_page():
    """Diagnostic test page for debugging chatbot issues"""
    return open('chatbot_test.html', 'r').read()

@app.get("/portfolio", response_class=HTMLResponse)
async def portfolio_page():
    """Portfolio tracking and management dashboard"""
    return open('portfolio.html', 'r').read()

# Authentication API Endpoints
@app.post("/auth/signup")
async def auth_signup(response: Response, data: Dict[str, Any]):
    """Signup endpoint with Supabase (falls back to file-based auth if Supabase unavailable)"""
    
    # Try Supabase first if available
    if supabase is not None and supabase_admin is not None:
        try:
            # Parse investor profile if provided
            investor_profile = None
            if data.get('investor_profile'):
                try:
                    investor_profile = InvestorProfileCreate(**data['investor_profile'])
                except Exception as e:
                    logger.warning(f"Failed to parse investor profile: {e}")
            
            # Create signup data
            signup_data = UserSignup(
                email=data['email'],
                password=data['password'],
                full_name=data.get('full_name')
            )
            
            # Call Supabase signup
            result = await auth_service.signup(signup_data, investor_profile)
            
            logger.info(f"✅ New user signed up via Supabase: {data.get('email')}")
            
            # Auto-login after signup
            login_data = UserLogin(email=data['email'], password=data['password'])
            login_result = await auth_service.login(login_data)
            
            # Set session cookie
            response.set_cookie(
                key="access_token",
                value=login_result['access_token'],
                httponly=True,
                max_age=24 * 60 * 60,
                path="/",
                samesite="lax",
                secure=False
            )
            
            return {
                'user': login_result['user'],
                'message': 'Account created successfully! You are now logged in.'
            }
        except ValueError as e:
            # User errors (duplicate email, invalid password, etc.) - don't fallback
            raise HTTPException(status_code=400, detail=str(e))
        except (ConnectionError, TimeoutError, OSError) as e:
            # Connection errors - fallback to file-based auth
            logger.warning(f"⚠️ Supabase connection error: {e}, falling back to file-based auth")
            # Fall through to fallback auth
        except Exception as e:
            # Check if it's a connection/DNS error
            error_str = str(e).lower()
            if 'nodename' in error_str or 'servname' in error_str or 'connection' in error_str or 'timeout' in error_str:
                logger.warning(f"⚠️ Supabase connection error: {e}, falling back to file-based auth")
                # Fall through to fallback auth
            else:
                # Other errors - don't fallback, raise them
                logger.error(f"❌ Supabase signup error: {e}")
                raise HTTPException(status_code=500, detail=f"Signup failed: {str(e)}")
    
    # Fallback to file-based auth system
    if FALLBACK_AUTH_AVAILABLE:
        try:
            fallback_auth = get_auth_system()
            investor_profile = data.get('investor_profile', {})
            
            result = fallback_auth.signup(
                email=data['email'],
                password=data['password'],
                investor_profile=investor_profile
            )
            
            logger.info(f"✅ New user signed up via file-based auth: {data.get('email')}")
            
            # Auto-login
            login_result = fallback_auth.login(data['email'], data['password'])
            
            if login_result:
                # Set session cookie with session token
                response.set_cookie(
                    key="access_token",
                    value=login_result['session_token'],
                    httponly=True,
                    max_age=7 * 24 * 60 * 60,  # 7 days
                    path="/",
                    samesite="lax",
                    secure=False
                )
                
                return {
                    'user_id': login_result['user_id'],
                    'email': login_result['email'],
                    'session_token': login_result['session_token'],
                    'investor_profile': login_result.get('investor_profile'),
                    'message': 'Account created successfully! You are now logged in.'
                }
            else:
                raise HTTPException(status_code=500, detail="Failed to login after signup")
                
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"❌ Fallback signup error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    else:
        raise HTTPException(
            status_code=503,
            detail="Authentication system not available. Please configure Supabase or ensure auth.py is available."
        )

@app.post("/auth/login")
async def auth_login(response: Response, data: Dict[str, str]):
    """Login endpoint with Supabase (falls back to file-based auth if Supabase unavailable)"""
    
    # Try Supabase first if available
    if supabase is not None and supabase_admin is not None:
        try:
            login_data = UserLogin(email=data['email'], password=data['password'])
            result = await auth_service.login(login_data)
            
            # Set session cookie with access token
            response.set_cookie(
                key="access_token",
                value=result['access_token'],
                httponly=True,
                max_age=24 * 60 * 60,  # 24 hours
                path="/",
                samesite="lax",
                secure=False
            )
            
            logger.info(f"✅ User logged in via Supabase: {data['email']}")
            
            return {
                'user': result['user'],
                'message': 'Logged in successfully!'
            }
        except ValueError as e:
            # User errors (invalid credentials, etc.) - don't fallback
            raise HTTPException(status_code=401, detail=str(e))
        except (ConnectionError, TimeoutError, OSError) as e:
            # Connection errors - fallback to file-based auth
            logger.warning(f"⚠️ Supabase connection error: {e}, falling back to file-based auth")
            # Fall through to fallback auth
        except Exception as e:
            # Check if it's a connection/DNS error
            error_str = str(e).lower()
            if 'nodename' in error_str or 'servname' in error_str or 'connection' in error_str or 'timeout' in error_str:
                logger.warning(f"⚠️ Supabase connection error: {e}, falling back to file-based auth")
                # Fall through to fallback auth
            else:
                # Other errors - don't fallback, raise them
                logger.error(f"❌ Supabase login error: {e}")
                raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")
    
    # Fallback to file-based auth system
    if FALLBACK_AUTH_AVAILABLE:
        try:
            fallback_auth = get_auth_system()
            login_result = fallback_auth.login(data['email'], data['password'])
            
            if not login_result:
                raise HTTPException(status_code=401, detail="Invalid email or password")
            
            logger.info(f"✅ User logged in via file-based auth: {data['email']}")
            
            # Set session cookie
            response.set_cookie(
                key="access_token",
                value=login_result['session_token'],
                httponly=True,
                max_age=7 * 24 * 60 * 60,  # 7 days
                path="/",
                samesite="lax",
                secure=False
            )
            
            return {
                'user_id': login_result['user_id'],
                'email': login_result['email'],
                'session_token': login_result['session_token'],
                'investor_profile': login_result.get('investor_profile'),
                'message': 'Logged in successfully!'
            }
        except ValueError as e:
            raise HTTPException(status_code=401, detail=str(e))
        except Exception as e:
            logger.error(f"❌ Fallback login error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    else:
        raise HTTPException(
            status_code=503,
            detail="Authentication system not available. Please configure Supabase or ensure auth.py is available."
        )

@app.get("/auth/me")
async def auth_me(access_token: Optional[str] = Cookie(default=None)):
    """Get current user data with investor profile (supports both Supabase and fallback auth)"""
    
    if not access_token:
        logger.error("No access token found in cookies")
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Try Supabase first if available
    if supabase is not None and supabase_admin is not None:
        try:
            logger.info(f"Verifying Supabase access token...")
            user = await auth_service.get_current_user(access_token)
            
            if not user:
                logger.error(f"Invalid or expired Supabase access token")
                raise HTTPException(status_code=401, detail="Invalid or expired session")
            
            logger.info(f"✅ User authenticated via Supabase: {user.email}")
            
            # Get investor profile from Supabase
            try:
                profile_response = supabase.table("investor_profiles")\
                    .select("*")\
                    .eq("user_id", user.id)\
                    .execute()
                
                investor_profile = profile_response.data[0] if profile_response.data else None
                
                return {
                    'user_id': user.id,
                    'email': user.email,
                    'full_name': user.full_name,
                    'investor_profile': investor_profile
                }
            except Exception as e:
                logger.error(f"Error fetching investor profile: {e}")
                # Return user data without profile if error
                return {
                    'user_id': user.id,
                    'email': user.email,
                    'full_name': user.full_name,
                    'investor_profile': None
                }
        except HTTPException:
            raise
        except Exception as e:
            # If Supabase fails, try fallback auth
            logger.debug(f"Supabase auth failed, trying fallback: {e}")
            # Fall through to fallback
    
    # Fallback to file-based auth
    if FALLBACK_AUTH_AVAILABLE:
        try:
            fallback_auth = get_auth_system()
            user_data = fallback_auth.verify_session(access_token)
            
            if not user_data:
                raise HTTPException(status_code=401, detail="Invalid or expired session")
            
            logger.info(f"✅ User authenticated via fallback auth: {user_data.get('email')}")
            
            return {
                'user_id': user_data.get('user_id'),
                'email': user_data.get('email'),
                'full_name': user_data.get('full_name'),
                'investor_profile': user_data.get('investor_profile')
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Fallback auth error: {e}")
            raise HTTPException(status_code=401, detail="Invalid or expired session")
    else:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

@app.post("/auth/logout")
async def auth_logout(response: Response, access_token: Optional[str] = Cookie(default=None)):
    """Logout endpoint with Supabase"""
    if access_token:
        await auth_service.logout(access_token)
    
    # Clear cookie properly with same path
    response.delete_cookie(key="access_token", path="/")
    
    return {"message": "Logged out successfully"}

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "PortfoliAI ML Service"}


@app.get("/api/market/quote")
async def get_market_quote(symbol: str):
    """Fetch live market quote via FMP for frontend usage"""
    if not symbol:
        raise HTTPException(status_code=400, detail="Symbol is required")
    
    try:
        quote = fmp_client.get_quote(symbol.upper())
        if not quote or quote.get("error"):
            detail = quote.get("error") if quote else "Quote unavailable"
            raise HTTPException(status_code=404, detail=f"{symbol.upper()}: {detail}")
        
        return {
            "symbol": quote.get("symbol"),
            "name": quote.get("name"),
            "price": quote.get("price"),
            "change": quote.get("change"),
            "change_percent": quote.get("change_percent"),
            "source": quote.get("source", "FMP"),
            "timestamp": quote.get("timestamp"),
            "raw": quote.get("raw_data"),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching market quote for {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch market quote")

# Conversation Management Endpoints
@app.get("/api/conversations")
async def get_conversations(access_token: Optional[str] = Cookie(default=None)):
    """Get all conversations for user"""
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = await auth_service.get_current_user(access_token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    user_data = {'user_id': user.id}
    
    try:
        cm = get_conversation_manager()
        conversations = cm.get_user_conversations(user_data['user_id'])
        
        # Return summary (without full message history for performance)
        summary = []
        for conv in conversations:
            summary.append({
                'conversation_id': conv['conversation_id'],
                'title': conv['title'],
                'message_count': len(conv.get('messages', [])),
                'created_at': conv['created_at'],
                'last_updated': conv['last_updated']
            })
        
        return {'conversations': summary}
    except Exception as e:
        logger.error(f"Error getting conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/conversations/create")
async def create_conversation(data: Dict[str, Any], access_token: Optional[str] = Cookie(default=None)):
    """Create a new conversation"""
    if not access_token:
        logger.warning("Create conversation: No access token")
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = await auth_service.get_current_user(access_token)
    if not user:
        logger.warning("Create conversation: Invalid session")
        raise HTTPException(status_code=401, detail="Invalid session")
    
    user_data = {'user_id': user.id}
    
    try:
        cm = get_conversation_manager()
        initial_message = data.get('initial_message')
        
        logger.info(f"Creating conversation for user {user_data['user_id']}")
        conversation = cm.create_conversation(user_data['user_id'], initial_message)
        logger.info(f"✅ Created conversation: {conversation['conversation_id']} - '{conversation['title']}'")
        
        return conversation
    except Exception as e:
        logger.error(f"❌ Error creating conversation: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error creating conversation: {str(e)}")

@app.post("/api/conversations/{conversation_id}/rename")
async def rename_conversation(conversation_id: str, data: Dict[str, Any], access_token: Optional[str] = Cookie(default=None)):
    """Rename a conversation"""
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = await auth_service.get_current_user(access_token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    user_data = {'user_id': user.id}
    
    try:
        cm = get_conversation_manager()
        new_title = data.get('title', '')
        
        if not new_title:
            raise HTTPException(status_code=400, detail="Title required")
        
        success = cm.rename_conversation(user_data['user_id'], conversation_id, new_title)
        
        if success:
            return {'success': True, 'title': new_title}
        else:
            raise HTTPException(status_code=404, detail="Conversation not found")
    except Exception as e:
        logger.error(f"Error renaming conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str, access_token: Optional[str] = Cookie(default=None)):
    """Delete a conversation"""
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = await auth_service.get_current_user(access_token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    user_data = {'user_id': user.id}
    
    try:
        cm = get_conversation_manager()
        success = cm.delete_conversation(user_data['user_id'], conversation_id)
        
        if success:
            return {'success': True}
        else:
            raise HTTPException(status_code=404, detail="Conversation not found")
    except Exception as e:
        logger.error(f"Error deleting conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/conversations/{conversation_id}")
async def get_conversation_messages(conversation_id: str, access_token: Optional[str] = Cookie(default=None)):
    """Get full conversation with all messages"""
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = await auth_service.get_current_user(access_token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    user_data = {'user_id': user.id}
    
    try:
        cm = get_conversation_manager()
        conversation = cm.get_conversation(user_data['user_id'], conversation_id)
        
        if conversation:
            return conversation
        else:
            raise HTTPException(status_code=404, detail="Conversation not found")
    except Exception as e:
        logger.error(f"Error getting conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Smart Chatbot API endpoint (now with conversation support)
@app.post("/api/chatbot")
async def smart_chatbot_query(
    data: Dict[str, Any],
    access_token: Optional[str] = Cookie(default=None),
    currency: str = 'USD'
):
    """
    Intelligent investment research chatbot with conversation management (Supabase)
    """
    try:
        user_message = data.get('message', '').strip()
        conversation_id = data.get('conversation_id')  # Optional - which conversation
        currency = normalize_currency(currency)
        
        if not user_message:
            return {
                "response": "Hi! I'm your investment research assistant. Ask me anything about stocks, like 'Should I invest in Apple?' or 'What do you think about Tesla?'",
                "type": "info"
            }
        
        # Default user profile if not authenticated
        user_profile = {
            'risk_score': 0.5,
            'risk_category': 'Comfortable',
            'persona': 'Strategic Balancer'
        }
        
        user_id = "anonymous"
        
        # Get user profile from Supabase or fallback auth
        if access_token:
            supabase_user_loaded = False
            try:
                user = await auth_service.get_current_user(access_token)
                if user:
                    user_id = user.id
                    supabase_user_loaded = True
                    
                    profile_response = supabase.table("investor_profiles")\
                        .select("*")\
                        .eq("user_id", user.id)\
                        .execute()
                    
                    if profile_response.data:
                        profile = profile_response.data[0]
                        user_profile = {
                            'risk_score': float(profile.get('risk_score', 0.5)),
                            'risk_category': profile.get('risk_category', 'Comfortable'),
                            'persona': profile.get('persona', 'Strategic Balancer')
                        }
                        logger.info(f"✅ Loaded profile from Supabase for user {user_id}: {user_profile['persona']}")
            except Exception as e:
                logger.warning(f"Could not load user profile from Supabase: {e}")

            if not supabase_user_loaded and FALLBACK_AUTH_AVAILABLE:
                try:
                    fallback_auth = get_auth_system()
                    user_data = fallback_auth.verify_session(access_token)
                    if user_data:
                        user_id = user_data.get('user_id') or user_data.get('email', 'anonymous')
                        profile = user_data.get('investor_profile') or {}
                        if profile:
                            user_profile = {
                                'risk_score': float(profile.get('risk_score', 0.5)),
                                'risk_category': profile.get('category', profile.get('risk_category', 'Comfortable')),
                                'persona': profile.get('persona', 'Strategic Balancer')
                            }
                        logger.info(f"✅ Loaded profile from fallback auth for user {user_id}")
                except Exception as e:
                    logger.warning(f"Fallback auth verification failed: {e}")
        
        logger.info(f"🤖 Chat query from {user_id} (conv: {conversation_id}): {user_message[:50]}...")
        
        # Get conversation manager
        cm = get_conversation_manager()
        
        # If no conversation_id, create new conversation
        if not conversation_id and user_id != "anonymous":
            conversation = cm.create_conversation(user_id, user_message)
            conversation_id = conversation['conversation_id']
            logger.info(f"✅ Created new conversation: {conversation['title']}")
        
        # Load conversation history to maintain context
        conversation_history = []
        if conversation_id and user_id != "anonymous":
            try:
                conversation = cm.get_conversation(user_id, conversation_id)
                if conversation and conversation.get('messages'):
                    # Build conversation history for chatbot context
                    conversation_history = conversation['messages']
                    logger.info(f"✅ Loaded {len(conversation_history)} messages from conversation history")
            except Exception as e:
                logger.warning(f"Could not load conversation history: {e}")
        
        # Fetch user's portfolio from Supabase if authenticated
        portfolio_data = None
        if USE_PORTFOLIO_CONTEXT and user_id != "anonymous":
            try:
                context_payload = build_portfolio_context(user_id, currency)
                if context_payload and context_payload.get('portfolio_data'):
                    portfolio_data = context_payload['portfolio_data']
                    logger.info(f"✅ Loaded portfolio context ({context_payload.get('source')}) for {user_id}")
            except Exception as e:
                logger.warning(f"Portfolio context builder failed: {e}")

        if portfolio_data is None and user_id != "anonymous":
            supabase_available = supabase is not None and supabase_admin is not None
            if supabase_available:
                try:
                    # Get portfolio
                    portfolio_response = supabase.table("portfolios")\
                        .select("id")\
                        .eq("user_id", user_id)\
                        .execute()
                    
                    if portfolio_response.data:
                        portfolio = portfolio_response.data[0]
                        portfolio_id = portfolio['id']
                        cash_balance = float(portfolio.get('cash_balance', 0) or 0)
                        
                        # Get positions
                        positions_response = supabase.table("positions")\
                            .select("*")\
                            .eq("portfolio_id", portfolio_id)\
                            .execute()
                        
                        positions = positions_response.data or []
                        
                        # Calculate total portfolio value (cash + current position values)
                        total_position_value = 0.0
                        allocation = []
                        largest_position = None
                        
                        for pos in positions:
                            qty = float(pos.get('total_quantity', 0) or 0)
                            price = pos.get('current_price')
                            if price is None:
                                price = pos.get('average_cost', 0)
                            current_price = float(price or 0)
                            value = qty * current_price
                            total_position_value += value
                            symbol = pos.get('symbol', 'N/A')
                            meta = SYMBOL_METADATA.get(symbol.upper(), {})
                            allocation.append({
                                'symbol': symbol,
                                'value': value,
                                'total_quantity': qty,
                                'current_price': current_price,
                                'sector': meta.get('sector', 'General'),
                                'region': meta.get('region', 'Global'),
                                'beta': meta.get('beta', 1.0)
                            })
                        
                        total_portfolio_value = cash_balance + total_position_value
                        
                        # Add allocation percentages & detect concentration
                        for alloc in allocation:
                            percent = (alloc['value'] / total_portfolio_value * 100) if total_portfolio_value > 0 else 0
                            alloc['percent'] = percent
                            if not largest_position or percent > largest_position['percent']:
                                largest_position = {
                                    'symbol': alloc['symbol'],
                                    'percent': percent,
                                    'value': alloc['value']
                                }
                        
                        concentration_alert = None
                        if largest_position and largest_position['percent'] > 60:
                            target_percent = 60
                            excess_percent = largest_position['percent'] - target_percent
                            suggested_sell_amount = total_portfolio_value * (excess_percent / 100)
                            concentration_alert = {
                                'symbol': largest_position['symbol'],
                                'current_percent': largest_position['percent'],
                                'target_percent': target_percent,
                                'suggested_sell_amount': suggested_sell_amount
                            }
                        
                        # Compute risk metrics
                        equity_value = total_position_value
                        equity_percent = (equity_value / total_portfolio_value * 100) if total_portfolio_value > 0 else 0
                        cash_percent = (cash_balance / total_portfolio_value * 100) if total_portfolio_value > 0 else 0
                        portfolio_beta = 0.0
                        for alloc in allocation:
                            weight = (alloc['value'] / total_portfolio_value) if total_portfolio_value > 0 else 0
                            portfolio_beta += weight * alloc.get('beta', 1.0)
                        estimated_volatility = round(0.18 * portfolio_beta, 4) if total_portfolio_value > 0 else 0
                        
                        # Basic correlation/diversification notes
                        tech_weight = sum(a['percent'] for a in allocation if a.get('sector') == 'Technology')
                        kenya_weight = sum(a['percent'] for a in allocation if a.get('region') == 'Kenya')
                        correlation_warnings = []
                        diversification_tips = []
                        if tech_weight > 70:
                            correlation_warnings.append(f"Technology exposure is {tech_weight:.1f}% — positions likely highly correlated.")
                        if kenya_weight < 10:
                            diversification_tips.append("Add more Kenyan/local assets to reduce USD concentration risk.")
                        if cash_percent < 5:
                            diversification_tips.append("Cash/T-bills buffer is low; consider boosting liquidity for withdrawals.")
                        
                        risk_metrics = {
                            'portfolio_beta': round(portfolio_beta, 2),
                            'estimated_volatility': estimated_volatility,
                            'equity_percent': round(equity_percent, 1),
                            'cash_percent': round(cash_percent, 1),
                            'correlation_warnings': correlation_warnings,
                            'diversification_tips': diversification_tips
                        }
                        
                        # Fetch recent withdrawals (last 20)
                        withdrawals = []
                        withdrawal_stats = {
                            'total_count': 0,
                            'ytd_count': 0,
                            'ytd_amount': 0.0,
                            'last_90d_amount': 0.0,
                            'last_withdrawal': None,
                            'safe_annual': total_portfolio_value * 0.04,
                            'safe_monthly': total_portfolio_value * 0.04 / 12 if total_portfolio_value else 0,
                            'safe_quarterly': total_portfolio_value * 0.04 / 4 if total_portfolio_value else 0
                        }
                        
                        try:
                            withdrawals_response = supabase.table("withdrawals")\
                                .select("*")\
                                .eq("portfolio_id", portfolio_id)\
                                .order("withdrawal_date", desc=True)\
                                .limit(20)\
                                .execute()
                            
                            withdrawals = withdrawals_response.data or []
                            withdrawal_stats['total_count'] = len(withdrawals)
                            
                            today = datetime.now().date()
                            start_of_year = datetime(today.year, 1, 1).date()
                            days_elapsed = max((today - start_of_year).days + 1, 1)
                            months_elapsed = max(days_elapsed / 30.0, 1.0)
                            current_year = today.year
                            
                            for idx, w in enumerate(withdrawals):
                                amount = float(w.get('amount', 0) or 0)
                                date_str = w.get('withdrawal_date')
                                withdrawal_date = None
                                if date_str:
                                    try:
                                        withdrawal_date = datetime.fromisoformat(date_str).date()
                                    except ValueError:
                                        try:
                                            withdrawal_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                                        except ValueError:
                                            withdrawal_date = None
                                
                                if idx == 0:
                                    withdrawal_stats['last_withdrawal'] = date_str
                                
                                if withdrawal_date:
                                    if withdrawal_date.year == current_year:
                                        withdrawal_stats['ytd_amount'] += amount
                                        withdrawal_stats['ytd_count'] += 1
                                    if (today - withdrawal_date).days <= 90:
                                        withdrawal_stats['last_90d_amount'] += amount
                            
                            avg_monthly_withdrawal = (withdrawal_stats['ytd_amount'] / months_elapsed) if months_elapsed > 0 else 0
                            runway_months = (cash_balance / avg_monthly_withdrawal) if avg_monthly_withdrawal > 0 else None
                            annualized_withdraw_pct = ((withdrawal_stats['ytd_amount'] / total_portfolio_value) * (12 / months_elapsed)) if total_portfolio_value > 0 else 0
                            projected_value_one_year = max(total_portfolio_value - (avg_monthly_withdrawal * 12), 0)
                            
                            withdrawal_projection = {
                                'avg_monthly_withdrawal': avg_monthly_withdrawal,
                                'runway_months': runway_months,
                                'annualized_withdraw_pct': annualized_withdraw_pct * 100 if annualized_withdraw_pct else 0,
                                'projected_value_one_year': projected_value_one_year,
                                'current_value': total_portfolio_value,
                                'cash_balance': cash_balance
                            }
                        except Exception as e:
                            logger.warning(f"Could not load withdrawals for chatbot: {e}")
                            withdrawal_projection = {}
                        
                        # Build scenario options for chatbot guidance
                        scenario_options = []
                        if concentration_alert:
                            scenario_options.append({
                                'name': 'Option A - Trim Concentration',
                                'summary': f"Reduce {concentration_alert['symbol']} from {concentration_alert['current_percent']:.1f}% to {concentration_alert['target_percent']}%",
                                'actions': [
                                    f"Sell approximately ${concentration_alert['suggested_sell_amount']:,.0f} of {concentration_alert['symbol']}",
                                    "Reallocate 50% into diversified ETF, 50% into T-bills for stability",
                                    "Target beta ≈ 0.85 and lower volatility by ~25%"
                                ]
                            })
                        if kenya_weight < 15 or not allocation:
                            scenario_options.append({
                                'name': 'Option B - Add Local Diversifiers',
                                'summary': "Introduce Kenyan equities/bonds for currency hedging and income",
                                'actions': [
                                    "Allocate 10-20% into Safaricom, Equity, or Kenyan consumer staples",
                                    "Park 10% in 91-day T-bills (currently ~15-16%) to fund withdrawals",
                                    "Improves correlation mix and reduces USD exposure"
                                ]
                            })
                        scenario_options.append({
                            'name': 'Option C - Pause & Observe',
                            'summary': "Hold positions, set alerts, reassess in 1-3 months",
                            'actions': [
                                "Set alerts if any holding drops 5% to avoid emotional trades",
                                "Use this window to rebuild cash buffer for upcoming withdrawals",
                                "Maintains current allocations but keeps risk monitoring active"
                            ]
                        })
                        
                        portfolio_data = {
                            'positions_count': len(positions),
                            'positions': positions,
                            'cash_balance': cash_balance,
                            'portfolio_value': total_portfolio_value,
                            'withdrawals': withdrawals,
                            'withdrawal_stats': withdrawal_stats,
                            'withdrawal_projection': withdrawal_projection,
                            'allocation': allocation,
                            'concentration_alert': concentration_alert,
                            'risk_metrics': risk_metrics,
                            'scenario_options': scenario_options
                        }
                        portfolio_data = convert_portfolio_data(portfolio_data, currency)
                        
                        logger.info(f"✅ Portfolio context: {len(positions)} positions, ${withdrawal_stats['ytd_amount']:.2f} YTD withdrawals")
                except Exception as e:
                    logger.warning(f"Could not load Supabase portfolio for chatbot: {e}")
            
            if portfolio_data is None:
                try:
                    portfolio_data = build_local_portfolio_context(user_id, currency)
                    if portfolio_data:
                        logger.info(f"✅ Loaded file-based portfolio for {user_id}: {portfolio_data['positions_count']} holdings (fallback)")
                except Exception as e:
                    logger.warning(f"Could not load file-based portfolio for chatbot: {e}")

        
        # Get conversational chatbot and process message
        # Pre-populate chatbot memory with conversation history
        chatbot = get_conversational_chatbot()
        
        # Load history into chatbot's memory for context
        context_id = conversation_id or user_id
        if conversation_history:
            # Convert conversation messages to chatbot history format
            chatbot.conversations[context_id] = [
                {'role': msg['role'], 'content': msg['content']}
                for msg in conversation_history
            ]
            logger.info(f"✅ Pre-populated chatbot memory with {len(conversation_history)} messages")
        
        response = chatbot.chat(user_message, user_profile, context_id, portfolio_data)
        
        # Save message to conversation if we have a conversation_id
        if conversation_id and user_id != "anonymous":
            cm.add_message(user_id, conversation_id, "user", user_message)
            cm.add_message(user_id, conversation_id, "assistant", response.get('response', ''))
        
        # Add conversation_id to response
        response['conversation_id'] = conversation_id
        response['currency'] = currency
        response['currency_symbol'] = get_currency_symbol(currency)
        
        return response
        
    except Exception as e:
        logger.error(f"❌ Chatbot error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "response": f"I encountered an error while analyzing. Please try again. Error: {str(e)}",
            "type": "error"
        }

# ========== PORTFOLIO MANAGEMENT ENDPOINTS ==========

@app.post("/api/portfolio/deposit")
async def deposit_cash(data: Dict[str, Any], access_token: Optional[str] = Cookie(default=None)):
    """Deposit cash into portfolio account"""
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = await auth_service.get_current_user(access_token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    try:
        portfolio = ensure_portfolio(user.id)
        amount = float(data['amount'])
        
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")
        
        # Update cash balance
        new_balance = float(portfolio.get('cash_balance', 0)) + amount
        
        supabase.table("portfolios")\
            .update({"cash_balance": new_balance})\
            .eq("id", portfolio['id'])\
            .execute()
        
        logger.info(f"✅ Deposited ${amount} for user {user.id}. New balance: ${new_balance}")
        
        return {
            'success': True,
            'amount': amount,
            'new_balance': new_balance,
            'message': f"Deposited ${amount:.2f}. Cash balance: ${new_balance:.2f}"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error depositing cash: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/portfolio/summary")
async def get_portfolio_summary(access_token: Optional[str] = Cookie(default=None), currency: str = 'USD'):
    """Get complete portfolio summary (Supabase)"""
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = await auth_service.get_current_user(access_token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid session")

    currency = normalize_currency(currency)
    
    try:
        portfolio = ensure_portfolio(user.id)
        cash_balance = float(portfolio.get('cash_balance', 0))
        
        # Get realized P/L from trade history (all-time)
        realized_pl_total = 0
        try:
            trade_history_response = supabase.table("trade_history")\
                .select("realized_pl")\
                .eq("portfolio_id", portfolio['id'])\
                .eq("trade_type", "sell")\
                .execute()
            
            if trade_history_response.data:
                realized_pl_total = sum(float(t.get('realized_pl', 0)) for t in trade_history_response.data)
                logger.info(f"📊 Total realized P/L: ${realized_pl_total:.2f}")
        except Exception as e:
            logger.warning(f"Could not fetch trade history (table may not exist): {e}")
        
        # Get all positions
        positions_response = supabase.table("positions")\
            .select("*")\
            .eq("portfolio_id", portfolio['id'])\
            .execute()
        
        positions = positions_response.data or []
        
        # Calculate totals from positions with null handling
        total_invested = 0
        for p in positions:
            val = p.get('total_invested')
            if val is not None:
                total_invested += float(val)
        
        # Get withdrawals from Supabase for YTD calculation
        current_year = datetime.now().year
        withdrawals_response = supabase.table("withdrawals")\
            .select("amount, withdrawal_date")\
            .eq("portfolio_id", portfolio['id'])\
            .gte("withdrawal_date", f"{current_year}-01-01")\
            .execute()
        
        withdrawals = withdrawals_response.data or []
        ytd_withdrawn = sum(float(w.get('amount', 0)) for w in withdrawals)
        
        # Get investor profile for health score
        profile_response = supabase.table("investor_profiles")\
            .select("risk_score")\
            .eq("user_id", user.id)\
            .execute()
        
        user_risk = 0.5
        if profile_response.data:
            user_risk = float(profile_response.data[0].get('risk_score', 0.5))
        
        # Calculate portfolio health based on actual metrics
        health_score = 0
        health_insights = []
        
        # Factor 1: Diversification (max 30 points)
        unique_symbols = len(set(p.get('symbol') for p in positions))
        if unique_symbols >= 10:
            health_score += 30
            health_insights.append("✅ Excellent diversification with 10+ holdings")
        elif unique_symbols >= 5:
            health_score += 20
            health_insights.append("👍 Good diversification with 5+ holdings")
        elif unique_symbols >= 3:
            health_score += 10
            health_insights.append("⚠️ Moderate diversification - consider adding more positions")
        elif unique_symbols > 0:
            health_score += 5
            health_insights.append("⚠️ Low diversification - highly concentrated portfolio")
        else:
            health_insights.append("⚠️ No positions yet - add investments to start building wealth")
        
        # Factor 2: Position sizing (max 25 points)
        if positions:
            # Check if any single position is > 30% of portfolio
            max_position_pct = max((float(p.get('total_invested', 0)) / total_invested * 100) if total_invested > 0 else 0 for p in positions)
            if max_position_pct < 20:
                health_score += 25
                health_insights.append("✅ Well-balanced position sizes")
            elif max_position_pct < 30:
                health_score += 15
                health_insights.append("👍 Acceptable position sizing")
            else:
                health_score += 5
                health_insights.append(f"⚠️ One position is {max_position_pct:.1f}% of portfolio - consider rebalancing")
        
        # Factor 3: Withdrawal sustainability (max 25 points)
        safe_annual = total_invested * 0.04
        if ytd_withdrawn == 0:
            health_score += 25
            health_insights.append("✅ No withdrawals yet - portfolio is growing")
        elif ytd_withdrawn <= safe_annual * 0.5:
            health_score += 25
            health_insights.append("✅ Withdrawals well within safe limits")
        elif ytd_withdrawn <= safe_annual:
            health_score += 15
            health_insights.append("👍 Withdrawals within 4% rule")
        elif ytd_withdrawn <= safe_annual * 1.5:
            health_score += 5
            health_insights.append("⚠️ Withdrawals exceeding recommended 4% - may impact sustainability")
        else:
            health_insights.append("🚨 Withdrawals significantly over safe limit - portfolio at risk")
        
        # Factor 4: Risk alignment (max 20 points)
        if user_risk:
            health_score += 20
            if user_risk < 0.3:
                health_insights.append("💡 Your conservative profile suggests focus on bonds and stable assets")
            elif user_risk < 0.6:
                health_insights.append("💡 Your balanced profile is well-suited for diversified equity/bond mix")
            else:
                health_insights.append("💡 Your aggressive profile supports growth-focused equity investments")
        
        # Determine health rating
        if health_score >= 80:
            health_rating = "Excellent"
        elif health_score >= 60:
            health_rating = "Good"
        elif health_score >= 40:
            health_rating = "Fair"
        else:
            health_rating = "Needs Improvement"
        
        # Format positions for frontend (add missing fields with proper null handling)
        formatted_holdings = []
        for pos in positions:
            # Safe get with None handling
            def safe_float(value, default=0):
                if value is None:
                    return default
                try:
                    return float(value)
                except (TypeError, ValueError):
                    return default
            
            total_qty = safe_float(pos.get('total_quantity'))
            avg_cost = safe_float(pos.get('average_cost'))
            total_inv = safe_float(pos.get('total_invested'))
            
            # Calculate current value and P/L
            current_price = safe_float(pos.get('current_price'))
            
            # If no current price set, use average cost as placeholder
            if current_price == 0:
                current_price = avg_cost
            
            current_value = total_qty * current_price
            unrealized_pl = current_value - total_inv
            unrealized_pl_pct = (unrealized_pl / total_inv * 100) if total_inv > 0 else 0
            
            formatted_holdings.append({
                'symbol': pos.get('symbol', ''),
                'total_quantity': total_qty,
                'average_cost': avg_cost,
                'current_price': current_price,
                'current_value': current_value,  # ← FIX: Now calculated!
                'total_pl': unrealized_pl,  # ← FIX: Now calculated!
                'total_pl_percent': unrealized_pl_pct,  # ← FIX: Now calculated!
                'entry_count': len(pos.get('entries', [])),
                'entries': pos.get('entries', []),
                'price_source': 'manual' if pos.get('manual_price') else 'api'
            })
        
        # Calculate unrealized P/L (current positions - sum from all formatted holdings)
        unrealized_pl = sum(h['total_pl'] for h in formatted_holdings)
        
        # Total P/L = Realized (from sales) + Unrealized (current positions)
        total_pl = realized_pl_total + unrealized_pl
        
        logger.info(f"💰 Portfolio P/L - Realized: ${realized_pl_total:.2f}, Unrealized: ${unrealized_pl:.2f}, Total: ${total_pl:.2f}")
        
        # Detect portfolio events
        event_detector = get_event_detector()
        user_profile_dict = {'risk_score': user_risk}
        portfolio_data_dict = {'total_value': cash_balance + total_invested}
        
        # Convert formatted_holdings to format expected by event detector
        positions_for_detector = []
        for holding in formatted_holdings:
            positions_for_detector.append({
                'symbol': holding['symbol'],
                'total_quantity': holding['total_quantity'],
                'average_cost': holding['average_cost'],
                'current_price': holding['current_price'],
                'entries': holding['entries']
            })
        
        detected_events = event_detector.detect_all_events(
            portfolio_data_dict,
            user_profile_dict,
            positions_for_detector
        )
        
        logger.info(f"🔔 Detected {len(detected_events)} portfolio events")
        
        # Format response to match frontend expectations
        total_portfolio_value = cash_balance + total_invested
        
        summary = {
            'overview': {
                'cash_balance': cash_balance,
                'total_value': total_portfolio_value,
                'total_invested': total_invested,
                'total_pl': total_pl,
                'total_pl_percent': (total_pl / total_invested * 100) if total_invested > 0 else 0,
                'realized_pl': realized_pl_total,  # From completed sales
                'unrealized_pl': unrealized_pl,    # From current positions
                'position_count': len(positions)
            },
            'health': {
                'total_score': health_score,
                'health_rating': health_rating,
                'insights': health_insights
            },
            'events': detected_events,  # NEW: Portfolio events/alerts
            'top_holdings': formatted_holdings[:5],
            'withdrawal': {
                'safe_monthly': total_invested * 0.04 / 12 if total_invested > 0 else 0,
                'safe_annual': total_invested * 0.04 if total_invested > 0 else 0,
                'ytd_withdrawn': ytd_withdrawn,
                'remaining_this_year': max(0, (total_invested * 0.04) - ytd_withdrawn) if total_invested > 0 else 0
            },
            'positions': formatted_holdings
        }
        summary = convert_portfolio_summary(summary, currency)
        return summary
    except Exception as e:
        logger.error(f"Error getting portfolio summary: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/portfolio/position/add")
async def add_position(data: Dict[str, Any], access_token: Optional[str] = Cookie(default=None)):
    """Add a new position to portfolio (Supabase)"""
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = await auth_service.get_current_user(access_token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    try:
        portfolio = ensure_portfolio(user.id)
        portfolio_id = portfolio['id']
        cash_balance = float(portfolio.get('cash_balance', 0))
        
        symbol = data['symbol'].upper()
        quantity = float(data['quantity'])
        purchase_price = float(data['purchase_price'])
        purchase_date = data.get('purchase_date') or datetime.now().strftime('%Y-%m-%d')
        market = data.get('market', 'US')
        is_manual = market == 'NSE'  # NSE stocks require manual prices
        asset_type = (data.get('asset_type') or 'stock').lower()
        allowed_asset_types = {'stock', 'etf', 'crypto', 'bond', 'other'}
        if asset_type == 'fund':
            asset_type = 'other'
        if asset_type not in allowed_asset_types:
            asset_type = 'other'
        
        # Calculate cost
        total_cost = quantity * purchase_price
        
        # Check if enough cash
        if cash_balance < total_cost:
            raise ValueError(f"Insufficient cash. Need ${total_cost:.2f}, have ${cash_balance:.2f}. Please deposit cash first.")
        
        # Create entry for this purchase
        entry = {
            "quantity": quantity,
            "price": purchase_price,
            "date": purchase_date,
            "notes": data.get('notes', '')
        }
        
        # Check if position already exists for this symbol
        existing_position = supabase.table("positions")\
            .select("*")\
            .eq("portfolio_id", portfolio_id)\
            .eq("symbol", symbol)\
            .execute()
        
        if existing_position.data:
            # Position exists - add to entries array
            pos = existing_position.data[0]
            current_entries = pos.get('entries', [])
            current_entries.append(entry)
            
            # Recalculate aggregated values
            total_quantity = sum(e['quantity'] for e in current_entries)
            total_invested = sum(e['quantity'] * e['price'] for e in current_entries)
            average_cost = total_invested / total_quantity if total_quantity > 0 else 0
            
            # Update position
            supabase.table("positions")\
                .update({
                    "entries": current_entries,
                    "total_quantity": total_quantity,
                    "average_cost": average_cost,
                    "total_invested": total_invested
                })\
                .eq("id", pos['id'])\
                .execute()
            
            logger.info(f"✅ Added entry to existing position: {quantity} shares of {symbol} @ ${purchase_price}")
            
            # Deduct cash from portfolio (for existing position update too)
            new_cash_balance = cash_balance - total_cost
            supabase.table("portfolios")\
                .update({"cash_balance": new_cash_balance})\
                .eq("id", portfolio_id)\
                .execute()
            
            logger.info(f"💰 Deducted ${total_cost:.2f} from cash. New balance: ${new_cash_balance:.2f}")
            
            return {
                'success': True,
                'message': f"Added {quantity} more shares of {symbol} @ ${purchase_price}. Total: {total_quantity} shares @ ${average_cost:.2f} avg. Cash: ${new_cash_balance:.2f}",
                'cash_spent': total_cost,
                'new_cash_balance': new_cash_balance
            }
        else:
            # New position - create it
            market = data.get('market', 'US')
            is_manual = market == 'NSE'  # NSE stocks require manual prices
            
            supabase.table("positions")\
                .insert({
                    "portfolio_id": portfolio_id,
                    "symbol": symbol,
                    "asset_type": asset_type,
                    "entries": [entry],
                    "total_quantity": quantity,
                    "average_cost": purchase_price,
                    "total_invested": quantity * purchase_price,
                    "current_price": purchase_price,  # Set initial current price
                    "manual_price": is_manual  # Mark if it's NSE/manual
                })\
                .execute()
            
            logger.info(f"✅ Created new position: {quantity} shares of {symbol} @ ${purchase_price} ({market})")
        
        # Deduct cash from portfolio
        new_cash_balance = cash_balance - total_cost
        supabase.table("portfolios")\
            .update({"cash_balance": new_cash_balance})\
            .eq("id", portfolio_id)\
            .execute()
        
        logger.info(f"💰 Deducted ${total_cost:.2f} from cash. New balance: ${new_cash_balance:.2f}")
        
        return {
            'success': True,
            'message': f"Added {quantity} shares of {symbol} @ ${purchase_price}. Cash balance: ${new_cash_balance:.2f}",
            'cash_spent': total_cost,
            'new_cash_balance': new_cash_balance
        }
    except Exception as e:
        logger.error(f"Error adding position: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/portfolio/position/sell")
async def sell_position(data: Dict[str, Any], access_token: Optional[str] = Cookie(default=None)):
    """Sell position (full or partial) and convert to cash"""
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = await auth_service.get_current_user(access_token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    try:
        portfolio = ensure_portfolio(user.id)
        portfolio_id = portfolio['id']
        cash_balance = float(portfolio.get('cash_balance', 0))
        
        symbol = data['symbol'].upper()
        quantity_to_sell = float(data['quantity'])
        sell_price = float(data.get('sell_price', 0))  # Price per share
        
        # Get position
        position_response = supabase.table("positions")\
            .select("*")\
            .eq("portfolio_id", portfolio_id)\
            .eq("symbol", symbol)\
            .execute()
        
        if not position_response.data:
            raise ValueError(f"Position {symbol} not found")
        
        pos = position_response.data[0]
        current_quantity = float(pos.get('total_quantity', 0))
        
        if quantity_to_sell > current_quantity:
            raise ValueError(f"Cannot sell {quantity_to_sell} shares. You only have {current_quantity} shares of {symbol}")
        
        # Calculate sale proceeds
        sale_proceeds = quantity_to_sell * sell_price
        
        # Calculate profit/loss on this sale
        avg_cost = float(pos.get('average_cost', 0))
        cost_basis = quantity_to_sell * avg_cost
        realized_pl = sale_proceeds - cost_basis
        realized_pl_pct = (realized_pl / cost_basis * 100) if cost_basis > 0 else 0
        
        # Add cash to portfolio
        new_cash_balance = cash_balance + sale_proceeds
        supabase.table("portfolios")\
            .update({"cash_balance": new_cash_balance})\
            .eq("id", portfolio_id)\
            .execute()
        
        # Record trade in history (optional - requires trade_history table)
        try:
            trade_record = {
                'portfolio_id': portfolio_id,
                'symbol': symbol,
                'trade_type': 'sell',
                'quantity': quantity_to_sell,
                'price_per_share': sell_price,
                'total_amount': sale_proceeds,
                'cost_basis': cost_basis,
                'realized_pl': realized_pl,
                'realized_pl_percent': realized_pl_pct,
                'trade_date': datetime.now().strftime('%Y-%m-%d'),
                'notes': data.get('notes', '')
            }
            supabase.table("trade_history").insert(trade_record).execute()
            logger.info(f"📊 Recorded trade: Sold {quantity_to_sell} {symbol}, P/L: ${realized_pl:.2f}")
        except Exception as e:
            logger.warning(f"Could not record trade history: {e}")
        
        if quantity_to_sell >= current_quantity:
            # Selling entire position - delete it
            supabase.table("positions")\
                .delete()\
                .eq("id", pos['id'])\
                .execute()
            
            logger.info(f"✅ Sold entire position: {quantity_to_sell} shares of {symbol} @ ${sell_price}. P/L: ${realized_pl:.2f}")
            message = f"Sold all {quantity_to_sell} shares of {symbol} @ ${sell_price:.2f}"
        else:
            # Partial sell - update quantities (simplified: reduces proportionally)
            new_quantity = current_quantity - quantity_to_sell
            old_invested = float(pos.get('total_invested', 0))
            new_invested = old_invested * (new_quantity / current_quantity)
            
            supabase.table("positions")\
                .update({
                    "total_quantity": new_quantity,
                    "total_invested": new_invested
                })\
                .eq("id", pos['id'])\
                .execute()
            
            logger.info(f"✅ Sold {quantity_to_sell} shares of {symbol} @ ${sell_price}. P/L: ${realized_pl:.2f}")
            message = f"Sold {quantity_to_sell} shares of {symbol} @ ${sell_price:.2f}. Remaining: {new_quantity:.2f} shares"
        
        # Build detailed response
        pl_text = f"+${realized_pl:.2f}" if realized_pl >= 0 else f"${realized_pl:.2f}"
        pl_pct_text = f"+{realized_pl_pct:.2f}%" if realized_pl_pct >= 0 else f"{realized_pl_pct:.2f}%"
        
        return {
            'success': True,
            'message': message,
            'sale_proceeds': sale_proceeds,
            'new_cash_balance': new_cash_balance,
            'realized_profit_loss': realized_pl,
            'realized_pl_percent': realized_pl_pct,
            'cost_basis': cost_basis
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error selling position: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/portfolio/price/update")
async def update_manual_price(data: Dict[str, Any], access_token: Optional[str] = Cookie(default=None)):
    """Update manual price for stocks (for Kenyan/NSE stocks without API)"""
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = await auth_service.get_current_user(access_token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    try:
        portfolio = ensure_portfolio(user.id)
        portfolio_id = portfolio['id']
        symbol = data['symbol'].upper()
        price = float(data['price'])
        is_manual = data.get('is_manual', True)  # Frontend can specify if it's manual or API
        
        # Update position's current price
        supabase.table("positions")\
            .update({
                "current_price": price,
                "manual_price": is_manual,
                "price_updated_at": datetime.now().isoformat()
            })\
            .eq("portfolio_id", portfolio_id)\
            .eq("symbol", symbol)\
            .execute()
        
        source_label = "manual" if is_manual else "API"
        logger.info(f"✅ Updated price for {symbol}: ${price} ({source_label})")
        
        return {
            'success': True,
            'message': f"Updated {symbol} price to ${price:.2f} (manual)"
        }
    except Exception as e:
        logger.error(f"Error updating price: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/portfolio/withdrawal/add")
async def add_withdrawal(data: Dict[str, Any], access_token: Optional[str] = Cookie(default=None)):
    """Record a withdrawal (Supabase)"""
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = await auth_service.get_current_user(access_token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    try:
        portfolio = ensure_portfolio(user.id)
        portfolio_id = portfolio['id']
        cash_balance = float(portfolio.get('cash_balance', 0))
        
        amount = float(data['amount'])
        
        # Check if enough cash to withdraw
        if cash_balance < amount:
            raise ValueError(f"Insufficient cash. You have ${cash_balance:.2f} available, but trying to withdraw ${amount:.2f}. Please sell positions first to get cash.")
        
        withdrawal_date = data.get('withdrawal_date') or datetime.now().strftime('%Y-%m-%d')
        
        # Deduct cash from portfolio
        new_cash_balance = cash_balance - amount
        supabase.table("portfolios")\
            .update({"cash_balance": new_cash_balance})\
            .eq("id", portfolio_id)\
            .execute()
        
        # Save withdrawal to Supabase
        withdrawal_data = {
            'portfolio_id': portfolio_id,
            'amount': amount,
            'withdrawal_date': withdrawal_date,
            'withdrawal_type': data.get('withdrawal_type', 'general'),
            'notes': data.get('notes', '')
        }
        
        supabase.table("withdrawals").insert(withdrawal_data).execute()
        
        logger.info(f"✅ Recorded withdrawal: ${amount} for user {user.id}. New cash balance: ${new_cash_balance}")
        
        return {
            'success': True,
            'message': f"Withdrew ${amount:.2f}. Cash balance: ${new_cash_balance:.2f}",
            'amount': amount,
            'new_cash_balance': new_cash_balance
        }
    except Exception as e:
        logger.error(f"Error adding withdrawal: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/portfolio/transactions/recent")
async def get_recent_transactions(access_token: Optional[str] = Cookie(default=None), limit: int = 20, currency: str = 'USD'):
    """Get recent transactions (buys, sells, deposits, withdrawals)"""
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = await auth_service.get_current_user(access_token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid session")

    currency = normalize_currency(currency)
    
    try:
        portfolio = ensure_portfolio(user.id)
        portfolio_id = portfolio['id']
        
        # Try to get trade history
        try:
            trade_history = supabase.table("trade_history")\
                .select("*")\
                .eq("portfolio_id", portfolio_id)\
                .order("created_at", desc=True)\
                .limit(limit)\
                .execute()
            
            transactions = trade_history.data or []
        except Exception as e:
            logger.warning(f"Trade history table not available: {e}")
            transactions = []
        
        # Format transactions for display
        formatted = []
        for txn in transactions:
            formatted.append({
                'date': txn.get('trade_date'),
                'type': txn.get('trade_type'),
                'symbol': txn.get('symbol'),
                'quantity': txn.get('quantity'),
                'price': txn.get('price_per_share'),
                'amount': txn.get('total_amount'),
                'realized_pl': txn.get('realized_pl'),
                'realized_pl_percent': txn.get('realized_pl_percent'),
                'notes': txn.get('notes'),
                'created_at': txn.get('created_at')
            })

        formatted = convert_transactions(formatted, currency)
        return {
            'transactions': formatted,
            'currency': currency,
            'currency_symbol': get_currency_symbol(currency)
        }
    except Exception as e:
        logger.error(f"Error getting transactions: {e}")
        return {'transactions': [], 'currency': currency, 'currency_symbol': get_currency_symbol(currency)}

@app.get("/api/portfolio/withdrawals/recent")
async def get_recent_withdrawals(access_token: Optional[str] = Cookie(default=None), limit: int = 10, currency: str = 'USD'):
    """Get recent withdrawal history"""
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = await auth_service.get_current_user(access_token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    currency = normalize_currency(currency)

    try:
        portfolio = ensure_portfolio(user.id)
        portfolio_id = portfolio['id']
        
        # Fetch withdrawals from Supabase
        withdrawals_response = supabase.table("withdrawals")\
            .select("*")\
            .eq("portfolio_id", portfolio_id)\
            .order("withdrawal_date", desc=True)\
            .limit(limit)\
            .execute()
        
        withdrawals = withdrawals_response.data or []
        withdrawals = convert_withdrawals(withdrawals, currency)
        
        return {
            'withdrawals': withdrawals,
            'currency': currency,
            'currency_symbol': get_currency_symbol(currency)
        }
    except Exception as e:
        logger.error(f"Error getting withdrawals: {e}")
        return {'withdrawals': [], 'currency': currency, 'currency_symbol': get_currency_symbol(currency)}

@app.get("/api/portfolio/withdrawal/plan")
async def get_withdrawal_plan(access_token: Optional[str] = Cookie(default=None), currency: str = 'USD'):
    """Get withdrawal plan and sustainability analysis (Supabase)"""
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = await auth_service.get_current_user(access_token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    currency = normalize_currency(currency)

    try:
        pm = get_portfolio_manager(user.id)
        planner = get_withdrawal_planner()
        
        portfolio_value = pm.calculate_total_portfolio()['total_value']
        safe_withdrawal = pm.calculate_safe_withdrawal()
        
        # Run Monte Carlo simulation
        monte_carlo = planner.run_monte_carlo(
            portfolio_value,
            safe_withdrawal['safe_annual'],
            years=30,
            simulations=1000
        )
        
        # Stress test
        stress_test = planner.stress_test(
            portfolio_value,
            safe_withdrawal['safe_annual']
        )
        
        plan = {
            'safe_withdrawal': safe_withdrawal,
            'monte_carlo': monte_carlo,
            'stress_test': stress_test
        }
        plan = convert_withdrawal_plan(plan, currency)
        return plan
    except Exception as e:
        logger.error(f"Error calculating withdrawal plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/portfolio/scenario")
async def run_scenario(data: Dict[str, Any], access_token: Optional[str] = Cookie(default=None)):
    """Run what-if scenario (Supabase)"""
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = await auth_service.get_current_user(access_token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    try:
        pm = get_portfolio_manager(user.id)
        planner = get_withdrawal_planner()
        
        portfolio_value = pm.calculate_total_portfolio()['total_value']
        scenario_withdrawal = float(data.get('withdrawal_amount', portfolio_value * 0.04))
        years = int(data.get('years', 30))
        
        # Run projection
        projection = planner.run_sustainability_projection(
            portfolio_value,
            scenario_withdrawal,
            years=years
        )
        
        return {
            'scenario': {
                'withdrawal_amount': scenario_withdrawal,
                'years': years
            },
            'projection': projection
        }
    except Exception as e:
        logger.error(f"Error running scenario: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# NEW: Redesigned Survey risk prediction endpoint
@app.post("/predict/survey-risk-v2")
async def predict_survey_risk_v2(survey_data: RedesignedSurveyData):
    """Predict risk profile from REDESIGNED user-friendly survey"""
    try:
        # Convert redesigned survey to backend format
        survey_dict = survey_data.model_dump()
        backend_data = map_redesigned_survey_to_backend(survey_dict)
        
        # Use existing ML service with mapped data
        result = ml_service.predict_survey_risk(backend_data)
        logger.info(f"Redesigned survey prediction completed: {result['risk_category']}")
        
        # Add mapping info for transparency
        result['mapped_from'] = 'redesigned_survey_v2'
        result['backend_features'] = backend_data
        
        return result
    except Exception as e:
        logger.error(f"Error predicting survey risk (v2): {e}")
        raise HTTPException(status_code=500, detail=str(e))

# NEW: Generate personalized profile card with LLM
@app.post("/generate/profile-card")
async def generate_profile_card(survey_data: RedesignedSurveyData, use_kenyan_context: bool = True, access_token: Optional[str] = Cookie(default=None)):
    """Generate personalized investor profile card with LLM-powered insights"""
    try:
        # Convert survey to backend format
        survey_dict = survey_data.model_dump()
        backend_data = map_redesigned_survey_to_backend(survey_dict)
        
        # Get risk prediction
        risk_result = ml_service.predict_survey_risk(backend_data)
        risk_result['backend_features'] = backend_data
        
        # Generate profile card with LLM
        profile_card = profile_generator.generate_profile_card(
            risk_result, 
            survey_dict,
            use_kenyan_context
        )
        
        logger.info(f"Profile card generated: {profile_card['persona']}, Generated by: {profile_card['generated_by']}")
        
        # If user is authenticated, update their profile in Supabase
        profile_updated = False
        if access_token:
            try:
                user = await auth_service.get_current_user(access_token)
                if user:
                    await update_investor_profile(user.id, risk_result, survey_dict)
                    logger.info(f"✅ Updated investor profile for user {user.id}")
                    profile_updated = True
            except Exception as e:
                logger.warning(f"Could not update profile for authenticated user: {e}")
        
        # Add update status to response
        profile_card['profile_updated'] = profile_updated
        
        return profile_card
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Error generating profile card: {e}\n{error_details}")
        raise HTTPException(status_code=500, detail=f"Profile card generation failed: {str(e)}")

async def update_investor_profile(user_id: str, risk_result: Dict[str, Any], survey_dict: Dict[str, Any]) -> None:
    """Update or create investor profile in Supabase"""
    try:
        # Prepare profile data
        profile_data = {
            "user_id": user_id,
            "risk_score": float(risk_result.get('risk_score', 0.5)),
            "risk_category": risk_result.get('risk_category', 'Comfortable'),
            "persona": risk_result.get('persona', 'Strategic Balancer'),
            "risk_tolerance": float(risk_result.get('risk_score', 0.5)),
            "survey_responses": survey_dict,
            "updated_at": datetime.now().isoformat()
        }
        
        # Map risk_category to database-allowed values
        risk_category_mapping = {
            'Balanced': 'Comfortable',
            'balanced': 'moderate',
            'Low': 'Conservative',
            'low': 'conservative',
            'High': 'Enthusiastic',
            'high': 'aggressive',
            'Moderate': 'Comfortable',
            'moderate': 'moderate',
            'Conservative': 'Conservative',
            'conservative': 'conservative',
            'Enthusiastic': 'Enthusiastic',
            'enthusiastic': 'aggressive',
            'Aggressive': 'Enthusiastic',
            'aggressive': 'aggressive'
        }
        
        if profile_data.get("risk_category"):
            mapped = risk_category_mapping.get(profile_data["risk_category"])
            if mapped:
                profile_data["risk_category"] = mapped
            elif profile_data["risk_category"] not in ['Conservative', 'Comfortable', 'Enthusiastic', 'conservative', 'moderate', 'aggressive']:
                profile_data["risk_category"] = 'moderate'
        
        # Check if profile exists
        existing_profile = supabase.table("investor_profiles")\
            .select("id")\
            .eq("user_id", user_id)\
            .execute()
        
        if existing_profile.data:
            # Update existing profile
            supabase_admin.table("investor_profiles")\
                .update(profile_data)\
                .eq("user_id", user_id)\
                .execute()
            logger.info(f"✅ Updated existing investor profile for user {user_id}")
        else:
            # Create new profile
            supabase_admin.table("investor_profiles")\
                .insert(profile_data)\
                .execute()
            logger.info(f"✅ Created new investor profile for user {user_id}")
            
    except Exception as e:
        logger.error(f"Error updating investor profile: {e}")
        raise

# OLD: Original Survey risk prediction endpoint (kept for backwards compatibility)
@app.post("/predict/survey-risk")
async def predict_survey_risk(survey_data: SurveyData):
    """Predict risk profile from survey data"""
    try:
        survey_dict = survey_data.model_dump()
        result = ml_service.predict_survey_risk(survey_dict)
        logger.info(f"Survey risk prediction completed: {result['risk_category']}")
        return result
    except Exception as e:
        logger.error(f"Error predicting survey risk: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Transaction risk prediction endpoint
@app.post("/predict/transaction-risk")
async def predict_transaction_risk(transactions: List[TransactionData]):
    """Predict risk profile from transaction data"""
    try:
        transactions_dict = [t.model_dump() for t in transactions]
        result = ml_service.predict_transaction_risk(transactions_dict)
        logger.info(f"Transaction risk prediction completed: {result['risk_category']}")
        return result
    except Exception as e:
        logger.error(f"Error predicting transaction risk: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Meta risk prediction endpoint
@app.post("/predict/meta-risk")
async def predict_meta_risk(request: MetaRiskRequest):
    """Predict meta risk profile combining survey and transaction data"""
    try:
        survey_dict = request.survey_data.model_dump()
        transactions_dict = [t.model_dump() for t in request.transaction_data] if request.transaction_data else None
        
        result = ml_service.predict_meta_risk(
            survey_dict,
            transactions_dict,
            request.survey_weight
        )
        logger.info(f"Meta risk prediction completed: {result['risk_bucket']}")
        return result
    except Exception as e:
        logger.error(f"Error predicting meta risk: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting PortfoliAI ML Service on http://0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)




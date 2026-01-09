from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.database import supabase, supabase_admin
from portfolio_manager import get_portfolio_manager
from app.services.currency import convert_portfolio_data, normalize_currency, get_currency_symbol

logger = logging.getLogger(__name__)

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


def build_portfolio_context(user_id: str, target_currency: str = 'USD') -> Optional[Dict[str, Any]]:
    """
    Build a structured portfolio context for grounding chatbot answers.

    Returns dict with keys:
      - source: supabase | file
      - portfolio_data: {...}  # matches existing chatbot expectations
    """
    if not user_id or user_id == "anonymous":
        return None

    currency = normalize_currency(target_currency)

    context = _build_supabase_context(user_id)
    if context:
        context['portfolio_data'] = convert_portfolio_data(context['portfolio_data'], currency)
        context['currency'] = currency
        context['currency_symbol'] = get_currency_symbol(currency)
        return context

    fallback = _build_local_context(user_id)
    if fallback:
        fallback['portfolio_data'] = convert_portfolio_data(fallback['portfolio_data'], currency)
        fallback['currency'] = currency
        fallback['currency_symbol'] = get_currency_symbol(currency)
    return fallback


def _build_supabase_context(user_id: str) -> Optional[Dict[str, Any]]:
    if supabase is None or supabase_admin is None:
        return None

    try:
        portfolio_response = supabase.table("portfolios") \
            .select("*") \
            .eq("user_id", user_id) \
            .execute()

        if not portfolio_response.data:
            return None

        portfolio = portfolio_response.data[0]
        portfolio_id = portfolio['id']
        cash_balance = float(portfolio.get('cash_balance', 0) or 0)

        positions_response = supabase.table("positions") \
            .select("*") \
            .eq("portfolio_id", portfolio_id) \
            .execute()
        positions_raw = positions_response.data or []

        holdings, total_position_value = _summarize_positions(positions_raw)
        total_portfolio_value = cash_balance + total_position_value
        allocation = _build_allocation(holdings, total_portfolio_value, cash_balance)

        concentration_alert = _detect_concentration(allocation, total_portfolio_value)
        risk_metrics = _build_risk_metrics(allocation, total_portfolio_value, cash_balance)

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
        withdrawal_projection: Dict[str, Any] = {}

        try:
            withdrawals_response = supabase.table("withdrawals") \
                .select("*") \
                .eq("portfolio_id", portfolio_id) \
                .order("withdrawal_date", desc=True) \
                .limit(20) \
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
            logger.debug(f"Could not load withdrawals for {user_id}: {e}")

        scenario_options: List[Dict[str, Any]] = []
        if concentration_alert:
            scenario_options.append({
                'name': 'Trim Concentration',
                'summary': f"Reduce {concentration_alert['symbol']} weight to {concentration_alert['target_percent']}%",
                'actions': [
                    f"Sell approx ${concentration_alert['suggested_sell_amount']:,.0f} of {concentration_alert['symbol']}",
                    "Reallocate into diversified ETF + T-bills",
                    "Target beta ≈ 0.85"
                ]
            })

        portfolio_data = {
            'positions_count': len(holdings),
            'positions': holdings,
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

        return {
            'source': 'supabase',
            'portfolio_data': portfolio_data
        }
    except Exception as e:
        logger.warning(f"Supabase portfolio context failed for {user_id}: {e}")
        return None


def _build_local_context(user_id: str) -> Optional[Dict[str, Any]]:
    try:
        pm = get_portfolio_manager(user_id)
        portfolio = pm.portfolio or {}
        positions_raw = portfolio.get('positions', [])
        cash_balance = float(portfolio.get('cash_balance', 0) or 0)

        if not positions_raw and cash_balance <= 0:
            return None

        holdings, total_position_value = _summarize_positions(positions_raw)
        total_portfolio_value = cash_balance + total_position_value
        allocation = _build_allocation(holdings, total_portfolio_value, cash_balance)
        concentration_alert = _detect_concentration(allocation, total_portfolio_value)
        risk_metrics = _build_risk_metrics(allocation, total_portfolio_value, cash_balance)

        portfolio_data = {
            'positions_count': len(holdings),
            'positions': holdings,
            'cash_balance': cash_balance,
            'portfolio_value': total_portfolio_value,
            'withdrawals': portfolio.get('withdrawals', []),
            'withdrawal_stats': {
                'total_count': len(portfolio.get('withdrawals', [])),
                'ytd_count': 0,
                'ytd_amount': 0.0,
                'last_90d_amount': 0.0,
                'last_withdrawal': None,
                'safe_annual': total_portfolio_value * 0.04,
                'safe_monthly': total_portfolio_value * 0.04 / 12 if total_portfolio_value else 0,
                'safe_quarterly': total_portfolio_value * 0.04 / 4 if total_portfolio_value else 0
            },
            'withdrawal_projection': {
                'current_value': total_portfolio_value,
                'cash_balance': cash_balance
            },
            'allocation': allocation,
            'concentration_alert': concentration_alert,
            'risk_metrics': risk_metrics,
            'scenario_options': []
        }

        return {
            'source': 'file',
            'portfolio_data': portfolio_data
        }
    except Exception as e:
        logger.warning(f"Local portfolio context failed for {user_id}: {e}")
        return None


def _summarize_positions(positions_raw: List[Dict[str, Any]]):
    holdings = []
    total_position_value = 0.0

    for pos in positions_raw:
        symbol = (pos.get('symbol') or 'N/A').upper()
        qty = float(pos.get('total_quantity', pos.get('quantity', 0)) or 0)
        if qty <= 0:
            continue

        current_price = pos.get('current_price')
        if current_price is None:
            current_price = pos.get('average_cost', 0)
        current_price = float(current_price or 0)

        total_invested = float(pos.get('total_invested', qty * pos.get('average_cost', 0)) or 0)
        current_value = qty * current_price
        total_pl = current_value - total_invested
        total_pl_percent = (total_pl / total_invested * 100) if total_invested > 0 else 0

        holdings.append({
            'symbol': symbol,
            'total_quantity': qty,
            'average_cost': float(pos.get('average_cost', current_price) or 0),
            'current_price': current_price,
            'current_value': current_value,
            'total_invested': total_invested,
            'total_pl': total_pl,
            'total_pl_percent': total_pl_percent,
            'entries': pos.get('entries', []),
            'entry_count': len(pos.get('entries', [])),
            'price_source': 'manual' if pos.get('manual_price') else 'api'
        })

        total_position_value += current_value

    return holdings, total_position_value


def _build_allocation(holdings: List[Dict[str, Any]], total_portfolio_value: float, cash_balance: float):
    allocation = []
    denom = total_portfolio_value if total_portfolio_value > 0 else 1

    for holding in holdings:
        meta = SYMBOL_METADATA.get(holding['symbol'].upper(), {})
        allocation.append({
            'symbol': holding['symbol'],
            'value': holding['current_value'],
            'percent': (holding['current_value'] / denom * 100),
            'sector': meta.get('sector', 'General'),
            'region': meta.get('region', 'Global'),
            'beta': meta.get('beta', 1.0)
        })

    if cash_balance > 0:
        allocation.append({
            'symbol': 'CASH',
            'value': cash_balance,
            'percent': (cash_balance / denom * 100),
            'sector': 'Liquidity',
            'region': 'Global',
            'beta': 0.0
        })

    return allocation


def _detect_concentration(allocation: List[Dict[str, Any]], total_value: float):
    if total_value <= 0 or not allocation:
        return None

    filtered = [a for a in allocation if a.get('symbol') != 'CASH']
    if not filtered:
        return None

    largest = max(filtered, key=lambda x: x.get('percent', 0), default=None)
    if not largest or largest.get('percent', 0) <= 60:
        return None

    target_percent = 60
    excess_percent = largest['percent'] - target_percent
    suggested_sell_amount = total_value * (excess_percent / 100)

    return {
        'symbol': largest['symbol'],
        'current_percent': largest['percent'],
        'target_percent': target_percent,
        'suggested_sell_amount': suggested_sell_amount
    }


def _build_risk_metrics(allocation: List[Dict[str, Any]], total_value: float, cash_balance: float):
    equity_value = sum(a.get('value', 0) for a in allocation)
    equity_percent = (equity_value / total_value * 100) if total_value > 0 else 0
    cash_percent = (cash_balance / total_value * 100) if total_value > 0 else 0
    portfolio_beta = 0.0
    for alloc in allocation:
        weight = (alloc['value'] / total_value) if total_value > 0 else 0
        portfolio_beta += weight * alloc.get('beta', 1.0)

    return {
        'portfolio_beta': round(portfolio_beta, 2),
        'estimated_volatility': round(0.18 * portfolio_beta, 4) if total_value > 0 else 0,
        'equity_percent': round(equity_percent, 1),
        'cash_percent': round(cash_percent, 1),
        'correlation_warnings': [],
        'diversification_tips': []
    }



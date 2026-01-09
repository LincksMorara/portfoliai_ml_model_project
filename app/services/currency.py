from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

SUPPORTED_CURRENCIES = {'USD', 'KES'}
CURRENCY_SYMBOLS = {'USD': '$', 'KES': 'KSh '}
USD_TO_KES = float(os.getenv('USD_TO_KES_RATE', '130'))


def normalize_currency(currency: Optional[str]) -> str:
    if not currency:
        return 'USD'
    currency = currency.upper()
    return currency if currency in SUPPORTED_CURRENCIES else 'USD'


def get_currency_symbol(currency: str) -> str:
    return CURRENCY_SYMBOLS.get(normalize_currency(currency), '$')


def convert_amount(amount: Optional[float], currency: str) -> Optional[float]:
    if amount is None:
        return None
    currency = normalize_currency(currency)
    value = float(amount)
    if currency == 'USD':
        return round(value, 2)
    rate = USD_TO_KES if currency == 'KES' else 1.0
    return round(value * rate, 2)


def convert_portfolio_summary(summary: Dict[str, Any], currency: str) -> Dict[str, Any]:
    currency = normalize_currency(currency)
    summary['currency'] = currency
    summary['currency_symbol'] = get_currency_symbol(currency)

    if currency == 'USD':
        return summary

    def conv(value):
        return convert_amount(value, currency)

    overview = summary.get('overview', {})
    for key in [
        'cash_balance', 'total_value', 'total_invested',
        'total_pl', 'realized_pl', 'unrealized_pl'
    ]:
        if key in overview:
            overview[key] = conv(overview[key])

    withdrawal = summary.get('withdrawal', {})
    for key in ['safe_monthly', 'safe_annual', 'ytd_withdrawn', 'remaining_this_year']:
        if key in withdrawal:
            withdrawal[key] = conv(withdrawal[key])

    positions = summary.get('positions', [])
    convert_positions(positions, currency)

    top_holdings = summary.get('top_holdings', [])
    convert_positions(top_holdings, currency)

    withdrawal_projection = summary.get('withdrawal_projection', {})
    for key in ['avg_monthly_withdrawal', 'runway_months', 'annualized_withdraw_pct']:
        if key not in withdrawal_projection:
            continue
        if key == 'runway_months' or key == 'annualized_withdraw_pct':
            continue
        withdrawal_projection[key] = conv(withdrawal_projection[key])

    return summary


def convert_positions(positions: List[Dict[str, Any]], currency: str) -> None:
    if normalize_currency(currency) == 'USD':
        return

    def conv(value):
        return convert_amount(value, currency)

    for holding in positions:
        for key in ['average_cost', 'current_price', 'current_value', 'total_invested', 'total_pl']:
            if key in holding:
                holding[key] = conv(holding[key])


def convert_portfolio_data(portfolio_data: Dict[str, Any], currency: str) -> Dict[str, Any]:
    currency = normalize_currency(currency)
    portfolio_data['currency'] = currency
    portfolio_data['currency_symbol'] = get_currency_symbol(currency)

    if currency == 'USD':
        return portfolio_data

    def conv(value):
        return convert_amount(value, currency)

    for key in ['cash_balance', 'portfolio_value']:
        if key in portfolio_data:
            portfolio_data[key] = conv(portfolio_data[key])

    if 'withdrawal_stats' in portfolio_data:
        stats = portfolio_data['withdrawal_stats']
        for stat_key in ['ytd_amount', 'last_90d_amount', 'safe_annual', 'safe_monthly', 'safe_quarterly']:
            if stat_key in stats:
                stats[stat_key] = conv(stats[stat_key])

    if 'withdrawal_projection' in portfolio_data:
        proj = portfolio_data['withdrawal_projection']
        for proj_key in ['avg_monthly_withdrawal', 'projected_value_one_year', 'current_value', 'cash_balance']:
            if proj_key in proj:
                proj[proj_key] = conv(proj[proj_key])

    if 'allocation' in portfolio_data:
        for alloc in portfolio_data['allocation']:
            if 'value' in alloc:
                alloc['value'] = conv(alloc['value'])

    if 'concentration_alert' in portfolio_data and portfolio_data['concentration_alert']:
        alert = portfolio_data['concentration_alert']
        if 'suggested_sell_amount' in alert:
            alert['suggested_sell_amount'] = conv(alert['suggested_sell_amount'])

    convert_positions(portfolio_data.get('positions', []), currency)

    return portfolio_data


def convert_transactions(transactions: List[Dict[str, Any]], currency: str) -> List[Dict[str, Any]]:
    currency = normalize_currency(currency)
    if currency == 'USD':
        return transactions

    def conv(value):
        return convert_amount(value, currency)

    for txn in transactions:
        for key in ['amount', 'price', 'total_amount', 'realized_pl']:
            if key in txn:
                txn[key] = conv(txn[key])
    return transactions


def convert_withdrawals(withdrawals: List[Dict[str, Any]], currency: str) -> List[Dict[str, Any]]:
    currency = normalize_currency(currency)
    if currency == 'USD':
        return withdrawals

    def conv(value):
        return convert_amount(value, currency)

    for w in withdrawals:
        if 'amount' in w:
            w['amount'] = conv(w['amount'])
    return withdrawals


def convert_withdrawal_plan(plan: Dict[str, Any], currency: str) -> Dict[str, Any]:
    currency = normalize_currency(currency)
    plan['currency'] = currency
    plan['currency_symbol'] = get_currency_symbol(currency)

    if currency == 'USD':
        return plan

    def conv(value):
        return convert_amount(value, currency)

    safe = plan.get('safe_withdrawal', {})
    for key in ['safe_annual', 'safe_monthly', 'safe_weekly']:
        if key in safe:
            safe[key] = conv(safe[key])

    if 'scenario' in plan and 'withdrawal_amount' in plan['scenario']:
        plan['scenario']['withdrawal_amount'] = conv(plan['scenario']['withdrawal_amount'])

    if 'projection' in plan:
        projection = plan['projection']
        for proj_key in ['starting_value', 'ending_value']:
            if proj_key in projection:
                projection[proj_key] = conv(projection[proj_key])

    return plan


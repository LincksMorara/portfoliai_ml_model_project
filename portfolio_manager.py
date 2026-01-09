"""
Portfolio Management System
Tracks positions, cost basis, P/L, withdrawals, and provides intelligent analytics
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import json
import os

from fmp_integration import get_fmp_client

logger = logging.getLogger(__name__)

@dataclass
class Position:
    """Individual stock position with cost basis"""
    symbol: str
    quantity: float
    purchase_price: float
    purchase_date: str
    asset_type: str = "stock"  # stock, fund, bond
    market: str = "US"  # US, NSE, other
    notes: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)

@dataclass
class Withdrawal:
    """Withdrawal record"""
    amount: float
    date: str
    withdrawal_type: str = "regular"  # regular, emergency, dividend
    notes: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)

class PortfolioManager:
    """
    Manages user's investment portfolio with multi-entry tracking,
    P/L calculation, health scoring, and withdrawal planning
    """
    
    def __init__(self, user_id: str, db_path: str = "users_db.json"):
        self.user_id = user_id
        self.db_path = db_path
        self.fmp = get_fmp_client()
        
        # Load user's portfolio data
        self.portfolio = self._load_portfolio()
    
    def _load_portfolio(self) -> Dict[str, Any]:
        """Load user's portfolio from database"""
        try:
            if not os.path.exists(self.db_path):
                return self._empty_portfolio()
            
            with open(self.db_path, 'r') as f:
                db = json.load(f)
            
            # Database is a flat dict with emails as keys, not an array
            # Find user by user_id
            for email, user_data in db.items():
                if isinstance(user_data, dict) and user_data.get('user_id') == self.user_id:
                    portfolio = user_data.get('portfolio', self._empty_portfolio())
                    logger.info(f"✅ Loaded portfolio for {self.user_id}: {len(portfolio.get('positions', []))} positions")
                    return portfolio
            
            # User not found - return empty portfolio
            logger.warning(f"User {self.user_id} not found in database")
            return self._empty_portfolio()
            
        except Exception as e:
            logger.error(f"Error loading portfolio: {e}")
            import traceback
            traceback.print_exc()
            return self._empty_portfolio()
    
    def _empty_portfolio(self) -> Dict[str, Any]:
        """Create empty portfolio structure"""
        return {
            'positions': [],
            'withdrawals': [],
            'cash_balance': 0.0,
            'manual_prices': {},  # For NSE stocks: {symbol: {price, last_updated}}
            'settings': {
                'base_currency': 'USD',
                'withdrawal_rate': 0.04,  # 4% rule
                'rebalance_threshold': 0.10  # 10% drift triggers alert
            },
            'created_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat()
        }
    
    def _save_portfolio(self):
        """Save portfolio back to database"""
        try:
            # Load full database
            if os.path.exists(self.db_path):
                with open(self.db_path, 'r') as f:
                    db = json.load(f)
            else:
                db = {}
            
            # Database is a flat dict with emails as keys
            # Find and update user's portfolio
            user_found = False
            for email, user_data in db.items():
                if isinstance(user_data, dict) and user_data.get('user_id') == self.user_id:
                    user_data['portfolio'] = self.portfolio
                    user_data['portfolio']['last_updated'] = datetime.now().isoformat()
                    user_found = True
                    logger.info(f"✅ Found and updated portfolio for {self.user_id} ({email})")
                    break
            
            if not user_found:
                logger.warning(f"User {self.user_id} not found in database - cannot save portfolio")
                return False
            
            # Save
            with open(self.db_path, 'w') as f:
                json.dump(db, f, indent=2)
            
            logger.info(f"✅ Saved portfolio for {self.user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving portfolio: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    # ========== POSITION MANAGEMENT ==========
    
    def add_position(self, 
                    symbol: str,
                    quantity: float,
                    purchase_price: float,
                    purchase_date: str = None,
                    asset_type: str = "stock",
                    market: str = "US",
                    notes: str = "") -> Dict[str, Any]:
        """
        Add a position to portfolio (supports multi-entry cost basis)
        """
        if purchase_date is None:
            purchase_date = datetime.now().strftime('%Y-%m-%d')
        
        position = Position(
            symbol=symbol.upper(),
            quantity=quantity,
            purchase_price=purchase_price,
            purchase_date=purchase_date,
            asset_type=asset_type,
            market=market,
            notes=notes
        )
        
        self.portfolio['positions'].append(position.to_dict())
        self._save_portfolio()
        
        logger.info(f"✅ Added position: {quantity} shares of {symbol} @ ${purchase_price}")
        
        return {
            'success': True,
            'position': position.to_dict(),
            'message': f"Added {quantity} shares of {symbol} @ ${purchase_price}"
        }
    
    def get_positions_by_symbol(self, symbol: str) -> List[Dict]:
        """Get all positions for a given symbol (for multi-entry tracking)"""
        symbol = symbol.upper()
        return [p for p in self.portfolio['positions'] if p['symbol'] == symbol]
    
    def get_all_positions(self) -> List[Dict]:
        """Get all positions"""
        return self.portfolio['positions']
    
    def get_unique_symbols(self) -> List[str]:
        """Get list of unique symbols in portfolio"""
        return list(set([p['symbol'] for p in self.portfolio['positions']]))
    
    # ========== P/L CALCULATION ==========
    
    def calculate_position_pl(self, position: Dict, current_price: float) -> Dict[str, Any]:
        """Calculate P/L for a single position entry"""
        cost_basis = position['quantity'] * position['purchase_price']
        current_value = position['quantity'] * current_price
        pl_amount = current_value - cost_basis
        pl_percent = (pl_amount / cost_basis * 100) if cost_basis > 0 else 0
        
        return {
            'symbol': position['symbol'],
            'quantity': position['quantity'],
            'purchase_price': position['purchase_price'],
            'purchase_date': position['purchase_date'],
            'current_price': current_price,
            'cost_basis': cost_basis,
            'current_value': current_value,
            'pl_amount': pl_amount,
            'pl_percent': pl_percent,
            'is_gain': pl_amount >= 0
        }
    
    def calculate_symbol_pl(self, symbol: str) -> Dict[str, Any]:
        """Calculate aggregated P/L for all entries of a symbol"""
        positions = self.get_positions_by_symbol(symbol)
        
        if not positions:
            return {'error': f'No positions found for {symbol}'}
        
        # Get current price
        current_price = self.get_current_price(symbol, positions[0].get('market', 'US'))
        
        if current_price is None:
            return {'error': f'Could not fetch current price for {symbol}'}
        
        # Calculate P/L for each entry
        entries = []
        total_quantity = 0
        total_cost_basis = 0
        total_current_value = 0
        
        for pos in positions:
            pl = self.calculate_position_pl(pos, current_price)
            entries.append(pl)
            total_quantity += pos['quantity']
            total_cost_basis += pl['cost_basis']
            total_current_value += pl['current_value']
        
        avg_cost = total_cost_basis / total_quantity if total_quantity > 0 else 0
        total_pl = total_current_value - total_cost_basis
        total_pl_pct = (total_pl / total_cost_basis * 100) if total_cost_basis > 0 else 0
        
        return {
            'symbol': symbol,
            'total_quantity': total_quantity,
            'average_cost': avg_cost,
            'current_price': current_price,
            'total_cost_basis': total_cost_basis,
            'current_value': total_current_value,
            'total_pl': total_pl,
            'total_pl_percent': total_pl_pct,
            'entries': entries,
            'entry_count': len(entries)
        }
    
    def calculate_total_portfolio(self) -> Dict[str, Any]:
        """Calculate complete portfolio value and P/L"""
        symbols = self.get_unique_symbols()
        
        holdings = []
        total_value = 0
        total_cost = 0
        
        for symbol in symbols:
            symbol_pl = self.calculate_symbol_pl(symbol)
            if 'error' not in symbol_pl:
                holdings.append(symbol_pl)
                total_value += symbol_pl['current_value']
                total_cost += symbol_pl['total_cost_basis']
        
        # Add cash
        cash = self.portfolio.get('cash_balance', 0)
        total_value += cash
        
        # Calculate overall P/L
        total_pl = total_value - total_cost
        total_pl_pct = (total_pl / total_cost * 100) if total_cost > 0 else 0
        
        return {
            'total_value': total_value,
            'total_cost_basis': total_cost,
            'cash_balance': cash,
            'total_pl': total_pl,
            'total_pl_percent': total_pl_pct,
            'holdings': holdings,
            'positions_count': len(self.portfolio['positions']),
            'unique_assets': len(symbols),
            'last_updated': datetime.now().isoformat()
        }
    
    def get_current_price(self, symbol: str, market: str = "US") -> Optional[float]:
        """
        Get current price from API or manual entry
        """
        if market == "NSE":
            # Check manual prices
            manual_prices = self.portfolio.get('manual_prices', {})
            if symbol in manual_prices:
                price_data = manual_prices[symbol]
                return price_data.get('price')
            return None
        
        # US stocks - use API
        try:
            quote = self.fmp.get_quote(symbol)
            if quote and not quote.get('error'):
                return quote.get('price')
        except Exception as e:
            logger.error(f"Error fetching price for {symbol}: {e}")
        
        return None
    
    def update_manual_price(self, symbol: str, price: float) -> Dict[str, Any]:
        """Update manual price for NSE stocks"""
        if 'manual_prices' not in self.portfolio:
            self.portfolio['manual_prices'] = {}
        
        self.portfolio['manual_prices'][symbol] = {
            'price': price,
            'last_updated': datetime.now().isoformat()
        }
        
        self._save_portfolio()
        
        return {
            'success': True,
            'symbol': symbol,
            'price': price,
            'message': f"Updated {symbol} price to KSh {price}"
        }
    
    def needs_price_update(self, symbol: str) -> bool:
        """Check if NSE stock price needs updating (older than 24 hours)"""
        manual_prices = self.portfolio.get('manual_prices', {})
        
        if symbol not in manual_prices:
            return True
        
        last_updated = manual_prices[symbol].get('last_updated')
        if not last_updated:
            return True
        
        last_update_time = datetime.fromisoformat(last_updated)
        return datetime.now() - last_update_time > timedelta(hours=24)
    
    # ========== WITHDRAWAL TRACKING ==========
    
    def add_withdrawal(self, amount: float, withdrawal_type: str = "regular", notes: str = "") -> Dict[str, Any]:
        """Record a withdrawal"""
        withdrawal = Withdrawal(
            amount=amount,
            date=datetime.now().strftime('%Y-%m-%d'),
            withdrawal_type=withdrawal_type,
            notes=notes
        )
        
        if 'withdrawals' not in self.portfolio:
            self.portfolio['withdrawals'] = []
        
        self.portfolio['withdrawals'].append(withdrawal.to_dict())
        self._save_portfolio()
        
        return {
            'success': True,
            'withdrawal': withdrawal.to_dict(),
            'message': f"Recorded ${amount:,.2f} withdrawal"
        }
    
    def get_withdrawal_summary(self, year: int = None) -> Dict[str, Any]:
        """Get withdrawal summary for a year"""
        if year is None:
            year = datetime.now().year
        
        withdrawals = self.portfolio.get('withdrawals', [])
        year_withdrawals = [w for w in withdrawals if w['date'].startswith(str(year))]
        
        total = sum(w['amount'] for w in year_withdrawals)
        count = len(year_withdrawals)
        
        by_type = {}
        for w in year_withdrawals:
            wtype = w.get('withdrawal_type', 'regular')
            by_type[wtype] = by_type.get(wtype, 0) + w['amount']
        
        return {
            'year': year,
            'total_withdrawn': total,
            'withdrawal_count': count,
            'by_type': by_type,
            'withdrawals': year_withdrawals
        }
    
    def calculate_safe_withdrawal(self) -> Dict[str, Any]:
        """Calculate safe withdrawal amount using 4% rule with guardrails"""
        portfolio_value = self.calculate_total_portfolio()['total_value']
        
        withdrawal_rate = self.portfolio.get('settings', {}).get('withdrawal_rate', 0.04)
        
        # Base calculation
        safe_annual = portfolio_value * withdrawal_rate
        safe_monthly = safe_annual / 12
        
        # Guardrails (ceiling/floor based on portfolio performance)
        floor_value = portfolio_value * 0.8  # 20% below current
        ceiling_value = portfolio_value * 1.2  # 20% above current
        
        floor_withdrawal = floor_value * 0.03  # Drop to 3% if portfolio drops 20%
        ceiling_withdrawal = ceiling_value * 0.045  # Increase to 4.5% if portfolio up 20%
        
        # YTD withdrawals
        ytd = self.get_withdrawal_summary(datetime.now().year)
        remaining_this_year = safe_annual - ytd['total_withdrawn']
        
        return {
            'portfolio_value': portfolio_value,
            'withdrawal_rate': withdrawal_rate,
            'safe_annual': safe_annual,
            'safe_monthly': safe_monthly,
            'ytd_withdrawn': ytd['total_withdrawn'],
            'remaining_this_year': remaining_this_year,
            'guardrails': {
                'floor': floor_withdrawal,
                'ceiling': ceiling_withdrawal,
                'current_is_safe': safe_annual >= floor_withdrawal
            }
        }
    
    # ========== PORTFOLIO ANALYTICS ==========
    
    def calculate_allocation(self) -> Dict[str, Any]:
        """Calculate asset allocation breakdown"""
        portfolio = self.calculate_total_portfolio()
        total_value = portfolio['total_value']
        
        if total_value == 0:
            return {'error': 'Portfolio is empty'}
        
        # By asset type
        by_type = {}
        # By market
        by_market = {}
        # By symbol
        by_symbol = {}
        
        for holding in portfolio['holdings']:
            symbol = holding['symbol']
            value = holding['current_value']
            percent = (value / total_value) * 100
            
            # Find position to get metadata
            positions = self.get_positions_by_symbol(symbol)
            if positions:
                asset_type = positions[0].get('asset_type', 'stock')
                market = positions[0].get('market', 'US')
                
                by_type[asset_type] = by_type.get(asset_type, 0) + percent
                by_market[market] = by_market.get(market, 0) + percent
            
            by_symbol[symbol] = {
                'value': value,
                'percent': percent,
                'pl_percent': holding.get('total_pl_percent', 0)
            }
        
        # Cash allocation
        cash_percent = (portfolio['cash_balance'] / total_value * 100) if total_value > 0 else 0
        by_type['cash'] = cash_percent
        
        return {
            'by_asset_type': by_type,
            'by_market': by_market,
            'by_symbol': by_symbol,
            'total_value': total_value
        }
    
    def calculate_portfolio_health_score(self, user_risk_score: float = 0.5) -> Dict[str, Any]:
        """
        Calculate portfolio health score (0-100)
        Based on diversification, risk alignment, performance, sustainability
        """
        scores = {}
        
        # 1. Diversification Score (0-25 points)
        allocation = self.calculate_allocation()
        by_symbol = allocation.get('by_symbol', {})
        
        diversification = 25
        # Penalty for concentration
        for symbol, data in by_symbol.items():
            if data['percent'] > 15:  # More than 15% in one stock
                diversification -= (data['percent'] - 15) * 0.5
        
        # Penalty for too few holdings
        unique_count = len(by_symbol)
        if unique_count < 5:
            diversification -= (5 - unique_count) * 3
        
        scores['diversification'] = max(0, min(25, diversification))
        
        # 2. Risk Alignment Score (0-25 points)
        portfolio_risk = self._estimate_portfolio_risk()
        risk_diff = abs(portfolio_risk - user_risk_score)
        
        if risk_diff < 0.1:
            scores['risk_alignment'] = 25
        elif risk_diff < 0.2:
            scores['risk_alignment'] = 20
        elif risk_diff < 0.3:
            scores['risk_alignment'] = 15
        else:
            scores['risk_alignment'] = 10
        
        # 3. Performance Score (0-25 points)
        portfolio = self.calculate_total_portfolio()
        pl_percent = portfolio.get('total_pl_percent', 0)
        
        if pl_percent > 20:
            scores['performance'] = 25
        elif pl_percent > 10:
            scores['performance'] = 20
        elif pl_percent > 5:
            scores['performance'] = 15
        elif pl_percent > 0:
            scores['performance'] = 10
        else:
            scores['performance'] = 5
        
        # 4. Withdrawal Sustainability (0-25 points)
        withdrawal_calc = self.calculate_safe_withdrawal()
        ytd_rate = withdrawal_calc['ytd_withdrawn'] / portfolio['total_value'] if portfolio['total_value'] > 0 else 0
        
        if ytd_rate < 0.04:
            scores['sustainability'] = 25
        elif ytd_rate < 0.05:
            scores['sustainability'] = 20
        elif ytd_rate < 0.06:
            scores['sustainability'] = 15
        else:
            scores['sustainability'] = 10
        
        # Total score
        total_score = sum(scores.values())
        
        # Health rating
        if total_score >= 85:
            health_rating = "Excellent"
        elif total_score >= 70:
            health_rating = "Good"
        elif total_score >= 55:
            health_rating = "Fair"
        else:
            health_rating = "Needs Attention"
        
        return {
            'total_score': total_score,
            'health_rating': health_rating,
            'scores': scores,
            'insights': self._generate_health_insights(scores, user_risk_score, portfolio_risk)
        }
    
    def _estimate_portfolio_risk(self) -> float:
        """Estimate portfolio risk score based on holdings"""
        allocation = self.calculate_allocation()
        by_symbol = allocation.get('by_symbol', {})
        
        if not by_symbol:
            return 0.5
        
        # Simple heuristic: tech stocks = higher risk, bonds/funds = lower risk
        high_risk_symbols = ['TSLA', 'NVDA', 'AMD']
        moderate_risk = ['AAPL', 'MSFT', 'GOOGL', 'AMZN']
        
        risk_total = 0
        for symbol, data in by_symbol.items():
            weight = data['percent'] / 100
            
            if symbol in high_risk_symbols:
                risk_total += weight * 0.8
            elif symbol in moderate_risk:
                risk_total += weight * 0.5
            else:
                risk_total += weight * 0.3
        
        return min(1.0, max(0.0, risk_total))
    
    def _generate_health_insights(self, scores: Dict, user_risk: float, portfolio_risk: float) -> List[str]:
        """Generate actionable insights from health scores"""
        insights = []
        
        if scores['diversification'] < 20:
            insights.append("⚠️ Concentration risk - Consider adding more positions or reducing large holdings")
        
        if scores['risk_alignment'] < 20:
            if portfolio_risk > user_risk:
                insights.append("⚠️ Portfolio is riskier than your comfort zone - Consider rebalancing to lower-risk assets")
            else:
                insights.append("💡 Portfolio is more conservative than needed - Could add growth positions")
        
        if scores['performance'] < 15:
            insights.append("📉 Portfolio underperforming - Review holdings and consider rebalancing")
        
        if scores['sustainability'] < 20:
            insights.append("⚠️ Withdrawal rate too high - Reduce withdrawals or grow portfolio")
        
        if not insights:
            insights.append("✅ Portfolio is healthy - Keep up the good work!")
        
        return insights
    
    def check_rebalancing_needed(self) -> Dict[str, Any]:
        """Check if portfolio needs rebalancing"""
        allocation = self.calculate_allocation()
        by_symbol = allocation.get('by_symbol', {})
        
        # Target allocations (simplified - can be customized per user)
        targets = {
            'stocks': 60,
            'bonds': 30,
            'cash': 10
        }
        
        threshold = self.portfolio.get('settings', {}).get('rebalance_threshold', 0.10)
        
        needs_rebalancing = False
        actions = []
        
        for symbol, data in by_symbol.items():
            if data['percent'] > 15:  # Single position over 15%
                needs_rebalancing = True
                trim_amount = (data['percent'] - 10) / 100 * allocation['total_value']
                actions.append(f"Trim {symbol} by ${trim_amount:,.0f} (reduce from {data['percent']:.1f}% to 10%)")
        
        return {
            'needs_rebalancing': needs_rebalancing,
            'threshold': threshold * 100,
            'actions': actions,
            'current_allocation': allocation
        }
    
    # ========== UTILITIES ==========
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get comprehensive portfolio summary for dashboard/chatbot"""
        portfolio = self.calculate_total_portfolio()
        health = self.calculate_portfolio_health_score()
        withdrawal = self.calculate_safe_withdrawal()
        rebalance = self.check_rebalancing_needed()
        allocation = self.calculate_allocation()
        
        return {
            'overview': {
                'total_value': portfolio['total_value'],
                'total_pl': portfolio['total_pl'],
                'total_pl_percent': portfolio['total_pl_percent'],
                'positions_count': portfolio['positions_count'],
                'cash_balance': portfolio['cash_balance']
            },
            'health': health,
            'withdrawal': withdrawal,
            'rebalancing': rebalance,
            'allocation': allocation,
            'top_holdings': sorted(
                portfolio['holdings'],
                key=lambda x: x['current_value'],
                reverse=True
            )[:5]
        }


# Helper function
def get_portfolio_manager(user_id: str) -> PortfolioManager:
    """Get portfolio manager for a user"""
    return PortfolioManager(user_id)


if __name__ == "__main__":
    # Test portfolio manager
    print("\n🧪 Testing Portfolio Manager\n")
    
    pm = PortfolioManager("test_user")
    
    # Add some positions
    print("Adding positions...")
    pm.add_position("AAPL", 10, 250.0, "2024-01-15")
    pm.add_position("AAPL", 5, 265.0, "2024-03-20")  # Multi-entry
    pm.add_position("MSFT", 8, 380.0, "2024-02-10")
    
    # Calculate P/L
    print("\n📊 Apple P/L (Multi-Entry):")
    apple_pl = pm.calculate_symbol_pl("AAPL")
    print(json.dumps(apple_pl, indent=2))
    
    # Total portfolio
    print("\n💼 Total Portfolio:")
    total = pm.calculate_total_portfolio()
    print(f"Value: ${total['total_value']:,.2f}")
    print(f"P/L: ${total['total_pl']:,.2f} ({total['total_pl_percent']:.2f}%)")
    
    # Health score
    print("\n🏥 Portfolio Health:")
    health = pm.calculate_portfolio_health_score(user_risk_score=0.65)
    print(f"Score: {health['total_score']}/100 ({health['health_rating']})")
    print(f"Insights: {health['insights']}")
    
    # Withdrawal planning
    print("\n💰 Safe Withdrawal:")
    withdrawal = pm.calculate_safe_withdrawal()
    print(f"Annual: ${withdrawal['safe_annual']:,.2f}")
    print(f"Monthly: ${withdrawal['safe_monthly']:,.2f}")


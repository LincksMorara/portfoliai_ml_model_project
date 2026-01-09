"""
Portfolio Event Detection System
Proactively identifies significant events that users should know about

Event Types:
- Price targets reached
- Risk drift detection
- Rebalancing opportunities
- Large price movements
- Concentration risk
- Tax optimization opportunities
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from tax_calculator import get_tax_calculator

logger = logging.getLogger(__name__)


class EventDetector:
    """
    Detect portfolio events and generate proactive alerts
    """
    
    # Event priority levels
    PRIORITY_CRITICAL = 'critical'  # Immediate action needed
    PRIORITY_HIGH = 'high'  # Should act soon
    PRIORITY_MEDIUM = 'medium'  # Informational, consider action
    PRIORITY_LOW = 'low'  # FYI only
    
    def __init__(self):
        logger.info("🔔 EventDetector initialized")
        self.tax_calc = get_tax_calculator()
    
    def detect_all_events(self,
                         portfolio_data: Dict,
                         user_profile: Dict,
                         positions: List[Dict]) -> List[Dict[str, Any]]:
        """
        Run all detection checks and return prioritized list of events
        
        Args:
            portfolio_data: Overall portfolio summary
            user_profile: User's risk profile and preferences
            positions: List of current positions
        
        Returns:
            List of event dicts with type, priority, message, data
        """
        events = []
        
        # Run all detectors
        events.extend(self._detect_price_movements(positions))
        events.extend(self._detect_risk_drift(portfolio_data, user_profile, positions))
        events.extend(self._detect_rebalancing_opportunities(positions))
        events.extend(self._detect_concentration_risk(positions))
        events.extend(self._detect_tax_opportunities(positions))
        events.extend(self._detect_profit_taking_opportunities(positions))
        events.extend(self._detect_stop_loss_triggers(positions))
        
        # Sort by priority
        priority_order = {
            self.PRIORITY_CRITICAL: 0,
            self.PRIORITY_HIGH: 1,
            self.PRIORITY_MEDIUM: 2,
            self.PRIORITY_LOW: 3
        }
        events.sort(key=lambda e: priority_order.get(e['priority'], 999))
        
        logger.info(f"✅ Detected {len(events)} portfolio events")
        return events
    
    def _detect_price_movements(self, positions: List[Dict]) -> List[Dict]:
        """Detect significant price movements (>5% up/down)"""
        events = []
        
        for pos in positions:
            symbol = pos.get('symbol')
            current_price = pos.get('current_price', 0)
            avg_cost = pos.get('average_cost', 0)
            
            if avg_cost > 0:
                price_change_pct = ((current_price - avg_cost) / avg_cost) * 100
                
                # Large gain (>20%)
                if price_change_pct > 20:
                    events.append({
                        'type': 'large_gain',
                        'priority': self.PRIORITY_HIGH,
                        'symbol': symbol,
                        'message': f"🚀 {symbol} is up {price_change_pct:.1f}%! Consider taking some profits.",
                        'data': {
                            'price_change_pct': price_change_pct,
                            'current_price': current_price,
                            'avg_cost': avg_cost
                        }
                    })
                
                # Large loss (>15%)
                elif price_change_pct < -15:
                    events.append({
                        'type': 'large_loss',
                        'priority': self.PRIORITY_MEDIUM,
                        'symbol': symbol,
                        'message': f"📉 {symbol} is down {abs(price_change_pct):.1f}%. Review your thesis or consider tax-loss harvesting.",
                        'data': {
                            'price_change_pct': price_change_pct,
                            'current_price': current_price,
                            'avg_cost': avg_cost
                        }
                    })
        
        return events
    
    def _detect_risk_drift(self,
                          portfolio_data: Dict,
                          user_profile: Dict,
                          positions: List[Dict]) -> List[Dict]:
        """Detect if portfolio risk has drifted from user's profile"""
        events = []
        
        user_risk_score = user_profile.get('risk_score', 0.5)
        
        # Calculate portfolio concentration as risk proxy
        total_value = sum(p.get('total_quantity', 0) * p.get('current_price', 0) for p in positions)
        
        if total_value == 0:
            return events
        
        # Check for sector/position concentration
        position_percentages = [
            (p.get('total_quantity', 0) * p.get('current_price', 0)) / total_value * 100
            for p in positions
        ]
        
        max_position_pct = max(position_percentages) if position_percentages else 0
        
        # Risk drift thresholds based on user profile
        if user_risk_score < 0.3:  # Conservative
            max_acceptable = 15
        elif user_risk_score < 0.6:  # Moderate
            max_acceptable = 25
        else:  # Aggressive
            max_acceptable = 35
        
        if max_position_pct > max_acceptable:
            largest_position = positions[position_percentages.index(max_position_pct)]
            events.append({
                'type': 'risk_drift',
                'priority': self.PRIORITY_HIGH,
                'symbol': largest_position.get('symbol'),
                'message': f"⚠️ {largest_position.get('symbol')} is {max_position_pct:.1f}% of your portfolio (target: <{max_acceptable}%). Your portfolio drifted from your risk profile.",
                'data': {
                    'position_pct': max_position_pct,
                    'max_acceptable': max_acceptable,
                    'user_risk_score': user_risk_score
                }
            })
        
        return events
    
    def _detect_rebalancing_opportunities(self, positions: List[Dict]) -> List[Dict]:
        """Detect when portfolio needs rebalancing"""
        events = []
        
        # Check last rebalance date (would need to store this)
        # For now, check if any position is >30% of portfolio
        
        total_value = sum(p.get('total_quantity', 0) * p.get('current_price', 0) for p in positions)
        
        if total_value == 0:
            return events
        
        for pos in positions:
            position_value = pos.get('total_quantity', 0) * pos.get('current_price', 0)
            position_pct = (position_value / total_value) * 100
            
            if position_pct > 30:
                events.append({
                    'type': 'rebalancing_needed',
                    'priority': self.PRIORITY_MEDIUM,
                    'symbol': pos.get('symbol'),
                    'message': f"⚖️ {pos.get('symbol')} has grown to {position_pct:.1f}% of your portfolio. Consider rebalancing to reduce concentration risk.",
                    'data': {
                        'position_pct': position_pct,
                        'position_value': position_value
                    }
                })
        
        return events
    
    def _detect_concentration_risk(self, positions: List[Dict]) -> List[Dict]:
        """Detect overall concentration risk"""
        events = []
        
        # Check diversification
        num_positions = len(positions)
        
        if num_positions == 1:
            events.append({
                'type': 'concentration_risk',
                'priority': self.PRIORITY_HIGH,
                'message': f"🎯 You only have 1 position. Consider adding 4-5 more stocks to reduce concentration risk.",
                'data': {
                    'num_positions': num_positions,
                    'recommendation': 'Add at least 4 more diversified positions'
                }
            })
        elif num_positions < 5:
            events.append({
                'type': 'low_diversification',
                'priority': self.PRIORITY_MEDIUM,
                'message': f"📊 You have {num_positions} positions. Adding a few more would improve diversification.",
                'data': {
                    'num_positions': num_positions,
                    'recommendation': f'Target: 5-10 positions for good diversification'
                }
            })
        
        return events
    
    def _detect_tax_opportunities(self, positions: List[Dict]) -> List[Dict]:
        """Detect tax optimization opportunities"""
        events = []
        
        for pos in positions:
            symbol = pos.get('symbol')
            quantity = pos.get('total_quantity', 0)
            current_price = pos.get('current_price', 0)
            avg_cost = pos.get('average_cost', 0)
            entries = pos.get('entries', [])
            
            if not entries:
                continue
            
            first_entry = entries[0]
            purchase_date_str = first_entry.get('date')
            
            if not purchase_date_str:
                continue
            
            try:
                purchase_date = datetime.fromisoformat(purchase_date_str.replace('Z', '+00:00'))
                holding_days = (datetime.now() - purchase_date).days
                unrealized_gain = (current_price - avg_cost) * quantity
                
                # Opportunity 1: Almost long-term (US tax optimization)
                if 0 < unrealized_gain and 335 <= holding_days < 365:
                    days_to_long_term = 365 - holding_days
                    events.append({
                        'type': 'tax_optimization_hold',
                        'priority': self.PRIORITY_HIGH,
                        'symbol': symbol,
                        'message': f"💰 {symbol}: Hold {days_to_long_term} more days to qualify for long-term capital gains rate (15% vs 22% - save ${unrealized_gain * 0.07:.0f} in taxes!)",
                        'data': {
                            'days_to_long_term': days_to_long_term,
                            'potential_tax_savings': unrealized_gain * 0.07,
                            'holding_days': holding_days
                        }
                    })
                
                # Opportunity 2: Tax loss harvesting
                elif unrealized_gain < -1000:
                    events.append({
                        'type': 'tax_loss_harvesting',
                        'priority': self.PRIORITY_MEDIUM,
                        'symbol': symbol,
                        'message': f"📉 {symbol}: Consider harvesting ${abs(unrealized_gain):.0f} tax loss to offset other gains.",
                        'data': {
                            'tax_loss_amount': abs(unrealized_gain),
                            'holding_days': holding_days
                        }
                    })
                
                # Opportunity 3: Year-end tax planning
                days_to_year_end = (datetime(datetime.now().year, 12, 31) - datetime.now()).days
                if 0 < days_to_year_end <= 45 and unrealized_gain < -500:
                    events.append({
                        'type': 'year_end_tax_planning',
                        'priority': self.PRIORITY_HIGH,
                        'symbol': symbol,
                        'message': f"📅 {symbol}: {days_to_year_end} days until year-end. Harvest this loss before Dec 31 to offset taxes this year.",
                        'data': {
                            'days_to_year_end': days_to_year_end,
                            'loss_amount': abs(unrealized_gain)
                        }
                    })
            
            except Exception as e:
                logger.warning(f"Could not check tax opportunities for {symbol}: {e}")
        
        return events
    
    def _detect_profit_taking_opportunities(self, positions: List[Dict]) -> List[Dict]:
        """Detect good profit-taking opportunities"""
        events = []
        
        for pos in positions:
            symbol = pos.get('symbol')
            quantity = pos.get('total_quantity', 0)
            current_price = pos.get('current_price', 0)
            avg_cost = pos.get('average_cost', 0)
            
            if avg_cost > 0:
                gain_pct = ((current_price - avg_cost) / avg_cost) * 100
                
                # Suggest profit-taking on large gains
                if gain_pct > 50:
                    events.append({
                        'type': 'profit_taking',
                        'priority': self.PRIORITY_MEDIUM,
                        'symbol': symbol,
                        'message': f"💎 {symbol} is up {gain_pct:.1f}%! Consider taking partial profits (sell 25-50%) to lock in gains.",
                        'data': {
                            'gain_pct': gain_pct,
                            'unrealized_gain': (current_price - avg_cost) * quantity
                        }
                    })
        
        return events
    
    def _detect_stop_loss_triggers(self, positions: List[Dict]) -> List[Dict]:
        """Detect positions that may need stop-loss consideration"""
        events = []
        
        for pos in positions:
            symbol = pos.get('symbol')
            current_price = pos.get('current_price', 0)
            avg_cost = pos.get('average_cost', 0)
            
            if avg_cost > 0:
                loss_pct = ((current_price - avg_cost) / avg_cost) * 100
                
                # Alert on significant losses
                if loss_pct < -25:
                    events.append({
                        'type': 'stop_loss_alert',
                        'priority': self.PRIORITY_HIGH,
                        'symbol': symbol,
                        'message': f"🚨 {symbol} is down {abs(loss_pct):.1f}%. Review your investment thesis - is it time to cut losses or average down?",
                        'data': {
                            'loss_pct': loss_pct,
                            'current_price': current_price,
                            'avg_cost': avg_cost
                        }
                    })
        
        return events


# Global instance
_event_detector = None


def get_event_detector() -> EventDetector:
    """Get or create event detector singleton"""
    global _event_detector
    if _event_detector is None:
        _event_detector = EventDetector()
    return _event_detector


if __name__ == "__main__":
    # Test event detector
    detector = EventDetector()
    
    print("\n🧪 Testing Event Detector\n")
    
    # Mock portfolio data
    mock_positions = [
        {
            'symbol': 'AAPL',
            'total_quantity': 10,
            'average_cost': 150.0,
            'current_price': 270.0,
            'entries': [{'date': '2024-01-15', 'quantity': 10, 'price': 150.0}]
        },
        {
            'symbol': 'MSFT',
            'total_quantity': 5,
            'average_cost': 300.0,
            'current_price': 250.0,
            'entries': [{'date': '2024-08-01', 'quantity': 5, 'price': 300.0}]
        }
    ]
    
    mock_portfolio = {
        'total_value': 4450.0
    }
    
    mock_user_profile = {
        'risk_score': 0.54
    }
    
    # Detect events
    events = detector.detect_all_events(mock_portfolio, mock_user_profile, mock_positions)
    
    print(f"Found {len(events)} events:\n")
    for event in events:
        priority_emoji = {
            'critical': '🔴',
            'high': '🟠',
            'medium': '🟡',
            'low': '🟢'
        }
        emoji = priority_emoji.get(event['priority'], '⚪')
        print(f"{emoji} [{event['priority'].upper()}] {event['type']}")
        print(f"   {event['message']}\n")





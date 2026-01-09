"""
Withdrawal Planning System
Implements 4% rule, guardrails, scenario analysis, and sustainability projections
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import random

logger = logging.getLogger(__name__)

class WithdrawalPlanner:
    """
    Advanced withdrawal planning with scenarios, stress testing, and sustainability analysis
    """
    
    def __init__(self):
        pass
    
    def calculate_basic_withdrawal(self, 
                                   portfolio_value: float,
                                   withdrawal_rate: float = 0.04) -> Dict[str, Any]:
        """Basic 4% rule calculation"""
        annual = portfolio_value * withdrawal_rate
        monthly = annual / 12
        weekly = annual / 52
        
        return {
            'portfolio_value': portfolio_value,
            'withdrawal_rate': withdrawal_rate,
            'annual': annual,
            'monthly': monthly,
            'weekly': weekly
        }
    
    def calculate_with_guardrails(self,
                                 portfolio_value: float,
                                 initial_portfolio: float,
                                 base_withdrawal: float,
                                 ceiling_percent: float = 0.20,
                                 floor_percent: float = 0.15) -> Dict[str, Any]:
        """
        Dynamic withdrawal with guardrails
        Adjusts based on portfolio performance
        """
        # Calculate current vs initial
        change_percent = ((portfolio_value - initial_portfolio) / initial_portfolio)
        
        # Determine withdrawal
        if change_percent > ceiling_percent:
            # Portfolio up significantly - can increase withdrawal
            new_rate = 0.045
            status = "increase_allowed"
            message = f"Portfolio up {change_percent*100:.1f}%! Can safely increase withdrawal to 4.5%"
        elif change_percent < -floor_percent:
            # Portfolio down significantly - should decrease
            new_rate = 0.035
            status = "decrease_recommended"
            message = f"Portfolio down {abs(change_percent)*100:.1f}%. Recommend reducing withdrawal to 3.5%"
        else:
            # Normal range - maintain 4%
            new_rate = 0.04
            status = "on_track"
            message = "Portfolio stable - maintain 4% withdrawal rate"
        
        recommended_withdrawal = portfolio_value * new_rate
        
        return {
            'current_value': portfolio_value,
            'initial_value': initial_portfolio,
            'change_percent': change_percent,
            'status': status,
            'recommended_rate': new_rate,
            'recommended_annual': recommended_withdrawal,
            'recommended_monthly': recommended_withdrawal / 12,
            'message': message,
            'base_withdrawal': base_withdrawal
        }
    
    def run_sustainability_projection(self,
                                     starting_portfolio: float,
                                     annual_withdrawal: float,
                                     years: int = 30,
                                     expected_return: float = 0.07,
                                     inflation: float = 0.03) -> Dict[str, Any]:
        """
        Project portfolio sustainability over time
        """
        projections = []
        portfolio = starting_portfolio
        withdrawal = annual_withdrawal
        
        for year in range(1, years + 1):
            # Apply returns
            portfolio = portfolio * (1 + expected_return)
            
            # Apply withdrawal
            portfolio -= withdrawal
            
            # Adjust withdrawal for inflation
            withdrawal = withdrawal * (1 + inflation)
            
            projections.append({
                'year': year,
                'portfolio_value': portfolio,
                'withdrawal_amount': withdrawal,
                'depleted': portfolio <= 0
            })
            
            if portfolio <= 0:
                break
        
        # Find depletion year
        depletion_year = next((p['year'] for p in projections if p['depleted']), None)
        
        success = depletion_year is None or depletion_year > years
        
        return {
            'starting_value': starting_portfolio,
            'initial_withdrawal': annual_withdrawal,
            'years_projected': years,
            'expected_return': expected_return,
            'inflation_rate': inflation,
            'success': success,
            'depletion_year': depletion_year,
            'final_value': projections[-1]['portfolio_value'] if projections else 0,
            'projections': projections
        }
    
    def run_monte_carlo(self,
                       starting_portfolio: float,
                       annual_withdrawal: float,
                       years: int = 30,
                       simulations: int = 1000) -> Dict[str, Any]:
        """
        Run Monte Carlo simulation for withdrawal sustainability
        Models market volatility and sequence of returns risk
        """
        successes = 0
        all_results = []
        
        for sim in range(simulations):
            portfolio = starting_portfolio
            withdrawal = annual_withdrawal
            survived = True
            
            for year in range(years):
                # Simulate annual return (mean 7%, std dev 15%)
                annual_return = random.gauss(0.07, 0.15)
                
                # Apply return
                portfolio = portfolio * (1 + annual_return)
                
                # Apply withdrawal
                portfolio -= withdrawal
                
                # Adjust withdrawal for inflation (3%)
                withdrawal *= 1.03
                
                if portfolio <= 0:
                    survived = False
                    break
            
            if survived:
                successes += 1
            
            all_results.append({
                'survived': survived,
                'final_value': max(0, portfolio)
            })
        
        success_rate = (successes / simulations) * 100
        
        # Calculate percentiles
        final_values = sorted([r['final_value'] for r in all_results])
        median = final_values[len(final_values) // 2]
        percentile_10 = final_values[int(len(final_values) * 0.1)]
        percentile_90 = final_values[int(len(final_values) * 0.9)]
        
        # Recommendation
        if success_rate >= 90:
            recommendation = "Excellent sustainability - portfolio very likely to last"
        elif success_rate >= 75:
            recommendation = "Good sustainability - portfolio likely to last with monitoring"
        elif success_rate >= 60:
            recommendation = "Moderate risk - consider reducing withdrawal rate"
        else:
            recommendation = "High risk - withdrawal rate likely unsustainable"
        
        return {
            'simulations': simulations,
            'success_rate': success_rate,
            'median_final_value': median,
            'worst_case_10th_percentile': percentile_10,
            'best_case_90th_percentile': percentile_90,
            'recommendation': recommendation,
            'confidence_level': "High" if success_rate >= 85 else "Moderate" if success_rate >= 70 else "Low"
        }
    
    def stress_test(self,
                   portfolio_value: float,
                   annual_withdrawal: float,
                   crash_scenarios: List[Tuple[str, float]] = None) -> Dict[str, Any]:
        """
        Stress test portfolio against market crashes
        """
        if crash_scenarios is None:
            crash_scenarios = [
                ("Moderate Correction", -0.20),  # 20% drop
                ("Severe Crash", -0.40),  # 40% drop (2008-style)
                ("Extreme Crisis", -0.50)  # 50% drop (worst case)
            ]
        
        results = []
        
        for scenario_name, crash_percent in crash_scenarios:
            # Portfolio value after crash
            crashed_value = portfolio_value * (1 + crash_percent)
            
            # Withdrawal as % of crashed portfolio
            new_withdrawal_rate = annual_withdrawal / crashed_value if crashed_value > 0 else 999
            
            # Is it sustainable?
            if new_withdrawal_rate > 0.06:
                status = "Unsustainable - must reduce withdrawals"
                action = f"Reduce to ${crashed_value * 0.04:,.0f}/year or pause temporarily"
            elif new_withdrawal_rate > 0.05:
                status = "Risky - should reduce withdrawals"
                action = f"Consider reducing to ${crashed_value * 0.04:,.0f}/year"
            else:
                status = "Sustainable - can maintain withdrawals"
                action = "Continue current withdrawal rate"
            
            results.append({
                'scenario': scenario_name,
                'crash_percent': crash_percent * 100,
                'portfolio_after_crash': crashed_value,
                'withdrawal_rate_after_crash': new_withdrawal_rate * 100,
                'status': status,
                'recommended_action': action
            })
        
        return {
            'original_portfolio': portfolio_value,
            'annual_withdrawal': annual_withdrawal,
            'scenarios': results
        }
    
    def calculate_required_portfolio(self,
                                    desired_annual_income: float,
                                    withdrawal_rate: float = 0.04) -> Dict[str, Any]:
        """
        Calculate portfolio size needed for desired income
        """
        required_portfolio = desired_annual_income / withdrawal_rate
        
        # Different scenarios
        scenarios = {
            'conservative_3pct': desired_annual_income / 0.03,
            'standard_4pct': desired_annual_income / 0.04,
            'aggressive_5pct': desired_annual_income / 0.05
        }
        
        return {
            'desired_annual_income': desired_annual_income,
            'withdrawal_rate': withdrawal_rate,
            'required_portfolio': required_portfolio,
            'scenarios': scenarios,
            'monthly_income': desired_annual_income / 12
        }


# Global instance
_withdrawal_planner = None

def get_withdrawal_planner() -> WithdrawalPlanner:
    """Get or create withdrawal planner singleton"""
    global _withdrawal_planner
    if _withdrawal_planner is None:
        _withdrawal_planner = WithdrawalPlanner()
    return _withdrawal_planner


if __name__ == "__main__":
    # Test withdrawal planner
    planner = WithdrawalPlanner()
    
    print("\n🧪 Testing Withdrawal Planner\n")
    
    # Basic 4% rule
    print("=" * 60)
    print("Basic 4% Rule:")
    basic = planner.calculate_basic_withdrawal(500000, 0.04)
    print(f"Portfolio: ${basic['portfolio_value']:,.0f}")
    print(f"Annual: ${basic['annual']:,.0f}")
    print(f"Monthly: ${basic['monthly']:,.0f}")
    
    # Guardrails
    print("\n" + "=" * 60)
    print("Guardrails Test (Portfolio up 25%):")
    guardrails = planner.calculate_with_guardrails(625000, 500000, 20000)
    print(f"Status: {guardrails['status']}")
    print(f"Message: {guardrails['message']}")
    print(f"Recommended: ${guardrails['recommended_annual']:,.0f}/year")
    
    # Sustainability projection
    print("\n" + "=" * 60)
    print("Sustainability Projection:")
    projection = planner.run_sustainability_projection(500000, 20000, years=30)
    print(f"Success: {projection['success']}")
    print(f"Final value: ${projection['final_value']:,.0f}")
    if projection['depletion_year']:
        print(f"⚠️ Depletes in year {projection['depletion_year']}")
    
    # Monte Carlo
    print("\n" + "=" * 60)
    print("Monte Carlo Simulation (1000 runs):")
    mc = planner.run_monte_carlo(500000, 20000, years=30, simulations=1000)
    print(f"Success rate: {mc['success_rate']:.1f}%")
    print(f"Recommendation: {mc['recommendation']}")
    print(f"Median final value: ${mc['median_final_value']:,.0f}")
    
    # Stress test
    print("\n" + "=" * 60)
    print("Stress Test:")
    stress = planner.stress_test(500000, 20000)
    for scenario in stress['scenarios']:
        print(f"\n{scenario['scenario']}: {scenario['crash_percent']:.0f}% crash")
        print(f"  Portfolio: ${scenario['portfolio_after_crash']:,.0f}")
        print(f"  Status: {scenario['status']}")
        print(f"  Action: {scenario['recommended_action']}")



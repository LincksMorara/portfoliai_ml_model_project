"""
Tax Calculator for Investment Returns
Handles both Kenyan and Global (US, EU) tax jurisdictions

Key Features:
- Capital gains tax (short-term vs long-term)
- Dividend tax
- Withholding tax
- Tax loss harvesting opportunities
- Multi-jurisdiction support
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from decimal import Decimal

logger = logging.getLogger(__name__)


class TaxCalculator:
    """
    Calculate tax implications for investment transactions
    Supports: Kenya, United States, United Kingdom, and general international rules
    """
    
    # Kenyan Tax Rates (as of 2024)
    KENYA_TAX_RATES = {
        'capital_gains': {
            'resident': 0.05,  # 5% for residents
            'non_resident': 0.05  # 5% for non-residents
        },
        'dividend_tax': {
            'resident': 0.05,  # 5% for residents
            'non_resident': 0.15  # 15% for non-residents
        },
        'withholding_tax': {
            'interest': 0.15,  # 15% on interest income
            'royalties': 0.20  # 20% on royalties
        },
        'exemptions': {
            'primary_residence': True,  # Primary residence exempt from CGT
            'annual_threshold': 0  # No tax-free threshold currently
        }
    }
    
    # US Tax Rates (Federal - 2024)
    US_TAX_RATES = {
        'capital_gains': {
            'short_term': [0.10, 0.12, 0.22, 0.24, 0.32, 0.35, 0.37],  # Same as income tax
            'long_term': [0.0, 0.15, 0.20],  # 0%, 15%, or 20% based on income
            'threshold_days': 365  # Hold >365 days for long-term rates
        },
        'dividend_tax': {
            'qualified': [0.0, 0.15, 0.20],  # Qualified dividends (long-term rates)
            'ordinary': [0.10, 0.12, 0.22, 0.24, 0.32, 0.35, 0.37]  # Ordinary (income rates)
        },
        'exemptions': {
            'long_term_0_bracket': 44625,  # Single filers, 0% rate up to this income
            'long_term_15_bracket': 492300,  # 15% rate up to this income
        }
    }
    
    # UK Tax Rates (2024/25)
    UK_TAX_RATES = {
        'capital_gains': {
            'annual_allowance': 3000,  # £3,000 tax-free per year (reduced from £12,300)
            'basic_rate': 0.10,  # 10% for basic rate taxpayers
            'higher_rate': 0.20  # 20% for higher rate taxpayers
        },
        'dividend_tax': {
            'allowance': 500,  # £500 tax-free dividend allowance
            'basic_rate': 0.0875,  # 8.75%
            'higher_rate': 0.3375,  # 33.75%
            'additional_rate': 0.3935  # 39.35%
        }
    }
    
    def __init__(self, default_jurisdiction: str = 'kenya'):
        """
        Initialize tax calculator
        
        Args:
            default_jurisdiction: 'kenya', 'us', 'uk', or 'international'
        """
        self.default_jurisdiction = default_jurisdiction.lower()
        logger.info(f"💰 TaxCalculator initialized (default: {default_jurisdiction})")
    
    def calculate_capital_gains_tax(self,
                                   purchase_price: float,
                                   sale_price: float,
                                   quantity: int,
                                   purchase_date: datetime,
                                   sale_date: datetime = None,
                                   jurisdiction: str = None,
                                   taxpayer_status: str = 'resident') -> Dict[str, Any]:
        """
        Calculate capital gains tax on a position sale
        
        Args:
            purchase_price: Average cost per share
            sale_price: Selling price per share
            quantity: Number of shares
            purchase_date: Date of purchase
            sale_date: Date of sale (default: today)
            jurisdiction: 'kenya', 'us', 'uk', or 'international'
            taxpayer_status: 'resident' or 'non_resident'
        
        Returns:
            Dict with gross_gain, tax_owed, net_gain, tax_rate, holding_period, etc.
        """
        if sale_date is None:
            sale_date = datetime.now()
        
        jurisdiction = (jurisdiction or self.default_jurisdiction).lower()
        
        # Calculate basics
        gross_gain = (sale_price - purchase_price) * quantity
        holding_period_days = (sale_date - purchase_date).days
        
        # No tax on losses
        if gross_gain <= 0:
            return {
                'gross_gain': gross_gain,
                'tax_owed': 0,
                'net_gain': gross_gain,
                'tax_rate': 0,
                'holding_period_days': holding_period_days,
                'jurisdiction': jurisdiction,
                'tax_loss': abs(gross_gain),  # Can be used for tax loss harvesting
                'recommendation': 'Consider tax loss harvesting - this loss can offset other gains'
            }
        
        # Calculate tax based on jurisdiction
        if jurisdiction == 'kenya':
            return self._calculate_kenya_cgt(gross_gain, holding_period_days, taxpayer_status)
        elif jurisdiction == 'us':
            return self._calculate_us_cgt(gross_gain, holding_period_days, purchase_price * quantity)
        elif jurisdiction == 'uk':
            return self._calculate_uk_cgt(gross_gain, holding_period_days)
        else:
            # International/default (conservative estimate)
            return self._calculate_international_cgt(gross_gain, holding_period_days)
    
    def _calculate_kenya_cgt(self, gross_gain: float, holding_days: int, taxpayer_status: str) -> Dict[str, Any]:
        """Calculate Kenyan capital gains tax"""
        
        # Kenya has flat 5% CGT for both residents and non-residents
        tax_rate = self.KENYA_TAX_RATES['capital_gains'][taxpayer_status]
        tax_owed = gross_gain * tax_rate
        net_gain = gross_gain - tax_owed
        
        recommendation = None
        if holding_days < 365:
            # No difference in Kenya, but mention for awareness
            recommendation = "Kenya has flat 5% CGT regardless of holding period"
        
        return {
            'gross_gain': gross_gain,
            'tax_owed': tax_owed,
            'net_gain': net_gain,
            'tax_rate': tax_rate,
            'holding_period_days': holding_days,
            'jurisdiction': 'kenya',
            'taxpayer_status': taxpayer_status,
            'recommendation': recommendation,
            'notes': 'Kenya CGT: Flat 5% on gains from property and shares'
        }
    
    def _calculate_us_cgt(self, gross_gain: float, holding_days: int, cost_basis: float) -> Dict[str, Any]:
        """Calculate US capital gains tax"""
        
        threshold_days = self.US_TAX_RATES['capital_gains']['threshold_days']
        
        if holding_days >= threshold_days:
            # Long-term capital gains (favorable rates)
            # Using 15% as typical middle-class rate
            tax_rate = 0.15
            tax_type = 'long_term'
            recommendation = "Long-term capital gains rate (held >1 year) - favorable tax treatment"
        else:
            # Short-term capital gains (ordinary income rates)
            # Using 22% as typical middle-class rate
            tax_rate = 0.22
            tax_type = 'short_term'
            days_to_long_term = threshold_days - holding_days
            recommendation = f"Short-term gains taxed as ordinary income. Hold {days_to_long_term} more days for lower long-term rates!"
        
        tax_owed = gross_gain * tax_rate
        net_gain = gross_gain - tax_owed
        
        return {
            'gross_gain': gross_gain,
            'tax_owed': tax_owed,
            'net_gain': net_gain,
            'tax_rate': tax_rate,
            'tax_type': tax_type,
            'holding_period_days': holding_days,
            'jurisdiction': 'us',
            'recommendation': recommendation,
            'notes': f'US CGT: {tax_type.replace("_", "-")} rate (assumed 15%/22% bracket)'
        }
    
    def _calculate_uk_cgt(self, gross_gain: float, holding_days: int) -> Dict[str, Any]:
        """Calculate UK capital gains tax"""
        
        annual_allowance = self.UK_TAX_RATES['capital_gains']['annual_allowance']
        
        # Deduct annual allowance
        taxable_gain = max(0, gross_gain - annual_allowance)
        
        # Assume basic rate (10%) - can be adjusted based on income
        tax_rate = self.UK_TAX_RATES['capital_gains']['basic_rate']
        tax_owed = taxable_gain * tax_rate
        net_gain = gross_gain - tax_owed
        
        recommendation = None
        if gross_gain < annual_allowance:
            recommendation = f"Gain within £{annual_allowance:,} annual allowance - no tax owed!"
        
        return {
            'gross_gain': gross_gain,
            'taxable_gain': taxable_gain,
            'tax_owed': tax_owed,
            'net_gain': net_gain,
            'tax_rate': tax_rate,
            'annual_allowance_used': min(gross_gain, annual_allowance),
            'holding_period_days': holding_days,
            'jurisdiction': 'uk',
            'recommendation': recommendation,
            'notes': f'UK CGT: £{annual_allowance:,} allowance, 10% basic rate'
        }
    
    def _calculate_international_cgt(self, gross_gain: float, holding_days: int) -> Dict[str, Any]:
        """Calculate international/general capital gains tax (conservative estimate)"""
        
        # Use 20% as conservative international average
        tax_rate = 0.20
        tax_owed = gross_gain * tax_rate
        net_gain = gross_gain - tax_owed
        
        return {
            'gross_gain': gross_gain,
            'tax_owed': tax_owed,
            'net_gain': net_gain,
            'tax_rate': tax_rate,
            'holding_period_days': holding_days,
            'jurisdiction': 'international',
            'recommendation': 'Consult local tax advisor for specific rates in your jurisdiction',
            'notes': 'Estimated 20% international average rate'
        }
    
    def calculate_dividend_tax(self,
                              dividend_amount: float,
                              jurisdiction: str = None,
                              taxpayer_status: str = 'resident') -> Dict[str, Any]:
        """
        Calculate tax on dividend income
        
        Args:
            dividend_amount: Total dividend received
            jurisdiction: 'kenya', 'us', 'uk'
            taxpayer_status: 'resident' or 'non_resident'
        
        Returns:
            Dict with tax_owed, net_dividend, tax_rate
        """
        jurisdiction = (jurisdiction or self.default_jurisdiction).lower()
        
        if jurisdiction == 'kenya':
            tax_rate = self.KENYA_TAX_RATES['dividend_tax'][taxpayer_status]
            notes = f"Kenya dividend tax: {tax_rate*100}% ({'resident' if taxpayer_status == 'resident' else 'non-resident'})"
        elif jurisdiction == 'us':
            # Assume qualified dividends (long-term rate)
            tax_rate = 0.15
            notes = "US qualified dividend rate (assumed 15% bracket)"
        elif jurisdiction == 'uk':
            allowance = self.UK_TAX_RATES['dividend_tax']['allowance']
            if dividend_amount <= allowance:
                return {
                    'dividend_amount': dividend_amount,
                    'tax_owed': 0,
                    'net_dividend': dividend_amount,
                    'tax_rate': 0,
                    'jurisdiction': jurisdiction,
                    'notes': f"Within £{allowance} dividend allowance - no tax"
                }
            tax_rate = self.UK_TAX_RATES['dividend_tax']['basic_rate']
            notes = f"UK dividend tax: 8.75% basic rate (after £{allowance} allowance)"
        else:
            tax_rate = 0.15
            notes = "International dividend withholding tax estimate"
        
        tax_owed = dividend_amount * tax_rate
        net_dividend = dividend_amount - tax_owed
        
        return {
            'dividend_amount': dividend_amount,
            'tax_owed': tax_owed,
            'net_dividend': net_dividend,
            'tax_rate': tax_rate,
            'jurisdiction': jurisdiction,
            'notes': notes
        }
    
    def get_tax_optimization_advice(self,
                                   positions: List[Dict],
                                   current_date: datetime = None) -> List[Dict[str, Any]]:
        """
        Analyze portfolio for tax optimization opportunities
        
        Args:
            positions: List of position dicts with purchase_date, current_price, avg_cost
            current_date: Current date (default: now)
        
        Returns:
            List of tax optimization recommendations
        """
        if current_date is None:
            current_date = datetime.now()
        
        recommendations = []
        
        for pos in positions:
            symbol = pos.get('symbol')
            purchase_date = pos.get('purchase_date')
            if isinstance(purchase_date, str):
                purchase_date = datetime.fromisoformat(purchase_date.replace('Z', '+00:00'))
            
            current_price = pos.get('current_price', 0)
            avg_cost = pos.get('average_cost', 0)
            quantity = pos.get('total_quantity', 0)
            
            holding_days = (current_date - purchase_date).days
            unrealized_gain = (current_price - avg_cost) * quantity
            
            # Check for long-term threshold opportunities (US)
            if self.default_jurisdiction == 'us' and 0 < unrealized_gain > 0:
                days_to_long_term = 365 - holding_days
                if 0 < days_to_long_term <= 30:
                    recommendations.append({
                        'symbol': symbol,
                        'type': 'hold_for_long_term',
                        'priority': 'high',
                        'message': f"💡 {symbol}: Hold {days_to_long_term} more days to qualify for long-term capital gains rate (15% vs 22%)",
                        'potential_tax_savings': unrealized_gain * 0.07,  # 7% savings
                        'days_remaining': days_to_long_term
                    })
            
            # Check for tax loss harvesting opportunities
            if unrealized_gain < -1000:  # Significant loss
                recommendations.append({
                    'symbol': symbol,
                    'type': 'tax_loss_harvesting',
                    'priority': 'medium',
                    'message': f"📉 {symbol}: Consider selling to harvest ${abs(unrealized_gain):.0f} tax loss (can offset other gains)",
                    'tax_loss_amount': abs(unrealized_gain),
                    'holding_days': holding_days
                })
            
            # Check for year-end tax planning
            days_to_year_end = (datetime(current_date.year, 12, 31) - current_date).days
            if days_to_year_end <= 60 and unrealized_gain < 0:
                recommendations.append({
                    'symbol': symbol,
                    'type': 'year_end_planning',
                    'priority': 'medium',
                    'message': f"📅 {symbol}: {days_to_year_end} days until year-end. Consider harvesting loss before Dec 31",
                    'days_to_year_end': days_to_year_end
                })
        
        return recommendations


# Global instance
_tax_calculator = None


def get_tax_calculator(jurisdiction: str = 'kenya') -> TaxCalculator:
    """Get or create tax calculator singleton"""
    global _tax_calculator
    if _tax_calculator is None:
        _tax_calculator = TaxCalculator(default_jurisdiction=jurisdiction)
    return _tax_calculator


if __name__ == "__main__":
    # Test tax calculator
    calc = TaxCalculator('kenya')
    
    print("\n🧪 Testing Tax Calculator\n")
    
    # Test 1: Kenya CGT
    purchase_date = datetime.now() - timedelta(days=200)
    result = calc.calculate_capital_gains_tax(
        purchase_price=150.0,
        sale_price=200.0,
        quantity=10,
        purchase_date=purchase_date,
        jurisdiction='kenya'
    )
    print(f"Kenya CGT Test:")
    print(f"  Gross gain: ${result['gross_gain']:.2f}")
    print(f"  Tax owed: ${result['tax_owed']:.2f} ({result['tax_rate']*100}%)")
    print(f"  Net gain: ${result['net_gain']:.2f}")
    print(f"  {result.get('recommendation', '')}\n")
    
    # Test 2: US CGT (short-term)
    purchase_date_short = datetime.now() - timedelta(days=180)
    result_us_short = calc.calculate_capital_gains_tax(
        purchase_price=150.0,
        sale_price=200.0,
        quantity=10,
        purchase_date=purchase_date_short,
        jurisdiction='us'
    )
    print(f"US Short-term CGT Test:")
    print(f"  Holding: {result_us_short['holding_period_days']} days")
    print(f"  Tax: ${result_us_short['tax_owed']:.2f} ({result_us_short['tax_rate']*100}%)")
    print(f"  💡 {result_us_short['recommendation']}\n")
    
    # Test 3: US CGT (long-term)
    purchase_date_long = datetime.now() - timedelta(days=400)
    result_us_long = calc.calculate_capital_gains_tax(
        purchase_price=150.0,
        sale_price=200.0,
        quantity=10,
        purchase_date=purchase_date_long,
        jurisdiction='us'
    )
    print(f"US Long-term CGT Test:")
    print(f"  Holding: {result_us_long['holding_period_days']} days")
    print(f"  Tax: ${result_us_long['tax_owed']:.2f} ({result_us_long['tax_rate']*100}%)")
    print(f"  💡 {result_us_long['recommendation']}\n")





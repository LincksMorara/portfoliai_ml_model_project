import re
import numpy as np
import pandas as pd

def parse_pct_midpoint(s: str) -> float:
    """
    Turn ranges like '10% - 20%' into midpoint, '20% and above' → base+5.
    NOTE: The TRAINING data has values as decimals (0.15, 0.25), but the MODELS 
    were trained with THIS function returning whole numbers (15, 25) and then 
    the scaler converts them. So we keep this as-is to match the trained models.
    """
    if pd.isna(s): return np.nan
    s = str(s).strip()
    nums = re.findall(r"(\d+\.?\d*)", s)
    if "above" in s.lower():
        return float(nums[0]) + 5.0 if nums else np.nan
    if len(nums) == 2:
        return (float(nums[0]) + float(nums[1])) / 2.0
    if len(nums) == 1:
        return float(nums[0])
    return np.nan

def map_horizon_to_years(s: str) -> float:
    """Convert textual horizons into approx. numeric years."""
    if pd.isna(s): return np.nan
    s = str(s).lower()
    if "more than 5" in s or "5+" in s or ">5" in s:
        return 7.0
    if "3" in s and "5" in s:
        return 4.0
    if "1" in s and "3" in s:
        return 2.0
    if "<1" in s or "less than 1" in s:
        return 0.5
    m = re.search(r"(\d+)", s)
    return float(m.group(1)) if m else np.nan

def map_monitoring_to_freq_per_month(s: str) -> float:
    """Map survey answers like 'Daily' → 30, 'Weekly' → 4."""
    if pd.isna(s): return np.nan
    s = str(s).lower()
    if "daily" in s: return 30.0
    if "weekly" in s: return 4.0
    if "monthly" in s: return 1.0
    if "quarter" in s: return 0.33
    return np.nan

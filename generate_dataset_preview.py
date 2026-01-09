#!/usr/bin/env python3
"""
Generate a formatted preview of the training dataset for screenshot purposes.
This creates an Excel file with the key columns formatted nicely.
"""

import pandas as pd
from pathlib import Path

def main():
    # Load the primary training dataset
    dataset_path = Path('data/processed/survey_with_scores_and_archetypes.csv')
    
    if not dataset_path.exists():
        print(f"❌ Error: {dataset_path} not found!")
        return
    
    print("📊 Loading dataset...")
    df = pd.read_csv(dataset_path)
    
    print(f"✅ Loaded: {len(df)} rows × {len(df.columns)} columns")
    
    # Select key columns for screenshot
    # Features (inputs)
    feature_cols = [
        'gender_male',
        'age',
        'education_level',
        'invest_prop_pct',
        'expected_return_pct',
        'horizon_years',
        'monitor_freq_per_month',
    ]
    
    # Target variables (outputs) - MOST IMPORTANT
    target_cols = [
        'survey_risk_score',  # Continuous risk score (0-1)
        'survey_archetype',   # Categorical: Conservative/Comfortable/Enthusiastic
        'risk_raw',           # Raw risk calculation
    ]
    
    # Combine and filter to only existing columns
    key_cols = [col for col in feature_cols + target_cols if col in df.columns]
    
    # Create preview (first 12 rows)
    preview = df[key_cols].head(12).copy()
    
    # Round numeric columns for cleaner display
    numeric_cols = preview.select_dtypes(include=['float64', 'int64']).columns
    for col in numeric_cols:
        if 'score' in col.lower() or 'pct' in col.lower():
            preview[col] = preview[col].round(3)
        else:
            preview[col] = preview[col].round(1)
    
    # Save to CSV (can be opened in Excel/Numbers)
    output_file = 'dataset_preview_for_screenshot.csv'
    print(f"\n💾 Saving preview to: {output_file}")
    
    preview.to_csv(output_file, index=False)
    
    print(f"✅ CSV file created: {output_file}")
    print(f"\n📸 Next steps:")
    print(f"   1. Open {output_file} in Excel/Numbers/Google Sheets")
    print(f"   2. Format header row (bold, freeze panes)")
    print(f"   3. Adjust column widths to fit content")
    print(f"   4. Take screenshot showing:")
    print(f"      - Header row with column names")
    print(f"      - 10-12 data rows")
    print(f"      - Key features + target variables (survey_risk_score, survey_archetype)")
    
    # Also print a text preview
    print(f"\n📋 Text Preview (first 5 rows):")
    print("=" * 100)
    print(preview.head(5).to_string(index=False))
    print("=" * 100)
    
    print(f"\n✨ Dataset Summary:")
    print(f"   Total Rows: {len(df):,}")
    print(f"   Total Columns: {len(df.columns)}")
    print(f"   Feature Columns Shown: {len(feature_cols)}")
    print(f"   Target Columns Shown: {len(target_cols)}")
    print(f"   Preview Rows: {len(preview)}")

if __name__ == '__main__':
    main()


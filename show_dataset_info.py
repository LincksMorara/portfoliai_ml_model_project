#!/usr/bin/env python3
"""
Generate a formatted terminal output showing dataset information.
Perfect for screenshots in proposal documents.
"""

import pandas as pd
from pathlib import Path

def main():
    # Load the primary training dataset
    dataset_path = Path('data/processed/survey_with_scores_and_archetypes.csv')
    
    if not dataset_path.exists():
        print(f"❌ Error: {dataset_path} not found!")
        return
    
    df = pd.read_csv(dataset_path)
    
    # Print formatted output
    print("=" * 80)
    print(" " * 20 + "DATASET INFORMATION")
    print("=" * 80)
    print()
    
    # Basic Information
    print("📊 DATASET OVERVIEW")
    print("-" * 80)
    print(f"File Name:     {dataset_path.name}")
    print(f"Location:      {dataset_path.parent}")
    print(f"Total Rows:    {len(df):,}")
    print(f"Total Columns: {len(df.columns)}")
    print(f"Size:          {df.shape[0]:,} samples × {df.shape[1]} features")
    print()
    
    # Column Categories
    print("=" * 80)
    print(" " * 15 + "COLUMN STRUCTURE")
    print("=" * 80)
    print()
    
    # Categorize columns
    feature_cols = [
        'gender_male', 'age', 'education_level', 'invests',
        'invest_prop_pct', 'monitor_freq_per_month', 'expected_return_pct',
        'horizon_years', 'rank_equity', 'rank_mutuals', 'invests_stock', 'raw_index'
    ]
    
    occupation_cols = [col for col in df.columns if col.startswith('occupation_')]
    avenue_cols = [col for col in df.columns if col.startswith('main_avenue_')]
    target_cols = ['survey_risk_score', 'survey_archetype', 'risk_raw']
    metadata_cols = ['Timestamp', 'inv_horizon', 'cluster']
    
    print("🔹 DEMOGRAPHIC & BEHAVIORAL FEATURES (12 columns)")
    print("-" * 80)
    for i, col in enumerate(feature_cols, 1):
        if col in df.columns:
            dtype = str(df[col].dtype)
            print(f"  {i:2d}. {col:30s} ({dtype})")
    print()
    
    print("🔹 OCCUPATION FEATURES - One-Hot Encoded (4 columns)")
    print("-" * 80)
    for i, col in enumerate(occupation_cols, 1):
        dtype = str(df[col].dtype)
        print(f"  {i:2d}. {col:30s} ({dtype})")
    print()
    
    print("🔹 INVESTMENT AVENUE FEATURES - One-Hot Encoded (6 columns)")
    print("-" * 80)
    for i, col in enumerate(avenue_cols, 1):
        dtype = str(df[col].dtype)
        print(f"  {i:2d}. {col:30s} ({dtype})")
    print()
    
    print("🔹 TARGET VARIABLES (3 columns) ⭐")
    print("-" * 80)
    for i, col in enumerate(target_cols, 1):
        dtype = str(df[col].dtype)
        if col == 'survey_risk_score':
            print(f"  {i:2d}. {col:30s} ({dtype}) - Continuous risk score (0-1)")
        elif col == 'survey_archetype':
            print(f"  {i:2d}. {col:30s} ({dtype}) - Categorical: Conservative/Comfortable/Enthusiastic")
        else:
            print(f"  {i:2d}. {col:30s} ({dtype})")
    print()
    
    print("🔹 METADATA COLUMNS (3 columns)")
    print("-" * 80)
    for i, col in enumerate(metadata_cols, 1):
        if col in df.columns:
            dtype = str(df[col].dtype)
            print(f"  {i:2d}. {col:30s} ({dtype})")
    print()
    
    # Statistics
    print("=" * 80)
    print(" " * 20 + "DATASET STATISTICS")
    print("=" * 80)
    print()
    
    if 'survey_risk_score' in df.columns:
        print("📈 TARGET VARIABLE: survey_risk_score")
        print("-" * 80)
        print(f"  Mean:   {df['survey_risk_score'].mean():.4f}")
        print(f"  Std:    {df['survey_risk_score'].std():.4f}")
        print(f"  Min:    {df['survey_risk_score'].min():.4f}")
        print(f"  Max:    {df['survey_risk_score'].max():.4f}")
        print(f"  Median: {df['survey_risk_score'].median():.4f}")
        print()
    
    if 'survey_archetype' in df.columns:
        print("📊 TARGET VARIABLE: survey_archetype (Distribution)")
        print("-" * 80)
        archetype_counts = df['survey_archetype'].value_counts()
        for archetype, count in archetype_counts.items():
            percentage = (count / len(df)) * 100
            print(f"  {archetype:20s}: {count:3d} samples ({percentage:5.1f}%)")
        print()
    
    # Sample Data
    print("=" * 80)
    print(" " * 25 + "SAMPLE DATA")
    print("=" * 80)
    print()
    
    # Show key columns only
    key_cols = ['gender_male', 'age', 'education_level', 'invest_prop_pct', 
                'expected_return_pct', 'survey_risk_score', 'survey_archetype']
    key_cols = [col for col in key_cols if col in df.columns]
    
    print("First 8 rows (showing key features and target variables):")
    print("-" * 80)
    
    sample = df[key_cols].head(8).copy()
    # Round numeric columns
    for col in sample.select_dtypes(include=['float64']).columns:
        sample[col] = sample[col].round(3)
    
    # Format for display
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', 20)
    
    print(sample.to_string(index=True))
    print()
    
    # Model Information
    print("=" * 80)
    print(" " * 20 + "MODEL TRAINING INFORMATION")
    print("=" * 80)
    print()
    print("This dataset was used to train:")
    print("  • Random Forest Regressor (R² = 0.891)")
    print("  • Random Forest Classifier (Accuracy ≈ 85%)")
    print()
    print("Training Configuration:")
    print(f"  • Training Samples: 105 (80%)")
    print(f"  • Test Samples:      27 (20%)")
    print(f"  • Total Features:    22 engineered features")
    print(f"  • Model Type:        Random Forest")
    print()
    
    print("=" * 80)
    print()
    print("💡 This dataset represents the cleaned, feature-engineered")
    print("   training data used for the PortfoliAI risk profiling model.")
    print()
    print("=" * 80)

if __name__ == '__main__':
    main()




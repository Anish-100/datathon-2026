import pandas as pd
import numpy as np

def load_data(filepath="ZipData.csv"):
    try:
        df = pd.read_csv(filepath)
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return pd.DataFrame()
    
    # Required columns for basic analysis
    required_cols = [
        "ZipCode", "City", "State", "Latitude", "Longitude",
        "TotalPopulation", "MedianHouseholdIncome", "MedianHomeValue",
        "MedianAge", "BusinessDeliveries", "ResidentialDeliveries",
        "EducationBachelorsDegree"
    ]
    
    # Keep only required columns that actually exist in the dataframe
    cols_to_use = [c for c in required_cols if c in df.columns]
    df = df[cols_to_use].copy()
    
    # Drop rows with missing lat/long or zeroes
    df = df.dropna(subset=['Latitude', 'Longitude'])
    df = df[(df['Latitude'] != 0) & (df['Longitude'] != 0)]
    
    return df

def score_locations(df: pd.DataFrame, params: dict):
    if df.empty:
        return df

    # Prepare normalized values for distance calculations
    # Target values
    t_income = params.get("target_median_income", 60000)
    t_age = params.get("target_median_age", 35)
    t_home = params.get("target_home_value", 300000)
    
    # Weights
    weights = params.get("importance_weights", {})
    w_income = weights.get("income", 0.2)
    w_age = weights.get("age", 0.2)
    w_home = weights.get("home_value", 0.2)
    w_comm = weights.get("commercial", 0.2)
    w_edu = weights.get("education", 0.2)
    
    # Feature Engineering
    # 1. Commercial Focus (ratio of business to residential) - simplified
    df['CommercialScore'] = 0.0
    if 'BusinessDeliveries' in df.columns and 'ResidentialDeliveries' in df.columns:
        total_del = df['BusinessDeliveries'] + df['ResidentialDeliveries']
        # Avoid division by zero
        df['CommercialRatio'] = np.where(total_del > 0, df['BusinessDeliveries'] / total_del, 0)
        max_cr = df['CommercialRatio'].max()
        if max_cr > 0:
             df['CommercialScore'] = df['CommercialRatio'] / max_cr

    # 2. Education Score (% of population with Bachelor's or higher)
    df['EducationScore'] = 0.0
    if 'EducationBachelorsDegree' in df.columns and 'TotalPopulation' in df.columns:
        df['EduRatio'] = np.where(df['TotalPopulation'] > 0, df['EducationBachelorsDegree'] / df['TotalPopulation'], 0)
        max_er = df['EduRatio'].max()
        if max_er > 0:
            df['EducationScore'] = df['EduRatio'] / max_er

    # 3. Target Distances (Income, Age, Home Value)
    # Using relative percentage difference, inverted (1 - diff) to become a score (higher is better matches target)
    
    def calculate_match_score(series, target):
        if target <= 0:
            return pd.Series(1.0, index=series.index)
        # Absolute relative difference
        diff = np.abs(series - target) / target
        # Cap difference at 1 (100% off), then invert so 0 diff = 1.0 score
        score = np.maximum(0, 1.0 - diff)
        return score
    
    df['IncomeScore'] = calculate_match_score(df.get('MedianHouseholdIncome', pd.Series(0, index=df.index)), t_income)
    df['AgeScore'] = calculate_match_score(df.get('MedianAge', pd.Series(0, index=df.index)), t_age)
    df['HomeScore'] = calculate_match_score(df.get('MedianHomeValue', pd.Series(0, index=df.index)), t_home)

    # Adjust base scores with boolean flags
    comm_focus = params.get("commercial_focus", False)
    high_edu = params.get("high_education_required", False)
    
    if comm_focus:
        # Boost commercial areas
        pass # The weight w_comm will handle its relative importance
    else:
        # Residential focus: invert commercial score
        df['CommercialScore'] = 1.0 - df['CommercialScore']
    
    if not high_edu:
        # If high education is not required, zero out its importance or weight
        w_edu = 0.0

    # Total Score
    total_weight = w_income + w_age + w_home + w_comm + w_edu
    if total_weight == 0:
        total_weight = 1.0 # fallback

    df['FinalScore'] = (
        (df['IncomeScore'] * w_income) +
        (df['AgeScore'] * w_age) +
        (df['HomeScore'] * w_home) +
        (df['CommercialScore'] * w_comm) +
        (df['EducationScore'] * w_edu)
    ) / total_weight

    # Scale to 0-100
    df['FinalScore'] = df['FinalScore'] * 100

    # Sort
    df = df.sort_values(by='FinalScore', ascending=False)
    
    return df

if __name__ == "__main__":
    df = load_data("ZipData.csv")
    print(f"Loaded {len(df)} zip codes.")
    params = {
      "target_median_income": 120000,
      "target_median_age": 30.0,
      "target_home_value": 800000,
      "commercial_focus": True,
      "high_education_required": True,
      "importance_weights": {
          "income": 0.3,
          "age": 0.2,
          "home_value": 0.1,
          "commercial": 0.2,
          "education": 0.2
      }
    }
    scored_df = score_locations(df, params)
    print(scored_df[['ZipCode', 'City', 'FinalScore']].head(5))

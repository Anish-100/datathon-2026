import pandas as pd

def filter_and_score_locations(df: pd.DataFrame, criteria: dict) -> pd.DataFrame:
    """
    Filters and scores zipcodes based on user slider parameters using the 
    merged demographics and financial datasets.
    """
    if df.empty:
        return pd.DataFrame()

    # Ensure numeric columns
    numeric_cols = [
        'Price Index', 'Median Household Income Last_12', 'Crime Data City Level (Arrest Disposition)', 
        'City Park Scores', 'Pop_Renters', 'Total_Pop_in_Units', 'Median_Year_Built', 
        'Avg_Household_Size', 'Home_Value_Median'
    ]
    
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Aggregate data by Zipcode
    agg_dict = {
        'City': 'first',
        'Price Index': 'mean',
        'Median Household Income Last_12': 'mean',
        'Crime Data City Level (Arrest Disposition)': 'mean',
        'City Park Scores': 'mean',
        'Pop_Renters': 'sum',
        'Total_Pop_in_Units': 'sum',
        'Median_Year_Built': 'mean',
        'Avg_Household_Size': 'mean',
        'Home_Value_Median': 'mean'
    }
    
    valid_agg_dict = {k: v for k, v in agg_dict.items() if k in df.columns}
    grouped = df.groupby('Zipcode').agg(valid_agg_dict).reset_index()

    # Derived Metrics
    if 'Pop_Renters' in grouped.columns and 'Total_Pop_in_Units' in grouped.columns:
        grouped['Renter Percentage'] = (grouped['Pop_Renters'] / grouped['Total_Pop_in_Units'].replace(0, 1)) * 100

    # Hard Filtering
    if 'Median Household Income Last_12' in grouped.columns:
        grouped = grouped[grouped['Median Household Income Last_12'] >= criteria.get('min_income', 0)]
    
    if 'Crime Data City Level (Arrest Disposition)' in grouped.columns:
        grouped = grouped[grouped['Crime Data City Level (Arrest Disposition)'] <= criteria.get('max_crime', 999999)]

    if grouped.empty:
        return grouped

    # Scoring Algorithm
    def normalize(series, reverse=False):
        min_val = series.min()
        max_val = series.max()
        if max_val == min_val:
            return pd.Series(1.0, index=series.index)
        normalized = (series - min_val) / (max_val - min_val)
        if reverse:
            return 1.0 - normalized
        return normalized

    scores = pd.Series(0.0, index=grouped.index)
    
    if 'Median Household Income Last_12' in grouped.columns:
        w_inc = criteria.get('focus_high_income', 0) / 10.0
        scores += normalize(grouped['Median Household Income Last_12']) * w_inc * 100
        
    if 'Home_Value_Median' in grouped.columns:
        w_price = criteria.get('focus_low_house_price', 0) / 10.0
        scores += normalize(grouped['Home_Value_Median'], reverse=True) * w_price * 100
    elif 'Price Index' in grouped.columns:
        w_price = criteria.get('focus_low_house_price', 0) / 10.0
        scores += normalize(grouped['Price Index'], reverse=True) * w_price * 100

    if 'City Park Scores' in grouped.columns:
        w_parks = criteria.get('importance_parks', 0) / 10.0
        scores += normalize(grouped['City Park Scores']) * w_parks * 100

    if 'Crime Data City Level (Arrest Disposition)' in grouped.columns:
        w_crime = criteria.get('focus_low_crime', 0) / 10.0
        scores += normalize(grouped['Crime Data City Level (Arrest Disposition)'], reverse=True) * w_crime * 100

    if 'Renter Percentage' in grouped.columns:
        w_renters = criteria.get('focus_renters', 0) / 10.0
        scores += normalize(grouped['Renter Percentage']) * w_renters * 100

    if 'Median_Year_Built' in grouped.columns:
        w_newer = criteria.get('focus_newer_devs', 0) / 10.0
        scores += normalize(grouped['Median_Year_Built']) * w_newer * 100
        
    if 'Avg_Household_Size' in grouped.columns:
        w_families = criteria.get('focus_families', 0) / 10.0
        scores += normalize(grouped['Avg_Household_Size']) * w_families * 100

    grouped['Viability Score'] = scores.round(1)
    
    result = grouped.sort_values(by='Viability Score', ascending=False)
    return result

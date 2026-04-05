import pandas as pd

def filter_and_score_locations(df: pd.DataFrame, criteria: dict) -> pd.DataFrame:
    """
    Filters and scores zipcodes based on user slider parameters using the 
    clean 'Orange_County_Home_Prices_Latest.csv'.
    """
    if df.empty:
        return pd.DataFrame()

    # Ensure numeric columns
    numeric_cols = ['Price Index', 'Median Household Income Last_12', 'Crime Data City Level (Arrest Disposition)', 
                   'Distance from Irvine Spectrum (km)']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # The new CSV is already aggregated/latest, but just in case we group by Zipcode
    agg_dict = {
        'City': 'first',
        'Price Index': 'mean',
        'Median Household Income Last_12': 'mean',
        'Crime Data City Level (Arrest Disposition)': 'mean',
        'Distance from Irvine Spectrum (km)': 'mean'
    }
    
    valid_agg_dict = {k: v for k, v in agg_dict.items() if k in df.columns}
    grouped = df.groupby('Zipcode').agg(valid_agg_dict).reset_index()

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
        
    if 'Price Index' in grouped.columns:
        w_price = criteria.get('focus_low_house_price', 0) / 10.0
        scores += normalize(grouped['Price Index'], reverse=True) * w_price * 100

    if 'Distance from Irvine Spectrum (km)' in grouped.columns:
        w_irvine = criteria.get('importance_irvine_proximity', 0) / 10.0
        scores += normalize(grouped['Distance from Irvine Spectrum (km)'], reverse=True) * w_irvine * 100

    grouped['Viability Score'] = scores.round(1)
    
    result = grouped.sort_values(by='Viability Score', ascending=False)
    return result

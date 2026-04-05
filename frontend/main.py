import streamlit as st
import pandas as pd
import pydeck as pdk
from pathlib import Path
import os
import sys

# Make sure we can import from Models
sys.path.append(str(Path(__file__).parent.parent))
from Models.main import filter_and_score_locations

# Set page config for a premium dashboard feel
st.set_page_config(page_title="Orange County Business Locations", layout="wide", page_icon="🍊")

# Custom CSS for better aesthetics
st.markdown("""
    <style>
    .main {
        background-color: #FAFAFA;
    }
    .stApp {
        font-family: 'Inter', 'Roboto', sans-serif;
    }
    h1, h2, h3 {
        color: #E65100; /* Orange County motif */
    }
    .stDataFrame {
        border-radius: 8px;
        border: 1px solid #e0e0e0;
    }
    .score-card {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
        border-left: 4px solid #E65100;
    }
    </style>
""", unsafe_allow_html=True)

# Datasets path
DATA_DIR = Path(__file__).parent.parent / "datasets"
API_DIR = Path(__file__).parent.parent / "API"

@st.cache_data
def load_housing_data():
    csv_path = DATA_DIR / "OCACS_2021_Housing_Characteristics_for_ZIP_Code_Tabulation_Areas.csv"
    if csv_path.exists():
        df = pd.read_csv(csv_path)
        # Rename INTPTLAT20 and INTPTLON20 to lat and lon for easy mapping
        if 'INTPTLAT20' in df.columns and 'INTPTLON20' in df.columns:
            df = df.rename(columns={'INTPTLAT20': 'lat', 'INTPTLON20': 'lon'})
            df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
            df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
        return df
    return pd.DataFrame()

@st.cache_data
def load_home_prices():
    csv_path = DATA_DIR / "Orange CountyHomePrices.csv"
    if csv_path.exists():
        # Large file, reading might take a moment
        return pd.read_csv(csv_path, low_memory=False)
    return pd.DataFrame()

@st.cache_data
def load_latest_home_prices():
    csv_path = API_DIR / "Orange_County_Home_Prices_Latest.csv"
    if csv_path.exists():
        return pd.read_csv(csv_path)
    return pd.DataFrame()

# Quick helper for zipcode coords since Orange CountyHomePrices lacks lat/lon directly
def get_zip_coords(housing_df):
    if not housing_df.empty and 'lat' in housing_df.columns and 'ZCTA5CE20' in housing_df.columns:
        coords = housing_df[['ZCTA5CE20', 'lat', 'lon']].copy()
        coords['Zipcode'] = pd.to_numeric(coords['ZCTA5CE20'], errors='coerce')
        return coords.drop(columns=['ZCTA5CE20']).dropna()
    return pd.DataFrame()

# Title
st.title("🍊 Orange County Optimal Business Locations")
st.markdown("Explore demographics, housing characteristics, and economic data across Orange County zip codes to discover the best locations for your business.")

# Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Select View:", [
    "Overview & Data Explorer", 
    "Geographical Map", 
    "Demographics & Economy", 
    "Business Location Predictor ✨"
])

st.sidebar.markdown("---")

housing_df = load_housing_data()
prices_df = load_home_prices()
latest_prices_df = load_latest_home_prices()

if page == "Overview & Data Explorer":
    st.header("Raw Data Explorer 🔍")
    st.write("Browse the datasets collected for the analysis. You can sort and search through the tables.")
    
    st.subheader("Housing Characteristics (2021 ZCTA)")
    if not housing_df.empty:
        st.dataframe(housing_df.head(500), use_container_width=True)
        st.caption(f"Total Rows: {len(housing_df)} | Showing first 500 rows")
    else:
        st.warning("Housing dataset not found.")
        
    st.markdown("---")
    
    st.subheader("Orange County Home Prices")
    if not prices_df.empty:
        st.dataframe(prices_df.head(500), use_container_width=True)
        st.caption(f"Total Rows: {len(prices_df)} | Showing first 500 rows")
    else:
        st.warning("Home prices dataset not found.")

elif page == "Geographical Map":
    st.header("Interactive Geographic Map 🗺️")
    st.write("Visualizing ZIP Code Tabulation Areas in Orange County.")
    
    if not housing_df.empty and 'lat' in housing_df.columns and 'lon' in housing_df.columns:
        map_df = housing_df.dropna(subset=['lat', 'lon'])
        st.markdown("### Basic Distribution")
        st.map(map_df, color="#E65100")
        
        st.markdown("### 🏢 Advanced Statistical Map: Housing & Economy")
        try:
            map_df['Zipcode'] = pd.to_numeric(map_df['ZCTA5CE20'], errors='coerce')
            avg_prices = prices_df.groupby('Zipcode')['Price Index'].mean().reset_index()
            merged_map_data = pd.merge(map_df, avg_prices, on='Zipcode', how='inner')
            
            prices_df['Income_Num'] = pd.to_numeric(prices_df['Median Household Income Last_12'], errors='coerce')
            avg_income = prices_df.groupby('Zipcode')['Income_Num'].mean().reset_index()
            merged_map_data = pd.merge(merged_map_data, avg_income, on='Zipcode', how='left')
            
            if not merged_map_data.empty:
                max_price = merged_map_data['Price Index'].max()
                merged_map_data['Elevation'] = (merged_map_data['Price Index'] / max_price) * 8000
                
                column_layer = pdk.Layer(
                    'ColumnLayer',
                    data=merged_map_data,
                    get_position='[lon, lat]',
                    get_elevation='Elevation',
                    elevation_scale=1,
                    radius=1000,
                    get_fill_color='[255, 180 - (Elevation/8000)*180, 0, 220]',
                    pickable=True,
                    auto_highlight=True,
                )
                
                view_state = pdk.ViewState(
                    latitude=33.74, longitude=-117.83, zoom=9, pitch=50, bearing=15
                )
                
                st.pydeck_chart(pdk.Deck(
                    map_style='mapbox://styles/mapbox/dark-v9',
                    layers=[column_layer], 
                    initial_view_state=view_state,
                    tooltip={"html": "<b>Zipcode:</b> {Zipcode}<br/><b>Avg Price Index:</b> ${Price Index}<br/><b>Avg Income:</b> ${Income_Num}"}
                ))
        except Exception as e:
            st.error(f"Error computing map: {e}")
    else:
        st.warning("No geographic coordinates found.")

elif page == "Demographics & Economy":
    st.header("Demographics & Economic Trends 📈")
    if not prices_df.empty:
        col1, col2 = st.columns(2)
        with col1:
            if 'Year' in prices_df.columns and 'Price Index' in prices_df.columns:
                yearly_prices = prices_df.groupby('Year')['Price Index'].mean().reset_index()
                st.subheader("Average Home Price Index")
                st.line_chart(yearly_prices.set_index('Year'), color="#E65100")
        with col2:
            if 'City' in prices_df.columns and 'Median Household Income Last_12' in prices_df.columns:
                st.subheader("Average Income by City")
                prices_df['Income_Num'] = pd.to_numeric(prices_df['Median Household Income Last_12'], errors='coerce')
                city_income = prices_df.groupby('City')['Income_Num'].mean().sort_values(ascending=False).head(15)
                st.bar_chart(city_income, color="#FFA726")
    else:
        st.warning("Home prices dataset not available.")

elif page == "Business Location Predictor ✨":
    st.header("Business Location Predictor 🎯")
    st.write("Use the sliders below to dial in the perfect parameters for your business. The model will calculate viability scores instantly.")
    
    st.markdown("### Location Parameters")
    
    col1, col2 = st.columns(2)
    with col1:
        min_inc = st.number_input("Minimum Neighborhood Household Income ($)", value=50000, step=5000)
        max_cr = st.number_input("Maximum Acceptable Crime Index (Lower is safer)", value=5000, step=500)
    with col2:
        irvine_prox = st.slider("Importance of Irvine Proximity (0-10)", 0, 10, 5)
        parks_prox = st.slider("Importance of City Parks Access (0-10)", 0, 10, 5)
    
    col3, col4 = st.columns(2)
    with col3:
        focus_inc = st.slider("Focus on High Income Areas (0-10)", 0, 10, 5)
        crime_focus = st.slider("Focus on Strict Low Crime (0-10)", 0, 10, 5)
    with col4:
        focus_cheap = st.slider("Focus on Affordable Real Estate (0-10)", 0, 10, 5)
        
    final_criteria = {
        "min_income": min_inc,
        "max_crime": max_cr,
        "importance_irvine_proximity": irvine_prox,
        "importance_parks": parks_prox,
        "focus_high_income": focus_inc,
        "focus_low_house_price": focus_cheap,
        "focus_low_crime": crime_focus
    }
    
    if st.button("Run Viability Model 🏆", use_container_width=True, type="primary"):
        if latest_prices_df.empty:
            st.error("The latest home pricing dataset is required but missing.")
        else:
            with st.spinner("Scoring locations across Orange County..."):
                results = filter_and_score_locations(latest_prices_df, final_criteria)
                
            if results.empty:
                st.warning("No areas matched your strict hard filters (e.g., minimum income or max crime). Try relaxing them.")
            else:
                st.markdown("### Top Recommended Locations")
                
                top_5 = results.head(5)
                
                cols = st.columns(3)
                for i, (idx, row) in enumerate(top_5.head(3).iterrows()):
                    c = cols[i]
                    c.markdown(f"""
                    <div class="score-card">
                        <h2 style="margin:0; font-size:24px;">#{i+1} {row['City']}</h2>
                        <p style="margin:5px 0;"><strong>Zipcode:</strong> {int(row['Zipcode'])}</p>
                        <p style="margin:5px 0; color:#E65100; font-weight:bold; font-size:18px;">Score: {row['Viability Score']}</p>
                        <p style="margin:5px 0; font-size:14px; color:#555;">Avg Income: ${row.get('Median Household Income Last_12', 0):,.0f}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                st.markdown("#### Full Viability Rankings")
                st.dataframe(results[['City', 'Zipcode', 'Viability Score', 'Median Household Income Last_12', 'Price Index', 'Crime Data City Level (Arrest Disposition)', 'Distance from Irvine Spectrum (km)', 'City Park Scores']], use_container_width=True)

                # Heatmap rendering
                st.markdown("### Viability Heatmap 🔥")
                coords = get_zip_coords(housing_df)
                if not coords.empty:
                    heatmap_data = pd.merge(coords, results, on='Zipcode', how='inner')
                    if not heatmap_data.empty:
                        max_score = heatmap_data['Viability Score'].max()
                        heatmap_data['Weight'] = heatmap_data['Viability Score'] / max_score if max_score > 0 else 1.0
                        
                        layer = pdk.Layer(
                            "HeatmapLayer",
                            heatmap_data,
                            opacity=0.9,
                            get_position=['lon', 'lat'],
                            threshold=0.1,
                            get_weight="Weight",
                            radiusPixels=50,
                        )
                        
                        view_state = pdk.ViewState(latitude=33.74, longitude=-117.83, zoom=9)
                        
                        st.pydeck_chart(pdk.Deck(
                            layers=[layer],
                            initial_view_state=view_state,
                            map_style='mapbox://styles/mapbox/light-v9'
                        ))
                    else:
                        st.info("Geographic visualization unavailable. Ensure ZCTA coordinates exist.")

import streamlit as st
import pandas as pd
import pydeck as pdk
from pathlib import Path
import os

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
    </style>
""", unsafe_allow_html=True)

# Datasets path
DATA_DIR = Path(__file__).parent.parent / "datasets"

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

# Title
st.title("🍊 Orange County Optimal Business Locations")
st.markdown("Explore demographics, housing characteristics, and economic data across Orange County zip codes to discover the best locations for your business.")

# Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Select View:", ["Overview & Data Explorer", "Geographical Map", "Demographics & Economy"])

st.sidebar.markdown("---")
st.sidebar.info("This dashboard visualizes messy raw datasets. As the data analysis pipeline progresses, these views will become more streamlined.")

housing_df = load_housing_data()
prices_df = load_home_prices()

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
    
    # We will use PyDeck for a premium, dynamic feel
    if not housing_df.empty and 'lat' in housing_df.columns and 'lon' in housing_df.columns:
        # Filter out NaN coordinates just in case
        map_df = housing_df.dropna(subset=['lat', 'lon'])
        
        st.markdown("### Basic Distribution")
        st.map(map_df, color="#E65100")
        
        st.markdown("### 🏢 Advanced Statistical Map: Housing & Economy")
        st.write("This map unifies ZCTA Housing characteristics with Orange County Home Prices to compute a dynamic 3D visual. Height portrays average Home Prices, combining both datasets.")
        
        try:
            # 1. Clean the ZCTA data
            # Ensure ZCTA is numeric to merge with prices
            map_df['Zipcode'] = pd.to_numeric(map_df['ZCTA5CE20'], errors='coerce')
            
            # 2. Extract aggregate home prices by Zipcode
            avg_prices = prices_df.groupby('Zipcode')['Price Index'].mean().reset_index()
            
            # 3. Merge Datasets
            merged_map_data = pd.merge(map_df, avg_prices, on='Zipcode', how='inner')
            
            # We also try to extract median income
            prices_df['Income_Num'] = pd.to_numeric(prices_df['Median Household Income Last_12'], errors='coerce')
            avg_income = prices_df.groupby('Zipcode')['Income_Num'].mean().reset_index()
            merged_map_data = pd.merge(merged_map_data, avg_income, on='Zipcode', how='left')
            
            if not merged_map_data.empty:
                max_price = merged_map_data['Price Index'].max()
                # Normalize elevation
                merged_map_data['Elevation'] = (merged_map_data['Price Index'] / max_price) * 8000
                
                # Construct Complex PyDeck Layer
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
                    latitude=33.74, 
                    longitude=-117.83, 
                    zoom=9, 
                    pitch=50,
                    bearing=15
                )
                
                st.pydeck_chart(pdk.Deck(
                    map_style='mapbox://styles/mapbox/dark-v9',
                    layers=[column_layer], 
                    initial_view_state=view_state,
                    tooltip={"html": "<b>Zipcode:</b> {Zipcode}<br/><b>Avg Price Index:</b> ${Price Index}<br/><b>Avg Income:</b> ${Income_Num}"}
                ))
            else:
                st.warning("Insufficient matching Zipcode data between the datasets to render.")
        except Exception as e:
            st.error(f"Error computing complex statistical map: {e}")
    else:
        st.warning("No geographic coordinates found in the dataset.")

elif page == "Demographics & Economy":
    st.header("Demographics & Economic Trends 📈")
    st.write("Analyze insights such as historic home prices or crime data over time.")
    
    if not prices_df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            if 'Year' in prices_df.columns and 'Price Index' in prices_df.columns:
                yearly_prices = prices_df.groupby('Year')['Price Index'].mean().reset_index()
                st.subheader("Average Home Price Index (Over Time)")
                st.line_chart(yearly_prices.set_index('Year'), color="#E65100")
                
        with col2:
            if 'City' in prices_df.columns and 'Median Household Income Last_12' in prices_df.columns:
                st.subheader("Average Income by City")
                try:
                    # Clean income string conversion
                    prices_df['Income_Num'] = pd.to_numeric(prices_df['Median Household Income Last_12'], errors='coerce')
                    city_income = prices_df.groupby('City')['Income_Num'].mean().sort_values(ascending=False).head(15)
                    st.bar_chart(city_income, color="#FFA726")
                except Exception as e:
                    st.write("Could not parse income data.")
        
        st.markdown("---")
        st.subheader("Distance Insights")
        if 'Distance from Disneyland (km)' in prices_df.columns and 'Distance to Nearest Beach (Km)' in prices_df.columns:
            st.write("Comparing distance from Disneyland vs distance to the Nearest Beach for listed areas.")
            dist_df = prices_df[['Distance from Disneyland (km)', 'Distance to Nearest Beach (Km)']].dropna().head(1000)
            
            st.scatter_chart(
                data=dist_df,
                x='Distance from Disneyland (km)',
                y='Distance to Nearest Beach (Km)',
                color="#FF7043"
            )
            
    else:
        st.warning("Home prices dataset not available to plot trends.")

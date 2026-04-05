import streamlit as st
import pandas as pd
import pydeck as pdk
from pathlib import Path
import os
import sys
import json
import re

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
    csv_path = API_DIR / "OC_Housing_Detailed_Cleaned.csv"
    if csv_path.exists():
        df = pd.read_csv(csv_path)
        # Rename columns to match what `get_zip_coords` down the line expects
        if 'Latitude' in df.columns and 'Longitude' in df.columns and 'Zip_Code' in df.columns:
            df = df.rename(columns={'Latitude': 'lat', 'Longitude': 'lon', 'Zip_Code': 'ZCTA5CE20'})
            df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
            df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
        return df
    return pd.DataFrame()

@st.cache_data
def load_raw_housing_data():
    csv_path = DATA_DIR / "Newest_with_headers_OCACS_2021_Housing_Characteristics_for_ZIP_Code_Tabulation_Areas copy.csv"
    if csv_path.exists():
        return pd.read_csv(csv_path)
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

# ── AI Parameter Extraction ─────────────────────────────────────────────────
AI_SYSTEM_PROMPT = """
You are a business location analytics assistant for Orange County, California.
Your job is to read a user's business description and return ONLY a JSON object
(no markdown, no explanation, no code fences) with exactly these 9 keys:

  min_income        : integer, min household income floor in dollars (e.g. 45000)
  max_crime         : integer, max acceptable crime index (e.g. 4000)
  focus_high_income : integer 0-10, importance of high-income customers
  focus_low_crime   : integer 0-10, importance of low crime rate
  focus_low_house_price : integer 0-10, importance of affordable real estate / rent
  importance_parks  : integer 0-10, importance of parks & walkable amenities
  focus_renters     : integer 0-10, importance of high renter population
  focus_newer_devs  : integer 0-10, importance of newer/modern developments
  focus_families    : integer 0-10, importance of large family households

After the JSON block, on a new line starting with "REASON:", write 1-2 sentences
explaining your parameter choices in plain English.

EXAMPLE OUTPUT:
{"min_income": 60000, "max_crime": 3000, "focus_high_income": 8, "focus_low_crime": 7,
 "focus_low_house_price": 3, "importance_parks": 5, "focus_renters": 4,
 "focus_newer_devs": 6, "focus_families": 3}
REASON: Targeting affluent professionals who value safety and modern environments.
"""

def ask_ai_for_parameters(user_prompt: str):
    """
    Calls the Gemini API and parses the returned JSON into a criteria dict.
    Returns (criteria_dict, reason_str) or raises an exception.
    """
    from dotenv import load_dotenv
    from google import genai
    from google.genai import types

    # Explicitly resolve .env from project root regardless of Streamlit's cwd
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(dotenv_path=env_path)
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in .env file. Make sure you created the .env file in the project root.")

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=AI_SYSTEM_PROMPT,
        ),
    )

    raw = response.text.strip()

    # Extract the JSON block (everything from first { to last })
    json_match = re.search(r'\{.*?\}', raw, re.DOTALL)
    if not json_match:
        raise ValueError(f"AI did not return valid JSON. Response:\n{raw}")
    params = json.loads(json_match.group())

    # Extract the REASON line if present
    reason = ""
    reason_match = re.search(r'REASON:\s*(.+)', raw, re.IGNORECASE | re.DOTALL)
    if reason_match:
        reason = reason_match.group(1).strip()

    # Validate and clamp all slider values to [0, 10]
    slider_keys = [
        "focus_high_income", "focus_low_crime", "focus_low_house_price",
        "importance_parks", "focus_renters", "focus_newer_devs", "focus_families"
    ]
    for k in slider_keys:
        params[k] = max(0, min(10, int(params.get(k, 5))))
    params["min_income"] = max(0, int(params.get("min_income", 50000)))
    params["max_crime"] = max(0, int(params.get("max_crime", 5000)))

    return params, reason

# Title
st.title("Orange County Optimal Business Locations")
st.markdown("Explore demographics, housing characteristics, and economic data across Orange County zip codes to discover the best locations for your business.")

# Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Select View:", [
    "Overview & Data Explorer", 
    "Geographical Map", 
    "Demographics & Economy", 
    "Business Location Predictor"
])

st.sidebar.markdown("---")

raw_housing_df = load_raw_housing_data()
housing_df = load_housing_data()
prices_df = load_home_prices()
latest_prices_df = load_latest_home_prices()

if page == "Overview & Data Explorer":
    st.header("Data Explorer (Raw vs Clean)")
    st.write("Explore the original raw datasets and compare them against their cleaned counterparts extracted via the API folder.")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "Raw Census (OCACS 2021)",
        "Cleaned Housing Characteristics",
        "Raw Home Prices (Full History)",
        "Cleaned Home Prices (Latest)"
    ])
    
    with tab1:
        st.subheader("Raw Census Export (OCACS 2021)")
        if not raw_housing_df.empty:
            st.dataframe(raw_housing_df.head(500), use_container_width=True)
            st.caption(f"Total Rows: {len(raw_housing_df)} | Showing first 500 rows")
        else:
            st.warning("Raw housing dataset not found.")
            
    with tab2:
        st.subheader("Clean Geo-Mapped Data")
        if not housing_df.empty:
            st.dataframe(housing_df.head(500), use_container_width=True)
            st.caption(f"Total Rows: {len(housing_df)} | Showing first 500 rows")
        else:
            st.warning("Clean housing dataset not found.")

    with tab3:
        st.subheader("Raw Economic Timelines (Home Prices)")
        if not prices_df.empty:
            st.dataframe(prices_df.head(500), use_container_width=True)
            st.caption(f"Total Rows: {len(prices_df)} | Showing first 500 rows")
        else:
            st.warning("Home prices dataset not found.")
            
    with tab4:
        st.subheader("Cleaned Financial Machine Learning File")
        if not latest_prices_df.empty:
            st.dataframe(latest_prices_df.head(500), use_container_width=True)
            st.caption(f"Total Rows: {len(latest_prices_df)} | Showing first 500 rows")
        else:
            st.warning("Latest clean prices dataset not found.")

elif page == "Geographical Map":
    st.header("Interactive Geographic Map")
    st.write("Visualizing ZIP Code Tabulation Areas in Orange County.")
    
    if not housing_df.empty and 'lat' in housing_df.columns and 'lon' in housing_df.columns:
        map_df = housing_df.dropna(subset=['lat', 'lon'])
        st.markdown("### Basic Distribution")
        st.map(map_df, color="#E65100")
        
        st.markdown("### Advanced Statistical Map: Housing & Economy")
        try:
            map_df['Zipcode'] = pd.to_numeric(map_df['ZCTA5CE20'], errors='coerce')
            avg_prices = latest_prices_df.groupby('Zipcode')['Price Index'].mean().reset_index()
            merged_map_data = pd.merge(map_df, avg_prices, on='Zipcode', how='inner')
            
            latest_prices_df['Income_Num'] = pd.to_numeric(latest_prices_df['Median Household Income Last_12'], errors='coerce')
            avg_income = latest_prices_df.groupby('Zipcode')['Income_Num'].mean().reset_index()
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
                    map_style='dark',
                    layers=[column_layer], 
                    initial_view_state=view_state,
                    tooltip={"html": "<b>Zipcode:</b> {Zipcode}<br/><b>Avg Price Index:</b> ${Price Index}<br/><b>Avg Income:</b> ${Income_Num}"}
                ))
        except Exception as e:
            st.error(f"Error computing map: {e}")
    else:
        st.warning("No geographic coordinates found.")

elif page == "Demographics & Economy":
    st.header("Clean Demographics & Economic Trends")
    if not latest_prices_df.empty:
        col1, col2 = st.columns(2)
        with col1:
            if 'City' in latest_prices_df.columns and 'City Park Scores' in latest_prices_df.columns:
                st.subheader("City Park Accessibility Scores")
                latest_prices_df['Park_Num'] = pd.to_numeric(latest_prices_df['City Park Scores'], errors='coerce')
                city_parks = latest_prices_df.groupby('City')['Park_Num'].mean().sort_values(ascending=False).head(15)
                st.bar_chart(city_parks, color="#2E7D32")
        with col2:
            if 'City' in latest_prices_df.columns and 'Median Household Income Last_12' in latest_prices_df.columns:
                st.subheader("Average Income by City (Cleaned)")
                latest_prices_df['Income_Num'] = pd.to_numeric(latest_prices_df['Median Household Income Last_12'], errors='coerce')
                city_income = latest_prices_df.groupby('City')['Income_Num'].mean().sort_values(ascending=False).head(15)
                st.bar_chart(city_income, color="#FFA726")
                
        if 'City' in latest_prices_df.columns and 'Crime Data City Level (Arrest Disposition)' in latest_prices_df.columns:
            st.subheader("Lowest Crime Indexes by City")
            latest_prices_df['Crime_Num'] = pd.to_numeric(latest_prices_df['Crime Data City Level (Arrest Disposition)'], errors='coerce')
            city_crime = latest_prices_df.groupby('City')['Crime_Num'].mean().sort_values(ascending=True).head(20)
            st.bar_chart(city_crime, color="#1565C0")
    else:
        st.warning("Clean latest home prices dataset not available.")

elif page == "Business Location Predictor":
    st.header("Business Location Predictor")

    # ── Session state defaults ───────────────────────────────────────────────
    PARAM_DEFAULTS = {
        "min_income": 50000,
        "max_crime": 5000,
        "focus_high_income": 5,
        "focus_low_crime": 5,
        "focus_low_house_price": 5,
        "importance_parks": 5,
        "focus_renters": 5,
        "focus_newer_devs": 5,
        "focus_families": 5,
        "ai_reason": "",
        "ai_set": False,
    }
    for k, v in PARAM_DEFAULTS.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # ── AI Prompt Section ────────────────────────────────────────────────────
    st.markdown("""
    <div style="background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%);
                border-left: 4px solid #E65100; border-radius: 8px;
                padding: 1.2rem 1.4rem; margin-bottom: 1.5rem;">
        <h3 style="margin:0 0 0.3rem 0; color:#E65100;">✨ Describe Your Business</h3>
        <p style="margin:0; color:#555; font-size:14px;">
            Tell the AI what kind of business you're opening and who your customers are.
            It will automatically tune all parameters below to match your needs.
        </p>
    </div>
    """, unsafe_allow_html=True)

    ai_prompt = st.text_area(
        label="Business description",
        placeholder='e.g. "I want to open a premium coffee shop targeting young professionals and remote workers who value walkable, modern neighborhoods."',
        height=100,
        label_visibility="collapsed",
        key="ai_prompt_input",
    )

    ai_col1, ai_col2 = st.columns([2, 5])
    with ai_col1:
        ask_ai_clicked = st.button("Ask AI to Set Parameters", type="primary", use_container_width=True)
    with ai_col2:
        if st.button("Reset to Defaults", use_container_width=True):
            for k, v in PARAM_DEFAULTS.items():
                st.session_state[k] = v
            st.rerun()

    if ask_ai_clicked:
        if not ai_prompt.strip():
            st.warning("Please enter a business description first.")
        else:
            with st.spinner("AI is analyzing your business and tuning parameters..."):
                try:
                    params, reason = ask_ai_for_parameters(ai_prompt.strip())
                    # Write all params into session state
                    for k, v in params.items():
                        st.session_state[k] = v
                    st.session_state["ai_reason"] = reason
                    st.session_state["ai_set"] = True
                    st.rerun()
                except Exception as e:
                    err = str(e)
                    if "429" in err or "RESOURCE_EXHAUSTED" in err or "quota" in err.lower():
                        st.error(
                            "**API Quota Exhausted.** Your Gemini API key has hit its free-tier limit.\n\n"
                            "**Fix:** Go to [aistudio.google.com](https://aistudio.google.com), generate a new API key "
                            "(use a different Google account if needed), and update `GEMINI_API_KEY` in your `.env` file."
                        )
                    elif "GEMINI_API_KEY" in err:
                        st.error("**Missing API Key.** Add `GEMINI_API_KEY=your_key` to the `.env` file in the project root.")
                    else:
                        st.error(f"AI parameter extraction failed: {e}")

    # Show AI reasoning banner if parameters were just set
    if st.session_state.get("ai_set") and st.session_state.get("ai_reason"):
        st.success(f"**AI Parameter Reasoning:** {st.session_state['ai_reason']}")

    st.markdown("---")

    # ── Parameter Sliders (driven by session_state) ──────────────────────────
    st.markdown("### Location Parameters")
    if st.session_state.get("ai_set"):
        st.caption("Parameters below were set by AI — you can still adjust any slider before running.")

    col1, col2 = st.columns(2)
    with col1:
        min_inc = st.number_input(
            "Minimum Neighborhood Household Income ($)",
            value=st.session_state["min_income"],
            step=5000,
            key="num_min_income",
        )
        max_cr = st.number_input(
            "Maximum Acceptable Crime Index (Lower is safer)",
            value=st.session_state["max_crime"],
            step=500,
            key="num_max_crime",
        )
        focus_inc = st.slider(
            "Focus on High Income Areas (0-10)", 0, 10,
            value=st.session_state["focus_high_income"],
            key="sl_focus_high_income",
        )
        crime_focus = st.slider(
            "Focus on Strict Low Crime (0-10)", 0, 10,
            value=st.session_state["focus_low_crime"],
            key="sl_focus_low_crime",
        )
    with col2:
        focus_cheap = st.slider(
            "Focus on Affordable Real Estate (0-10)", 0, 10,
            value=st.session_state["focus_low_house_price"],
            key="sl_focus_low_house_price",
        )
        parks_prox = st.slider(
            "Importance of City Parks (0-10)", 0, 10,
            value=st.session_state["importance_parks"],
            key="sl_importance_parks",
        )
        focus_renters = st.slider(
            "Focus on High Renter Population (0-10)", 0, 10,
            value=st.session_state["focus_renters"],
            key="sl_focus_renters",
        )
        focus_newer = st.slider(
            "Focus on Newer Developments (0-10)", 0, 10,
            value=st.session_state["focus_newer_devs"],
            key="sl_focus_newer_devs",
        )
        focus_family = st.slider(
            "Focus on Large Families (0-10)", 0, 10,
            value=st.session_state["focus_families"],
            key="sl_focus_families",
        )

    final_criteria = {
        "min_income": min_inc,
        "max_crime": max_cr,
        "focus_high_income": focus_inc,
        "focus_low_crime": crime_focus,
        "focus_low_house_price": focus_cheap,
        "importance_parks": parks_prox,
        "focus_renters": focus_renters,
        "focus_newer_devs": focus_newer,
        "focus_families": focus_family,
    }

    if st.button("Run Viability Model", use_container_width=True, type="primary"):
        if latest_prices_df.empty:
            st.error("The latest home pricing dataset is required but missing.")
        else:
            with st.spinner("Scoring locations across Orange County..."):
                if not housing_df.empty:
                    merged_df = pd.merge(latest_prices_df, housing_df, left_on='Zipcode', right_on='ZCTA5CE20', how='inner')
                else:
                    merged_df = latest_prices_df
                results = filter_and_score_locations(merged_df, final_criteria)

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
                display_cols = ['City', 'Zipcode', 'Viability Score']
                for col in ['Median Household Income Last_12', 'Crime Data City Level (Arrest Disposition)', 'Home_Value_Median', 'City Park Scores', 'Renter Percentage', 'Median_Year_Built', 'Avg_Household_Size']:
                    if col in results.columns:
                        display_cols.append(col)
                st.dataframe(results[display_cols], use_container_width=True)

                # Heatmap rendering
                st.markdown("### Viability Heatmap")
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
                            map_style='dark'
                        ))
                    else:
                        st.info("Geographic visualization unavailable. Ensure ZCTA coordinates exist.")

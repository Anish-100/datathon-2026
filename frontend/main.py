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
    Calls the Groq API (llama-3.3-70b-versatile) and parses the returned JSON
    into a criteria dict. Returns (criteria_dict, reason_str) or raises.
    """
    from dotenv import load_dotenv
    from groq import Groq

    # Explicitly resolve .env from project root regardless of Streamlit's cwd
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(dotenv_path=env_path, override=True)
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in .env file. Add it as: GROQ_API_KEY=gsk_...")

    client = Groq(api_key=api_key)
    chat = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": AI_SYSTEM_PROMPT},
            {"role": "user",   "content": user_prompt},
        ],
        temperature=0.3,
    )

    raw = chat.choices[0].message.content.strip()

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
    "Business Location Predictor",
    "RSM Consumer Predictor"
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

    # Map AI param keys → widget keys (they must match for session_state to drive the widget)
    PARAM_TO_WIDGET_KEY = {
        "min_income": "min_income",
        "max_crime": "max_crime",
        "focus_high_income": "focus_high_income",
        "focus_low_crime": "focus_low_crime",
        "focus_low_house_price": "focus_low_house_price",
        "importance_parks": "importance_parks",
        "focus_renters": "focus_renters",
        "focus_newer_devs": "focus_newer_devs",
        "focus_families": "focus_families",
    }

    # ── AI Prompt Section ────────────────────────────────────────────────────
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
            st.session_state["ai_set"] = False
            st.session_state["ai_reason"] = ""
            st.rerun()

    if ask_ai_clicked:
        if not ai_prompt.strip():
            st.warning("Please enter a business description first.")
        else:
            with st.spinner("AI is analyzing your business and tuning parameters..."):
                try:
                    params, reason = ask_ai_for_parameters(ai_prompt.strip())
                    # Write params into session state using widget keys so
                    # Streamlit picks them up properly on rerun
                    for param_key, widget_key in PARAM_TO_WIDGET_KEY.items():
                        if param_key in params:
                            st.session_state[widget_key] = params[param_key]
                    st.session_state["ai_reason"] = reason
                    st.session_state["ai_set"] = True
                    st.rerun()
                except Exception as e:
                    err = str(e)
                    if "rate_limit" in err.lower() or "429" in err or "quota" in err.lower():
                        st.error(
                            "**Groq Rate Limit Hit.** Wait a few seconds and try again — "
                            "Groq free tier allows ~30 requests/minute."
                        )
                    elif "GROQ_API_KEY" in err:
                        st.error(
                            "**Missing Groq API Key.** Go to [console.groq.com](https://console.groq.com), "
                            "create an API key, and add `GROQ_API_KEY=gsk_...` to your `.env` file."
                        )
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
        # Using the session_state key as the widget key (no separate value=)
        # so that writing to st.session_state[key] before st.rerun() takes effect.
        min_inc = st.number_input(
            "Minimum Neighborhood Household Income ($)",
            min_value=0,
            step=5000,
            key="min_income",
        )
        max_cr = st.number_input(
            "Maximum Acceptable Crime Index (Lower is safer)",
            min_value=0,
            step=500,
            key="max_crime",
        )
        focus_inc = st.slider(
            "Focus on High Income Areas (0-10)", 0, 10,
            key="focus_high_income",
        )
        crime_focus = st.slider(
            "Focus on Strict Low Crime (0-10)", 0, 10,
            key="focus_low_crime",
        )
    with col2:
        focus_cheap = st.slider(
            "Focus on Affordable Real Estate (0-10)", 0, 10,
            key="focus_low_house_price",
        )
        parks_prox = st.slider(
            "Importance of City Parks (0-10)", 0, 10,
            key="importance_parks",
        )
        focus_renters = st.slider(
            "Focus on High Renter Population (0-10)", 0, 10,
            key="focus_renters",
        )
        focus_newer = st.slider(
            "Focus on Newer Developments (0-10)", 0, 10,
            key="focus_newer_devs",
        )
        focus_family = st.slider(
            "Focus on Large Families (0-10)", 0, 10,
            key="focus_families",
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

# ── RSM Consumer Predictor ──────────────────────────────────────────────────
elif page == "RSM Consumer Predictor":
    import ast
    import sys as _sys
    from pathlib import Path as _Path

    # Ensure root is on sys.path so we can import API.*
    _root = str(_Path(__file__).parent.parent)
    if _root not in _sys.path:
        _sys.path.insert(0, _root)

    import API.api as _api
    from API.Prediction import melissa_prediction as _mp
    from API.Prediction import closest_commerical_zone as _ccz

    _RSM_PROMPT = """
Based on the business idea proposed, modify these traits where Y is yes N is No.
 This is based in rancho santa margarita, so take that in concern when creating your values.
You will create a a list of 9 tuples, the first of each tuple will be specificed below also with tags of what it should look like.
The second of each tuple will be the weight you think will apply to each tuple out of 100.
The more important these core ideas are to the business idea, the higher weightage they should get out of 100. 
('Y', 0.0),    # dog_owner
('N', 0.0),    # cat_owner
(9, 80.0),     # net_worth
('Y', 50.0),   # cc_user
(2, 20.0),     # vehicle_count
('O', 30.0),   # owner_renter
(3, 15.0),     # household_size
(1, 10.0),     # num_children
('Y', 0.0),    # home_improvement_diy
Ensure no special symbols like %/^&*@!
Return them in this order only.
Return a list of these tuples in Python, and nothing else. 
"""

    _RSM_PROMPT_2 = """
dog_owner: Compares dog-owner flag ('Y'/'N') against the RSM ZIP code's mode.

cat_owner: Compares cat-owner flag ('Y'/'N') against the RSM ZIP code's mode.

net_worth: Compares net worth code (1-9) against the RSM ZIP code's median code. 1=<$1, 2=$1-4.9k, 3=$5-14.9k, 4=$15-24.9k, 5=$25-49.9k, 6=$50-99.9k, 7=$100-249.9k, 8=$250-499.9k, 9=$500k+

cc_user: Compares credit card user flag ('Y'/'N') against the RSM ZIP code's mode.

vehicle_count: Compares number of registered vehicles per household against the RSM ZIP code's median. RSM is car-dependent; 2-3 vehicles per household is typical.

owner_renter: Compares owner/renter flag ('O'/'R') against the RSM ZIP code's mode. 92688 ~71% owners, 92679 ~91% owners.

household_size: Compares household size (integer count) against the RSM ZIP code's average. 92688 ~2.87, 92679 ~2.99 — both lean family-sized.

num_children: Compares number of children (integer count) against the RSM ZIP code's average. RSM is family-oriented; typical range is 1-2 children per household.

home_improvement_diy: Compares home-improvement DIY flag ('Y'/'N') against the RSM ZIP code's mode.
"""

    st.header("RSM Consumer Predictor")
    st.markdown(
        "Describe your business idea and the AI will score every consumer coordinate in "
        "Rancho Santa Margarita, identify the best-fit locations, and find the nearest "
        "commercial zone to those hot-spots."
    )

    rsm_prompt_input = st.text_area(
        "Business description",
        placeholder='e.g. "A premium pet grooming salon for affluent dog owners in RSM."',
        height=110,
        key="rsm_prompt_input",
    )

    run_rsm = st.button("Run RSM Prediction", type="primary", use_container_width=True)

    if run_rsm:
        if not rsm_prompt_input.strip():
            st.warning("Please enter a business description first.")
        else:
            # ── Step 1: Ask Gemini to build the parameter list ────────────────
            with st.spinner("Step 1/3 — AI is building your parameter tuple list..."):
                try:
                    full_prompt = rsm_prompt_input.strip() + _RSM_PROMPT + _RSM_PROMPT_2
                    raw_query = _api.main(prompt=full_prompt)
                    pairs = ast.literal_eval(raw_query.strip())
                    st.success(f"✅ AI generated {len(pairs)} parameter tuples.")
                    with st.expander("View raw parameter tuples"):
                        st.code(str(pairs), language="python")
                except Exception as e:
                    st.error(f"AI parameter generation failed: {e}")
                    st.stop()

            # ── Step 2: Score all consumer coordinates ────────────────────────
            with st.spinner("Step 2/3 — Scoring all RSM consumer coordinates (this may take a moment)..."):
                try:
                    _mp.main(pairs)
                    st.success("✅ Viability scores computed and saved.")
                except Exception as e:
                    st.error(f"Scoring failed: {e}")
                    st.stop()

            # ── Step 3: Parse pretty_text.txt → DataFrame ─────────────────────
            pretty_path = _Path(__file__).parent.parent / "API" / "Prediction" / "pretty_text.txt"
            raw2_path   = _Path(__file__).parent.parent / "API" / "Prediction" / "raw_text_2.txt"

            rows_rsm = []
            if pretty_path.exists():
                with open(pretty_path, "r") as _f:
                    for line in _f.readlines()[1:]:  # skip header
                        m = re.match(r"\(([^,]+),\s*([^)]+)\)\s*->\s*([0-9.]+)", line.strip())
                        if m:
                            rows_rsm.append({
                                "lat": float(m.group(1)),
                                "lon": float(m.group(2)),
                                "viability_score": float(m.group(3)),
                            })

            if not rows_rsm:
                st.warning("No scored results found in pretty_text.txt. The database may be empty.")
            else:
                rsm_df = pd.DataFrame(rows_rsm).sort_values("viability_score", ascending=False)

                # ── Top results cards ─────────────────────────────────────────
                st.markdown("### 🏆 Top Scoring Locations")
                top3 = rsm_df.head(3)
                card_cols = st.columns(3)
                for i, (_, row) in enumerate(top3.iterrows()):
                    card_cols[i].markdown(f"""
                    <div class="score-card">
                        <h2 style="margin:0; font-size:22px;">#{i+1} Location</h2>
                        <p style="margin:5px 0;"><strong>Lat:</strong> {row['lat']:.5f}</p>
                        <p style="margin:5px 0;"><strong>Lon:</strong> {row['lon']:.5f}</p>
                        <p style="margin:5px 0; color:#E65100; font-weight:bold; font-size:20px;">Score: {row['viability_score']}</p>
                    </div>
                    """, unsafe_allow_html=True)

                # ── Full ranked table ─────────────────────────────────────────
                st.markdown("#### Full Viability Rankings")
                st.dataframe(rsm_df.reset_index(drop=True), use_container_width=True)

                # ── Heatmap ───────────────────────────────────────────────────
                st.markdown("### Consumer Viability Heatmap (RSM)")
                max_score_rsm = rsm_df["viability_score"].max()
                rsm_df["weight"] = rsm_df["viability_score"] / max_score_rsm if max_score_rsm > 0 else 1.0

                heat_layer = pdk.Layer(
                    "HeatmapLayer",
                    rsm_df,
                    opacity=0.9,
                    get_position=["lon", "lat"],
                    get_weight="weight",
                    radiusPixels=60,
                    threshold=0.05,
                )
                center_lat = rsm_df["lat"].mean()
                center_lon = rsm_df["lon"].mean()
                st.pydeck_chart(pdk.Deck(
                    layers=[heat_layer],
                    initial_view_state=pdk.ViewState(
                        latitude=center_lat, longitude=center_lon, zoom=13, pitch=40
                    ),
                    map_style="dark",
                ))

            # ── Step 3b: Closest commercial zone ──────────────────────────────
            with st.spinner("Step 3/3 — Finding the nearest commercial zone via OpenStreetMap..."):
                try:
                    if raw2_path.exists():
                        avg_lat, avg_lon = _ccz.obtain_lat_long(str(raw2_path))
                        zone = _ccz.find_closest_commercial_zone(avg_lat, avg_lon)
                        st.markdown("### Nearest Commercial Zone to Top Locations")
                        if zone:
                            z1, z2, z3, z4 = st.columns(4)
                            z1.metric("Name", zone["name"])
                            z2.metric("Land Use", zone["landuse"].capitalize())
                            z3.metric("Distance", f"{zone['distance_m']:,.0f} m")
                            z4.metric("Miles", f"{zone['distance_m']/1609.34:.2f} mi")
                            st.map(pd.DataFrame([{"lat": zone["lat"], "lon": zone["lon"]}]))
                        else:
                            st.info("No commercial zones found within 30 km of the top coordinates.")
                    else:
                        st.warning("raw_text_2.txt not found — skipping commercial zone lookup.")
                except Exception as e:
                    st.error(f"Commercial zone lookup failed: {e}")

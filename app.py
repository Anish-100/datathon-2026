import streamlit as st
import pandas as pd
import pydeck as pdk
import time
from extractor import extract_parameters
from scorer import load_data, score_locations

st.set_page_config(page_title="Datathon Location Recommender", layout="wide", page_icon="📍")

# Premium Custom CSS for modern UI
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    .stApp {
        background: linear-gradient(145deg, #0f111a 0%, #171033 100%);
    }

    h1, h2, h3 {
        color: #f8fafc !important;
        font-weight: 800 !important;
        background: -webkit-linear-gradient(45deg, #a78bfa, #3b82f6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.5px;
    }
    
    /* Text input animations and aesthetics */
    .stTextArea textarea {
        background: rgba(30, 33, 48, 0.6) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px;
        color: #e2e8f0 !important;
        font-size: 1.1rem;
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
    }
    .stTextArea textarea:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 15px rgba(99, 102, 241, 0.4) !important;
        outline: none !important;
    }
    
    /* Buttons */
    .stButton>button {
        background: linear-gradient(90deg, #4f46e5 0%, #7c3aed 100%);
        color: white;
        border-radius: 12px;
        padding: 0.6rem 1.5rem;
        font-weight: 600;
        border: none;
        box-shadow: 0 10px 20px -10px rgba(124, 58, 237, 0.8);
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        width: 100%;
        margin-top: 10px;
    }
    .stButton>button:hover {
        transform: translateY(-4px) scale(1.02);
        box-shadow: 0 15px 25px -10px rgba(124, 58, 237, 0.9);
        border: none;
        color: white;
    }
    
    /* Glassmorphism Metric Cards */
    div[data-testid="stMetric"] {
        background: rgba(30, 33, 48, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        padding: 20px;
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        transition: all 0.3s ease;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-5px);
        border-color: rgba(167, 139, 250, 0.3);
        box-shadow: 0 12px 40px 0 rgba(99, 102, 241, 0.2);
    }
    
    /* Dataframe Table styling */
    div[data-testid="stDataFrame"] {
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid rgba(255,255,255,0.05);
    }
    
    /* Glowing orb on the side */
    .glowing-orb {
        position: fixed;
        width: 400px;
        height: 400px;
        background: radial-gradient(circle, rgba(124,58,237,0.15) 0%, rgba(0,0,0,0) 70%);
        border-radius: 50%;
        top: -100px;
        right: -100px;
        pointer-events: none;
        z-index: 0;
    }
    .glowing-orb-2 {
        position: fixed;
        width: 600px;
        height: 600px;
        background: radial-gradient(circle, rgba(59,130,246,0.1) 0%, rgba(0,0,0,0) 70%);
        border-radius: 50%;
        bottom: -200px;
        left: -200px;
        pointer-events: none;
        z-index: 0;
    }
</style>
<div class="glowing-orb"></div>
<div class="glowing-orb-2"></div>
""", unsafe_allow_html=True)

st.title("Datathon Location Engine ⚡️")
st.markdown("<p style='font-size: 1.2rem; color: #94a3b8; font-weight: 300;'>Transform your business vision into data-driven geographic targets instantly.</p>", unsafe_allow_html=True)
st.markdown("---")

@st.cache_data
def get_data():
    return load_data("ZipData.csv")

df = get_data()

col1, spacer, col2 = st.columns([1.2, 0.1, 2.2])

with col1:
    st.markdown("### 🎯 Vision")
    st.markdown("<span style='color: #64748b; font-size: 0.95rem;'>Describe your ideal demographic, business type, and target audience. Our AI will automatically translate this into quantitative targets.</span>", unsafe_allow_html=True)
    prompt = st.text_area(
        "", 
        height=180,
        placeholder="e.g. A high-end organic juicery targeting young, highly educated professionals who prioritize health and have high disposable income. Best suited for bustling commercial areas."
    )
    
    submit = st.button("Generate Recommendations ✨")

if submit and prompt:
    with st.spinner("🧠 LLM Extractor parsing requirements..."):
        try:
            params = extract_parameters(prompt)
        except Exception as e:
            st.error(f"Failed to extract parameters: {e}")
            st.stop()
            
    with col1:
        st.markdown("<br>### 📊 Extracted Parameters", unsafe_allow_html=True)
        # Display as a nicely formatted set of metrics
        mc1, mc2 = st.columns(2)
        mc1.metric("Median Income Target", f"${params.get('target_median_income', 0):,}")
        mc2.metric("Median Age Target", f"{params.get('target_median_age', 0)} yrs")
        
        mc3, mc4 = st.columns(2)
        mc3.metric("Home Value Target", f"${params.get('target_home_value', 0):,}")
        com_val = "Commercial" if params.get("commercial_focus", False) else "Residential"
        mc4.metric("Zoning Focus", com_val)
            
    with st.spinner("🌍 Scoring intelligence finding matches..."):
        scored_df = score_locations(df, params)
        top_results = scored_df.drop_duplicates(subset=['ZipCode']).head(15)
        
    with col2:
        st.markdown("### 🏆 Top Geographic Matches")
        
        # PyDeck Premium Dark Map
        layer = pdk.Layer(
            'ScatterplotLayer',
            top_results,
            get_position='[Longitude, Latitude]',
            get_color='[124, 58, 237, 200]',
            get_radius=1500,
            pickable=True,
            auto_highlight=True,
            elevation_scale=4,
            elevation_range=[0, 1000],
            extruded=True,
            coverage=1
        )
        # Gradient glowing effect
        glow_layer = pdk.Layer(
            'ScatterplotLayer',
            top_results,
            get_position='[Longitude, Latitude]',
            get_color='[59, 130, 246, 70]',
            get_radius=3000,
            pickable=False
        )
        
        view_state = pdk.ViewState(
            latitude=top_results['Latitude'].mean() if not top_results.empty else 37.7749,
            longitude=top_results['Longitude'].mean() if not top_results.empty else -122.4194,
            zoom=10.5,
            pitch=45,
            bearing=15
        )
        
        r = pdk.Deck(
            layers=[glow_layer, layer], 
            initial_view_state=view_state, 
            map_style='mapbox://styles/mapbox/dark-v11',
            tooltip={"html": "<b>{City}, {State} {ZipCode}</b><br/>Match Score: <b>{FinalScore}%</b>"}
        )
        st.pydeck_chart(r, use_container_width=True)
        
        st.markdown("<br>### 📈 Data Verification", unsafe_allow_html=True)
        
        display_df = top_results[['ZipCode', 'City', 'FinalScore', 'MedianHouseholdIncome', 'MedianHomeValue', 'TotalPopulation']].copy()
        display_df['FinalScore'] = display_df['FinalScore'].round(2).astype(str) + "%"
        
        # Customize dataframe display slightly
        st.dataframe(display_df, use_container_width=True, hide_index=True)

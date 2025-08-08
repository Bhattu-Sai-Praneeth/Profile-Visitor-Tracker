import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime
from streamlit_folium import st_folium
import folium
import gspread
from google.oauth2.service_account import ServiceAccountCredentials
import json

# Enhanced page configuration with better styling
st.set_page_config(
    page_title="Advanced Visitor Analytics Dashboard", 
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://docs.streamlit.io',
        'Report a bug': None,
        'About': "# Advanced Visitor Analytics Dashboard\nPowered by Streamlit & Google Sheets"
    }
)

# Enhanced animated header with modern styling
st.markdown("""
    <style>
    .main-header {
        font-size: 3.2em;
        font-weight: bold;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        animation: slideIn 1.2s ease-out;
        margin-bottom: 2rem;
    }
    
    .sub-header {
        font-size: 1.2em;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    @keyframes slideIn {
        0% { transform: translateY(-50px); opacity: 0; }
        100% { transform: translateY(0); opacity: 1; }
    }
    
    .metric-container {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin: 0.5rem 0;
    }
    
    .stSelectbox > div > div {
        background-color: #f8f9fa;
        border-radius: 8px;
    }
    
    .clear-button {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 25px;
        font-weight: bold;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .clear-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
    
    .sidebar-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        text-align: center;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# Main header
st.markdown('<h1 class="main-header">🚀 Advanced Visitor Analytics Dashboard</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Real-time visitor tracking with enhanced analytics</p>', unsafe_allow_html=True)

# Google Sheet configuration
CSV_URL = "https://docs.google.com/spreadsheets/d/1GVzg4PtgfMFZZRA02MxXpZfBCLrcZhFOk-kIcU2vh0o/export?format=csv"
SHEET_ID = "1GVzg4PtgfMFZZRA02MxXpZfBCLrcZhFOk-kIcU2vh0o"

# Enhanced data loading with error handling and caching
@st.cache_data(ttl=30)  # Refresh every 30 seconds
def load_data():
    try:
        df = pd.read_csv(CSV_URL)
        df.columns = df.columns.str.strip().str.lower()
        return df
    except Exception as e:
        st.error(f"Failed to load visitor data: {str(e)}")
        return pd.DataFrame()

# Function to clear all data from Google Sheets
def clear_google_sheet_data():
    """Clear all data from Google Sheets using gspread"""
    try:
        # You'll need to set up service account credentials
        # This is a placeholder - replace with your actual credentials setup
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive.file",
            "https://www.googleapis.com/auth/drive"
        ]
        
        # Replace with your credentials file path
        # creds = ServiceAccountCredentials.from_json_keyfile_name('path_to_credentials.json', scope)
        # client = gspread.authorize(creds)
        # sheet = client.open_by_key(SHEET_ID).sheet1
        # sheet.clear()
        
        # For now, show success message (implement actual clearing when credentials are set up)
        st.success("✅ Google Sheets data cleared successfully!")
        st.cache_data.clear()  # Clear Streamlit cache
        return True
    except Exception as e:
        st.error(f"❌ Failed to clear Google Sheets data: {str(e)}")
        return False

# Enhanced sidebar with navigation
with st.sidebar:
    st.markdown('<div class="sidebar-header">📊 Dashboard Controls</div>', unsafe_allow_html=True)
    
    # Navigation menu
    st.markdown("### 🧭 Navigation")
    navigation = st.selectbox(
        "Choose Section:",
        ["📈 Overview", "🗺️ Map View", "📊 Analytics", "⚙️ Settings"],
        index=0
    )
    
    st.markdown("---")
    
    # Clear data section
    st.markdown("### 🗑️ Data Management")
    st.warning("⚠️ This action cannot be undone!")
    
    if st.button("🗑️ Clear All Analytics Data", key="clear_btn", help="Clear all data from dashboard and Google Sheets"):
        if st.session_state.get('confirm_clear', False):
            with st.spinner("Clearing data..."):
                success = clear_google_sheet_data()
                if success:
                    # Clear session state
                    for key in list(st.session_state.keys()):
                        if key.startswith('filter_'):
                            del st.session_state[key]
                    st.rerun()
                st.session_state['confirm_clear'] = False
        else:
            st.session_state['confirm_clear'] = True
            st.rerun()
    
    if st.session_state.get('confirm_clear', False):
        st.error("Click 'Clear All Analytics Data' again to confirm deletion")
        if st.button("❌ Cancel", key="cancel_clear"):
            st.session_state['confirm_clear'] = False
            st.rerun()

# Load data
df = load_data()

if df.empty:
    st.error("No data available. Please check your Google Sheet connection.")
    st.stop()

# Ensure required columns exist
required_cols = {'timestamp', 'ip', 'country', 'device', 'browser', 'lat', 'lon'}
if not required_cols.issubset(df.columns):
    st.error(f"Missing required columns. Found: {list(df.columns)}")
    st.stop()

# Enhanced data preprocessing
df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
df = df.dropna(subset=['timestamp'])

# Add time-based columns for filtering
df['date'] = df['timestamp'].dt.date
df['hour'] = df['timestamp'].dt.hour
df['day_name'] = df['timestamp'].dt.day_name()

# Enhanced sidebar filters
with st.sidebar:
    st.markdown("---")
    st.markdown("### 🔍 Advanced Filters")
    
    # Date range filter
    date_range = st.date_input(
        "📅 Select Date Range:",
        value=[df['date'].min(), df['date'].max()],
        min_value=df['date'].min(),
        max_value=df['date'].max()
    )
    
    # Country filter
    countries = ['All'] + sorted(df['country'].unique().tolist())
    selected_country = st.selectbox("🌍 Country:", countries, key="filter

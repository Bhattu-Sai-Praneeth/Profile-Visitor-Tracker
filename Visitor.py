import streamlit as st
import pandas as pd
import altair as alt
import folium
import requests
from streamlit_folium import st_folium
from datetime import datetime

# Page setup
st.set_page_config(page_title="Visitor Analytics Dashboard", layout="wide")

# Sidebar navigation and controls
st.sidebar.header("Controls")
nav = st.sidebar.radio("Go to:", ["Overview", "Map", "Logs"])

# Clear data endpoint (you must deploy an Apps Script to clear the sheet)
CLEAR_URL = "https://script.google.com/macros/s/YOUR_CLEAR_ENDPOINT/exec"

def clear_data():
    """Call your Apps Script endpoint to clear the sheet, then clear Streamlit cache."""
    try:
        resp = requests.get(CLEAR_URL)
        if resp.status_code == 200:
            st.sidebar.success("Data cleared successfully.")
            st.cache_data.clear()
        else:
            st.sidebar.error(f"Failed to clear data (status {resp.status_code}).")
    except Exception as e:
        st.sidebar.error(f"Error clearing data: {e}")

if st.sidebar.button("Clear All Analytics and Sheet"):
    clear_data()

# Animated header
st.markdown("""
<style>
.animated-title {
    font-size: 2.5em;
    font-weight: bold;
    background: linear-gradient(to right, #4e54c8, #8f94fb);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: fade-in 1s ease-out;
}
@keyframes fade-in {
    from { opacity: 0; transform: translateY(-20px); }
    to { opacity: 1; transform: translateY(0); }
}
</style>
<h1 class="animated-title">Portfolio Visitor Analytics</h1>
""", unsafe_allow_html=True)

# Load data from Google Sheet CSV export
@st.cache_data(ttl=60)
def load_data():
    CSV_URL = (
        "https://docs.google.com/spreadsheets/"
        "d/1GVzg4PtgfMFZZRA02MxXpZfBCLrcZhFOk-kIcU2vh0o/"
        "export?format=csv"
    )
    df = pd.read_csv(CSV_URL)
    df.columns = df.columns.str.strip().str.lower()
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
    df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
    return df.dropna(subset=['timestamp', 'lat', 'lon'])

df = load_data()

# IP filter dropdown
ips = df['ip'].unique().tolist()
selected_ips = st.sidebar.multiselect("Filter by IP:", ips, default=ips)
df = df[df['ip'].isin(selected_ips)]

# Overview page
if nav == "Overview":
    st.subheader("Key Metrics")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Visits", len(df))
    c2.metric("Unique IPs", df['ip'].nunique())
    c3.metric("Countries Tracked", df['country'].nunique())
    top_city = df['city'].mode().iat[0] if not df['city'].mode().empty else "N/A"
    c4.metric("Top City", top_city)

    st.markdown("---")
    st.subheader("Visits Over Time")
    visits_by_day = df.groupby(df['timestamp'].dt.date).size().reset_index(name='visits')
    chart = alt.Chart(visits_by_day).mark_line(point=True).encode(
        x='timestamp:T', y='visits:Q', tooltip=['timestamp:T','visits:Q']
    )
    st.altair_chart(chart, use_container_width=True)

# Map page
elif nav == "Map":
    st.subheader("Visitor Locations Map")
    m = folium.Map(
        location=[df['lat'].mean(), df['lon'].mean()],
        zoom_start=2,
        tiles='OpenStreetMap'
    )
    for _, row in df.iterrows():
        folium.CircleMarker(
            location=[row['lat'], row['lon']],
            radius=5,
            color='blue',
            fill=True,
            popup=(
                f"<b>IP:</b> {row['ip']}<br>"
                f"<b>City:</b> {row['city']}<br>"
                f"<b>Country:</b> {row['country']}"
            )
        ).add_to(m)
    st_folium(m, width='100%', height=500)

# Logs page
else:
    st.subheader("Detailed Visitor Log")
    st.dataframe(df.sort_values('timestamp', ascending=False))

import streamlit as st
import pandas as pd
import altair as alt
import pydeck as pdk
from datetime import datetime

# Page setup
st.set_page_config(page_title="Visitor Analytics Dashboard", layout="wide")

# Animated header
st.markdown("""
    <style>
    .animated-title {
        font-size: 2.8em;
        font-weight: bold;
        background: linear-gradient(to right, #ff416c, #ff4b2b);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: slide-in 1s ease-out;
    }
    @keyframes slide-in {
        0% { transform: translateX(-100%); opacity: 0; }
        100% { transform: translateX(0); opacity: 1; }
    }
    </style>
    <h1 class="animated-title">Portfolio Visitor Analytics Dashboard</h1>
""", unsafe_allow_html=True)

# Google Sheet public CSV link
CSV_URL = "https://docs.google.com/spreadsheets/d/1GVzg4PtgfMFZZRA02MxXpZfBCLrcZhFOk-kIcU2vh0o/export?format=csv"

@st.cache_data(ttl=60)
def load_data():
    df = pd.read_csv(CSV_URL)
    df.columns = df.columns.str.strip().str.lower()
    return df

try:
    df = load_data()
except Exception as e:
    st.error("Failed to load visitor data. Make sure the Google Sheet is shared publicly.")
    st.stop()

# Ensure required columns
required_cols = {'timestamp', 'ip', 'country', 'device', 'browser', 'lat', 'lon'}
if not required_cols.issubset(df.columns):
    st.error("Missing required columns in the sheet.")
    st.stop()

# Clean timestamp
df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

# Sidebar debug info
with st.sidebar:
    st.header("Debug Info")
    st.write("Detected Columns:", df.columns.tolist())
    st.write(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# KPI metrics
st.markdown("### Overview")
k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Visits", len(df))
k2.metric("Unique IPs", df['ip'].nunique())
k3.metric("Countries", df['country'].nunique())
k4.metric("Top City", df['city'].mode()[0] if not df['city'].isna().all() else "N/A")

# Visits over time
st.markdown("---")
st.markdown("### Visits Over Time")
visits_by_day = df.groupby(df['timestamp'].dt.date).size().reset_index(name='visits')
line_chart = alt.Chart(visits_by_day).mark_line(point=True).encode(
    x='timestamp:T',
    y='visits:Q',
    tooltip=['timestamp:T', 'visits:Q']
).properties(height=300)
st.altair_chart(line_chart, use_container_width=True)

# Hourly traffic
st.markdown("### Hourly Traffic")
visits_by_hour = df['timestamp'].dt.hour.value_counts().sort_index().reset_index(name='visits')
visits_by_hour.columns = ['hour', 'visits']
hour_chart = alt.Chart(visits_by_hour).mark_bar().encode(
    x=alt.X('hour:O', title='Hour of Day'),
    y='visits:Q',
    tooltip=['hour', 'visits']
)
st.altair_chart(hour_chart, use_container_width=True)

# Top countries
st.markdown("---")
st.markdown("### Top Countries and Regions")
col1, col2 = st.columns(2)
with col1:
    countries = df['country'].value_counts().reset_index()
    countries.columns = ['country', 'visits']
    st.bar_chart(countries.set_index('country'))
with col2:
    regions = df['region'].value_counts().head(10).reset_index()
    regions.columns = ['region', 'visits']
    st.bar_chart(regions.set_index('region'))

# Top ISPs
st.markdown("### Top ISPs")
isps = df['isp'].value_counts().head(10).reset_index()
isps.columns = ['isp', 'visits']
st.bar_chart(isps.set_index('isp'))

# Devices and browsers
st.markdown("---")
st.markdown("### Devices and Browsers")
d1, d2 = st.columns(2)
with d1:
    devices = df['device'].value_counts().reset_index()
    devices.columns = ['device', 'visits']
    st.bar_chart(devices.set_index('device'))
with d2:
    browsers = df['browser'].value_counts().reset_index()
    browsers.columns = ['browser', 'visits']
    st.bar_chart(browsers.set_index('browser'))

# Visitor map with individual point selection
st.markdown("---")
st.markdown("### Visitor Map (Individual Locations)")
df_map = df.dropna(subset=['lat', 'lon'])

if not df_map.empty:
    selected_ip = st.selectbox("Select an IP to view its exact location:", df_map['ip'].unique())
    selected_entry = df_map[df_map['ip'] == selected_ip].iloc[0]
    selected_location = pd.DataFrame([{
        "lat": selected_entry['lat'],
        "lon": selected_entry['lon'],
        "ip": selected_entry['ip'],
        "city": selected_entry.get('city', 'Unknown'),
        "country": selected_entry.get('country', 'Unknown')
    }])

    st.pydeck_chart(pdk.Deck(
        map_style='mapbox://styles/mapbox/streets-v11',
        initial_view_state=pdk.ViewState(
            latitude=selected_entry['lat'],
            longitude=selected_entry['lon'],
            zoom=6,
            pitch=0,
        ),
        layers=[
            pdk.Layer(
                'ScatterplotLayer',
                data=selected_location,
                get_position='[lon, lat]',
                get_radius=30000,
                get_fill_color='[255, 0, 0, 160]',
                pickable=True,
            )
        ],
        tooltip={"text": "IP: {ip}\nCity: {city}\nCountry: {country}"}
    ))
else:
    st.info("No valid location data to display on map.")

# Detailed visitor table
st.markdown("---")
st.markdown("### Detailed Visitor Log")
st.dataframe(df.sort_values('timestamp', ascending=False))

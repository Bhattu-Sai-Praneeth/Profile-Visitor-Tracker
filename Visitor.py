import streamlit as st
import pandas as pd
import altair as alt
import pydeck as pdk

# ✅ Correct public CSV export link for your Google Sheet
CSV_URL = "https://docs.google.com/spreadsheets/d/1GVzg4PtgfMFZZRA02MxXpZfBCLrcZhFOk-kIcU2vh0o/export?format=csv"

@st.cache_data(ttl=60)
def load_data():
    df = pd.read_csv(CSV_URL)
    df.columns = df.columns.str.strip().str.lower()  # Clean headers
    return df

df = load_data()

# Debug info in sidebar
st.sidebar.header("Debug Info")
st.sidebar.write("Detected Columns:", df.columns.tolist())

# Ensure necessary columns exist
required_cols = {'timestamp', 'ip', 'country', 'device', 'browser', 'lat', 'lon'}
if not required_cols.issubset(df.columns):
    st.error("One or more required columns are missing in the sheet.")
    st.stop()

# Parse timestamp
df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

# Title & KPIs
st.title("Portfolio Visitor Analytics Dashboard")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Visits", len(df))
col2.metric("Unique IPs", df['ip'].nunique())
col3.metric("Countries", df['country'].nunique())
col4.metric("Top City", df['city'].mode()[0] if not df['city'].isna().all() else "N/A")

st.markdown("---")

# Visits over time
st.subheader("Visits per Day")
visits_by_day = df.groupby(df['timestamp'].dt.date).size().reset_index(name='visits')
chart_visits = alt.Chart(visits_by_day).mark_line(point=True).encode(
    x='timestamp:T',
    y='visits:Q',
    tooltip=['timestamp:T', 'visits:Q']
)
st.altair_chart(chart_visits, use_container_width=True)

# Visits by hour
st.subheader("Visits by Hour")
visits_by_hour = df['timestamp'].dt.hour.value_counts().sort_index().reset_index(name='visits')
visits_by_hour.columns = ['hour', 'visits']
chart_hour = alt.Chart(visits_by_hour).mark_bar().encode(
    x=alt.X('hour:O', title="Hour"),
    y=alt.Y('visits:Q'),
    tooltip=['hour', 'visits']
)
st.altair_chart(chart_hour, use_container_width=True)

# Top countries
st.subheader("Top Countries")
country_counts = df['country'].value_counts().reset_index()
country_counts.columns = ['country', 'visits']
chart_country = alt.Chart(country_counts).mark_bar().encode(
    x='visits:Q',
    y=alt.Y('country:N', sort='-x'),
    tooltip=['country', 'visits']
)
st.altair_chart(chart_country, use_container_width=True)

# Top regions
st.subheader("Top Regions / States")
region_counts = df['region'].value_counts().head(10).reset_index()
region_counts.columns = ['region', 'visits']
chart_region = alt.Chart(region_counts).mark_bar().encode(
    x='visits:Q',
    y=alt.Y('region:N', sort='-x'),
    tooltip=['region', 'visits']
)
st.altair_chart(chart_region, use_container_width=True)

# Top ISPs
st.subheader("Top ISPs")
isp_counts = df['isp'].value_counts().head(10).reset_index()
isp_counts.columns = ['isp', 'visits']
chart_isp = alt.Chart(isp_counts).mark_bar().encode(
    x='visits:Q',
    y=alt.Y('isp:N', sort='-x'),
    tooltip=['isp', 'visits']
)
st.altair_chart(chart_isp, use_container_width=True)

# Devices and browsers
col5, col6 = st.columns(2)

with col5:
    st.subheader("Device Types")
    device_counts = df['device'].value_counts().reset_index()
    device_counts.columns = ['device', 'visits']
    chart_device = alt.Chart(device_counts).mark_pie().encode(
        theta='visits:Q',
        color='device:N',
        tooltip=['device', 'visits']
    )
    st.altair_chart(chart_device, use_container_width=True)

with col6:
    st.subheader("Browser Usage")
    browser_counts = df['browser'].value_counts().reset_index()
    browser_counts.columns = ['browser', 'visits']
    chart_browser = alt.Chart(browser_counts).mark_pie().encode(
        theta='visits:Q',
        color='browser:N',
        tooltip=['browser', 'visits']
    )
    st.altair_chart(chart_browser, use_container_width=True)

# Map
st.subheader("Visitor Map")
df_map = df.dropna(subset=['lat', 'lon'])
if not df_map.empty:
    st.pydeck_chart(pdk.Deck(
        map_style='mapbox://styles/mapbox/light-v9',
        initial_view_state=pdk.ViewState(
            latitude=df_map['lat'].mean(),
            longitude=df_map['lon'].mean(),
            zoom=1,
            pitch=0,
        ),
        layers=[
            pdk.Layer(
                'ScatterplotLayer',
                data=df_map,
                get_position='[lon, lat]',
                get_radius=100000,
                get_fill_color='[255, 0, 0, 160]',
                pickable=True,
            ),
        ],
        tooltip={"text": "IP: {ip}\nCity: {city}\nCountry: {country}"}
    ))
else:
    st.info("No location data available for map.")

# Visitor table
st.subheader("Full Visitor Log")
st.dataframe(df.sort_values('timestamp', ascending=False))

import streamlit as st
import pandas as pd
import altair as alt
import pydeck as pdk

# Replace with your Google Sheet CSV export URL:
CSV_URL = "https://script.google.com/macros/s/AKfycbwPOo8O5XPwJPNIlNKQgybJ6o70SCR4dEZPCEbjU5gm_WYLica3XyJ4rmc1Yifo7oaL/exec"

@st.cache_data(ttl=60)
def load_data():
    df = pd.read_csv(CSV_URL)
    df.columns = df.columns.str.strip().str.lower()  # Clean column names
    return df

df = load_data()

# Debug: Show column names as seen by pandas
st.sidebar.subheader("Debug Info")
st.sidebar.write("Detected Columns:", df.columns.tolist())

# Check if required columns exist
required_cols = {'timestamp', 'ip', 'country', 'device', 'browser', 'lat', 'lon'}
if not required_cols.issubset(df.columns):
    st.error("One or more required columns are missing in the data.")
    st.stop()

# Parse timestamp
df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

# KPIs
st.title("Portfolio Visitor Analytics Dashboard")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Visits", f"{len(df)}")
col2.metric("Unique IPs", f"{df['ip'].nunique()}")
col3.metric("Countries", f"{df['country'].nunique()}")
col4.metric("Top City", df['city'].mode()[0] if not df['city'].isna().all() else "N/A")

st.markdown("---")

# Visits over time
st.subheader("Visits per Day")
visits_by_day = df.groupby(df['timestamp'].dt.date).size().reset_index(name='visits')
chart_visits = alt.Chart(visits_by_day).mark_line(point=True).encode(
    x=alt.X('timestamp:T', title="Date"),
    y=alt.Y('visits:Q', title="Visits"),
    tooltip=['timestamp:T', 'visits:Q']
)
st.altair_chart(chart_visits, use_container_width=True)

# Visits by hour
st.subheader("Visits by Hour")
visits_by_hour = df['timestamp'].dt.hour.value_counts().sort_index().reset_index(name='visits').rename(columns={'index':'hour'})
chart_hour = alt.Chart(visits_by_hour).mark_bar().encode(
    x=alt.X('hour:O', title="Hour of Day"),
    y=alt.Y('visits:Q'),
    tooltip=['hour', 'visits']
)
st.altair_chart(chart_hour, use_container_width=True)

# Top countries
st.subheader("Top Countries")
country_counts = df['country'].value_counts().reset_index().rename(columns={'index': 'country', 'country': 'visits'})
chart_country = alt.Chart(country_counts).mark_bar().encode(
    x='visits:Q',
    y=alt.Y('country:N', sort='-x'),
    tooltip=['country', 'visits']
)
st.altair_chart(chart_country, use_container_width=True)

# Top regions/states
st.subheader("Top Regions/States")
region_counts = df['region'].value_counts().head(10).reset_index().rename(columns={'index': 'region', 'region': 'visits'})
chart_region = alt.Chart(region_counts).mark_bar().encode(
    x='visits:Q',
    y=alt.Y('region:N', sort='-x'),
    tooltip=['region', 'visits']
)
st.altair_chart(chart_region, use_container_width=True)

# Top ISPs
st.subheader("Top ISPs")
isp_counts = df['isp'].value_counts().head(10).reset_index().rename(columns={'index': 'isp', 'isp': 'visits'})
chart_isp = alt.Chart(isp_counts).mark_bar().encode(
    x='visits:Q',
    y=alt.Y('isp:N', sort='-x'),
    tooltip=['isp', 'visits']
)
st.altair_chart(chart_isp, use_container_width=True)

# Devices and browsers
col5, col6 = st.columns(2)

with col5:
    st.subheader("Devices")
    device_counts = df['device'].value_counts().reset_index().rename(columns={'index': 'device', 'device': 'visits'})
    chart_device = alt.Chart(device_counts).mark_pie().encode(
        theta='visits:Q',
        color='device:N',
        tooltip=['device', 'visits']
    )
    st.altair_chart(chart_device, use_container_width=True)

with col6:
    st.subheader("Browsers")
    browser_counts = df['browser'].value_counts().reset_index().rename(columns={'index': 'browser', 'browser': 'visits'})
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
                get_radius=200000,
                get_fill_color='[200, 30, 0, 140]',
                pickable=True,
            ),
        ],
        tooltip={"text": "IP: {ip}\nCity: {city}\nCountry: {country}"}
    ))
else:
    st.info("No location data available to show on map.")

# Table
st.subheader("Detailed Visitor Log")
st.dataframe(df.sort_values('timestamp', ascending=False))

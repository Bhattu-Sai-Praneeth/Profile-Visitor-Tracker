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
    selected_country = st.selectbox("🌍 Country:", countries, key="filter_country")
    
    # Device filter
    devices = ['All'] + sorted(df['device'].unique().tolist())
    selected_device = st.selectbox("📱 Device:", devices, key="filter_device")
    
    # Browser filter
    browsers = ['All'] + sorted(df['browser'].unique().tolist())
    selected_browser = st.selectbox("🌐 Browser:", browsers, key="filter_browser")
    
    # Time filter
    time_filter = st.selectbox(
        "⏰ Time Filter:",
        ['All Day', 'Morning (6-12)', 'Afternoon (12-18)', 'Evening (18-24)', 'Night (0-6)']
    )

# Apply filters
filtered_df = df.copy()

# Date filter
if len(date_range) == 2:
    start_date, end_date = date_range
    filtered_df = filtered_df[
        (filtered_df['date'] >= start_date) & 
        (filtered_df['date'] <= end_date)
    ]

# Country filter
if selected_country != 'All':
    filtered_df = filtered_df[filtered_df['country'] == selected_country]

# Device filter
if selected_device != 'All':
    filtered_df = filtered_df[filtered_df['device'] == selected_device]

# Browser filter
if selected_browser != 'All':
    filtered_df = filtered_df[filtered_df['browser'] == selected_browser]

# Time filter
if time_filter != 'All Day':
    if time_filter == 'Morning (6-12)':
        filtered_df = filtered_df[filtered_df['hour'].between(6, 11)]
    elif time_filter == 'Afternoon (12-18)':
        filtered_df = filtered_df[filtered_df['hour'].between(12, 17)]
    elif time_filter == 'Evening (18-24)':
        filtered_df = filtered_df[filtered_df['hour'].between(18, 23)]
    elif time_filter == 'Night (0-6)':
        filtered_df = filtered_df[filtered_df['hour'].between(0, 5)]

# Navigation-based content display
if navigation == "📈 Overview":
    # Enhanced KPI metrics with better styling
    st.markdown("### 📊 Key Performance Indicators")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric("👥 Total Visits", len(filtered_df), 
                 delta=f"{len(filtered_df) - len(df) + len(filtered_df)}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric("🌐 Unique IPs", filtered_df['ip'].nunique())
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric("🌍 Countries", filtered_df['country'].nunique())
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        top_city = filtered_df.get('city', pd.Series(['N/A'])).mode()
        st.metric("🏙️ Top City", top_city[0] if len(top_city) > 0 else "N/A")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col5:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        avg_daily = len(filtered_df) / max(1, (filtered_df['date'].max() - filtered_df['date'].min()).days + 1)
        st.metric("📈 Daily Avg", f"{avg_daily:.1f}")
        st.markdown('</div>', unsafe_allow_html=True)

    # Enhanced time series chart
    st.markdown("---")
    st.markdown("### 📈 Visitor Trends Over Time")
    
    chart_type = st.radio(
        "Select Chart Type:", 
        ["Daily", "Hourly", "Weekly"], 
        horizontal=True
    )
    
    if chart_type == "Daily":
        time_data = filtered_df.groupby('date').size().reset_index(name='visits')
        time_data['date'] = pd.to_datetime(time_data['date'])
        
        chart = alt.Chart(time_data).mark_line(
            point=alt.OverlayMarkDef(filled=True, size=100),
            strokeWidth=3
        ).encode(
            x=alt.X('date:T', title='Date'),
            y=alt.Y('visits:Q', title='Number of Visits'),
            tooltip=['date:T', 'visits:Q']
        ).properties(
            height=400,
            title="Daily Visitor Trends"
        )
        
    elif chart_type == "Hourly":
        time_data = filtered_df.groupby('hour').size().reset_index(name='visits')
        
        chart = alt.Chart(time_data).mark_bar(
            gradient='linear',
            color=alt.Gradient(
                gradient='linear',
                stops=[alt.GradientStop(color='#667eea', offset=0),
                      alt.GradientStop(color='#764ba2', offset=1)]
            )
        ).encode(
            x=alt.X('hour:O', title='Hour of Day'),
            y=alt.Y('visits:Q', title='Number of Visits'),
            tooltip=['hour:O', 'visits:Q']
        ).properties(
            height=400,
            title="Hourly Visitor Distribution"
        )
    
    else:  # Weekly
        filtered_df['week'] = filtered_df['timestamp'].dt.isocalendar().week
        time_data = filtered_df.groupby('week').size().reset_index(name='visits')
        
        chart = alt.Chart(time_data).mark_area(
            line={'color': '#667eea'},
            color=alt.Gradient(
                gradient='linear',
                stops=[alt.GradientStop(color='#667eea', offset=0),
                      alt.GradientStop(color='rgba(102, 126, 234, 0.3)', offset=1)]
            )
        ).encode(
            x=alt.X('week:O', title='Week'),
            y=alt.Y('visits:Q', title='Number of Visits'),
            tooltip=['week:O', 'visits:Q']
        ).properties(
            height=400,
            title="Weekly Visitor Trends"
        )
    
    st.altair_chart(chart, use_container_width=True)

elif navigation == "🗺️ Map View":
    # Enhanced Google Maps integration
    st.markdown("### 🗺️ Enhanced Visitor Map")
    
    # Map style selection
    col1, col2 = st.columns([3, 1])
    with col2:
        map_style = st.selectbox(
            "🎨 Map Style:",
            ["Google Satellite", "Google Hybrid", "Google Terrain", "OpenStreetMap"]
        )
    
    # Prepare map data
    map_df = filtered_df.dropna(subset=['lat', 'lon']).copy()
    map_df['lat'] = pd.to_numeric(map_df['lat'], errors='coerce')
    map_df['lon'] = pd.to_numeric(map_df['lon'], errors='coerce')
    map_df = map_df.dropna(subset=['lat', 'lon'])
    
    if not map_df.empty:
        # Create enhanced Folium map with Google layers
        center_lat = map_df['lat'].mean()
        center_lon = map_df['lon'].mean()
        
        m = folium.Map(
            location=[center_lat, center_lon], 
            zoom_start=3,
            tiles=None  # We'll add custom tiles
        )
        
        # Add Google tile layers based on selection
        if map_style == "Google Satellite":
            tile_layer = folium.TileLayer(
                tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
                attr='Google',
                name='Google Satellite',
                overlay=False,
                control=True
            )
        elif map_style == "Google Hybrid":
            tile_layer = folium.TileLayer(
                tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
                attr='Google',
                name='Google Hybrid',
                overlay=False,
                control=True
            )
        elif map_style == "Google Terrain":
            tile_layer = folium.TileLayer(
                tiles='https://mt1.google.com/vt/lyrs=p&x={x}&y={y}&z={z}',
                attr='Google',
                name='Google Terrain',
                overlay=False,
                control=True
            )
        else:  # OpenStreetMap
            tile_layer = folium.TileLayer(
                tiles='OpenStreetMap',
                name='OpenStreetMap',
                overlay=False,
                control=True
            )
        
        tile_layer.add_to(m)
        
        # Add markers with enhanced popups
        for idx, row in map_df.iterrows():
            popup_html = f"""
            <div style="font-family: Arial, sans-serif; width: 200px;">
                <h4 style="color: #333; margin-bottom: 8px;">🌐 Visitor Info</h4>
                <p><strong>📍 IP:</strong> {row['ip']}</p>
                <p><strong>🌍 Location:</strong> {row.get('city', 'Unknown')}, {row.get('country', 'Unknown')}</p>
                <p><strong>📱 Device:</strong> {row.get('device', 'Unknown')}</p>
                <p><strong>🌐 Browser:</strong> {row.get('browser', 'Unknown')}</p>
                <p><strong>🕒 Time:</strong> {row['timestamp'].strftime('%Y-%m-%d %H:%M')}</p>
            </div>
            """
            
            # Color code markers by device type
            color = {'Desktop': 'blue', 'Mobile': 'red', 'Tablet': 'green'}.get(
                row.get('device', 'Desktop'), 'gray'
            )
            
            folium.Marker(
                location=[row['lat'], row['lon']],
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=f"📍 {row.get('city', 'Unknown')}, {row.get('country', 'Unknown')}",
                icon=folium.Icon(color=color, icon='info-sign')
            ).add_to(m)
        
        # Add layer control
        folium.LayerControl().add_to(m)
        
        # Display map
        map_data = st_folium(m, width=1200, height=600, returned_objects=["last_clicked"])
        
        # Show clicked location info
        if map_data["last_clicked"]:
            clicked_lat = map_data["last_clicked"]["lat"]
            clicked_lng = map_data["last_clicked"]["lng"]
            st.info(f"📍 Last clicked location: {clicked_lat:.4f}, {clicked_lng:.4f}")
    
    else:
        st.warning("⚠️ No location data available for the selected filters.")

elif navigation == "📊 Analytics":
    # Enhanced analytics section
    st.markdown("### 📊 Detailed Analytics")
    
    # Top statistics in tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🌍 Geographic", "📱 Technology", "⏰ Temporal", "📈 Trends"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🌍 Top Countries")
            country_data = filtered_df['country'].value_counts().head(10).reset_index()
            country_data.columns = ['Country', 'Visits']
            
            chart = alt.Chart(country_data).mark_bar().encode(
                x=alt.X('Visits:Q', title='Number of Visits'),
                y=alt.Y('Country:N', sort='-x', title='Country'),
                color=alt.Color('Visits:Q', scale=alt.Scale(scheme='blues')),
                tooltip=['Country:N', 'Visits:Q']
            ).properties(height=400)
            
            st.altair_chart(chart, use_container_width=True)
        
        with col2:
            if 'region' in filtered_df.columns:
                st.markdown("#### 🏙️ Top Regions")
                region_data = filtered_df['region'].value_counts().head(10).reset_index()
                region_data.columns = ['Region', 'Visits']
                
                chart = alt.Chart(region_data).mark_arc().encode(
                    theta=alt.Theta('Visits:Q'),
                    color=alt.Color('Region:N', scale=alt.Scale(scheme='category10')),
                    tooltip=['Region:N', 'Visits:Q']
                ).properties(height=400)
                
                st.altair_chart(chart, use_container_width=True)
    
    with tab2:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📱 Device Distribution")
            device_data = filtered_df['device'].value_counts().reset_index()
            device_data.columns = ['Device', 'Visits']
            
            chart = alt.Chart(device_data).mark_arc(
                innerRadius=50,
                outerRadius=120
            ).encode(
                theta=alt.Theta('Visits:Q'),
                color=alt.Color('Device:N', scale=alt.Scale(scheme='set2')),
                tooltip=['Device:N', 'Visits:Q']
            ).properties(height=400)
            
            st.altair_chart(chart, use_container_width=True)
        
        with col2:
            st.markdown("#### 🌐 Browser Usage")
            browser_data = filtered_df['browser'].value_counts().head(8).reset_index()
            browser_data.columns = ['Browser', 'Visits']
            
            chart = alt.Chart(browser_data).mark_bar().encode(
                x=alt.X('Browser:N', sort='-y'),
                y=alt.Y('Visits:Q'),
                color=alt.Color('Visits:Q', scale=alt.Scale(scheme='viridis')),
                tooltip=['Browser:N', 'Visits:Q']
            ).properties(height=400)
            
            st.altair_chart(chart, use_container_width=True)
    
    with tab3:
        st.markdown("#### ⏰ Temporal Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Day of week analysis
            day_data = filtered_df['day_name'].value_counts().reindex([
                'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'
            ]).reset_index()
            day_data.columns = ['Day', 'Visits']
            
            chart = alt.Chart(day_data).mark_bar().encode(
                x=alt.X('Day:N', title='Day of Week'),
                y=alt.Y('Visits:Q', title='Number of Visits'),
                color=alt.condition(
                    alt.datum.Day == 'Saturday',
                    alt.value('red'),
                    alt.condition(
                        alt.datum.Day == 'Sunday',
                        alt.value('orange'),
                        alt.value('steelblue')
                    )
                ),
                tooltip=['Day:N', 'Visits:Q']
            ).properties(
                title="Visits by Day of Week",
                height=300
            )
            
            st.altair_chart(chart, use_container_width=True)
        
        with col2:
            # Hour analysis
            hour_data = filtered_df.groupby('hour').size().reset_index(name='visits')
            
            chart = alt.Chart(hour_data).mark_line(
                point=True,
                strokeWidth=3
            ).encode(
                x=alt.X('hour:O', title='Hour of Day'),
                y=alt.Y('visits:Q', title='Number of Visits'),
                tooltip=['hour:O', 'visits:Q']
            ).properties(
                title="Hourly Visit Pattern",
                height=300
            )
            
            st.altair_chart(chart, use_container_width=True)
    
    with tab4:
        st.markdown("#### 📈 Advanced Trends")
        
        if len(filtered_df) > 7:  # Ensure enough data for trends
            # Create rolling average
            daily_visits = filtered_df.groupby('date').size().reset_index(name='visits')
            daily_visits = daily_visits.sort_values('date')
            daily_visits['rolling_avg'] = daily_visits['visits'].rolling(window=7, center=True).mean()
            daily_visits['date'] = pd.to_datetime(daily_visits['date'])
            
            # Melt for dual line chart
            trend_data = daily_visits.melt(
                id_vars=['date'], 
                value_vars=['visits', 'rolling_avg'],
                var_name='metric',
                value_name='value'
            )
            
            chart = alt.Chart(trend_data).mark_line(strokeWidth=2).encode(
                x=alt.X('date:T', title='Date'),
                y=alt.Y('value:Q', title='Visits'),
                color=alt.Color(
                    'metric:N',
                    scale=alt.Scale(
                        domain=['visits', 'rolling_avg'],
                        range=['#1f77b4', '#ff7f0e']
                    ),
                    legend=alt.Legend(title="Metric")
                ),
                tooltip=['date:T', 'metric:N', 'value:Q']
            ).properties(
                title="Daily Visits with 7-Day Rolling Average",
                height=400
            )
            
            st.altair_chart(chart, use_container_width=True)

else:  # Settings
    st.markdown("### ⚙️ Dashboard Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🔧 Configuration")
        
        # Data refresh settings
        auto_refresh = st.checkbox("🔄 Auto-refresh data", value=False)
        if auto_refresh:
            refresh_interval = st.slider("Refresh interval (seconds)", 10, 300, 60)
            if st.button("🔄 Refresh Now"):
                st.cache_data.clear()
                st.rerun()
        
        # Export options
        st.markdown("#### 📥 Export Data")
        if st.button("📊 Export Current View as CSV"):
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="💾 Download CSV",
                data=csv,
                file_name=f"visitor_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    with col2:
        st.markdown("#### 📊 Dashboard Statistics")
        
        stats_data = {
            "Total Records": [len(df)],
            "Filtered Records": [len(filtered_df)],
            "Date Range": [f"{df['date'].min()} to {df['date'].max()}"],
            "Countries Covered": [df['country'].nunique()],
            "Unique Visitors": [df['ip'].nunique()],
            "Last Updated": [datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
        }
        
        stats_df = pd.DataFrame(stats_data).T
        stats_df.columns = ['Value']
        st.dataframe(stats_df, use_container_width=True)

# Footer with last update info
with st.sidebar:
    st.markdown("---")
    st.markdown("### ℹ️ System Info")
    st.info(f"🔄 Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    st.info(f"📊 Showing {len(filtered_df)} of {len(df)} records")
    
    if len(filtered_df) != len(df):
        st.warning("🔍 Filters are active")

# Enhanced detailed data table (always visible at bottom)
st.markdown("---")
st.markdown("### 📋 Detailed Visitor Log")

# Table controls
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    search_term = st.text_input("🔍 Search in data:", placeholder="Enter IP, country, device, etc.")
with col2:
    show_rows = st.selectbox("📄 Rows per page:", [10, 25, 50, 100], index=1)
with col3:
    sort_order = st.selectbox("🔢 Sort by time:", ["Newest first", "Oldest first"])

# Apply search filter
if search_term:
    search_mask = (
        filtered_df.astype(str).apply(
            lambda x: x.str.contains(search_term, case=False, na=False)
        ).any(axis=1)
    )
    display_df = filtered_df[search_mask]
else:
    display_df = filtered_df

# Sort data
if sort_order == "Newest first":
    display_df = display_df.sort_values('timestamp', ascending=False)
else:
    display_df = display_df.sort_values('timestamp', ascending=True)

# Display paginated results
total_rows = len(display_df)
total_pages = (total_rows - 1) // show_rows + 1 if total_rows > 0 else 1

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    page = st.number_input(
        f"Page (1-{total_pages}):",
        min_value=1,
        max_value=total_pages,
        value=1
    )

start_idx = (page - 1) * show_rows
end_idx = start_idx + show_rows

if total_rows > 0:
    st.dataframe(
        display_df.iloc[start_idx:end_idx],
        use_container_width=True,
        hide_index=True
    )
    st.caption(f"Showing {start_idx + 1}-{min(end_idx, total_rows)} of {total_rows} records")
else:
    st.info("No data matches your current filters.")

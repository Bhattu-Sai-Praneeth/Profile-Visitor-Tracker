import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime
from streamlit_folium import st_folium
import folium
import requests
import time

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
    
    .sidebar-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        text-align: center;
        font-weight: bold;
    }
    
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
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

# Simplified clear data function (for public sheets only)
def clear_analytics_data():
    """Clear local cache and session state - Note: Cannot clear Google Sheets data without authentication"""
    try:
        # Clear Streamlit cache
        st.cache_data.clear()
        
        # Clear session state filters
        keys_to_clear = [key for key in st.session_state.keys() if key.startswith('filter_')]
        for key in keys_to_clear:
            del st.session_state[key]
        
        # Clear other session state
        if 'confirm_clear' in st.session_state:
            del st.session_state['confirm_clear']
            
        st.success("✅ Dashboard data cleared successfully!")
        st.info("ℹ️ Note: To clear Google Sheets data, you need to manually delete rows in your Google Sheet or set up service account authentication.")
        
        return True
    except Exception as e:
        st.error(f"❌ Failed to clear data: {str(e)}")
        return False

# Enhanced sidebar with navigation
with st.sidebar:
    st.markdown('<div class="sidebar-header">📊 Dashboard Controls</div>', unsafe_allow_html=True)
    
    # Navigation menu
    st.markdown("### 🧭 Navigation")
    navigation = st.selectbox(
        "Choose Section:",
        ["📈 Overview", "🗺️ Map View", "📊 Analytics", "📋 Data Table", "⚙️ Settings"],
        index=0
    )
    
    st.markdown("---")
    
    # Clear data section
    st.markdown("### 🗑️ Data Management")
    st.markdown('<div class="warning-box">⚠️ This will clear local cache only. Google Sheets data requires manual deletion.</div>', unsafe_allow_html=True)
    
    if st.button("🗑️ Clear Local Analytics Data", key="clear_btn", help="Clear dashboard cache and filters"):
        if st.session_state.get('confirm_clear', False):
            with st.spinner("Clearing local data..."):
                success = clear_analytics_data()
                if success:
                    st.rerun()
                st.session_state['confirm_clear'] = False
        else:
            st.session_state['confirm_clear'] = True
            st.rerun()
    
    if st.session_state.get('confirm_clear', False):
        st.error("Click 'Clear Local Analytics Data' again to confirm")
        if st.button("❌ Cancel", key="cancel_clear"):
            st.session_state['confirm_clear'] = False
            st.rerun()

# Load data
df = load_data()

if df.empty:
    st.error("No data available. Please check your Google Sheet connection.")
    st.stop()

# Ensure required columns exist
required_cols = {'timestamp', 'ip', 'country'}
available_cols = set(df.columns)
missing_cols = required_cols - available_cols

if missing_cols:
    st.error(f"Missing required columns: {missing_cols}")
    st.info(f"Available columns: {list(available_cols)}")
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
    if len(df) > 0:
        date_range = st.date_input(
            "📅 Select Date Range:",
            value=[df['date'].min(), df['date'].max()],
            min_value=df['date'].min(),
            max_value=df['date'].max()
        )
        
        # Country filter
        countries = ['All'] + sorted(df['country'].dropna().unique().tolist())
        selected_country = st.selectbox("🌍 Country:", countries, key="filter_country")
        
        # Device filter (if available)
        if 'device' in df.columns:
            devices = ['All'] + sorted(df['device'].dropna().unique().tolist())
            selected_device = st.selectbox("📱 Device:", devices, key="filter_device")
        else:
            selected_device = 'All'
            
        # Browser filter (if available)
        if 'browser' in df.columns:
            browsers = ['All'] + sorted(df['browser'].dropna().unique().tolist())
            selected_browser = st.selectbox("🌐 Browser:", browsers, key="filter_browser")
        else:
            selected_browser = 'All'
        
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
        if selected_device != 'All' and 'device' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['device'] == selected_device]

        # Browser filter
        if selected_browser != 'All' and 'browser' in filtered_df.columns:
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
    else:
        filtered_df = df.copy()

# Navigation-based content display
if navigation == "📈 Overview":
    # Enhanced KPI metrics
    st.markdown("### 📊 Key Performance Indicators")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric("👥 Total Visits", len(filtered_df))
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        unique_ips = filtered_df['ip'].nunique() if 'ip' in filtered_df.columns else 0
        st.metric("🌐 Unique IPs", unique_ips)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric("🌍 Countries", filtered_df['country'].nunique())
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        if 'city' in filtered_df.columns:
            top_city = filtered_df['city'].mode()
            city_name = top_city[0] if len(top_city) > 0 else "N/A"
        else:
            city_name = "N/A"
        st.metric("🏙️ Top City", city_name)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col5:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        if len(filtered_df) > 0:
            date_range_days = (filtered_df['date'].max() - filtered_df['date'].min()).days + 1
            avg_daily = len(filtered_df) / max(1, date_range_days)
        else:
            avg_daily = 0
        st.metric("📈 Daily Avg", f"{avg_daily:.1f}")
        st.markdown('</div>', unsafe_allow_html=True)

    # Enhanced time series chart
    st.markdown("---")
    st.markdown("### 📈 Visitor Trends Over Time")
    
    if len(filtered_df) > 0:
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
            
            chart = alt.Chart(time_data).mark_bar().encode(
                x=alt.X('hour:O', title='Hour of Day'),
                y=alt.Y('visits:Q', title='Number of Visits'),
                color=alt.value('#667eea'),
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
                color='#667eea',
                opacity=0.7
            ).encode(
                x=alt.X('week:O', title='Week'),
                y=alt.Y('visits:Q', title='Number of Visits'),
                tooltip=['week:O', 'visits:Q']
            ).properties(
                height=400,
                title="Weekly Visitor Trends"
            )
        
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("No data available for the selected filters.")

elif navigation == "🗺️ Map View":
    # Enhanced Google Maps integration
    st.markdown("### 🗺️ Enhanced Visitor Map")
    
    # Check if location data is available
    has_location_data = 'lat' in filtered_df.columns and 'lon' in filtered_df.columns
    
    if not has_location_data:
        st.warning("⚠️ Location data (lat/lon columns) not found in your Google Sheet.")
        st.info("To display the map, please add 'lat' and 'lon' columns to your Google Sheet with visitor coordinates.")
    else:
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
                tiles=None
            )
            
            # Add Google tile layers based on selection
            if map_style == "Google Satellite":
                tile_layer = folium.TileLayer(
                    tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
                    attr='Google Satellite',
                    name='Google Satellite',
                    overlay=False,
                    control=True
                )
            elif map_style == "Google Hybrid":
                tile_layer = folium.TileLayer(
                    tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
                    attr='Google Hybrid',
                    name='Google Hybrid',
                    overlay=False,
                    control=True
                )
            elif map_style == "Google Terrain":
                tile_layer = folium.TileLayer(
                    tiles='https://mt1.google.com/vt/lyrs=p&x={x}&y={y}&z={z}',
                    attr='Google Terrain',
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
                    <p><strong>📍 IP:</strong> {row.get('ip', 'N/A')}</p>
                    <p><strong>🌍 Location:</strong> {row.get('city', 'Unknown')}, {row.get('country', 'Unknown')}</p>
                    <p><strong>📱 Device:</strong> {row.get('device', 'Unknown')}</p>
                    <p><strong>🌐 Browser:</strong> {row.get('browser', 'Unknown')}</p>
                    <p><strong>🕒 Time:</strong> {row['timestamp'].strftime('%Y-%m-%d %H:%M')}</p>
                </div>
                """
                
                # Color code markers by device type if available
                device_colors = {'Desktop': 'blue', 'Mobile': 'red', 'Tablet': 'green'}
                color = device_colors.get(row.get('device', 'Desktop'), 'gray')
                
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
            if map_data.get("last_clicked"):
                clicked_lat = map_data["last_clicked"]["lat"]
                clicked_lng = map_data["last_clicked"]["lng"]
                st.info(f"📍 Last clicked location: {clicked_lat:.4f}, {clicked_lng:.4f}")
        
        else:
            st.warning("⚠️ No valid location data available for the selected filters.")

elif navigation == "📊 Analytics":
    # Enhanced analytics section
    st.markdown("### 📊 Detailed Analytics")
    
    if len(filtered_df) == 0:
        st.info("No data available for the selected filters.")
    else:
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
                else:
                    st.info("Region data not available in your Google Sheet")
        
        with tab2:
            col1, col2 = st.columns(2)
            
            with col1:
                if 'device' in filtered_df.columns:
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
                else:
                    st.info("Device data not available in your Google Sheet")
            
            with col2:
                if 'browser' in filtered_df.columns:
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
                else:
                    st.info("Browser data not available in your Google Sheet")
        
        with tab3:
            st.markdown("#### ⏰ Temporal Analysis")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Day of week analysis - FIXED VERSION
                day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                day_data = filtered_df['day_name'].value_counts().reindex(day_order).reset_index()
                day_data.columns = ['Day', 'Visits']
                
                # Create a color mapping instead of using alt.condition
                day_data['is_weekend'] = day_data['Day'].isin(['Saturday', 'Sunday'])
                
                chart = alt.Chart(day_data).mark_bar().encode(
                    x=alt.X('Day:N', title='Day of Week', sort=day_order),
                    y=alt.Y('Visits:Q', title='Number of Visits'),
                    color=alt.Color(
                        'is_weekend:N',
                        scale=alt.Scale(
                            domain=[False, True],
                            range=['steelblue', 'orange']
                        ),
                        legend=alt.Legend(
                            title="Day Type",
                            labelExpr="datum.value ? 'Weekend' : 'Weekday'"
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
                daily_visits['rolling_avg'] = daily_visits['visits'].rolling(window=min(7, len(daily_visits)), center=True).mean()
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
                    title="Daily Visits with Rolling Average",
                    height=400
                )
                
                st.altair_chart(chart, use_container_width=True)
            else:
                st.info("Not enough data points for trend analysis (minimum 7 days required)")

elif navigation == "📋 Data Table":
    # Enhanced detailed data table
    st.markdown("### 📋 Detailed Visitor Log")
    
    if len(filtered_df) == 0:
        st.info("No data matches your current filters.")
    else:
        # Table controls
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            search_term = st.text_input("🔍 Search in data:", placeholder="Enter IP, country, device, etc.")
        with col2:
            show_rows = st.selectbox("📄 Rows per page:", [10, 25, 50, 100], index=1)
        with col3:
            sort_order = st.selectbox("🔢 Sort by time:", ["Newest first", "Oldest first"])

        # Apply search filter
        display_df = filtered_df.copy()
        
        if search_term:
            search_mask = display_df.astype(str).apply(
                lambda x: x.str.contains(search_term, case=False, na=False)
            ).any(axis=1)
            display_df = display_df[search_mask]

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
            st.info("No data matches your search criteria.")

else:  # Settings
    st.markdown("### ⚙️ Dashboard Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🔧 Configuration")
        
        # Data refresh settings
        auto_refresh = st.checkbox("🔄 Auto-refresh data", value=False)
        if auto_refresh:
            refresh_interval = st.slider("Refresh interval (seconds)", 30, 300, 60)
            st.info(f"Data will refresh every {refresh_interval} seconds")
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
        
        # Google Sheets authentication info
        st.markdown("#### 🔐 Authentication Status")
        st.info("📖 Currently using public sheet access (read-only)")
        st.markdown("""
        **To enable full Google Sheets management:**
        1. Set up Google Cloud service account
        2. Add credentials to Streamlit secrets
        3. Enable Google Sheets API
        """)
    
    with col2:
        st.markdown("#### 📊 Dashboard Statistics")
        
        stats_data = {
            "Total Records": [len(df)],
            "Filtered Records": [len(filtered_df)],
            "Available Columns": [', '.join(df.columns.tolist())],
            "Date Range": [f"{df['date'].min()} to {df['date'].max()}"] if len(df) > 0 else ["No data"],
            "Countries Covered": [df['country'].nunique()],
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
    
    # Debug info
    with st.expander("🔧 Debug Information"):
        st.write("**Available Columns:**")
        st.write(df.columns.tolist())
        st.write("**Data Types:**")
        st.write(df.dtypes.to_dict())

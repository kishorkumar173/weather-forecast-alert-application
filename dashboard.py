"""
dashboard.py
------------------------------------------------------------------------------
Interactive Enterprise Meteorological Dashboard (Streamlit).
Visualizes real-time weather analytics, 5-day predictive trends,
geospatial maps, and dynamic risk alerts with threshold tuning.
------------------------------------------------------------------------------
"""

import streamlit as st
import pandas as pd
from datetime import datetime

from src.api_client import WeatherApiClient
from src.alert_engine import AlertEngine, AlertThresholds
from src.data_processor import WeatherDataProcessor
from src.visualizer import WeatherVisualizer
from src.report_generator import WeatherReportGenerator
from src.simulator import WeatherSimulator

# -----------------------------------------------------------------------------
# PAGE CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Weather Forecast & Risk Alert Dashboard",
    page_icon="🌦️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark modern enterprise styling
st.markdown("""
<style>
    .metric-card {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 15px;
        color: #f8fafc;
        margin-bottom: 10px;
    }
    .alert-critical {
        background-color: rgba(239, 68, 68, 0.15);
        border-left: 6px solid #ef4444;
        padding: 14px;
        border-radius: 6px;
        margin-bottom: 12px;
    }
    .alert-high {
        background-color: rgba(249, 115, 22, 0.15);
        border-left: 6px solid #f97316;
        padding: 14px;
        border-radius: 6px;
        margin-bottom: 12px;
    }
    .alert-moderate {
        background-color: rgba(234, 179, 8, 0.15);
        border-left: 6px solid #eab308;
        padding: 14px;
        border-radius: 6px;
        margin-bottom: 12px;
    }
    .alert-normal {
        background-color: rgba(34, 197, 94, 0.15);
        border-left: 6px solid #22c55e;
        padding: 14px;
        border-radius: 6px;
        margin-bottom: 12px;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# INITIALIZE SERVICES
# -----------------------------------------------------------------------------
@st.cache_resource
def get_services():
    client = WeatherApiClient()
    data_proc = WeatherDataProcessor()
    vis = WeatherVisualizer()
    rep = WeatherReportGenerator()
    sim = WeatherSimulator()
    return client, data_proc, vis, rep, sim

api_client, data_processor, visualizer, report_gen, simulator = get_services()

# -----------------------------------------------------------------------------
# SIDEBAR CONTROLS & THRESHOLD CALIBRATION
# -----------------------------------------------------------------------------
st.sidebar.image("https://images.unsplash.com/photo-1592210454359-9043f067919b?w=400&q=80", use_container_width=True)
st.sidebar.title("⚡ Control Panel")

data_mode = st.sidebar.radio(
    "Data Ingestion Mode",
    ["Virtual Simulator (Safe Offline Mode)", "Live REST API (OpenWeather / WeatherAPI)"]
)

# City Selection
if "Virtual" in data_mode:
    sim_type = st.sidebar.selectbox(
        "Simulation Scenario",
        ["Preset City", "Severe Heatwave", "Monsoon Torrential Rain", "Coastal Gale Storm", "Sub-Zero Freeze", "Dense Smog AQI"]
    )
    if sim_type == "Preset City":
        city = st.sidebar.selectbox("Select Benchmark City", ["Mumbai", "London", "Tokyo", "New York", "Sydney", "Delhi"])
    else:
        city = st.sidebar.text_input("Target Location Name", value="Regional Sector 4")
else:
    city = st.sidebar.text_input("Enter City / Region", value="Mumbai")

st.sidebar.markdown("---")
st.sidebar.subheader("🛡️ Risk Threshold Settings")
with st.sidebar.expander("Calibrate Alert Thresholds", expanded=False):
    t_high = st.slider("Heatwave Trigger (°C)", min_value=30.0, max_value=50.0, value=38.0, step=0.5)
    t_low = st.slider("Frost / Cold Trigger (°C)", min_value=-15.0, max_value=15.0, value=4.0, step=0.5)
    r_rain = st.slider("Heavy Rain Trigger (mm)", min_value=5.0, max_value=50.0, value=15.0, step=1.0)
    w_wind = st.slider("Gale Wind Trigger (km/h)", min_value=20.0, max_value=100.0, value=40.0, step=2.0)
    h_humid = st.slider("High Humidity Trigger (%)", min_value=60, max_value=100, value=85, step=1)
    a_aqi = st.slider("AQI Hazard Trigger (PM2.5)", min_value=50.0, max_value=300.0, value=100.0, step=5.0)

custom_thresholds = AlertThresholds(
    temp_high_c=t_high,
    temp_low_c=t_low,
    rain_heavy_mm=r_rain,
    wind_gale_kmh=w_wind,
    humidity_high_pct=h_humid,
    aqi_pm25_hazard=a_aqi
)
alert_engine = AlertEngine(custom_thresholds)

# -----------------------------------------------------------------------------
# DATA INGESTION
# -----------------------------------------------------------------------------
force_sim = "Virtual" in data_mode
if force_sim and sim_type != "Preset City":
    scenario_map = {
        "Severe Heatwave": "heatwave",
        "Monsoon Torrential Rain": "monsoon",
        "Coastal Gale Storm": "gale",
        "Sub-Zero Freeze": "freeze",
        "Dense Smog AQI": "air_hazard"
    }
    raw_weather = simulator.simulate_scenario(scenario_map[sim_type], city_name=city)
    raw_weather["data_source"] = f"Virtual Atmospheric Simulator [{sim_type.upper()}]"
else:
    raw_weather = api_client.fetch_weather_and_forecast(city=city, force_simulation=force_sim)

current = raw_weather.get("current", {})
forecast_list = raw_weather.get("forecast_5d", [])
forecast_df = data_processor.forecast_to_dataframe(forecast_list)
summary = data_processor.compute_summary_metrics(current, forecast_df)
alerts = alert_engine.evaluate(current, city_override=raw_weather.get("city", city))

# -----------------------------------------------------------------------------
# MAIN DASHBOARD INTERFACE
# -----------------------------------------------------------------------------
st.title("🌦️ Enterprise Weather Intelligence & Risk Alert System")
st.caption(f"📍 Location: **{raw_weather.get('city', city)}, {raw_weather.get('country', '')}** | Data Source: `{raw_weather.get('data_source', 'N/A')}` | Synchronized: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}`")

# 1. RISK ALERT BANNERS
critical_alerts = [a for a in alerts if a.severity in ("CRITICAL", "HIGH")]
moderate_alerts = [a for a in alerts if a.severity == "MODERATE"]
normal_alerts = [a for a in alerts if a.severity in ("NORMAL", "INFO")]

if critical_alerts:
    for a in critical_alerts:
        badge_cls = "alert-critical" if a.severity == "CRITICAL" else "alert-high"
        st.markdown(f"""
        <div class="{badge_cls}">
            <h4 style="margin:0; color:#f87171;">⚠️ {a.title} [{a.severity}]</h4>
            <p style="margin:5px 0;">{a.description}</p>
            <b>Sectors Impacted:</b> {', '.join(a.affected_sectors)}<br/>
            <b>Operational Recommendation:</b> {a.recommendation}
        </div>
        """, unsafe_allow_html=True)

if moderate_alerts:
    for a in moderate_alerts:
        st.markdown(f"""
        <div class="alert-moderate">
            <h4 style="margin:0; color:#fbbf24;">⚡ {a.title} [MODERATE]</h4>
            <p style="margin:5px 0;">{a.description}</p>
            <b>Sectors Impacted:</b> {', '.join(a.affected_sectors)}<br/>
            <b>Operational Recommendation:</b> {a.recommendation}
        </div>
        """, unsafe_allow_html=True)

if normal_alerts and not (critical_alerts or moderate_alerts):
    for a in normal_alerts:
        st.markdown(f"""
        <div class="alert-normal">
            <h4 style="margin:0; color:#4ade80;">✅ {a.title}</h4>
            <p style="margin:5px 0;">{a.description}</p>
            <b>Operational Status:</b> {a.recommendation}
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# 2. KEY ATMOSPHERIC KPI CARDS
kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)
with kpi1:
    st.metric("Temperature", f"{current.get('temperature', 0)}°C", f"Feels {current.get('feels_like', 0)}°C")
with kpi2:
    st.metric("Precipitation (1h)", f"{current.get('rain_1h_mm', 0)} mm", "Rainfall")
with kpi3:
    st.metric("Wind Speed", f"{current.get('wind_speed_kmh', 0)} km/h", f"Gust {current.get('wind_gust_kmh', 0)}")
with kpi4:
    st.metric("Humidity", f"{current.get('humidity', 0)}%", f"Pressure {current.get('pressure', 0)} hPa")
with kpi5:
    st.metric("Condition", current.get("weather_condition", "Fair")[:16])
with kpi6:
    st.metric("AQI (PM2.5)", f"{current.get('aqi_pm25', 0)} µg/m³", "Air Quality")

st.markdown("---")

# 3. INTERACTIVE VISUALIZATION TABS
tab_charts, tab_table, tab_map, tab_export = st.tabs(["📊 Interactive Forecast Charts", "📅 5-Day Data Grid", "🗺️ Geographic Geospatial", "📥 Audit Reports"])

with tab_charts:
    if not forecast_df.empty:
        plotly_fig = visualizer.create_interactive_forecast_plotly(forecast_df, city)
        st.plotly_chart(plotly_fig, use_container_width=True)
    else:
        st.info("No forecast data available for visualization.")

with tab_table:
    st.subheader("5-Day Predictive Atmospheric Ledger")
    if not forecast_df.empty:
        display_cols = ["day", "date", "condition", "temp_max", "temp_min", "humidity", "rain_prob_pct", "rain_volume_mm", "wind_kmh"]
        available_cols = [c for c in display_cols if c in forecast_df.columns]
        st.dataframe(
            forecast_df[available_cols].style.highlight_max(subset=["temp_max", "rain_volume_mm", "wind_kmh"], color="#450a0a"),
            use_container_width=True
        )
    else:
        st.warning("Forecast horizon unavailable.")

with tab_map:
    st.subheader(f"Geospatial Coordinates: {raw_weather.get('city')}")
    coords = raw_weather.get("coordinates", {})
    lat = coords.get("lat", 20.0)
    lon = coords.get("lon", 78.0)
    map_df = pd.DataFrame([{"lat": lat, "lon": lon}])
    st.map(map_df, zoom=9)

with tab_export:
    st.subheader("Operational Audit & Compliance Reports")
    col_exp1, col_exp2 = st.columns(2)
    
    # Generate CSV & JSON
    csv_file = report_gen.export_csv_report(city, current, forecast_df, alerts)
    json_file = report_gen.export_json_report(city, raw_weather, alerts)
    
    with open(csv_file, "rb") as f_csv:
        col_exp1.download_button(
            label="📄 Download Operational CSV Report",
            data=f_csv,
            file_name=f"weather_report_{city.lower()}.csv",
            mime="text/csv",
            use_container_width=True
        )
        
    with open(json_file, "rb") as f_json:
        col_exp2.download_button(
            label="📋 Download Telemetry JSON Audit Log",
            data=f_json,
            file_name=f"weather_audit_{city.lower()}.json",
            mime="application/json",
            use_container_width=True
        )

# Footer
st.markdown("---")
st.caption("Proof-of-Work Project: Weather Forecast & Risk Alert Application | Built with Python 3.13, FastAPI, Streamlit, Pandas, Plotly")

"""
main.py
------------------------------------------------------------------------------
Main Command Line Interface (CLI) & System Orchestrator.
Cross-platform compatible across Windows (cp1252), Linux, and macOS.
Provides terminal execution, virtual anomaly simulations, static chart generation,
and launches for FastAPI and Streamlit dashboard servers.
------------------------------------------------------------------------------
"""

import argparse
import sys
import os
import subprocess
from datetime import datetime

# Configure UTF-8 encoding for standard output on Windows consoles
if sys.platform.startswith("win"):
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from src.api_client import WeatherApiClient
from src.alert_engine import AlertEngine, AlertThresholds
from src.data_processor import WeatherDataProcessor
from src.visualizer import WeatherVisualizer
from src.report_generator import WeatherReportGenerator
from src.simulator import WeatherSimulator


def print_banner():
    banner = """
================================================================================
     [WEATHER] FORECAST & RISK ALERT APPLICATION (CLI & ORCHESTRATOR)
================================================================================
"""
    print(banner)


def run_cli_weather_check(city: str, force_simulation: bool = False, scenario: str = None):
    """
    Executes a comprehensive meteorological assessment directly in the terminal.
    """
    api_client = WeatherApiClient()
    alert_engine = AlertEngine()
    data_processor = WeatherDataProcessor()
    visualizer = WeatherVisualizer()
    report_gen = WeatherReportGenerator()
    simulator = WeatherSimulator()

    print(f"[*] Ingesting meteorological telemetry for: '{city}'...")
    if scenario:
        weather_data = simulator.simulate_scenario(scenario=scenario, city_name=city)
        weather_data["data_source"] = f"Virtual Simulator [Scenario: {scenario.upper()}]"
    else:
        weather_data = api_client.fetch_weather_and_forecast(city=city, force_simulation=force_simulation)

    current = weather_data.get("current", {})
    forecast_list = weather_data.get("forecast_5d", [])
    df = data_processor.forecast_to_dataframe(forecast_list)
    summary = data_processor.compute_summary_metrics(current, df)
    alerts = alert_engine.evaluate(current, city_override=weather_data.get("city", city))

    # 1. Output Header
    print(f"\n[+] Ingestion Success!")
    print(f"    Target Location: {weather_data.get('city')}, {weather_data.get('country')}")
    print(f"    Data Ingestion Provider: {weather_data.get('data_source')}")
    print(f"    Observation Timestamp: {current.get('timestamp')}")
    print("-" * 80)

    # 2. Current Conditions
    print("[+] CURRENT METEOROLOGICAL OBSERVATION:")
    print(f"    Temperature:       {current.get('temperature')} C (Feels like: {current.get('feels_like')} C)")
    print(f"    Atmospheric State: {current.get('weather_condition')}")
    print(f"    Relative Humidity: {current.get('humidity')}% | Pressure: {current.get('pressure')} hPa")
    print(f"    Wind Speed:        {current.get('wind_speed_kmh')} km/h (Gusts: {current.get('wind_gust_kmh')} km/h)")
    print(f"    Rain Volume (1h):  {current.get('rain_1h_mm')} mm")
    print(f"    Air Quality (AQI): {current.get('aqi_pm25')} ug/m3 PM2.5")
    print("-" * 80)

    # 3. 5-Day Forecast Grid
    print("[+] 5-DAY PREDICTIVE FORECAST HORIZON:")
    print(f"    {'Day':<8} | {'Date':<10} | {'Max C':<7} | {'Min C':<7} | {'Rain (mm)':<10} | {'Wind (km/h)':<11} | {'Condition':<20}")
    print("    " + "-" * 76)
    for f in forecast_list:
        print(f"    {f.get('day'):<8} | {f.get('date'):<10} | {f.get('temp_max', 0):<7.1f} | {f.get('temp_min', 0):<7.1f} | {f.get('rain_volume_mm', 0):<10.1f} | {f.get('wind_kmh', 0):<11.1f} | {f.get('condition', ''):<20}")
    print("-" * 80)

    # 4. Evaluated Alerts
    print("[+] RISK EVALUATION & HAZARD ALERTS:")
    for a in alerts:
        sev_tag = f"[{a.severity}]"
        print(f"    [!] {sev_tag:<10} : {a.title}")
        print(f"        Trigger:       {a.trigger_metric} = {a.trigger_value} (Threshold: {a.threshold_value})")
        print(f"        Details:       {a.description}")
        print(f"        Sectors:       {', '.join(a.affected_sectors)}")
        print(f"        Action Advice: {a.recommendation}\n")
    print("-" * 80)

    # 5. Export artifacts
    chart_path = visualizer.generate_static_forecast_plot(df, weather_data.get("city", city))
    csv_path = report_gen.export_csv_report(weather_data.get("city", city), current, df, alerts)
    json_path = report_gen.export_json_report(weather_data.get("city", city), weather_data, alerts)

    print("[+] ARTIFACTS GENERATED:")
    print(f"    [*] Static Plot:  {chart_path}")
    print(f"    [*] CSV Report:   {csv_path}")
    print(f"    [*] JSON Audit:   {json_path}")
    print("=" * 80)


def main():
    print_banner()
    parser = argparse.ArgumentParser(description="Weather Forecast & Risk Alert System Runner")
    parser.add_argument("--city", type=str, default="Mumbai", help="Target city name (e.g. London, Mumbai, Tokyo)")
    parser.add_argument("--simulate", action="store_true", help="Run in virtual simulation mode")
    parser.add_argument("--scenario", type=str, default=None, choices=["heatwave", "monsoon", "gale", "freeze", "moderate", "air_hazard"], help="Simulate a specific meteorological anomaly")
    parser.add_argument("--serve", action="store_true", help="Launch FastAPI REST server via Uvicorn")
    parser.add_argument("--dashboard", action="store_true", help="Launch interactive Streamlit dashboard")
    parser.add_argument("--port", type=int, default=8000, help="Port for FastAPI server (default: 8000)")

    args = parser.parse_args()

    if args.serve:
        print(f"[*] Starting FastAPI REST API on http://127.0.0.1:{args.port} ...")
        print("[*] Interactive Swagger Docs available at http://127.0.0.1:8000/docs")
        subprocess.run([sys.executable, "-m", "uvicorn", "app:app", "--host", "127.0.0.1", "--port", str(args.port), "--reload"])
    elif args.dashboard:
        print("[*] Launching Streamlit Dashboard ...")
        subprocess.run([sys.executable, "-m", "streamlit", "run", "dashboard.py"])
    else:
        run_cli_weather_check(
            city=args.city,
            force_simulation=args.simulate,
            scenario=args.scenario
        )


if __name__ == "__main__":
    main()

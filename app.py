"""
app.py
------------------------------------------------------------------------------
Enterprise FastAPI REST API Backend for Weather Forecast & Alert Application.
Provides high-throughput async endpoints for current weather retrieval,
multi-day forecasts, rule-engine hazard evaluations, and report generation.
------------------------------------------------------------------------------
"""

from typing import Optional, Dict, Any
from fastapi import FastAPI, Query, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.api_client import WeatherApiClient
from src.alert_engine import AlertEngine, AlertThresholds
from src.data_processor import WeatherDataProcessor
from src.simulator import WeatherSimulator
from src.report_generator import WeatherReportGenerator
from src.visualizer import WeatherVisualizer

app = FastAPI(
    title="Weather Forecast & Risk Alert API",
    description="Industry-grade REST API providing real-time meteorological intelligence and risk alerting for logistics, agriculture, and public safety.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for front-end integration (Next.js, React, Streamlit, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared Service Singletons
api_client = WeatherApiClient()
alert_engine = AlertEngine()
data_processor = WeatherDataProcessor()
simulator = WeatherSimulator()
report_generator = WeatherReportGenerator()
visualizer = WeatherVisualizer()


class CustomEvaluationRequest(BaseModel):
    city: str = Field(default="Custom City", example="Mumbai")
    temperature: float = Field(default=35.0, example=41.5)
    humidity: float = Field(default=80.0, example=88.0)
    wind_speed_kmh: float = Field(default=25.0, example=45.0)
    rain_1h_mm: float = Field(default=0.0, example=22.0)
    aqi_pm25: float = Field(default=35.0, example=120.0)
    custom_thresholds: Optional[AlertThresholds] = None


@app.get("/", tags=["General"])
def root():
    return {
        "project": "Weather Forecast & Alert Application",
        "version": "1.0.0",
        "status": "ONLINE",
        "documentation": "/docs",
        "endpoints": [
            "/api/v1/health",
            "/api/v1/weather/current",
            "/api/v1/weather/forecast",
            "/api/v1/weather/simulate",
            "/api/v1/weather/report"
        ]
    }


@app.get("/api/v1/health", tags=["General"])
def health_check():
    return {
        "status": "healthy",
        "api_provider": api_client.provider,
        "is_live_key_present": api_client._is_valid_key(),
        "simulation_fallback_ready": True
    }


@app.get("/api/v1/weather/current", tags=["Weather Intelligence"])
def get_current_weather(
    city: str = Query(default="Mumbai", description="Name of the city or municipality"),
    force_simulation: bool = Query(default=False, description="Force virtual offline simulation")
):
    """
    Fetches real-time observation and computes active risk alerts.
    """
    try:
        raw_data = api_client.fetch_weather_and_forecast(city=city, force_simulation=force_simulation)
        current = raw_data.get("current", {})
        alerts = alert_engine.evaluate(current, city_override=raw_data.get("city", city))
        
        return {
            "city": raw_data.get("city", city),
            "country": raw_data.get("country", ""),
            "coordinates": raw_data.get("coordinates", {}),
            "data_source": raw_data.get("data_source", "Unknown"),
            "current_weather": current,
            "active_alerts_count": len([a for a in alerts if a.severity != "NORMAL"]),
            "alerts": [a.model_dump() for a in alerts]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process weather observation: {str(e)}")


@app.get("/api/v1/weather/forecast", tags=["Weather Intelligence"])
def get_forecast(
    city: str = Query(default="Mumbai", description="Target city"),
    force_simulation: bool = Query(default=False)
):
    """
    Retrieves 5-day predictive forecast and statistical summary aggregates.
    """
    raw_data = api_client.fetch_weather_and_forecast(city=city, force_simulation=force_simulation)
    forecast_list = raw_data.get("forecast_5d", [])
    df = data_processor.forecast_to_dataframe(forecast_list)
    summary = data_processor.compute_summary_metrics(raw_data.get("current", {}), df)
    
    return {
        "city": raw_data.get("city", city),
        "data_source": raw_data.get("data_source", ""),
        "summary_metrics": summary,
        "forecast_5d": forecast_list
    }


@app.post("/api/v1/weather/alerts/evaluate", tags=["Alert Engine"])
def evaluate_custom_conditions(req: CustomEvaluationRequest):
    """
    Runs rule-based hazard detection against user-provided telemetry parameters.
    """
    engine = AlertEngine(req.custom_thresholds) if req.custom_thresholds else alert_engine
    payload = {
        "city": req.city,
        "temperature": req.temperature,
        "humidity": req.humidity,
        "wind_speed_kmh": req.wind_speed_kmh,
        "rain_1h_mm": req.rain_1h_mm,
        "aqi_pm25": req.aqi_pm25
    }
    alerts = engine.evaluate(payload)
    return {
        "input_telemetry": payload,
        "alerts_generated": [a.model_dump() for a in alerts]
    }


@app.get("/api/v1/weather/simulate", tags=["Virtual Simulation"])
def run_simulation_scenario(
    scenario: str = Query(default="heatwave", description="Scenario: heatwave, monsoon, gale, freeze, moderate, air_hazard"),
    city: str = Query(default="SimulatedCity")
):
    """
    Executes a high-impact weather anomaly simulation for stress-testing and demonstration.
    """
    valid_scenarios = simulator.get_supported_scenarios()
    if scenario.lower() not in valid_scenarios:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid scenario. Supported scenarios: {valid_scenarios}"
        )
    sim_data = simulator.simulate_scenario(scenario=scenario, city_name=city)
    alerts = alert_engine.evaluate(sim_data["current"])
    
    return {
        "scenario": scenario,
        "simulation_data": sim_data,
        "evaluated_alerts": [a.model_dump() for a in alerts]
    }


@app.get("/api/v1/weather/report", tags=["Reporting"])
def generate_and_download_report(
    city: str = Query(default="Mumbai"),
    format: str = Query(default="csv", regex="^(csv|json)$")
):
    """
    Generates and exports an operational weather report in CSV or JSON.
    """
    raw_data = api_client.fetch_weather_and_forecast(city=city)
    df = data_processor.forecast_to_dataframe(raw_data.get("forecast_5d", []))
    alerts = alert_engine.evaluate(raw_data.get("current", {}), city_override=raw_data.get("city", city))

    if format == "csv":
        csv_path = report_generator.export_csv_report(city, raw_data.get("current", {}), df, alerts)
        with open(csv_path, "r", encoding="utf-8") as f:
            content = f.read()
        return Response(content=content, media_type="text/csv", headers={
            "Content-Disposition": f"attachment; filename=weather_report_{city.lower()}.csv"
        })
    else:
        json_path = report_generator.export_json_report(city, raw_data, alerts)
        with open(json_path, "r", encoding="utf-8") as f:
            content = f.read()
        return Response(content=content, media_type="application/json", headers={
            "Content-Disposition": f"attachment; filename=weather_report_{city.lower()}.json"
        })

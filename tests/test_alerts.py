"""
test_alerts.py
------------------------------------------------------------------------------
Automated Pytest Suite for Weather Risk Engine, Data Processor, & Simulator.
------------------------------------------------------------------------------
"""

import os
import pytest
from src.alert_engine import AlertEngine, AlertThresholds
from src.simulator import WeatherSimulator
from src.data_processor import WeatherDataProcessor
from src.report_generator import WeatherReportGenerator


@pytest.fixture
def alert_engine():
    return AlertEngine()


@pytest.fixture
def simulator():
    return WeatherSimulator()


@pytest.fixture
def test_temp_dir(tmp_path):
    return str(tmp_path)


def test_heatwave_alert(alert_engine):
    """Verifies that temperatures >= 38.0°C trigger a heatwave alert."""
    payload = {
        "city": "TestCity",
        "temperature": 40.5,
        "humidity": 45,
        "wind_speed_kmh": 15.0,
        "rain_1h_mm": 0.0,
        "aqi_pm25": 30.0
    }
    alerts = alert_engine.evaluate(payload)
    severities = [a.severity for a in alerts]
    categories = [a.category for a in alerts]
    
    assert "TEMPERATURE" in categories
    assert any(s in ["HIGH", "CRITICAL"] for s in severities)


def test_torrential_rain_alert(alert_engine):
    """Verifies that rain volume >= 15.0 mm triggers a rain alert."""
    payload = {
        "city": "RainCity",
        "temperature": 24.0,
        "humidity": 95,
        "wind_speed_kmh": 20.0,
        "rain_1h_mm": 22.0,
        "aqi_pm25": 15.0
    }
    alerts = alert_engine.evaluate(payload)
    categories = [a.category for a in alerts]
    assert "RAIN" in categories
    rain_alert = next(a for a in alerts if a.category == "RAIN")
    assert rain_alert.severity == "CRITICAL"


def test_freezing_cold_alert(alert_engine):
    """Verifies that sub-zero temperatures trigger freeze hazard."""
    payload = {
        "city": "FreezeCity",
        "temperature": -2.0,
        "humidity": 70,
        "wind_speed_kmh": 25.0,
        "rain_1h_mm": 0.0,
        "aqi_pm25": 20.0
    }
    alerts = alert_engine.evaluate(payload)
    categories = [a.category for a in alerts]
    assert "TEMPERATURE" in categories
    temp_alert = next(a for a in alerts if a.category == "TEMPERATURE")
    assert temp_alert.severity == "CRITICAL"
    assert "Freeze" in temp_alert.title or "Sub-Zero" in temp_alert.title


def test_gale_wind_alert(alert_engine):
    """Verifies that wind speed >= 40 km/h triggers wind advisory."""
    payload = {
        "city": "WindCity",
        "temperature": 22.0,
        "humidity": 60,
        "wind_speed_kmh": 48.0,
        "rain_1h_mm": 0.0,
        "aqi_pm25": 25.0
    }
    alerts = alert_engine.evaluate(payload)
    categories = [a.category for a in alerts]
    assert "WIND" in categories


def test_normal_stable_weather(alert_engine):
    """Verifies that benign conditions result in a NORMAL status."""
    payload = {
        "city": "CalmCity",
        "temperature": 22.0,
        "humidity": 55,
        "wind_speed_kmh": 12.0,
        "rain_1h_mm": 0.0,
        "aqi_pm25": 25.0
    }
    alerts = alert_engine.evaluate(payload)
    assert len(alerts) == 1
    assert alerts[0].severity == "NORMAL"


def test_simulator_scenarios(simulator):
    """Tests all simulation presets."""
    for sc in simulator.get_supported_scenarios():
        res = simulator.simulate_scenario(sc, "SimCity")
        assert "current" in res
        assert "forecast_5d" in res
        assert len(res["forecast_5d"]) == 5
        assert res["current"]["temperature"] is not None


def test_data_processor_dataframe():
    """Verifies DataFrame parsing and range computations."""
    sample_forecast = [
        {"day": "Day 1", "date": "2026-11-20", "temp_max": 30.0, "temp_min": 20.0, "humidity": 60, "rain_prob_pct": 20, "rain_volume_mm": 1.0, "wind_kmh": 15.0},
        {"day": "Day 2", "date": "2026-11-21", "temp_max": 32.0, "temp_min": 22.0, "humidity": 65, "rain_prob_pct": 40, "rain_volume_mm": 3.0, "wind_kmh": 18.0}
    ]
    df = WeatherDataProcessor.forecast_to_dataframe(sample_forecast)
    assert len(df) == 2
    assert "temp_range" in df.columns
    assert df.loc[0, "temp_range"] == 10.0


def test_report_generation(test_temp_dir):
    """Verifies CSV and JSON export functionality."""
    rep_gen = WeatherReportGenerator(reports_dir=test_temp_dir)
    engine = AlertEngine()
    current = {"temperature": 25.0, "humidity": 60, "wind_speed_kmh": 15.0, "rain_1h_mm": 0.0}
    alerts = engine.evaluate(current)
    
    csv_file = rep_gen.export_csv_report("TestCity", current, WeatherDataProcessor.forecast_to_dataframe([]), alerts)
    json_file = rep_gen.export_json_report("TestCity", {"current": current, "forecast_5d": []}, alerts)
    
    assert os.path.exists(csv_file)
    assert os.path.exists(json_file)
    assert os.path.getsize(csv_file) > 50
    assert os.path.getsize(json_file) > 50

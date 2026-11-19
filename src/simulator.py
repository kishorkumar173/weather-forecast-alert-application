"""
simulator.py
------------------------------------------------------------------------------
Virtual Atmospheric Simulation Engine.
Enables offline development, testing, CI/CD pipeline validation, and portfolio
demonstration without requiring an active external API key.
Provides predefined high-risk meteorological scenarios and synthetic data synthesis.
------------------------------------------------------------------------------
"""

import json
import os
import random
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List


class WeatherSimulator:
    """Simulates realistic atmospheric observations and multi-day forecasts."""

    def __init__(self, sample_data_path: str = None):
        if not sample_data_path:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            sample_data_path = os.path.join(base_dir, "data", "sample_weather.json")
        self.sample_data_path = sample_data_path
        self._cached_data = self._load_sample_data()

    def _load_sample_data(self) -> Dict[str, Any]:
        """Loads static baseline sample data from JSON if available."""
        if os.path.exists(self.sample_data_path):
            try:
                with open(self.sample_data_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"cities": {}}

    def get_supported_scenarios(self) -> List[str]:
        return ["heatwave", "monsoon", "gale", "freeze", "moderate", "air_hazard"]

    def simulate_scenario(self, scenario: str, city_name: str = "SimulatedCity") -> Dict[str, Any]:
        """
        Synthesizes a specialized high-impact weather condition scenario.
        """
        scenario = scenario.lower()
        now_iso = datetime.now(timezone.utc).isoformat()

        if scenario == "heatwave":
            current = {
                "temperature": 43.5,
                "feels_like": 49.8,
                "temp_min": 35.0,
                "temp_max": 44.0,
                "humidity": 45,
                "pressure": 1004,
                "wind_speed_kmh": 18.0,
                "wind_gust_kmh": 26.0,
                "wind_direction_deg": 280,
                "weather_condition": "Severe Heatwave / Blistering Sun",
                "weather_code": 800,
                "rain_1h_mm": 0.0,
                "cloudiness_pct": 5,
                "visibility_meters": 7000,
                "uv_index": 11.0,
                "aqi_pm25": 85.0,
                "timestamp": now_iso
            }
        elif scenario == "monsoon":
            current = {
                "temperature": 27.5,
                "feels_like": 31.0,
                "temp_min": 25.0,
                "temp_max": 28.5,
                "humidity": 96,
                "pressure": 996,
                "wind_speed_kmh": 38.0,
                "wind_gust_kmh": 55.0,
                "wind_direction_deg": 210,
                "weather_condition": "Torrential Monsoon Downpour",
                "weather_code": 502,
                "rain_1h_mm": 32.5,
                "cloudiness_pct": 100,
                "visibility_meters": 2000,
                "uv_index": 1.0,
                "aqi_pm25": 18.0,
                "timestamp": now_iso
            }
        elif scenario == "gale":
            current = {
                "temperature": 19.0,
                "feels_like": 16.5,
                "temp_min": 17.0,
                "temp_max": 21.0,
                "humidity": 70,
                "pressure": 984,
                "wind_speed_kmh": 68.0,
                "wind_gust_kmh": 92.0,
                "wind_direction_deg": 90,
                "weather_condition": "Severe Coastal Gale Storm",
                "weather_code": 905,
                "rain_1h_mm": 18.0,
                "cloudiness_pct": 95,
                "visibility_meters": 4000,
                "uv_index": 2.0,
                "aqi_pm25": 30.0,
                "timestamp": now_iso
            }
        elif scenario == "freeze":
            current = {
                "temperature": -4.5,
                "feels_like": -11.0,
                "temp_min": -7.0,
                "temp_max": -2.0,
                "humidity": 82,
                "pressure": 1028,
                "wind_speed_kmh": 32.0,
                "wind_gust_kmh": 48.0,
                "wind_direction_deg": 350,
                "weather_condition": "Deep Freeze & Severe Frost",
                "weather_code": 602,
                "rain_1h_mm": 6.0,
                "cloudiness_pct": 90,
                "visibility_meters": 3000,
                "uv_index": 1.5,
                "aqi_pm25": 40.0,
                "timestamp": now_iso
            }
        elif scenario == "air_hazard":
            current = {
                "temperature": 28.0,
                "feels_like": 29.5,
                "temp_min": 22.0,
                "temp_max": 30.0,
                "humidity": 65,
                "pressure": 1012,
                "wind_speed_kmh": 6.0,
                "wind_gust_kmh": 10.0,
                "wind_direction_deg": 120,
                "weather_condition": "Dense Smog & Air Inversion",
                "weather_code": 711,
                "rain_1h_mm": 0.0,
                "cloudiness_pct": 50,
                "visibility_meters": 1500,
                "uv_index": 4.0,
                "aqi_pm25": 215.0,
                "timestamp": now_iso
            }
        else:  # Moderate / stable
            current = {
                "temperature": 24.0,
                "feels_like": 24.2,
                "temp_min": 19.0,
                "temp_max": 26.5,
                "humidity": 55,
                "pressure": 1015,
                "wind_speed_kmh": 14.0,
                "wind_gust_kmh": 20.0,
                "wind_direction_deg": 180,
                "weather_condition": "Fair / Clear Skies",
                "weather_code": 800,
                "rain_1h_mm": 0.0,
                "cloudiness_pct": 15,
                "visibility_meters": 10000,
                "uv_index": 6.0,
                "aqi_pm25": 32.0,
                "timestamp": now_iso
            }

        # Synthesize a coherent 5-day forecast
        forecast_5d = []
        base_date = datetime.now(timezone.utc)
        for i in range(1, 6):
            f_date = (base_date + timedelta(days=i)).strftime("%Y-%m-%d")
            delta_t = (i - 1) * 0.8
            forecast_5d.append({
                "day": f"Day {i}",
                "date": f_date,
                "temp_max": round(current["temp_max"] - delta_t, 1),
                "temp_min": round(current["temp_min"] - delta_t * 0.5, 1),
                "humidity": min(98, max(20, current["humidity"] + random.randint(-5, 5))),
                "condition": current["weather_condition"],
                "rain_prob_pct": min(100, max(0, int(current["rain_1h_mm"] * 3) + random.randint(-5, 5))),
                "rain_volume_mm": max(0.0, round(current["rain_1h_mm"] * (1.1 - 0.15 * i), 1)),
                "wind_kmh": round(max(5.0, current["wind_speed_kmh"] * (1.0 - 0.05 * i)), 1)
            })

        return {
            "city": city_name,
            "country": "SIM",
            "coordinates": {"lat": 28.6139, "lon": 77.2090},
            "source": f"Virtual Simulator ({scenario.upper()})",
            "current": current,
            "forecast_5d": forecast_5d
        }

    def get_weather_for_city(self, city: str) -> Dict[str, Any]:
        """
        Retrieves weather for a city from sample data, or creates a realistic
        dynamically synthesized profile if not in cache.
        """
        cities_dict = self._cached_data.get("cities", {})
        # Case-insensitive match in sample database
        for cached_city, payload in cities_dict.items():
            if cached_city.lower() == city.strip().lower():
                res = dict(payload)
                res["source"] = "Virtual Simulator (Cached Benchmark)"
                return res

        # Generate realistic data based on hash seed for repeatability
        seed_val = sum(ord(c) for c in city)
        random.seed(seed_val)
        temp = round(random.uniform(15.0, 36.0), 1)
        humidity = random.randint(35, 90)
        wind = round(random.uniform(8.0, 42.0), 1)
        rain = round(random.uniform(0.0, 18.0) if humidity > 75 else 0.0, 1)

        now_iso = datetime.now(timezone.utc).isoformat()
        current = {
            "temperature": temp,
            "feels_like": round(temp + (0.05 * humidity) - 2.0, 1),
            "temp_min": round(temp - 4.5, 1),
            "temp_max": round(temp + 3.5, 1),
            "humidity": humidity,
            "pressure": 1012,
            "wind_speed_kmh": wind,
            "wind_gust_kmh": round(wind * 1.3, 1),
            "wind_direction_deg": random.randint(0, 360),
            "weather_condition": "Scattered Clouds / Variable" if rain == 0 else "Passing Rain Showers",
            "weather_code": 801 if rain == 0 else 500,
            "rain_1h_mm": rain,
            "cloudiness_pct": random.randint(10, 80),
            "visibility_meters": 8000,
            "uv_index": round(random.uniform(3.0, 9.0), 1),
            "aqi_pm25": round(random.uniform(25.0, 95.0), 1),
            "timestamp": now_iso
        }

        forecast_5d = []
        base_date = datetime.now(timezone.utc)
        for i in range(1, 6):
            forecast_5d.append({
                "day": f"Day {i}",
                "date": (base_date + timedelta(days=i)).strftime("%Y-%m-%d"),
                "temp_max": round(temp + random.uniform(-2, 3), 1),
                "temp_min": round(temp - random.uniform(3, 7), 1),
                "humidity": min(95, max(30, humidity + random.randint(-10, 10))),
                "condition": "Partly Cloudy",
                "rain_prob_pct": random.randint(10, 60),
                "rain_volume_mm": round(random.uniform(0.0, 5.0), 1),
                "wind_kmh": round(wind + random.uniform(-5, 5), 1)
            })

        return {
            "city": city.title(),
            "country": "GLOBAL",
            "coordinates": {"lat": 20.0, "lon": 78.0},
            "source": "Virtual Simulator (Synthetic Generator)",
            "current": current,
            "forecast_5d": forecast_5d
        }

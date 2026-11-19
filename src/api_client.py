"""
api_client.py
------------------------------------------------------------------------------
Resilient Weather API Client with Automatic Virtual Simulator Fallback.
Supports OpenWeatherMap (Free Tier) and WeatherAPI.
Gracefully handles missing API keys, network timeouts, and rate limits
by seamlessly falling back to high-fidelity virtual simulation.
------------------------------------------------------------------------------
"""

import os
import requests
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from src.simulator import WeatherSimulator

load_dotenv()


class WeatherApiClient:
    """Enterprise HTTP API Client for Meteorological Ingestion."""

    def __init__(self, api_key: Optional[str] = None, provider: str = "openweathermap"):
        self.provider = provider.lower()
        self.api_key = api_key or os.getenv("OPENWEATHER_API_KEY", "") or os.getenv("WEATHERAPI_KEY", "")
        self.simulator = WeatherSimulator()
        self.timeout = 6.0  # seconds

    def _is_valid_key(self) -> bool:
        """Checks if the user provided an actual non-placeholder API key."""
        if not self.api_key:
            return False
        clean = self.api_key.strip().lower()
        invalid_markers = ["your_", "none", "xxxx", "test", "demo", "placeholder"]
        return not any(marker in clean for marker in invalid_markers) and len(clean) > 8

    def fetch_weather_and_forecast(self, city: str, force_simulation: bool = False) -> Dict[str, Any]:
        """
        Unified fetching method:
        Attempts live API ingestion; falls back instantly to simulation
        if credentials are absent or remote host fails.
        """
        force_env = os.getenv("FORCE_SIMULATION_MODE", "false").lower() == "true"
        if force_simulation or force_env or not self._is_valid_key():
            data = self.simulator.get_weather_for_city(city)
            data["data_source"] = "Virtual Simulator (Offline/Keyless Mode)"
            return data

        try:
            if self.provider == "openweathermap":
                return self._fetch_openweathermap(city)
            elif self.provider == "weatherapi":
                return self._fetch_weatherapi(city)
            else:
                data = self.simulator.get_weather_for_city(city)
                data["data_source"] = "Virtual Simulator (Unsupported Provider Fallback)"
                return data
        except Exception as err:
            # Fallback to simulator on network error, rate limit, or invalid city response
            data = self.simulator.get_weather_for_city(city)
            data["data_source"] = f"Virtual Simulator (Network Fallback: {str(err)[:50]})"
            return data

    def _fetch_openweathermap(self, city: str) -> Dict[str, Any]:
        """Queries OpenWeatherMap current weather and 5-day / 3-hour forecast."""
        base_url = "https://api.openweathermap.org/data/2.5"
        
        # 1. Current Weather
        cur_resp = requests.get(
            f"{base_url}/weather",
            params={"q": city, "appid": self.api_key, "units": "metric"},
            timeout=self.timeout
        )
        cur_resp.raise_for_status()
        cur_json = cur_resp.json()

        # 2. 5-Day Forecast
        fore_resp = requests.get(
            f"{base_url}/forecast",
            params={"q": city, "appid": self.api_key, "units": "metric"},
            timeout=self.timeout
        )
        fore_resp.raise_for_status()
        fore_json = fore_resp.json()

        # Normalization
        current_data = {
            "temperature": round(cur_json["main"]["temp"], 1),
            "feels_like": round(cur_json["main"]["feels_like"], 1),
            "temp_min": round(cur_json["main"]["temp_min"], 1),
            "temp_max": round(cur_json["main"]["temp_max"], 1),
            "humidity": cur_json["main"]["humidity"],
            "pressure": cur_json["main"]["pressure"],
            "wind_speed_kmh": round(cur_json.get("wind", {}).get("speed", 0.0) * 3.6, 1),
            "wind_gust_kmh": round(cur_json.get("wind", {}).get("gust", cur_json.get("wind", {}).get("speed", 0.0)) * 3.6, 1),
            "wind_direction_deg": cur_json.get("wind", {}).get("deg", 0),
            "weather_condition": cur_json["weather"][0]["description"].title(),
            "weather_code": cur_json["weather"][0]["id"],
            "rain_1h_mm": cur_json.get("rain", {}).get("1h", 0.0),
            "cloudiness_pct": cur_json.get("clouds", {}).get("all", 0),
            "visibility_meters": cur_json.get("visibility", 10000),
            "uv_index": 5.0,  # OWM one-call requires paid tier; baseline estimation
            "aqi_pm25": 45.0, # Baseline estimation
            "timestamp": cur_json.get("dt")
        }

        # Parse 5 daily buckets from 3-hour forecast list
        forecast_5d = []
        seen_days = set()
        day_counter = 1
        for item in fore_json.get("list", []):
            dt_txt = item.get("dt_txt", "")
            date_part = dt_txt.split(" ")[0]
            if date_part not in seen_days and len(seen_days) < 5:
                seen_days.add(date_part)
                forecast_5d.append({
                    "day": f"Day {day_counter}",
                    "date": date_part,
                    "temp_max": round(item["main"]["temp_max"], 1),
                    "temp_min": round(item["main"]["temp_min"], 1),
                    "humidity": item["main"]["humidity"],
                    "condition": item["weather"][0]["description"].title(),
                    "rain_prob_pct": int(item.get("pop", 0) * 100),
                    "rain_volume_mm": item.get("rain", {}).get("3h", 0.0),
                    "wind_kmh": round(item.get("wind", {}).get("speed", 0.0) * 3.6, 1)
                })
                day_counter += 1

        return {
            "city": cur_json["name"],
            "country": cur_json.get("sys", {}).get("country", ""),
            "coordinates": {
                "lat": cur_json.get("coord", {}).get("lat", 0.0),
                "lon": cur_json.get("coord", {}).get("lon", 0.0)
            },
            "data_source": "OpenWeatherMap Live REST API",
            "current": current_data,
            "forecast_5d": forecast_5d
        }

    def _fetch_weatherapi(self, city: str) -> Dict[str, Any]:
        """Queries WeatherAPI.com forecast endpoint."""
        url = "https://api.weatherapi.com/v1/forecast.json"
        resp = requests.get(
            url,
            params={"key": self.api_key, "q": city, "days": 5, "aqi": "yes"},
            timeout=self.timeout
        )
        resp.raise_for_status()
        data = resp.json()

        cur = data["current"]
        current_data = {
            "temperature": round(cur["temp_c"], 1),
            "feels_like": round(cur["feelslike_c"], 1),
            "temp_min": round(cur["temp_c"] - 3.0, 1),
            "temp_max": round(cur["temp_c"] + 2.0, 1),
            "humidity": cur["humidity"],
            "pressure": int(cur["pressure_mb"]),
            "wind_speed_kmh": round(cur["wind_kph"], 1),
            "wind_gust_kmh": round(cur.get("gust_kph", cur["wind_kph"]), 1),
            "wind_direction_deg": cur.get("wind_degree", 0),
            "weather_condition": cur["condition"]["text"],
            "weather_code": cur["condition"]["code"],
            "rain_1h_mm": round(cur.get("precip_mm", 0.0), 1),
            "cloudiness_pct": cur.get("cloud", 0),
            "visibility_meters": int(cur.get("vis_km", 10) * 1000),
            "uv_index": cur.get("uv", 5.0),
            "aqi_pm25": round(cur.get("air_quality", {}).get("pm2_5", 35.0), 1),
            "timestamp": cur.get("last_updated")
        }

        forecast_5d = []
        for i, fday in enumerate(data.get("forecast", {}).get("forecastday", [])):
            d = fday["day"]
            forecast_5d.append({
                "day": f"Day {i+1}",
                "date": fday["date"],
                "temp_max": round(d["maxtemp_c"], 1),
                "temp_min": round(d["mintemp_c"], 1),
                "humidity": d["avghumidity"],
                "condition": d["condition"]["text"],
                "rain_prob_pct": d.get("daily_chance_of_rain", 0),
                "rain_volume_mm": round(d.get("totalprecip_mm", 0.0), 1),
                "wind_kmh": round(d.get("maxwind_kph", 15.0), 1)
            })

        return {
            "city": data["location"]["name"],
            "country": data["location"]["country"],
            "coordinates": {
                "lat": data["location"]["lat"],
                "lon": data["location"]["lon"]
            },
            "data_source": "WeatherAPI.com Live API",
            "current": current_data,
            "forecast_5d": forecast_5d
        }

# REST API Specification: Weather Forecast & Alert Service

The service runs locally at `http://127.0.0.1:8000`. Interactive OpenAPI documentation is accessible at `/docs` (Swagger UI) and `/redoc` (ReDoc).

---

## Endpoints Summary

### 1. Health Status
- **Method**: `GET`
- **Route**: `/api/v1/health`
- **Description**: Returns operational status of the service, active API provider, and fallback readiness.
- **Sample Response**:
```json
{
  "status": "healthy",
  "api_provider": "openweathermap",
  "is_live_key_present": false,
  "simulation_fallback_ready": true
}
```

---

### 2. Current Weather & Risk Alerts
- **Method**: `GET`
- **Route**: `/api/v1/weather/current`
- **Query Parameters**:
  - `city` (string, default: `"Mumbai"`): City or regional jurisdiction name.
  - `force_simulation` (boolean, default: `false`): Force synthetic offline generator.
- **Sample Response**:
```json
{
  "city": "Mumbai",
  "country": "IN",
  "coordinates": {"lat": 19.0760, "lon": 72.8777},
  "data_source": "Virtual Simulator (Offline/Keyless Mode)",
  "current_weather": {
    "temperature": 39.4,
    "feels_like": 46.2,
    "humidity": 88,
    "wind_speed_kmh": 24.5,
    "rain_1h_mm": 0.0,
    "aqi_pm25": 142.0
  },
  "active_alerts_count": 3,
  "alerts": [
    {
      "alert_id": "HEAT-CRITICAL-Mumbai",
      "category": "TEMPERATURE",
      "severity": "CRITICAL",
      "title": "Extreme Severe Heatwave in Mumbai",
      "description": "Recorded temperature 39.4°C (Heat Index: 88.0°C)...",
      "affected_sectors": ["Citizens", "Logistics", "Power Grid"],
      "recommendation": "Suspend outdoor manual labor between 11 AM - 4 PM."
    }
  ]
}
```

---

### 3. Predictive 5-Day Forecast
- **Method**: `GET`
- **Route**: `/api/v1/weather/forecast`
- **Query Parameters**:
  - `city` (string, default: `"Mumbai"`)
- **Sample Response**:
```json
{
  "city": "Mumbai",
  "data_source": "Virtual Simulator",
  "summary_metrics": {
    "current_temp": 39.4,
    "5d_max_temp": 40.2,
    "5d_min_temp": 27.0,
    "5d_total_rain_mm": 75.5,
    "peak_rain_day": "Day 5 (45.0 mm)"
  },
  "forecast_5d": [ ... ]
}
```

---

### 4. Custom Anomaly Simulation
- **Method**: `GET`
- **Route**: `/api/v1/weather/simulate`
- **Query Parameters**:
  - `scenario` (`heatwave`, `monsoon`, `gale`, `freeze`, `air_hazard`)
  - `city` (string, default: `"SimulatedCity"`)

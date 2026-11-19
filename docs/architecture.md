# System Architecture: Weather Forecast & Risk Alert Application

## 1. High-Level Architectural Overview

The **Weather Forecast & Alert Application** is designed according to a clean **layered decoupling pattern**, separating external telemetry ingestion, meteorological business logic, analytical processing, and dual presentation layers (REST API & Interactive Streamlit Dashboard).

```
+-----------------------------------------------------------------------------------+
|                                 USER INTERFACES                                   |
|   +---------------------------------------+   +-------------------------------+   |
|   | Streamlit Web Dashboard               |   | Command Line Interface (CLI)  |   |
|   | (Real-time KPI cards, Plotly charts,  |   | (Terminal tables, alerts,     |   |
|   |  risk badges, CSV/JSON downloads)     |   |  chart generation runner)     |   |
|   +---------------------------------------+   +-------------------------------+   |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                              FASTAPI REST SERVICE                                 |
|   Endpoints:                                                                      |
|   - GET  /api/v1/health             : System telemetry & key verification         |
|   - GET  /api/v1/weather/current    : Real-time observations & active alerts      |
|   - GET  /api/v1/weather/forecast   : 5-Day predictive trend aggregations         |
|   - POST /api/v1/weather/alerts/eval: Custom telemetry risk evaluation            |
|   - GET  /api/v1/weather/simulate   : Virtual anomaly stress tests                |
|   - GET  /api/v1/weather/report     : CSV & JSON compliance downloads             |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                            APPLICATION LOGIC LAYER                                |
|   +-----------------------+   +--------------------+   +----------------------+   |
|   |   Alert Rule Engine   |   | Data Processor     |   | Report Generator     |   |
|   | (Heat, Cold, Rain,    |   | (Pandas DataFrame, |   | (CSV & JSON audit    |   |
|   |  Gale, AQI thresholds)|   |  aggregations, min/|   |  telemetry export)   |   |
|   |                       |   |  max thermal range)|   |                      |   |
|   +-----------------------+   +--------------------+   +----------------------+   |
|                                         |                                         |
|                                         v                                         |
|                               +--------------------+                              |
|                               | Visualizer Suite   |                              |
|                               | (Matplotlib static |                              |
|                               |  & Plotly charts)  |                              |
|                               +--------------------+                              |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                           INGESTION & DATA ACCESS LAYER                           |
|   +---------------------------------------+   +-------------------------------+   |
|   | OpenWeatherMap / WeatherAPI Client    |   | Virtual Meteorological        |   |
|   | (Live HTTP ingestion, timeout guard,  |   | Simulator                     |   |
|   |  auto-fallback to simulation)         |   | (Keyless offline generator,   |   |
|   |                                       |   |  pre-seeded disaster cases)   |   |
|   +---------------------------------------+   +-------------------------------+   |
+-----------------------------------------------------------------------------------+
```

## 2. Component Breakdown

### 2.1 Ingestion & Resilience Layer (`api_client.py` & `simulator.py`)
- **Fault-Tolerant Fallback**: If an API key is missing, invalid, or rate-limited, the system seamlessly redirects to the `WeatherSimulator`. This ensures zero crashes and 100% testability.
- **Provider Agnostic**: Normalizes responses from OpenWeatherMap and WeatherAPI into a standard internal dictionary schema.

### 2.2 Domain Logic & Rules Engine (`alert_engine.py`)
- **Multi-Factor Hazard Evaluation**:
  - **Heatwave**: Assesses ambient temperature and calculated Heat Index using the Rothfusz regression model.
  - **Cold & Frost**: Detects freezing transitions (< 0°C) and cold wave damage thresholds (< 4°C).
  - **Hydrological Inundation**: Monitors hourly precipitation rate against flooding benchmarks (> 15 mm/hr).
  - **Aerodynamic Gale**: Flags wind gusts and sustained speeds exceeding 40 km/h and 60 km/h.
  - **Respiratory Air Quality**: Assesses fine particulate matter (PM2.5) above 100 µg/m³.
- **Sector Mapping**: Automatically associates triggered hazards with logistics, agriculture, aviation, and public municipal operations.

### 2.3 Data Analytics & Reporting (`data_processor.py` & `report_generator.py`)
- Converts unstructured weather dictionaries into normalized Pandas DataFrames.
- Computes thermal oscillations, rain risk distributions, and creates standardized audit logs in `reports/`.

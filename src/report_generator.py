"""
report_generator.py
------------------------------------------------------------------------------
Enterprise Meteorological Report Generation Subsystem.
Compiles weather observations, statistical trends, and evaluated hazard alerts
into structured, auditable CSV and JSON reports saved in reports/.
------------------------------------------------------------------------------
"""

import json
import os
from datetime import datetime, timezone
from typing import Dict, Any, List
import pandas as pd
from src.alert_engine import WeatherAlert


class WeatherReportGenerator:
    """Compiles and exports enterprise audit reports."""

    def __init__(self, reports_dir: str = None):
        if not reports_dir:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            reports_dir = os.path.join(base_dir, "reports")
        self.reports_dir = reports_dir
        os.makedirs(self.reports_dir, exist_ok=True)

    def export_csv_report(
        self,
        city: str,
        current_data: Dict[str, Any],
        forecast_df: pd.DataFrame,
        alerts: List[WeatherAlert]
    ) -> str:
        """
        Exports a consolidated CSV report containing current conditions,
        forecast horizon, and triggered risk alerts.
        """
        timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        safe_city = "".join(c for c in city if c.isalnum() or c in ("_", "-")).lower()
        filepath = os.path.join(self.reports_dir, f"report_{safe_city}_{timestamp_str}.csv")

        # Prepare unified rows
        rows = []
        # Current observation row
        rows.append({
            "record_type": "CURRENT_OBSERVATION",
            "city": city,
            "period": "Current",
            "temperature_c": current_data.get("temperature", ""),
            "feels_like_c": current_data.get("feels_like", ""),
            "humidity_pct": current_data.get("humidity", ""),
            "pressure_hpa": current_data.get("pressure", ""),
            "wind_kmh": current_data.get("wind_speed_kmh", ""),
            "rain_mm": current_data.get("rain_1h_mm", 0.0),
            "condition": current_data.get("weather_condition", ""),
            "alert_severity": "",
            "alert_title": "",
            "alert_recommendation": ""
        })

        # Forecast rows
        if not forecast_df.empty:
            for _, r in forecast_df.iterrows():
                rows.append({
                    "record_type": "FORECAST",
                    "city": city,
                    "period": f"{r.get('day')} ({r.get('date')})",
                    "temperature_c": f"Max {r.get('temp_max')} / Min {r.get('temp_min')}",
                    "feels_like_c": "",
                    "humidity_pct": r.get("humidity", ""),
                    "pressure_hpa": "",
                    "wind_kmh": r.get("wind_kmh", ""),
                    "rain_mm": r.get("rain_volume_mm", 0.0),
                    "condition": r.get("condition", ""),
                    "alert_severity": "",
                    "alert_title": "",
                    "alert_recommendation": ""
                })

        # Alert rows
        for alert in alerts:
            rows.append({
                "record_type": "ALERT_TRIGGER",
                "city": city,
                "period": "Active Hazard Alert",
                "temperature_c": "",
                "feels_like_c": "",
                "humidity_pct": "",
                "pressure_hpa": "",
                "wind_kmh": "",
                "rain_mm": "",
                "condition": alert.category,
                "alert_severity": alert.severity,
                "alert_title": alert.title,
                "alert_recommendation": alert.recommendation
            })

        export_df = pd.DataFrame(rows)
        export_df.to_csv(filepath, index=False, encoding="utf-8")
        return filepath

    def export_json_report(
        self,
        city: str,
        full_weather_data: Dict[str, Any],
        alerts: List[WeatherAlert]
    ) -> str:
        """
        Exports a rich JSON telemetry audit report.
        """
        timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        safe_city = "".join(c for c in city if c.isalnum() or c in ("_", "-")).lower()
        filepath = os.path.join(self.reports_dir, f"report_{safe_city}_{timestamp_str}.json")

        report_payload = {
            "metadata": {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "city": city,
                "system": "Weather Forecast & Alert Application",
                "version": "1.0.0"
            },
            "weather": full_weather_data,
            "alerts": [a.model_dump() for a in alerts]
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report_payload, f, indent=2)

        return filepath

"""
data_processor.py
------------------------------------------------------------------------------
Atmospheric Data Transformation and Analytics Pipeline.
Parses meteorological payloads into structured Pandas DataFrames,
computes 5-day statistical aggregates, and prepares analysis summaries.
------------------------------------------------------------------------------
"""

import pandas as pd
from typing import Dict, Any, Tuple


class WeatherDataProcessor:
    """Transforms raw weather feeds into normalized DataFrames and analytics summaries."""

    @staticmethod
    def forecast_to_dataframe(forecast_list: list) -> pd.DataFrame:
        """
        Converts the 5-day forecast array into a clean Pandas DataFrame.
        """
        if not forecast_list:
            return pd.DataFrame()
        df = pd.DataFrame(forecast_list)
        numeric_cols = ["temp_max", "temp_min", "humidity", "rain_prob_pct", "rain_volume_mm", "wind_kmh"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # Derive thermal oscillation / diurnal range
        if "temp_max" in df.columns and "temp_min" in df.columns:
            df["temp_range"] = (df["temp_max"] - df["temp_min"]).round(1)
            df["temp_avg"] = ((df["temp_max"] + df["temp_min"]) / 2.0).round(1)

        return df

    @staticmethod
    def compute_summary_metrics(current_dict: Dict[str, Any], forecast_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculates key high-level descriptive statistics across the temporal window.
        """
        summary = {
            "current_temp": current_dict.get("temperature", 0.0),
            "feels_like": current_dict.get("feels_like", 0.0),
            "current_humidity": current_dict.get("humidity", 0),
            "current_wind": current_dict.get("wind_speed_kmh", 0.0),
            "current_condition": current_dict.get("weather_condition", "N/A"),
            "aqi_pm25": current_dict.get("aqi_pm25", 0.0),
        }

        if not forecast_df.empty:
            summary["5d_max_temp"] = float(forecast_df["temp_max"].max())
            summary["5d_min_temp"] = float(forecast_df["temp_min"].min())
            summary["5d_avg_temp"] = float(forecast_df["temp_avg"].mean()) if "temp_avg" in forecast_df else summary["current_temp"]
            summary["5d_total_rain_mm"] = float(forecast_df["rain_volume_mm"].sum())
            summary["5d_max_wind_kmh"] = float(forecast_df["wind_kmh"].max())
            
            # Find peak rain day
            if "rain_volume_mm" in forecast_df.columns and forecast_df["rain_volume_mm"].max() > 0:
                peak_rain_row = forecast_df.loc[forecast_df["rain_volume_mm"].idxmax()]
                summary["peak_rain_day"] = f"{peak_rain_row.get('day', '')} ({peak_rain_row.get('rain_volume_mm', 0)} mm)"
            else:
                summary["peak_rain_day"] = "No Significant Rain Forecasted"

            # Find peak heat day
            if "temp_max" in forecast_df.columns:
                peak_heat_row = forecast_df.loc[forecast_df["temp_max"].idxmax()]
                summary["peak_heat_day"] = f"{peak_heat_row.get('day', '')} ({peak_heat_row.get('temp_max', 0)}°C)"
        else:
            summary["5d_max_temp"] = summary["current_temp"]
            summary["5d_min_temp"] = summary["current_temp"]
            summary["5d_avg_temp"] = summary["current_temp"]
            summary["5d_total_rain_mm"] = 0.0
            summary["5d_max_wind_kmh"] = summary["current_wind"]
            summary["peak_rain_day"] = "N/A"
            summary["peak_heat_day"] = "N/A"

        return summary

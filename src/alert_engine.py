"""
alert_engine.py
------------------------------------------------------------------------------
Enterprise-grade Multi-Factor Weather Risk Evaluation Engine.
Evaluates current and forecasted atmospheric metrics against configurable
safety thresholds and outputs structured alerts with actionable recommendations
for logistics, agriculture, travel, and public safety.
------------------------------------------------------------------------------
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field


class AlertThresholds(BaseModel):
    """Configurable risk thresholds for alert triggering."""
    temp_high_c: float = Field(default=38.0, description="Heatwave threshold in °C")
    temp_severe_high_c: float = Field(default=42.0, description="Severe heat emergency in °C")
    temp_low_c: float = Field(default=4.0, description="Frost/Cold warning in °C")
    temp_freeze_c: float = Field(default=0.0, description="Sub-zero freezing warning in °C")
    rain_moderate_mm: float = Field(default=5.0, description="Moderate rain threshold in mm")
    rain_heavy_mm: float = Field(default=15.0, description="Severe rain/flood risk in mm")
    wind_gale_kmh: float = Field(default=40.0, description="Gale wind warning in km/h")
    wind_storm_kmh: float = Field(default=60.0, description="Storm wind hazard in km/h")
    humidity_high_pct: float = Field(default=85.0, description="Excessive humidity threshold in %")
    aqi_pm25_hazard: float = Field(default=100.0, description="Unhealthy air quality threshold")


class WeatherAlert(BaseModel):
    """Structured risk alert event."""
    alert_id: str
    category: str               # TEMPERATURE, RAIN, WIND, HUMIDITY, AIR_QUALITY, MULTI_HAZARD
    severity: str               # CRITICAL, HIGH, MODERATE, INFO, NORMAL
    title: str
    description: str
    trigger_metric: str
    trigger_value: float
    threshold_value: float
    affected_sectors: List[str] # Logistics, Agriculture, Aviation, Citizens, Events
    recommendation: str


class AlertEngine:
    """Core logic engine evaluating multi-hazard conditions."""

    def __init__(self, thresholds: Optional[AlertThresholds] = None):
        self.thresholds = thresholds or AlertThresholds()

    def calculate_heat_index(self, temp_c: float, humidity_pct: float) -> float:
        """
        Calculates apparent temperature / Heat Index using Rothfusz regression.
        Essential for human bioclimatological risk modeling.
        """
        t = temp_c
        r = humidity_pct
        if t < 26.0 or r < 40.0:
            return t  # Heat index formula applies mainly to warm, humid conditions

        # Simplified Steadman & Rothfusz equation approximation
        hi = -8.78469475556 + 1.61139411 * t + 2.33854883889 * r \
             - 0.14611605 * t * r - 0.012308094 * (t ** 2) \
             - 0.0164248277778 * (r ** 2) + 0.002211732 * (t ** 2) * r \
             + 0.00072546 * t * (r ** 2) - 0.000003582 * (t ** 2) * (r ** 2)
        return round(hi, 1)

    def evaluate(self, weather_data: Dict[str, Any], city_override: Optional[str] = None) -> List[WeatherAlert]:
        """
        Evaluates a single weather snapshot and returns zero or more alerts.
        """
        alerts: List[WeatherAlert] = []
        city = city_override or weather_data.get("city") or "Target Area"
        temp = float(weather_data.get("temperature", 25.0))
        humidity = float(weather_data.get("humidity", 50.0))
        wind_kmh = float(weather_data.get("wind_speed_kmh", 10.0))
        rain_mm = float(weather_data.get("rain_1h_mm", 0.0))
        aqi = float(weather_data.get("aqi_pm25", 25.0))
        heat_index = self.calculate_heat_index(temp, humidity)

        # 1. High Temperature / Heatwave Checks
        if temp >= self.thresholds.temp_severe_high_c or heat_index >= 45.0:
            alerts.append(WeatherAlert(
                alert_id=f"HEAT-CRITICAL-{city}",
                category="TEMPERATURE",
                severity="CRITICAL",
                title=f"Extreme Severe Heatwave in {city}",
                description=f"Recorded temperature {temp}°C (Heat Index: {heat_index}°C). High danger of heatstroke and dehydration.",
                trigger_metric="temperature_c",
                trigger_value=temp,
                threshold_value=self.thresholds.temp_severe_high_c,
                affected_sectors=["Citizens", "Logistics", "Power Grid", "Construction"],
                recommendation="Suspend outdoor manual labor between 11 AM - 4 PM. Ensure mandatory hydration breaks and check cooling for perishable cold-chain shipments."
            ))
        elif temp >= self.thresholds.temp_high_c:
            alerts.append(WeatherAlert(
                alert_id=f"HEAT-HIGH-{city}",
                category="TEMPERATURE",
                severity="HIGH",
                title=f"High Heat Alert in {city}",
                description=f"Ambient temperature reached {temp}°C with feels-like {heat_index}°C.",
                trigger_metric="temperature_c",
                trigger_value=temp,
                threshold_value=self.thresholds.temp_high_c,
                affected_sectors=["Citizens", "Public Transport", "Agriculture"],
                recommendation="Stay hydrated, wear light clothing, and monitor vulnerable livestock and sensitive crops."
            ))

        # 2. Low Temperature / Frost & Freeze Checks
        if temp <= self.thresholds.temp_freeze_c:
            alerts.append(WeatherAlert(
                alert_id=f"FREEZE-CRITICAL-{city}",
                category="TEMPERATURE",
                severity="CRITICAL",
                title=f"Sub-Zero Freeze Hazard in {city}",
                description=f"Temperature dropped to {temp}°C. Black ice formation and frostbite hazard.",
                trigger_metric="temperature_c",
                trigger_value=temp,
                threshold_value=self.thresholds.temp_freeze_c,
                affected_sectors=["Logistics", "Aviation", "Agriculture", "Municipal Roads"],
                recommendation="Apply anti-icing brine to roadways. Inspect pipe insulation to avoid bursting; de-ice aircraft surfaces."
            ))
        elif temp <= self.thresholds.temp_low_c:
            alerts.append(WeatherAlert(
                alert_id=f"COLD-MODERATE-{city}",
                category="TEMPERATURE",
                severity="MODERATE",
                title=f"Cold Wave / Ground Frost Alert in {city}",
                description=f"Temperature at {temp}°C. Risk of frost damage to young horticultural crops.",
                trigger_metric="temperature_c",
                trigger_value=temp,
                threshold_value=self.thresholds.temp_low_c,
                affected_sectors=["Agriculture", "Travelers"],
                recommendation="Protect tender vegetation with row covers; carry winter protective gear."
            ))

        # 3. Rain & Storm Flood Checks
        if rain_mm >= self.thresholds.rain_heavy_mm:
            alerts.append(WeatherAlert(
                alert_id=f"RAIN-CRITICAL-{city}",
                category="RAIN",
                severity="CRITICAL",
                title=f"Torrential Rainfall & Flash Flood Hazard in {city}",
                description=f"Precipitation intensity {rain_mm} mm/hr. Severe waterlogging and transit disruption expected.",
                trigger_metric="rain_1h_mm",
                trigger_value=rain_mm,
                threshold_value=self.thresholds.rain_heavy_mm,
                affected_sectors=["Logistics", "Urban Drainage", "Commuters", "Aviation"],
                recommendation="Avoid low-lying underpasses and waterlogged routes. Reroute logistics freight and activate stormwater pumping stations."
            ))
        elif rain_mm >= self.thresholds.rain_moderate_mm:
            alerts.append(WeatherAlert(
                alert_id=f"RAIN-MODERATE-{city}",
                category="RAIN",
                severity="MODERATE",
                title=f"Moderate Rain Alert in {city}",
                description=f"Precipitation measured at {rain_mm} mm/hr. Wet roadway conditions.",
                trigger_metric="rain_1h_mm",
                trigger_value=rain_mm,
                threshold_value=self.thresholds.rain_moderate_mm,
                affected_sectors=["Travelers", "Outdoor Events", "Delivery Fleets"],
                recommendation="Carry waterproof gear; delivery riders should reduce driving speed to avoid hydroplaning."
            ))

        # 4. Wind Gale / Storm Checks
        if wind_kmh >= self.thresholds.wind_storm_kmh:
            alerts.append(WeatherAlert(
                alert_id=f"WIND-CRITICAL-{city}",
                category="WIND",
                severity="CRITICAL",
                title=f"Severe Storm / Gale Force Wind Warning in {city}",
                description=f"Sustained winds at {wind_kmh} km/h with high gust hazard. Risk of falling trees and structural damage.",
                trigger_metric="wind_speed_kmh",
                trigger_value=wind_kmh,
                threshold_value=self.thresholds.wind_storm_kmh,
                affected_sectors=["Port Operations", "Power Lines", "Outdoor Events", "Aviation"],
                recommendation="Halt tower crane operations and harbor vessel docking. Anchor temporary outdoor tents and structures."
            ))
        elif wind_kmh >= self.thresholds.wind_gale_kmh:
            alerts.append(WeatherAlert(
                alert_id=f"WIND-HIGH-{city}",
                category="WIND",
                severity="HIGH",
                title=f"Strong High Wind Advisory in {city}",
                description=f"Wind speeds reaching {wind_kmh} km/h.",
                trigger_metric="wind_speed_kmh",
                trigger_value=wind_kmh,
                threshold_value=self.thresholds.wind_gale_kmh,
                affected_sectors=["Aviation", "Highway Transport"],
                recommendation="High-profile vehicles (trucks/buses) must exercise caution against highway crosswinds."
            ))

        # 5. Excessive Humidity Discomfort
        if humidity >= self.thresholds.humidity_high_pct and temp >= 30.0:
            alerts.append(WeatherAlert(
                alert_id=f"HUMID-MODERATE-{city}",
                category="HUMIDITY",
                severity="MODERATE",
                title=f"High Humidity & Heat Discomfort in {city}",
                description=f"Relative humidity {humidity}% combined with {temp}°C impedes sweat evaporation.",
                trigger_metric="humidity_pct",
                trigger_value=humidity,
                threshold_value=self.thresholds.humidity_high_pct,
                affected_sectors=["Citizens", "Athletics", "Warehouses"],
                recommendation="Maintain indoor ventilation and dehumidification in pharmaceutical/grain storage facilities."
            ))

        # 6. Air Quality Index (AQI PM2.5) Check
        if aqi >= self.thresholds.aqi_pm25_hazard:
            alerts.append(WeatherAlert(
                alert_id=f"AQI-HIGH-{city}",
                category="AIR_QUALITY",
                severity="HIGH",
                title=f"Unhealthy Air Quality (AQI PM2.5) in {city}",
                description=f"Particulate matter PM2.5 level at {aqi} µg/m³. Exceeds safe respiratory guidelines.",
                trigger_metric="aqi_pm25",
                trigger_value=aqi,
                threshold_value=self.thresholds.aqi_pm25_hazard,
                affected_sectors=["Citizens", "Elderly & Children", "Schools"],
                recommendation="Wear N95 protective masks outdoors; operate HEPA air purifiers in schools and offices."
            ))

        # If no alerts triggered, emit a NORMAL status notice
        if not alerts:
            alerts.append(WeatherAlert(
                alert_id=f"STABLE-INFO-{city}",
                category="NORMAL",
                severity="NORMAL",
                title=f"Stable Weather Conditions in {city}",
                description=f"All monitored parameters (Temp: {temp}°C, Rain: {rain_mm}mm, Wind: {wind_kmh}km/h, AQI: {aqi}) are within safe operating limits.",
                trigger_metric="status",
                trigger_value=0.0,
                threshold_value=0.0,
                affected_sectors=["General Public"],
                recommendation="Ideal conditions for outdoor logistics, travel, and farming activities."
            ))

        return alerts

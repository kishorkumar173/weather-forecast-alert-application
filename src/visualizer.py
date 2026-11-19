"""
visualizer.py
------------------------------------------------------------------------------
Meteorological Data Visualization Suite.
Generates publication-quality Matplotlib figures for static reports
and interactive Plotly charts for web dashboard rendering.
------------------------------------------------------------------------------
"""

import os
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend safe for servers and scripts
import matplotlib.pyplot as plt
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


class WeatherVisualizer:
    """Creates static and interactive meteorological charts."""

    def __init__(self, output_dir: str = None):
        if not output_dir:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            output_dir = os.path.join(base_dir, "outputs", "charts")
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_static_forecast_plot(self, df: pd.DataFrame, city: str) -> str:
        """
        Generates and saves a dual-panel Matplotlib infographic chart.
        Panel 1: Temperature Envelope (Max, Min, Avg)
        Panel 2: Precipitation Probability & Wind Speed
        Returns the absolute file path of the saved PNG.
        """
        if df.empty:
            return ""

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), dpi=150, sharex=True)
        fig.patch.set_facecolor("#0f172a")

        # Styling helper
        for ax in (ax1, ax2):
            ax.set_facecolor("#1e293b")
            ax.grid(True, linestyle="--", alpha=0.3, color="#94a3b8")
            ax.tick_params(colors="#cbd5e1", labelsize=10)
            for spine in ax.spines.values():
                spine.set_color("#334155")

        x = df["day"]

        # Panel 1: Temperature Trends
        ax1.plot(x, df["temp_max"], marker="o", color="#f87171", linewidth=2.5, label="Max Temp (°C)")
        ax1.plot(x, df["temp_min"], marker="s", color="#38bdf8", linewidth=2.5, label="Min Temp (°C)")
        ax1.fill_between(x, df["temp_min"], df["temp_max"], color="#f87171", alpha=0.15)

        # Annotate temperature values
        for i, row in df.iterrows():
            ax1.annotate(f"{row['temp_max']}°C", (row["day"], row["temp_max"] + 0.6),
                         color="#fca5a5", ha="center", fontsize=9, weight="bold")
            ax1.annotate(f"{row['temp_min']}°C", (row["day"], row["temp_min"] - 1.2),
                         color="#7dd3fc", ha="center", fontsize=9, weight="bold")

        ax1.set_title(f"5-Day Meteorological Forecast & Risk Profile - {city.upper()}",
                      fontsize=14, color="#f8fafc", weight="bold", pad=12)
        ax1.set_ylabel("Temperature (°C)", color="#f8fafc", fontsize=11, weight="bold")
        ax1.legend(loc="upper right", facecolor="#0f172a", edgecolor="#334155", labelcolor="#f8fafc")

        # Panel 2: Precipitation and Wind
        bar_colors = ["#3b82f6" if p > 50 else "#60a5fa" for p in df["rain_prob_pct"]]
        bars = ax2.bar(x, df["rain_volume_mm"], width=0.4, color=bar_colors, alpha=0.85, label="Precipitation (mm)")

        ax2_wind = ax2.twinx()
        ax2_wind.plot(x, df["wind_kmh"], marker="^", color="#f59e0b", linewidth=2.2, linestyle="-.", label="Wind (km/h)")
        ax2_wind.tick_params(colors="#fcd34d", labelsize=10)
        ax2_wind.set_ylabel("Wind Speed (km/h)", color="#fcd34d", fontsize=11, weight="bold")

        ax2.set_ylabel("Rain Volume (mm)", color="#60a5fa", fontsize=11, weight="bold")
        ax2.set_xlabel("Forecast Horizon", color="#f8fafc", fontsize=11, weight="bold")

        # Combine legends for ax2 and ax2_wind
        lines1, labels1 = ax2.get_legend_handles_labels()
        lines2, labels2 = ax2_wind.get_legend_handles_labels()
        ax2.legend(lines1 + lines2, labels1 + labels2, loc="upper right", facecolor="#0f172a", edgecolor="#334155", labelcolor="#f8fafc")

        plt.tight_layout()

        safe_city = "".join(c for c in city if c.isalnum() or c in ("_", "-")).lower()
        filename = f"{safe_city}_forecast_chart.png"
        filepath = os.path.join(self.output_dir, filename)
        fig.savefig(filepath, facecolor=fig.get_facecolor(), bbox_inches="tight")
        plt.close(fig)

        return filepath

    def create_interactive_forecast_plotly(self, df: pd.DataFrame, city: str) -> go.Figure:
        """
        Creates a high-interactivity dual-axis Plotly figure for Streamlit dashboards.
        """
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.12,
            subplot_titles=(
                f"<b>5-Day Thermal Range (Min/Max Temperature) - {city}</b>",
                "<b>Hydrological & Wind Risk (Rainfall mm vs. Wind Speed km/h)</b>"
            )
        )

        # Upper chart: Temperature Range
        fig.add_trace(
            go.Scatter(
                x=df["day"], y=df["temp_max"],
                mode="lines+markers+text",
                name="Max Temp (°C)",
                text=[f"{v}°C" for v in df["temp_max"]],
                textposition="top center",
                line=dict(color="#ef4444", width=3),
                marker=dict(size=8, symbol="circle")
            ),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(
                x=df["day"], y=df["temp_min"],
                mode="lines+markers+text",
                name="Min Temp (°C)",
                text=[f"{v}°C" for v in df["temp_min"]],
                textposition="bottom center",
                line=dict(color="#0ea5e9", width=3),
                fill="tonexty",
                fillcolor="rgba(239, 68, 68, 0.12)",
                marker=dict(size=8, symbol="square")
            ),
            row=1, col=1
        )

        # Lower chart: Rain bars + Wind line
        fig.add_trace(
            go.Bar(
                x=df["day"], y=df["rain_volume_mm"],
                name="Rain Volume (mm)",
                marker_color="#3b82f6",
                opacity=0.75
            ),
            row=2, col=1
        )
        fig.add_trace(
            go.Scatter(
                x=df["day"], y=df["wind_kmh"],
                mode="lines+markers",
                name="Wind Speed (km/h)",
                line=dict(color="#f59e0b", width=2.5, dash="dash"),
                marker=dict(size=7)
            ),
            row=2, col=1
        )

        fig.update_layout(
            template="plotly_dark",
            height=600,
            hovermode="x unified",
            margin=dict(l=40, r=40, t=60, b=40),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        return fig

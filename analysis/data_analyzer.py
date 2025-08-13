import pandas as pd
from typing import Dict, Any, List, Optional
import matplotlib.pyplot as plt
import flet as ft
import io
import base64
import geopandas
from shapely.geometry import Point
import contextily as cx

# This catalog defines the pre-canned questions the admin can ask.
ANALYSIS_QUESTIONS_CATALOG = [
    {
        "id": "Q01",
        "category": "Análisis de Infracciones",
        "question": "¿Cuáles son las 5 infracciones más comunes en el municipio?",
        "analysis_function": "get_top_5_infractions"
    },
    {
        "id": "Q02",
        "category": "Análisis de Infracciones",
        "question": "¿En qué días de la semana se concentran los comparendos?",
        "analysis_function": "get_fines_by_day_of_week"
    },
    {
        "id": "Q03",
        "category": "Análisis de Flota Vehicular",
        "question": "¿Cuál es la distribución de tipos de vehículos en el parque automotor?",
        "analysis_function": "get_vehicle_type_distribution"
    },
    {
        "id": "Q04",
        "category": "Análisis Geoespacial",
        "question": "Generar un mapa de calor de las infracciones en el municipio.",
        "analysis_function": "generate_fines_heatmap"
    },
]

class DataAnalyzer:
    """
    Handles the logic for processing data and generating analytical Flet controls.
    """
    def __init__(self, all_fines: List[Dict], all_vehicles: List[Dict], api_key: Optional[str] = None):
        """
        Initializes the analyzer with data and a placeholder for an API key.
        """
        # --- API Key Management Placeholder ---
        if not api_key:
            print("Warning: API Key not provided. For future versions, this will be required.")
        self.api_key = api_key
        # -------------------------------------

        self.fines_df = pd.DataFrame(all_fines) if all_fines else pd.DataFrame()
        self.vehicles_df = pd.DataFrame(all_vehicles) if all_vehicles else pd.DataFrame()

    def analyze(self, function_name: str) -> ft.Control:
        """
        Dynamically calls an analysis function and returns a Flet control.
        """
        if not hasattr(self, function_name):
            return ft.Text(f"Error: La función de análisis '{function_name}' no fue encontrada.", color=ft.colors.RED)

        analysis_method = getattr(self, function_name)
        try:
            result_control = analysis_method()
            return result_control
        except Exception as e:
            return ft.Text(f"Error durante el análisis: {e}", color=ft.colors.RED)

    def _create_plot_base64(self, fig) -> str:
        """Saves a matplotlib figure to a base64 encoded string."""
        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight")
        buf.seek(0)
        img_str = base64.b64encode(buf.getvalue()).decode("utf-8")
        plt.close(fig)
        return img_str

    # --- Analysis Functions ---

    def get_top_5_infractions(self) -> ft.Control:
        """Analyzes and returns the top 5 most common infractions as a DataTable."""
        if self.fines_df.empty:
            return ft.Text("No hay datos de infracciones para analizar.")

        top_fines = self.fines_df['infraction_code'].value_counts().nlargest(5).reset_index()
        top_fines.columns = ["Código de Infracción", "Número de Comparendos"]

        return ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text(col)) for col in top_fines.columns
            ],
            rows=[
                ft.DataRow(cells=[ft.DataCell(ft.Text(str(value))) for value in row])
                for row in top_fines.itertuples(index=False)
            ]
        )

    def get_fines_by_day_of_week(self) -> ft.Control:
        """Analyzes and returns the number of fines per day of the week as a bar chart."""
        if self.fines_df.empty or 'date' not in self.fines_df.columns:
            return ft.Text("No hay datos de infracciones o falta la columna 'date' para analizar.")

        df = self.fines_df.copy()
        df['date'] = pd.to_datetime(df['date'])

        day_names_es = {0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 3: 'Jueves', 4: 'Viernes', 5: 'Sábado', 6: 'Domingo'}
        df['day_of_week'] = df['date'].dt.dayofweek.map(day_names_es)

        days_order = list(day_names_es.values())
        fines_by_day = df['day_of_week'].value_counts().reindex(days_order, fill_value=0)

        fig, ax = plt.subplots(figsize=(10, 6))
        fines_by_day.plot(kind='bar', ax=ax, color='#2a9d8f')
        ax.set_title('Comparendos por Día de la Semana')
        ax.set_ylabel('Número de Comparendos')
        ax.tick_params(axis='x', rotation=45)

        img_base64 = self._create_plot_base64(fig)
        return ft.Image(src_base64=img_base64)

    def get_vehicle_type_distribution(self) -> ft.Control:
        """Analyzes and returns the distribution of vehicle types as a pie chart."""
        if self.vehicles_df.empty or 'type' not in self.vehicles_df.columns:
            return ft.Text("No hay datos de vehículos o falta la columna 'type' para analizar.")

        type_counts = self.vehicles_df['type'].value_counts()

        fig, ax = plt.subplots(figsize=(8, 8))
        ax.pie(type_counts, labels=type_counts.index, autopct='%1.1f%%', startangle=90, colors=plt.cm.Paired.colors)
        ax.set_title('Distribución de Tipos de Vehículos')
        ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

        img_base64 = self._create_plot_base64(fig)
        return ft.Image(src_base64=img_base64)

    def generate_fines_heatmap(self) -> ft.Control:
        """
        Generates and returns a heatmap of fine locations.
        Requires `geopandas` and `contextily`.
        """
        if self.fines_df.empty or 'latitude' not in self.fines_df.columns or 'longitude' not in self.fines_df.columns:
            return ft.Text("No hay suficientes datos de geolocalización para generar un mapa de calor.")

        # Filter out rows with no location data
        geo_fines = self.fines_df.dropna(subset=['latitude', 'longitude'])
        if geo_fines.empty:
            return ft.Text("No se encontraron infracciones con datos de geolocalización.")

        # Create a GeoDataFrame
        gdf = geopandas.GeoDataFrame(
            geo_fines,
            geometry=geopandas.points_from_xy(geo_fines.longitude, geo_fines.latitude),
            crs="EPSG:4326"  # WGS 84
        )

        # Create plot
        fig, ax = plt.subplots(1, 1, figsize=(12, 12))

        # Reproject to a CRS suitable for web maps (like contextily's default)
        gdf = gdf.to_crs(epsg=3857)

        # Plot heatmap using kernel density estimation
        geopandas.tools.plot_kde(gdf.geometry, ax=ax, cmap='viridis', alpha=0.5)

        # Add a basemap from contextily
        cx.add_basemap(ax, source=cx.providers.OpenStreetMap.Mapnik)

        ax.set_axis_off()
        ax.set_title("Mapa de Calor de Infracciones")

        img_base64 = self._create_plot_base64(fig)
        return ft.Image(src_base64=img_base64)

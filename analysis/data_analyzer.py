import pandas as pd
from typing import Dict, Any, List
import matplotlib.pyplot as plt
import uuid

# This catalog defines the pre-canned questions the admin can ask.
# In a real application, this might be stored in a database.
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
    # Add more questions here as they are implemented
]


class DataAnalyzer:
    """
    Handles the logic for processing and analyzing data for reports.
    """
    def __init__(self, all_fines: List[Dict], all_vehicles: List[Dict]):
        """
        Initializes the analyzer with the necessary data.
        In a real app, this might take a DB connection instead.
        """
        self.fines_df = pd.DataFrame(all_fines)
        self.vehicles_df = pd.DataFrame(all_vehicles)

    def analyze(self, function_name: str) -> Dict[str, Any]:
        """
        Dynamically calls an analysis function based on its name.
        """
        if not hasattr(self, function_name):
            raise ValueError(f"Analysis function '{function_name}' not found.")

        analysis_method = getattr(self, function_name)
        result = analysis_method()
        return result

    # --- Analysis Functions ---

    def get_top_5_infractions(self) -> Dict[str, Any]:
        """Analyzes and returns the top 5 most common infractions."""
        if self.fines_df.empty:
            return {"type": "text", "data": "No hay datos de infracciones para analizar."}

        top_fines = self.fines_df['infraction_code'].value_counts().nlargest(5)

        # In a real implementation, we would generate a bar chart here.
        # For now, we return the data as a dictionary.
        return {
            "type": "table",
            "title": "Top 5 Infracciones Comunes",
            "data": top_fines.reset_index().to_dict('records'),
            "columns": ["Código de Infracción", "Número de Comparendos"]
        }

    def get_fines_by_day_of_week(self) -> Dict[str, Any]:
        """Analyzes and returns the number of fines per day of the week."""
        if self.fines_df.empty:
            return {"type": "text", "data": "No hay datos de infracciones para analizar."}

        self.fines_df['date'] = pd.to_datetime(self.fines_df['date'])
        day_names_es = {
            'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
            'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
        }
        self.fines_df['day_of_week'] = self.fines_df['date'].dt.day_name().map(day_names_es)

        days_order_es = list(day_names_es.values())
        fines_by_day = self.fines_df['day_of_week'].value_counts().reindex(days_order_es, fill_value=0)

        # Generate and save chart
        plt.figure(figsize=(10, 6))
        fines_by_day.plot(kind='bar', color='#2a9d8f')
        plt.title('Comparendos por Día de la Semana')
        plt.ylabel('Número de Comparendos')
        plt.xticks(rotation=45)
        plt.tight_layout()

        filename = f"assets/reports/fines_by_day_{uuid.uuid4()}.png"
        plt.savefig(filename)
        plt.close()

        return {
            "type": "image",
            "title": "Comparendos por Día de la Semana",
            "path": filename
        }

    # Add other analysis functions here...
    def get_vehicle_type_distribution(self) -> Dict[str, Any]:
        return {"type": "text", "data": "Análisis de distribución de vehículos aún no implementado."}

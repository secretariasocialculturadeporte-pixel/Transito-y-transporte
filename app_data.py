import json
from typing import Dict, Any

# --- Static Application Data ---

UVB_VALUE_2025 = 11552

# This catalog is based on the information provided by the user.
# In a real system, this would be managed in a database.
INFRACTIONS_CATALOG = [
    # Tipo A
    {'code': 'A01', 'category': 'A', 'description': 'No transitar por la derecha de la vía', 'uvb_value': 13.95},
    {'code': 'A02', 'category': 'A', 'description': 'Agarrarse de otro vehículo en circulación', 'uvb_value': 13.95},
    # Tipo B
    {'code': 'B01', 'category': 'B', 'description': 'Conducir sin llevar la licencia de conducción', 'uvb_value': 27.86},
    {'code': 'B02', 'category': 'B', 'description': 'Conducir con la licencia de conducción vencida', 'uvb_value': 27.86},
    # Tipo C
    {'code': 'C02', 'category': 'C', 'description': 'Estacionar en sitios prohibidos', 'uvb_value': 52.29},
    {'code': 'C04', 'category': 'C', 'description': 'No utilizar el cinturón de seguridad', 'uvb_value': 52.29},
    {'code': 'C29', 'category': 'C', 'description': 'Conducir un vehículo a velocidad superior a la máxima permitida', 'uvb_value': 52.29},
    # Tipo D
    {'code': 'D01', 'category': 'D', 'description': 'Guiar un vehículo sin haber obtenido la licencia de conducción correspondiente', 'uvb_value': 104.55},
    {'code': 'D02', 'category': 'D', 'description': 'Conducir sin portar los seguros ordenados por la ley', 'uvb_value': 104.55},
    {'code': 'D04', 'category': 'D', 'description': 'No detenerse ante una luz roja o amarilla de semáforo', 'uvb_value': 104.55},
    # Tipo E
    {'code': 'E02', 'category': 'E', 'description': 'Negarse a prestar el servicio público sin causa justificada', 'uvb_value': 156.84},
    # Tipo F
    {'code': 'F01', 'category': 'F', 'description': 'Conducir bajo el influjo del alcohol (Grado 0, 1ra vez)', 'uvb_value': 313.68},
]

COURSES_CATALOG = [
    {'id': 'C001', 'name': 'Curso de Normas de Tránsito General', 'description': 'Curso de sensibilización sobre las normas de tránsito básicas.', 'duration_hours': 2},
    {'id': 'C002', 'name': 'Curso para Infractores por Velocidad', 'description': 'Curso enfocado en los riesgos del exceso de velocidad.', 'duration_hours': 3},
]

# User roles available in the application
USER_ROLES = [
    "Ciudadano",
    "Admin Area",
    "Admin Municipal",
    "Admin Departamental",
    "SuperAdmin"
]

# Simulated DANE data for departments and municipalities
# In a real application, this would come from a database or a more complete file.
dane_data = {
    "05": {
        "name": "Antioquia",
        "municipalities": {
            "05001": "Medellín",
            "05088": "Bello",
            "05360": "Itagüí"
        }
    },
    "76": {
        "name": "Valle del Cauca",
        "municipalities": {
            "76001": "Cali",
            "76520": "Palmira",
            "76111": "Buenaventura"
        }
    },
    "11": {
        "name": "Bogotá, D.C.",
        "municipalities": {
            "11001": "Bogotá, D.C."
        }
    }
}

# --- Internationalization (i18n) ---

_translations: Dict[str, Any] = {}
_current_lang: str = "es"

def load_translations(lang: str = "es"):
    """
    Loads the translation file for the given language into memory.
    """
    global _translations, _current_lang
    try:
        with open(f"assets/lang/{lang}.json", "r", encoding="utf-8") as f:
            _translations = json.load(f)
            _current_lang = lang
            print(f"Successfully loaded language file: {lang}.json")
    except FileNotFoundError:
        print(f"Error: Language file not found for '{lang}'. Defaulting to empty.")
        _translations = {}
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from language file for '{lang}'.")
        _translations = {}

def _t(key: str, default: str = None, **kwargs) -> str:
    """
    Translates a given key using the loaded language file.

    Args:
        key (str): The key for the translation string (e.g., "login_title").
        default (str, optional): A default value to return if the key is not found.
                                 If None, the key itself is returned.
        **kwargs: Keyword arguments for string formatting.

    Returns:
        str: The translated and formatted string.
    """
    # Use the provided default value, or the key itself if no default is given
    default_value = default if default is not None else key

    # Get the template from the translations, or use the default value
    template = _translations.get(key, default_value)

    # Format the string with any provided kwargs
    if kwargs:
        try:
            return template.format(**kwargs)
        except KeyError as e:
            print(f"Warning: Formatting key {e} not found in template for '{key}'")
            return template # Return unformatted template on error

    return template

# Load default translations on module import
load_translations(_current_lang)

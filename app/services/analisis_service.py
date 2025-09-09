import os
import time
import random
import json
import google.generativeai as genai
from PIL import Image
from dotenv import load_dotenv
from app.utils.api_helpers import es_429, extraer_retry_delay

# Cargar la API Key desde el archivo .env
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def analizar_contenido(html_limpio: str, ruta_imagen: str, nivel_tolerancia: str) -> dict:
    """
    Envía el contenido y la imagen a la IA de Gemini para su análisis visual.
    Maneja reintentos en caso de errores de cuota.
    """
    model = genai.GenerativeModel("gemini-1.5-flash") # Usamos 1.5 que es más reciente

    Tolerancia = {
        "alta": "Sólo errores críticos que impiden usar la página o la hacen ilegible (ej: botones superpuestos, texto tapado).",
        "media": "Errores visibles que afectan la experiencia, aunque no la bloqueen (ej: alineaciones desprolijas, textos juntos).",
        "baja": "Detalles menores o estéticos que podrían mejorarse (ej: márgenes desparejos, colores poco armoniosos)."
    }

    prompt = f"""
    Sos un verificador visual de interfaces. Devolveme SOLO JSON válido.

    Campos requeridos:
    - "queVeo": string (descripción breve de lo que se ve en la web)
    - "necesitaModificacion": boolean
    - "modificaciones": array de strings, cada ítem una corrección concreta.

    Criterio: detectá únicamente problemas visuales reales (texto superpuesto, botones desalineados, recortes, etc.).
    Tolerancia: {nivel_tolerancia} ({Tolerancia.get(nivel_tolerancia, "media")}).

    IMPORTANTE:
    - Si no hay problemas, "necesitaModificacion": false y "modificaciones": [].
    - No agregues texto fuera del JSON.

    A continuación, la IMAGEN (screenshot) y un extracto del HTML plano.
    HTML:
    """

    MAX_RETRIES = 6
    intento = 0

    while True:
        try:
            print("Consultando al modelo de IA...")
            parts = [
                prompt,
                html_limpio,
                Image.open(ruta_imagen),
            ]
            resp = model.generate_content(parts, generation_config={
                "response_mime_type": "application/json"
            })
            return json.loads(resp.text)

        except Exception as e:
            intento += 1
            if es_429(e) and intento <= MAX_RETRIES:
                delay = extraer_retry_delay(e, fallback=60)
                delay = max(delay, 2 ** intento) + random.uniform(1, 3)
                print(f"Error de cuota (429). Reintentando en {int(delay)}s (intento {intento}/{MAX_RETRIES})...")
                time.sleep(delay)
                continue
            else:
                print(f"Error inesperado al contactar la IA: {e}")
                raise  # Relanzamos la excepción si no es manejable
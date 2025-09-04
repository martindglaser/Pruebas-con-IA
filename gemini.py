import re, time, random, json
import google.generativeai as genai
from PIL import Image
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup 

# --- Navegación y captura ---
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)  # True si no necesitás ventana
    page = browser.new_page()
    page.goto("https://infobae.com/", wait_until="domcontentloaded")
    print("Título:", page.title())
    contenido = page.content()
    print("URL actual:", page.url)
    page.screenshot(path="pagina.png", full_page=True)
    browser.close()

ClaveApi = "AIzaSyAuy0mbLHZKUxYU8aGS9KpN7_NXAHmTEjk"

# --- Helper de backoff ---
def extraer_retry_delay(e: Exception, fallback=60):
    s = str(e)
    m = re.search(r"retry[_\s-]?delay\s*{\s*seconds:\s*(\d+)", s, re.I)
    if m:
        return int(m.group(1))
    m = re.search(r"Retry-After:\s*(\d+)", s, re.I)
    if m:
        return int(m.group(1))
    return fallback

def es_429(e: Exception):
    s = str(e).lower()
    return ("429" in s) or ("resource exhausted" in s) or ("quota" in s)

# --- Sanitizar y recortar HTML ---
def limpiar_html(raw: str, max_len: int = 80000) -> str:
    soup = BeautifulSoup(raw, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    limpio = soup.get_text(separator="\n")
    limpio = re.sub(r"\n{3,}", "\n\n", limpio).strip()
    return limpio[:max_len]

html_limpio = limpiar_html(contenido)

# --- Config del modelo ---
genai.configure(api_key=ClaveApi)
model = genai.GenerativeModel("gemini-2.5-flash")

Tolerancia = {
    "alta": "Sólo errores críticos que impiden usar la página o la hacen ilegible (ej: botones superpuestos que no se pueden clickear, texto tapado, contraste que impide leer).",
    "media": "Errores visibles que afectan la experiencia de usuario, aunque no la bloqueen (ej: alineaciones desprolijas, botones que se cortan, textos demasiado juntos).",
    "baja": "Detalles menores o estéticos que podrían mejorarse, sin afectar la funcionalidad (ej: márgenes desparejos, tamaños de fuente inconsistentes, colores poco armoniosos)."
}



nivel_tolerancia = "baja"  # <-- cambiá esto si querés

PROMPT = f"""
Sos un verificador visual de interfaces. Devolveme SOLO JSON válido.

Campos requeridos:
- "queVeo": string (descripción breve de lo que se ve)
- "necesitaModificacion": boolean
- "modificaciones": array de strings, cada ítem una corrección concreta (por ejemplo: "alinear el botón X con el título Y", "evitar texto superpuesto en Z").

Criterio: detectá únicamente problemas visuales reales (texto superpuesto, botones desalineados, recortes, contrastes ilegibles, overlays que tapan CTA, etc.).
Tolerancia: {nivel_tolerancia} ({Tolerancia[nivel_tolerancia]}).

IMPORTANTE:
- Si no hay problemas reales, "necesitaModificacion": false y "modificaciones": [].
- No agregues texto fuera del JSON.
- No incluyas el HTML en la respuesta.

A continuación, primero recibirás la IMAGEN (screenshot) y luego un extracto del HTML plano.

HTML:
"""

MAX_RETRIES = 6
intento = 0

while True:
    try:
        print("Consultando modelo...")
        parts = [
            PROMPT,
            html_limpio,              # texto grande pero ya limpio/recortado
            Image.open("pagina.png"), # imagen
        ]
        resp = model.generate_content(parts, generation_config={
            "response_mime_type": "application/json"
        })
        # Validar JSON
        data = json.loads(resp.text)
        print(json.dumps(data, ensure_ascii=False, indent=2))
        break
    except Exception as e:
        intento += 1
        if es_429(e) and intento <= MAX_RETRIES:
            delay = extraer_retry_delay(e, fallback=60)
            delay = max(delay, 2 ** intento) + random.uniform(1, 3)
            print(f"429/Quota: espero {int(delay)}s y reintento (intento {intento}/{MAX_RETRIES})...")
            time.sleep(delay)
            continue
        else:
            raise

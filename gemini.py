import re, time, random
import google.generativeai as genai
import PIL.Image
from playwright.sync_api import sync_playwright

# --- Navegación y captura ---
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto("https://infobae.com/")
    print("Título:", page.title())
    contenido = page.content()
    print("URL actual:", page.url)
    page.screenshot(path="pagina.png", full_page=True)
    browser.close()

ClaveApi = 'AIzaSyAuy0mbLHZKUxYU8aGS9KpN7_NXAHmTEjk'  # clave de valen

def extraer_retry_delay(e: Exception, fallback=60):
    s = str(e)
    # Ej.: retry_delay { seconds: 52 }
    m = re.search(r"retry_delay\s*{\s*seconds:\s*(\d+)", s, re.I)
    if m:
        return int(m.group(1))
    # A veces llega como header Retry-After
    m = re.search(r"Retry-After:\s*(\d+)", s, re.I)
    if m:
        return int(m.group(1))
    return fallback

def es_429(e: Exception):
    s = str(e).lower()
    return ("429" in s) or ("resource exhausted" in s) or ("quota" in s)

# --- Lógica de llamadas ---
genai.configure(api_key=ClaveApi)
model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",  # en Flash sí podemos apagar thinking
    generation_config={
        "response_mime_type": "application/json",
    },
)

img = PIL.Image.open("pagina.png")

MAX_RETRIES = 6
intento = 0
while True:
    try:
        print("Consultando modelo...")
        prompt = (
            "Te voy a dar una imagen y la estructura HTML de una pagina web. "
            "Necesito que me respondas en formato JSON con estas claves: "
            "queVeo: (string) descripción breve de lo que ves en la imagen y text"
            "necesitaModificacion (boolean) y modificaciones (array de strings). "
            "Detecta solo si hay problemas visuales reales (texto superpuesto, botón desalineado, etc.). "
            "HTML: "
        )
        response = model.generate_content([prompt + contenido, img])
        print(response.text)
        break
    except Exception as e:
        intento += 1
        if es_429(e) and intento <= MAX_RETRIES:
            delay = extraer_retry_delay(e, fallback=60)
            # Backoff exponencial con jitter, respetando el retry_delay mínimo del servidor
            delay = max(delay, 2 ** intento) + random.uniform(1, 3)
            print(f"429/Quota: espero {int(delay)}s y reintento (intento {intento}/{MAX_RETRIES})...")
            time.sleep(delay)
            continue
        else:
            raise

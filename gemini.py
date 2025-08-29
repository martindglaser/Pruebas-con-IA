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

ClavesApis = [
    'AIzaSyAuy0mbLHZKUxYU8aGS9KpN7_NXAHmTEjk',  # clave de valen
    'AIzaSyAlkqDVXRVx0VB56PcC7JE25RUcntoJIeA',
]

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
genai.configure(api_key=ClavesApis[0])  # usá 1 sola clave por proyecto
model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",  # en Flash sí podemos apagar thinking
    generation_config={
        # Respuesta en JSON (más barato y estable para tu caso)
        "response_mime_type": "application/json",
        # Nota: en este SDK legacy no siempre está disponible thinking_config.
        # Si migrás al SDK nuevo (google-genai), podés añadir:
        # "thinking_config": {"thinking_budget": 0}
    },
)

img = PIL.Image.open("pagina.png")

MAX_RETRIES = 6
intento = 0
while True:
    try:
        print("Usando modelo: gemini-2.5-flash (thinking desactivado)")
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
        elif "API key not valid" in str(e) or "PERMISSION_DENIED" in str(e):
            # Solo rotá clave si realmente es problema de credenciales, no por cuota.
            idx = (ClavesApis.index(genai._options.api_key) + 1) % len(ClavesApis)
            genai.configure(api_key=ClavesApis[idx])
            print("Clave inválida: cambiando a la siguiente.")
            continue
        else:
            raise

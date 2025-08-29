import google.generativeai as genai
import PIL.Image
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto("https://infobae.com/")
    #page.goto("https://aulavirtual.instituto.ort.edu.ar")
    print("Título:", page.title())
    contenido = page.content()
    print("URL actual:", page.url)
    page.screenshot(path="pagina.png", full_page=True)
    browser.close()




ClavesApis = [
    'AIzaSyAuy0mbLHZKUxYU8aGS9KpN7_NXAHmTEjk', #clave de valen
    'AIzaSyAlkqDVXRVx0VB56PcC7JE25RUcntoJIeA',
    'AIzaSyAKKCyca-ddWrKrvE6lCacX5mwXqvwgYWY',
]

claveAPI = 0
respuestaExitosa = False
while(not respuestaExitosa):
    if(claveAPI > ClavesApis.__len__()-1):
        claveAPI = 0

    try:
        genai.configure(api_key = ClavesApis[claveAPI] )
        print("Usando clave API: ", ClavesApis[claveAPI])
        model = genai.GenerativeModel('gemini-2.5-pro')
        img = PIL.Image.open('pagina.png')
        response = model.generate_content(["Te voy a dar una imagen y la estructura HTML de una pagina web. Necesito que me respondas en formato json. 'necesitaModifacacion' boolean necesita modificacion segun tu consideracion, tenes que fijarte si hay errores, sino no necesita modificacion, un ejemplo de error sería texto superpuesto a otro o boton torcido, 'modificaciones': array de strings con las modificaciones que consideras pertinentes. te paso el HTML" + contenido, img])
        print(response.text)
        respuestaExitosa = True
    except Exception as e:
        print(f"Se terminó la cuota, pasando a proxima clave API ",e)
        claveAPI += 1
        continue





from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto("https://aulavirtual.instituto.ort.edu.ar")
    print("Título:", page.title())
    print("Contenido:", page.content())
    print("URL actual:", page.url)
    page.screenshot(path="pagina.png", full_page=True)

    
    browser.close()

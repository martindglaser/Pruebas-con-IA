from playwright.sync_api import sync_playwright, Error

def capturar_pagina(url: str) -> tuple[str, str]:
    """
    Navega a una URL, toma una captura de pantalla y devuelve el contenido HTML.
    Retorna una tupla (ruta_de_captura, contenido_html).
    Lanza una excepción si la URL es inválida o no se puede acceder.
    """
    screenshot_path = "pagina.png"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60000) # Timeout de 60s
            page.screenshot(path=screenshot_path, full_page=True)
            contenido_html = page.content()
        except Error as e:
            browser.close()
            raise ValueError(f"No se pudo acceder o procesar la URL: {url}. Error: {e}")

        browser.close()
    return screenshot_path, contenido_html
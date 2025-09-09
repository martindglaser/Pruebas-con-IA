1. python -m venv venv
2. source venv/bin/activate  # En Windows: venv\Scripts\activate
3. pip install -r requirements.txt
4. playwright install chromium # Instala el navegador que usa Playwright
5. flask --app app/main.py run --port 5001


Endpoints
    - POST: /analizar
        Params
            url,
            tolerancia (alta, media o baja)
        Response
            queVeo: String,
            necesitaModificacion: Boolean,
            modificaciones: String[]

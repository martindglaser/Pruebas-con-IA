from flask import Flask, request, jsonify
from app.services import captura_service, analisis_service
from app.utils import html_cleaner

app = Flask(__name__)

@app.route('/analizar', methods=['POST'])
def analizar_url():
    """
    Endpoint para analizar una URL.
    Recibe un JSON con "url" y "tolerancia".
    Devuelve el análisis en formato JSON.
    """
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({"error": "La URL es requerida"}), 400

    url = data['url']
    # La tolerancia es opcional, por defecto 'media'
    tolerancia = data.get('tolerancia', 'media').lower()
    if tolerancia not in ['alta', 'media', 'baja']:
        return jsonify({"error": "La tolerancia debe ser 'alta', 'media' o 'baja'"}), 400

    try:
        print(f"1. Iniciando captura para la URL: {url}")
        ruta_imagen, html_crudo = captura_service.capturar_pagina(url)

        print("2. Limpiando HTML...")
        html_limpio_texto = html_cleaner.limpiar_html(html_crudo)

        print("3. Enviando a la IA para análisis...")
        resultado_analisis = analisis_service.analizar_contenido(
            html_limpio=html_limpio_texto,
            ruta_imagen=ruta_imagen,
            nivel_tolerancia=tolerancia
        )

        print("4. Análisis completado. Devolviendo resultado.")
        return jsonify(resultado_analisis)

    except ValueError as e:
        # Error al capturar la página (URL inválida, timeout, etc.)
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        # Cualquier otro error inesperado
        print(f"Error inesperado en el servidor: {e}")
        return jsonify({"error": "Ocurrió un error interno en el servidor de análisis"}), 500

if __name__ == '__main__':
    # Para ejecutar directamente: python -m app.main
    app.run(debug=True, port=5001)
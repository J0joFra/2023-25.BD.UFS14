import azure.functions as func
import logging
import os

app = func.FunctionApp()

@app.route(route="MyHttpTrigger", auth_level=func.AuthLevel.ANONYMOUS)
def MyHttpTrigger(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    # Utilizza un percorso relativo per l'immagine
    image_path = os.path.join(os.path.dirname(__file__), "QR_code.svg")
    try:
        with open(image_path, "rb") as image_file:
            image_data = image_file.read()
        return func.HttpResponse(
            image_data,
            mimetype="image/svg+xml",  # Specifica il mimetype corretto per SVG
            status_code=200
        )
    except FileNotFoundError:
        return func.HttpResponse(
            "Immagine non trovata",
            status_code=404
        )

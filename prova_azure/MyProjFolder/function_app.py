import azure.functions as func
import datetime
import json
import logging
import os

def MyHttpTrigger(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    # Carica l'immagine dal file system
    image_path = os.path.join(os.getcwd(), r"C:\Users\JoaquimFrancalanci\QR_code.svg")
    # Utilizza un percorso relativo per l'immagine
    image_path = os.path.join(os.path.dirname(__file__), "QR_code.svg")
    try:
        with open(image_path, "rb") as image_file:
            image_data = image_file.read()
        return func.HttpResponse(
            image_data,
            mimetype=r"C:\Users\JoaquimFrancalanci\QR_code.svg",
            mimetype="image/svg+xml", 
            status_code=200
        )
    except FileNotFoundError:
        return func.HttpResponse(
            "Immagine non trovata",
            status_code=404
        )
import logging
import pymongo
import os
import json
import azure.functions as func

# Connessione a MongoDB
def connect_to_mongodb():
    mongo_uri = os.getenv("MONGO_URI")  # Usa una variabile d'ambiente per la sicurezza
    client = pymongo.MongoClient(mongo_uri)
    db = client["Healthcare"]
    return db["Pediatri"]

# Funzione principale dell'Azure Function
@app.route(route="MyScraperFunction", auth_level=func.AuthLevel.ANONYMOUS)
def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("HTTP trigger processed a request.")

    # Parametri della richiesta
    nome = req.params.get("nome")
    if not nome:
        return func.HttpResponse(
            "Parametro 'nome' mancante. Usa ?nome=<nome> per effettuare la ricerca.",
            status_code=400,
        )

    try:
        # Connessione a MongoDB
        collection = connect_to_mongodb()

        # Ricerca nel database
        query = {"NomeCompleto": {"$regex": nome, "$options": "i"}}  # Ricerca case-insensitive
        results = list(collection.find(query, {"_id": 0}))  # Esclude il campo `_id`

        # Controlla se ci sono risultati
        if not results:
            return func.HttpResponse(
                f"Nessun pediatra trovato con nome '{nome}'.",
                status_code=404,
            )

        # Risultati della ricerca
        response_data = {
            "results": results
        }

        return func.HttpResponse(
            json.dumps(response_data, indent=4),
            mimetype="application/json",
        )

    except Exception as e:
        logging.error(f"Errore: {str(e)}")
        return func.HttpResponse(
            f"Errore interno del server: {str(e)}",
            status_code=500,
        )

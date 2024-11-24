import azure.functions as func
import logging
import os
import pymongo
import pandas as pd


def connect_to_mongodb(uri):
    client = pymongo.MongoClient(uri)
    db = client["tavola_periodica"]
    collezione_elementi = db["elementi"]
    return client, collezione_elementi


def create_db(client):
    db = client["tavola_periodica"]
    collezione_elementi = db["elementi"]

    # Percorso relativo al file CSV 
    csv_path = os.getenv("CSV_PATH", "elements.csv")
    df = pd.read_csv(csv_path)

    # Inserimento dei dati nella collezione MongoDB
    elementi_da_inserire = df.to_dict(orient="records")
    collezione_elementi.insert_many(elementi_da_inserire)
    return collezione_elementi


@app.route(route="MyScraperFunction", auth_level=func.AuthLevel.ANONYMOUS)
def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("HTTP trigger processed a request.")

    # URI MongoDB (può essere configurato tramite variabile d'ambiente)
    mongo_uri = os.getenv("MONGO_URI", "mongodb+srv://jofrancalanci:Cf8m2xsQdZgll1hz@element.2o7dxct.mongodb.net/")

    try:
        # Connessione al database
        client, collezione_elementi = connect_to_mongodb(mongo_uri)

        # Leggi il parametro di query 'elemento'
        elemento = req.params.get('elemento')

        if elemento:
            # Cerca l'elemento nel database
            risultato = collezione_elementi.find_one({"name": elemento}, {"_id": 0})
            if risultato:
                return func.HttpResponse(
                    json.dumps(risultato),
                    status_code=200,
                    mimetype="application/json"
                )
            else:
                return func.HttpResponse(
                    f"L'elemento '{elemento}' non è stato trovato nel database.",
                    status_code=404
                )
        else:
            # Setup del database se nessun elemento è richiesto
            create_db(client)
            return func.HttpResponse(
                "Database configurato correttamente!",
                status_code=200
            )

    except Exception as e:
        logging.error(f"Errore durante il setup del database: {e}")
        return func.HttpResponse(
            f"Errore: {str(e)}",
            status_code=500
        )

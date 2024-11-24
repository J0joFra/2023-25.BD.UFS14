import azure.functions as func
import datetime
import json
import logging
import os

import azure.functions as func
import logging
import os
import pymongo
import pandas as pd

# Importa le funzioni da db_setup.py
def connect_to_mongodb(uri):
    client = pymongo.MongoClient(uri)
    db = client["tavola_periodica"]
    collezione_elementi = db["elementi"]
    return client, collezione_elementi

def create_db(client):
    db = client["tavola_periodica"]
    collezione_elementi = db["elementi"]

    # Percorso relativo al file CSV (puoi adattarlo a una variabile di ambiente)
    csv_path = os.getenv("CSV_PATH", "path_al_tuo_file.csv")
    df = pd.read_csv(csv_path)

    # Inserimento dei dati nella collezione MongoDB
    elementi_da_inserire = df.to_dict(orient="records")
    collezione_elementi.insert_many(elementi_da_inserire)
    return collezione_elementi

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("HTTP trigger processed a request.")

    # URI MongoDB (può essere configurato tramite variabile d'ambiente)
    mongo_uri = os.getenv("MONGO_URI", "mongodb+srv://jofrancalanci:Cf8m2xsQdZgll1hz@element.2o7dxct.mongodb.net/")

    try:
        # Connessione al database
        client, collezione_elementi = connect_to_mongodb(mongo_uri)

        # Setup del database
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

import logging
import pymongo
import urllib.request
import json
import pandas as pd
import numpy as np
import azure.functions as func

app = func.FunctionApp()

# Funzione per connettersi al database MongoDB
def connect_to_mongodb():
    mongo_uri = "mongodb+srv://jofrancalanci:Cf8m2xsQdZgll1hz@element.2o7dxct.mongodb.net/"
    client = pymongo.MongoClient(mongo_uri)
    db = client["Healthcare"]
    return db["Pediatri"]

# Funzione principale per elaborare e inserire i dati in MongoDB
def main():
    url = 'https://dati.comune.milano.it/api/3/action/datastore_search?resource_id=22b05e1f-c5d2-4468-90e5-c098977856ef'
    response = urllib.request.urlopen(url)
    data = json.load(response)
    records = data["result"]["records"]

    # Converti i dati in un DataFrame
    df = pd.DataFrame(records)

    # Preprocessing
    df = df.fillna({
        'civico': 'N/A',
        'luogo_ambulatorio': 'Milano'
    })

    # Converti la colonna 'dataNascita' in formato datetime
    df['dataNascita'] = pd.to_datetime(df['dataNascita'], errors='coerce')

    # Calcola l'età
    df['età'] = df['dataNascita'].apply(calcola_eta)

    # Standardizza la colonna 'tipoMedico'
    df['tipoMedico'] = df['tipoMedico'].replace({
        'PLS': 'Pediatra di Libera Scelta',
        'Incaricato provvisorio Pediatra': 'Pediatra Incaricato Provvisorio'
    })

    # Converti 'attivo' e 'ambulatorioPrincipale' in booleani
    df['attivo'] = df['attivo'].astype(bool, errors='ignore')
    df['ambulatorioPrincipale'] = df['ambulatorioPrincipale'].astype(bool, errors='ignore')

    # Crea la colonna 'nome_completo'
    df['nome_completo'] = (df['nomeMedico'].astype(str) + ' ' + df['cognomeMedico'].astype(str)).str.title()

    # Pulisci le colonne di testo
    text_columns = ['nomeMedico', 'cognomeMedico', 'comune_medico', 'aft', 'via', 'luogo_ambulatorio', 'NIL']
    for col in text_columns:
        if col in df.columns:
            df[col] = df[col].str.strip().str.title()

    # Converti le coordinate in float
    df['LONG_X_4326'] = pd.to_numeric(df['LONG_X_4326'], errors='coerce')
    df['LAT_Y_4326'] = pd.to_numeric(df['LAT_Y_4326'], errors='coerce')

    # Rimuovi colonne inutili
    df = df.drop(columns=['nomeMedico', 'cognomeMedico'], errors='ignore')

    # Trasforma i nomi delle colonne in "Title Case"
    df.columns = df.columns.str.replace('_', ' ').str.title().str.replace(' ', '')

    # Riordina le colonne
    columns_order = ['IdMedico', 'NomeCompleto', 'CodiceRegionaleMedico', 
                     'DataNascita', 'Età', 'TipoMedico', 'Attivo', 'AmbulatorioPrincipale', 'ComuneMedico', 
                     'Aft', 'Via', 'Civico', 'LuogoAmbulatorio', 'Cap', 'Municipio', 'IdNil', 'Nil', 
                     'LongX4326', 'LatY4326', 'Location']
    existing_columns_order = [col for col in columns_order if col in df.columns]
    df = df[existing_columns_order]

    # Connessione a MongoDB e inserimento dei dati
    collection = connect_to_mongodb()
    collection.delete_many({})
    data_dict = df.to_dict("records")
    collection.insert_many(data_dict)
    print(f"Inseriti {len(data_dict)} documenti nella collezione 'Pediatri'.")

# Funzione per generare la pagina HTML con il form di ricerca
def generate_html_form():
    return """
    <!DOCTYPE html>
    <html lang="it">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Ricerca Pediatri a Milano</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background-color: #f0f8ff;
                color: #333;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                flex-direction: column;
            }
            .container {
                background-color: #fff;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
                text-align: center;
                max-width: 400px;
                width: 90%;
            }
            h1 {
                color: #4CAF50;
            }
            input, button {
                margin: 10px 0;
                padding: 10px;
                width: 90%;
                border: 1px solid #ccc;
                border-radius: 5px;
                font-size: 1rem;
            }
            button {
                background-color: #4CAF50;
                color: white;
                cursor: pointer;
            }
            button:hover {
                background-color: #45a049;
            }
        </style>
    </head>
    <body>
        <h1>Ricerca Pediatri a Milano</h1>
        <div class="container">
            <form action="/api/PediatriSearch" method="get">
                <input type="text" name="nome" placeholder="Inserisci il nome o cognome del pediatra"><br>
                <input type="text" name="zona" placeholder="Inserisci la zona"><br>
                <input type="text" name="indirizzo" placeholder="Inserisci l'indirizzo"><br>
                <input type="text" name="comune" placeholder="Inserisci il comune"><br>
                <input type="text" name="cap" placeholder="Inserisci il CAP"><br>
                <input type="text" name="municipio" placeholder="Inserisci il municipio"><br>
                <button type="submit">Cerca</button>
            </form>
        </div>
    </body>
    </html>
    """

# Funzione per generare la risposta HTML con i risultati della ricerca
def generate_html_results(results):
    results_html = """
    <!DOCTYPE html>
    <html lang="it">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Risultati Ricerca Pediatri</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background-color: #f0f8ff;
                color: #333;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                flex-direction: column;
            }
            .container {
                background-color: #fff;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
                max-width: 800px;
                width: 90%;
                margin-top: 20px;
            }
            h1 {
                color: #4CAF50;
            }
            .result {
                margin-bottom: 15px;
                font-size: 1.1rem;
                color: #444;
            }
            .result span {
                font-weight: bold;
                color: #4CAF50;
            }
            hr {
                border: none;
                border-top: 1px solid #4CAF50;
                margin: 20px 0;
            }
        </style>
    </head>
    <body>
        <h1>Risultati Ricerca Pediatri</h1>
        <div class="container">
    """
    if results:
        for pediatra in results:
            results_html += f"""
            <div class="result">
                <p>Nome: <span>{pediatra['NomeCompleto']}</span></p>
                <p>Indirizzo: <span>{pediatra['Via']} {pediatra['Civico']}</span></p>
                <p>Zona: <span>{pediatra.get('Nil', 'Non specificata')}</span></p>
                <p>Comune: <span>{pediatra.get('ComuneMedico', 'Non specificato')}</span></p>
                <p>CAP: <span>{pediatra.get('Cap', 'Non specificato')}</span></p>
                <p>Municipio: <span>{pediatra.get('Municipio', 'Non specificato')}</span></p>
            </div>
            <hr>
            """
    else:
        results_html += "<p>Nessun pediatra trovato con i criteri forniti.</p>"

    results_html += """
        </div>
    </body>
    </html>
    """
    return results_html

@app.route(route="PediatriSearch", auth_level=func.AuthLevel.ANONYMOUS, methods=["GET"])
def search_pediatri(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Elaborazione della richiesta HTTP trigger per la ricerca dei pediatri.")

    # Recupera i parametri di ricerca
    nome = req.params.get("nome")
    zona = req.params.get("zona")
    indirizzo = req.params.get("indirizzo")
    comune = req.params.get("comune")
    cap = req.params.get("cap")
    municipio = req.params.get("municipio")

    # Se nessun parametro di ricerca è fornito, mostra il form
    if not nome and not zona and not indirizzo and not comune and not cap and not municipio:
        return func.HttpResponse(generate_html_form(), mimetype="text/html", status_code=200)

    try:
        # Connessione al database MongoDB
        collection = connect_to_mongodb()

        # Costruzione della query di ricerca dinamica
        query = {}
        if nome:
            query["NomeCompleto"] = {"$regex": nome, "$options": "i"}
        if zona:
            query["Nil"] = {"$regex": zona, "$options": "i"} 
        if indirizzo:
            query["Via"] = {"$regex": indirizzo, "$options": "i"} 
        if comune:
            query["ComuneMedico"] = {"$regex": comune, "$options": "i"} 
        if cap:
            query["Cap"] = {"$regex": cap, "$options": "i"} 
        if municipio:
            query["Municipio"] = {"$regex": municipio, "$options": "i"} 

        # Esecuzione della query di ricerca
        results = list(collection.find(query, {
            "_id": 0, "NomeCompleto": 1, "Via": 1, "Civico": 1, "Nil": 1, "ComuneMedico": 1, "Cap": 1, "Municipio": 1
        }))

        # Genera i risultati in HTML
        return func.HttpResponse(generate_html_results(results), mimetype="text/html", status_code=200)

    except Exception as e:
        logging.error(f"Errore durante la ricerca: {str(e)}")
        return func.HttpResponse(f"Errore interno del server: {str(e)}", status_code=500)

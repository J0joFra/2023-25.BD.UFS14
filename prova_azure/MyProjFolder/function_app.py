import logging
import pymongo
import os
import json
import azure.functions as func

app = func.FunctionApp()

# Funzione per connettersi al database MongoDB
def connect_to_mongodb():
    mongo_uri = os.getenv("MONGO_URI")  # Usa una variabile d'ambiente per la sicurezza
    client = pymongo.MongoClient(mongo_uri)
    db = client["Healthcare"]
    return db["Pediatri"]

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
                <input type="text" name="nome" placeholder="Inserisci il nome del pediatra" required><br>
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
                <p>Indirizzo: <span>{pediatra['Indirizzo']}</span></p>
            </div>
            """
    else:
        results_html += "<p>Nessun pediatra trovato con il nome fornito.</p>"

    results_html += """
        </div>
    </body>
    </html>
    """
    return results_html

@app.route(route="PediatriSearch", auth_level=func.AuthLevel.ANONYMOUS, methods=["GET"])
def search_pediatri(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Elaborazione della richiesta HTTP trigger per la ricerca dei pediatri.")

    # Se nessun parametro di ricerca è fornito, mostra il form
    nome = req.params.get("nome")
    if not nome:
        return func.HttpResponse(generate_html_form(), mimetype="text/html", status_code=200)

    try:
        # Connessione al database MongoDB
        collection = connect_to_mongodb()

        # Ricerca dei pediatri per nome
        query = {"NomeCompleto": {"$regex": nome, "$options": "i"}}  # Ricerca case-insensitive
        results = list(collection.find(query, {"_id": 0, "NomeCompleto": 1, "Indirizzo": 1}))

        # Genera i risultati in HTML
        return func.HttpResponse(generate_html_results(results), mimetype="text/html", status_code=200)

    except Exception as e:
        logging.error(f"Errore durante la ricerca: {str(e)}")
        return func.HttpResponse(f"Errore interno del server: {str(e)}", status_code=500)

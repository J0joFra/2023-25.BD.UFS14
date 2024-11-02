import azure.functions as func
import logging
import urllib.request
import json
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pymongo
import os

app = func.FunctionApp()

@app.route(route="MyHttpTrigger", auth_level=func.AuthLevel.ANONYMOUS)
def MyHttpTrigger(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    # Funzione per caricare il dataset JSON dai dati online
    def load_data(url):
        fileobj = urllib.request.urlopen(url)
        data = json.load(fileobj)
        return pd.DataFrame(data["result"]["records"])

    # Funzione per capitalizzare le colonne e i valori stringa
    def title_columns_and_values(df):
        df.columns = [col.capitalize() for col in df.columns]
        df = df.applymap(lambda x: x.title() if isinstance(x, str) else x)
        return df

    # Funzione per rinominare le colonne
    def rename_columns(df):
        return df.rename(columns={
            "Idmedico": "ID_med",
            "Nomemedico": "Name_med",
            "Cognomemedico": "Surname_med",
            "Nil": "Zone",
            "Long_x_4326": "Long",
            "Lat_y_4326": "Lat",
            "Codice_regionale_medico": "Code_med",
            'Datanascita': "Age",
            "Tipomedico": "Type_med",
            "Attivo": "Open",
            "Ambulatorioprincipale": "Main_amb",
            "Luogo_ambulatorio": "L_ambul"
        })

    # Funzione per calcolare l'età dal campo data di nascita
    def calculate_age(df):
        today = datetime.today().date()
        df['Age'] = df['Age'].apply(lambda x: datetime.strptime(x.split("T")[0], '%Y-%m-%d').date() if pd.notna(x) else None)
        df['Age'] = df['Age'].apply(lambda birth_date: relativedelta(today, birth_date).years if birth_date else None)
        return df

    # Funzione per creare la colonna combinata 'Address' 
    def create_address_column(df):
        def create_address(row):
            parts = []
            if 'Via' in row and pd.notna(row['Via']):
                parts.append(row['Via'])
            if 'Civico' in row and pd.notna(row['Civico']):
                parts.append(row['Civico'])
            if 'L_ambul' in row and pd.notna(row['L_ambul']):
                parts.append(row['L_ambul'])
            return ', '.join(parts)
        
        df['Address'] = df.apply(create_address, axis=1).str.title()
        return df

    # Procedi a eliminare le colonne solo dopo che sono state usate per creare l'indirizzo
    def drop_unnecessary_columns(df):
        columns_to_drop = ['_id', 'Via', 'Civico', 'L_ambul', 'Location']
        existing_columns = [col for col in columns_to_drop if col in df.columns]
        return df.drop(existing_columns, axis=1)

    # Funzione per creare la colonna geometrica nel dataset
    def create_geometry_column(df):
        geometry = [Point(xy) for xy in zip(df['Long'], df['Lat'])]
        gdf = gpd.GeoDataFrame(df, geometry=geometry)
        return gdf.set_crs("EPSG:4326")

    # Funzione per caricare il file GeoJSON con le aree di Milano
    def load_geojson(path):
        return gpd.read_file(path).to_crs("EPSG:4326")

    # Funzione per effettuare il join spaziale e aggiornare le zone
    def spatial_join_update_zones(gdf_data, gdf_zones):
        gdf_joined = gpd.sjoin(gdf_data, gdf_zones, how="left", predicate="within")
        gdf_data['Zone'] = gdf_joined['name']
        return gdf_data

    # Funzione per creare e popolare il database MongoDB
    def create_mongo_db(dataframe):
        client = pymongo.MongoClient("mongodb+srv://jofrancalanci:Cf8m2xsQdZgll1hz@element.2o7dxct.mongodb.net/")
        db = client["Healthcare"]
        collection = db["Pediatri"]
        collection.delete_many({})
        data_dict = dataframe.to_dict("records")
        collection.insert_many(data_dict) 
        logging.info(f"Inseriti {len(data_dict)} documenti nella collezione 'Pediatri'.")

    # URL e percorso per il dataset e il GeoJSON
    url = 'https://dati.comune.milano.it/api/3/action/datastore_search?resource_id=22b05e1f-c5d2-4468-90e5-c098977856ef'
    geojson_path = os.path.join(os.path.dirname(__file__), "Datasets/MilanCity.geojson")

    try:
        # Carica e processa i dati
        df = load_data(url)
        df = title_columns_and_values(df)
        df = rename_columns(df)
        df = calculate_age(df)
        df = create_address_column(df)
        df = drop_unnecessary_columns(df)

        # Crea la colonna geometrica e aggiorna le zone
        gdf_data = create_geometry_column(df)
        gdf_zones = load_geojson(geojson_path)
        gdf_data = spatial_join_update_zones(gdf_data, gdf_zones)

        # Salva nel database MongoDB
        create_mongo_db(df)

        return func.HttpResponse("Dati elaborati e caricati nel database MongoDB con successo.", status_code=200)
    except Exception as e:
        logging.error(f"Errore durante l'elaborazione dei dati: {e}")
        return func.HttpResponse("Errore durante l'elaborazione dei dati.", status_code=500)

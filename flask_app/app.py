from flask import Flask, render_template, request, redirect, url_for
import os
import json
import csv
import requests
from elasticsearch import Elasticsearch

app = Flask(__name__)

es = Elasticsearch(["http://localhost:9200"])

LOGS_DIR = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..', 'logstash', 'logs')

if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

# Define Kibana URL and visualization ID
KIBANA_URL = "https://5601-cs-22d925ca-5e97-409d-804f-4cd080d6f287.cs-europe-west1-haha.cloudshell.dev/"
VISUALIZATION_ID = "a2cbb630-b0ea-11ef-bffc-c7786914d8da"


@app.route('/')
def index():
    error_message = request.args.get('error_message')
    return render_template('index.html', error_message=error_message)

ALLOWED_EXTENSIONS = {'json', 'csv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Traiter le fichier JSON
def process_json(filename):
    with open(filename, 'r') as file:
        data = json.load(file)
        print(f"Fichier JSON traité: {filename}")

# Traiter le fichier CSV
def process_csv(filename):
    with open(filename, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            print(f"Ligne CSV: {row}")

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(url_for('index', error_message="Aucun fichier sélectionné"))

    file = request.files['file']

    if file.filename == '':
        return redirect(url_for('index', error_message="Aucun fichier sélectionné"))

    if file and allowed_file(file.filename):
        # Déterminer le dossier cible en fonction de l'extension
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        subfolder = 'csv' if file_extension == 'csv' else 'json'
        target_dir = os.path.join(LOGS_DIR, subfolder)

        # Créer le dossier cible s'il n'existe pas
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

        # Enregistrer le fichier dans le sous-dossier approprié
        file_path = os.path.join(target_dir, file.filename)
        file.save(file_path)

        try:
            if filename.endswith('.json'):
                process_json(filename)
            elif filename.endswith('.csv'):
                process_csv(filename)
        except Exception as e:
            return redirect(url_for('index'))

        return redirect(url_for('index'))

    return redirect(url_for('index', error_message="Fichier non autorisé, uniquement JSON ou CSV."))

@app.route('/dashboard')
def show_visualization():
    return render_template('dashboard.html')

@app.route('/dashboardjson')
def show_visualizationjson():
    return render_template('dashboardjson.html')

@app.route('/search', methods=['GET', 'POST'])
def search_logs():
    results = []
    query = ""
    if request.method == 'POST':
        query = request.form.get('query')
        if query:
            # Elasticsearch search query
            es_query = {
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": ["LineId", "Label", "Timestamp", "Date", "User", "Month", "Day", "Time", "Location", "Component", "PID", "Content", "EventId", "EventTemplate"]
                    }
                }
            }
            response = es.search(index="csvmyindex-2024.12.12", body=es_query)
            results = response.get('hits', {}).get('hits', [])

            # Remove duplicates based on 'LineId'
            results = {result['_source']['LineId']
                : result for result in results}.values()

    return render_template('search.html', results=results, query=query)

import re
@app.route('/searchjson', methods=['GET', 'POST'])
def search_logs_json():
    results = []
    queryj = ""
    if request.method == 'POST':
        queryj = request.form.get('queryj')
        if queryj:
            es_queryj = {
                "query": {
                    "multi_match": {
                        "query": queryj,
                        "fields": ["lineid", "timestamp", "EventTemplate", "eventid"],
                        "type": "best_fields"
                    }
                }
            }
            try:
                response = es.search(index="jsonmyindex-2024.12.12", body=es_queryj)
                results = response.get('hits', {}).get('hits', [])

                # Remove duplicates based on 'lineid'
                unique_results = {}
                for result in results:
                    source = result.get('_source', {})
                    if 'lineid' in source:
                        unique_results[source['lineid']] = source


                results = unique_results.values()
            except Exception as e:
                print(f"Error while searching: {e}")

    return render_template('searchjson.html', results=results, queryj=queryj)

# @app.route('/searchjson', methods=['GET', 'POST'])
# def search_logs_json():
#     results = []
#     query = ""
#     if request.method == 'POST':
#         query = request.form.get('query')
#         if query:
#             # Échapper les caractères spéciaux
#             query = re.escape(query)
            
#             # Elasticsearch search query
#             es_query = {
#                 "query": {
#                     "multi_match": {
#                         "query": query,
#                         "fields": ["lineid", "timestamp", "EventTemplate", "eventid"]
#                     }
#                 }
#             }
#             try:
#                 response = es.search(index="jsonmyindex-2024.12.12", body=es_query)
#                 results = response.get('hits', {}).get('hits', [])

#                 # Supprimer les doublons basés sur 'LineId'
#                 results = {result['_source']['LineId']: result for result in results}.values()
#             except Exception as e:
#                 # Log the error or handle it accordingly
#                 print(f"Error: {str(e)}")

#     return render_template('searchjson.html', results=results, query=query)


if __name__ == '__main__':
    app.run(debug=True)

from flask import Flask, render_template, request, redirect, url_for
import os
import json
import csv
import requests 
# import requests  # Don't forget to import requests

app = Flask(__name__)

LOGS_DIR = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..', 'logstash', 'logs')

if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

# Define Kibana URL and visualization ID
KIBANA_URL = "https://organic-barnacle-v7447rjg7rwcpr9w-5601.app.github.dev"
#/  # URL complète de votre instance Kibana
VISUALIZATION_ID = "a2cbb630-b0ea-11ef-bffc-c7786914d8da"

@app.route('/')
def index():
    error_message = request.args.get('error_message')
    return render_template('index.html', error_message=error_message)


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(url_for('index', error_message="Aucun fichier sélectionné"))

    file = request.files['file']

    if file.filename == '':
        return redirect(url_for('index', error_message="Aucun fichier sélectionné"))

    if file and allowed_file(file.filename):
        filename = os.path.join(LOGS_DIR, file.filename)
        file.save(filename)

        try:
            if filename.endswith('.json'):
                process_json(filename)
            elif filename.endswith('.csv'):
                process_csv(filename)
        except Exception as e:
            return redirect(url_for('index', error_message=f"Erreur lors du traitement du fichier: {str(e)}"))

        return redirect(url_for('index'))

    return redirect(url_for('index', error_message="Fichier non autorisé, uniquement JSON ou CSV."))

@app.route('/dashboard')
def show_visualization():
    return render_template('dashboard.html')

@app.route('/search')
def show_search():
    return render_template('search.html')

if __name__ == '__main__':
    app.run(debug=True)




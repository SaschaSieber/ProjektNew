import threading
import webbrowser
from urllib.request import Request, urlopen
from flask import Flask, request, render_template, send_file
import pandas as pd
from Simple_Gulp_Finder import scrape_gulp
#from projekt_finder import scrape_protip
from Simple_Projekt_Finder import scrape_protip
import os
import time
import spacy
import de_core_news_md
from datetime import datetime

nlp = de_core_news_md.load()

app = Flask(__name__)

# Results folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_FOLDER = os.path.join(BASE_DIR, "results")
os.makedirs(RESULTS_FOLDER, exist_ok=True)


@app.route('/')
def home():
    return render_template('NewLanding.html')


@app.route('/process', methods=['POST'])
def process():
    try:
        website = request.form.get('website')
        threshold = request.form.get('threshold')

        if not threshold:
            return "Threshold must be provided.", 400
        try:
            threshold = float(threshold)
        except ValueError:
            return "Invalid threshold value.", 400

        # Handle inclusion file upload
        inclusion_file = request.files.get('inclusion_file')
        if not inclusion_file:
            return "Inclusion file must be provided.", 400
        try:
            inclusion_df = pd.read_excel(inclusion_file)
        except Exception as e:
            return f"Error reading inclusion file: {str(e)}", 500

        # Handle exclusion file upload (optional)
        exclusion_file = request.files.get('exclusion_file')
        if exclusion_file:
            try:
                exclusion_df = pd.read_excel(exclusion_file)
                exclusion_terms = exclusion_df.iloc[:, 0].tolist()  # Assumes first column contains exclusion terms
            except Exception as e:
                return f"Error reading exclusion file: {str(e)}", 500
        else:
            exclusion_terms = []  # Empty list if no exclusion file is provided

        current_date = datetime.now().strftime("%Y-%m-%d_%H-%M")

        if website == "Gulp":
            output_filename = f"Ergebnis_Gulp_{current_date}.xlsx"
            updated_df = scrape_gulp(inclusion_df, exclusion_terms)

        elif website == "Protip":
            output_filename = f"Ergebnis_Protip_{current_date}.xlsx"
            updated_df = scrape_protip(inclusion_df, exclusion_terms)

        else:
            return "Invalid website selection!", 400

        output_file = os.path.join(RESULTS_FOLDER, output_filename)
        updated_df.to_excel(output_file, index=False)

        return send_file(output_file, as_attachment=True, download_name=output_filename)

    except Exception as e:
        return f"An error occurred: {str(e)}", 500


def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()


BASE_URL = '82.165.126.38:8080'
SHUTDOWN = '/shutdown'


def request_shutdown(url=BASE_URL + SHUTDOWN):
    req = Request(url, method='POST')
    req = urlopen(req)
    content = req.read()
    print(content)


@app.route('/shutdown', methods=['POST'])
def shutdown():
    shutdown_server()
    request_shutdown()
    return "Server shutting down..."


def open_browser():
    time.sleep(2)
    webbrowser.open_new('82.165.126.38:8080')


if __name__ == '__main__':
    threading.Thread(target=open_browser).start()
    app.run(debug=False, host='0.0.0.0', port=8080)

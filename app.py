# app.py
from flask import Flask, render_template, Response
import csv
import os
from scrape_dutchmarket import detect_creatine_variant_visibility_js

app = Flask(__name__)

@app.route("/")
def home():
    # Run scraper to get the latest data
    try:
        detect_creatine_variant_visibility_js()
    except Exception as e:
        app.logger.error(f"[ERROR] Scraper failed: {e}")

    # Load CSV results
    variants = []
    csv_path = "visible_variants.csv"
    if os.path.exists(csv_path):
        with open(csv_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            variants = list(reader)

    return render_template("index.html", variants=variants)

@app.route("/data")
def data():
    # Serve the CSV file directly
    csv_path = "visible_variants.csv"
    if os.path.exists(csv_path):
        with open(csv_path, newline='', encoding='utf-8') as csvfile:
            return Response(csvfile.read(), mimetype='text/csv')
    return Response("No data available.", mimetype='text/plain', status=404)

if __name__ == "__main__":
    app.run(debug=True)

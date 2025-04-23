from flask import Flask, render_template, Response, redirect, url_for
import csv
import os
import subprocess
from datetime import datetime

app = Flask(__name__)

@app.route("/")
def home():
    variants = []
    last_updated = None
    csv_path = "visible_variants.csv"

    if os.path.exists(csv_path):
        last_modified = os.path.getmtime(csv_path)
        last_updated = datetime.fromtimestamp(last_modified).strftime('%Y-%m-%d %H:%M')

        with open(csv_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    price_per_100g = float(row.get("price_per_100g", 0).replace(",", "."))
                    if 1.0 <= price_per_100g <= 10.0:
                        variants.append(row)
                except (ValueError, TypeError):
                    continue

        variants = sorted(variants, key=lambda x: float(x["price_per_100g"].replace(",", ".")))

    return render_template("index.html", variants=variants, last_updated=last_updated)

@app.route("/data")
def data():
    csv_path = "visible_variants.csv"
    if os.path.exists(csv_path):
        with open(csv_path, newline='', encoding='utf-8') as csvfile:
            return Response(csvfile.read(), mimetype='text/csv')
    return Response("No data available.", mimetype='text/plain', status=404)

@app.route("/scrape")
def scrape():
    try:
        script_path = os.path.join(os.path.dirname(__file__), "scrape_dutchmarket.py")
        subprocess.run(["python", script_path], check=True)
    except subprocess.CalledProcessError as e:
        return f"<h3>Scraper failed:</h3><pre>{e}</pre>", 500
    except Exception as e:
        return f"<h3>Unexpected error:</h3><pre>{e}</pre>", 500
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True)

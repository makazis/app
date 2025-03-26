from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import os
from flask_sqlalchemy import SQLAlchemy

# Flask konfigurācija
app = Flask(__name__)
os.makedirs("static", exist_ok=True)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///data.db"
db = SQLAlchemy(app)

# Datubāzes modelis
class Country(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    population = db.Column(db.Integer)
    area = db.Column(db.Integer)
    join_year = db.Column(db.Integer)
    gdp = db.Column(db.Integer)
    avg_income = db.Column(db.Integer)
    border_length = db.Column(db.Integer)

# Sākumlapa
@app.route("/")
def index():
    return render_template("index.html")

# Datu ielāde no Excel uz datubāzi
@app.route("/load_data")
def load_data():
    df = pd.read_excel("programmesana.xlsx")
    df.to_sql("country", db.engine, if_exists="replace", index=False)
    return "Dati ielādēti!"

# Valstu tabula ar meklēšanu
@app.route("/countries", methods=["GET", "POST"])
def countries():
    search_query = request.form.get("search", "")
    if search_query:
        data = Country.query.filter(Country.name.contains(search_query)).all()
    else:
        data = Country.query.all()
    return render_template("table.html", data=data, search_query=search_query)

# Grafiku ģenerēšana
@app.route("/charts")
def charts():
    df = pd.read_sql("SELECT * FROM country", db.engine)
    
    # Vidējo ienākumu diagramma
    plt.figure(figsize=(10,6))
    sns.barplot(x="name", y="avg_income", data=df)
    plt.xticks(rotation=90)
    plt.title("Vidējie gada ienākumi ES valstīs")
    plt.savefig("static/income_chart.png")
    plt.close()
    
    # Iedzīvotāju histogramma
    plt.figure(figsize=(10,6))
    sns.histplot(df["population"], bins=10, kde=True)
    plt.title("Iedzīvotāju sadalījums")
    plt.savefig("static/population_hist.png")
    plt.close()
    
    # Korelācijas matrica
    plt.figure(figsize=(8,6))
    sns.heatmap(df.corr(), annot=True, cmap="coolwarm", fmt=".2f")
    plt.title("Datu korelācija")
    plt.savefig("static/correlation_matrix.png")
    plt.close()
    
    return render_template("chart.html", charts=[
        "static/income_chart.png",
        "static/population_hist.png",
        "static/correlation_matrix.png"
    ])

# Interaktīvs grafiks ar Plotly
@app.route("/interactive-chart")
def interactive_chart():
    df = pd.read_sql("SELECT * FROM country", db.engine)
    fig = px.scatter(df, x="gdp", y="avg_income", text="name", size="population", title="IKP pret Vidējo Ienākumu")
    chart_html = fig.to_html(full_html=False)
    return render_template("interactive_chart.html", chart_html=chart_html)

# CSV augšupielāde
@app.route("/upload", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        file = request.files["file"]
        if file:
            df = pd.read_csv(file)
            df.to_sql("country", db.engine, if_exists="append", index=False)
            return "Dati veiksmīgi augšupielādēti!"
    return render_template("upload.html")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)

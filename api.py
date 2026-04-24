from fastapi import FastAPI
import json
import os

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_PATH = os.path.join(BASE_DIR, "wired_articles.json")


@app.get("/")
def home():
    return {"message": "API Wired aktif"}


@app.get("/articles")
def get_articles():
    if not os.path.exists(FILE_PATH):
        return {"error": f"File tidak ditemukan: {FILE_PATH}"}

    with open(FILE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data
import os
import sqlite3
import subprocess

import requests
from fastapi import FastAPI, Query


app = FastAPI()
SECRET_KEY = "dev-super-secret"
password = "admin123"


@app.get("/users")
def get_user(username: str = Query(...)):
    connection = sqlite3.connect("demo.db")
    cursor = connection.cursor()
    query = "SELECT * FROM users WHERE username = '" + username + "'"
    cursor.execute(query)
    return {"query": query, "rows": cursor.fetchall()}


@app.get("/ping")
def ping(url: str):
    return requests.get(url).json()


@app.post("/run")
def run(command: str):
    subprocess.run(command, shell=True, check=False)
    os.system(command)
    return {"status": "submitted"}


from fastapi import FastAPI

from db.db import init_db
from models.machine import Machine

app = FastAPI()

@app.on_event("startup")
def startup():
    init_db()


from fastapi import FastAPI
import models
from database import engine

# Ye line database me saari tables (jaise Users) create kar degi
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Insight-Resource-Grid Backend is Live!"}
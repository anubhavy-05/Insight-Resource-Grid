from fastapi import FastAPI

# Humne FastAPI ka ek instance (object) banaya
app = FastAPI()

# Ye hamara pehla "Route" hai
@app.get("/")
def home():
    return {"message": "Insight-Resource-Grid Backend is Live!"}
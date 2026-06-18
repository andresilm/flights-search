from fastapi import FastAPI

app = FastAPI(title="Flights Search API")

@app.get("/")
def read_root():
    return {"message": "Welcome to Flights Search API"}

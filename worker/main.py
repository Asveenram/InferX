import os
from fastapi import FastAPI
from pydantic import BaseModel
from model import MockModel

app = FastAPI()

WORKER_ID = os.environ.get("WORKER_ID", "worker-1")
model = MockModel(worker_id=WORKER_ID)

class PredictRequest(BaseModel):
    data: dict

@app.get("/health")
def health():
    return {"status": "ok", "worker_id": WORKER_ID}

@app.post("/predict")
def predict(request: PredictRequest):
    result = model.predict(request.data)
    return result
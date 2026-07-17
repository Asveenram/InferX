import time
import httpx
from fastapi import FastAPI, Response
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = FastAPI()

WORKERS = [
    "http://worker1:8000",
    "http://worker2:8000",
    "http://worker3:8000",
]

current_index = 0

class PredictRequest(BaseModel):
    data: dict

# Metrics
REQUEST_COUNT = Counter("inferx_requests_total", "Total prediction requests", ["status"])
REQUEST_LATENCY = Histogram("inferx_request_latency_seconds", "Request latency in seconds")
WORKER_FAILURES = Counter("inferx_worker_failures_total", "Worker failure count", ["worker"])

def get_next_worker():
    global current_index
    worker = WORKERS[current_index]
    current_index = (current_index + 1) % len(WORKERS)
    return worker

@app.post("/predict")
async def predict(request: PredictRequest):
    start_time = time.time()
    last_error = None

    for attempt in range(len(WORKERS)):
        worker_url = get_next_worker()
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.post(f"{worker_url}/predict", json=request.dict())
                response.raise_for_status()
                result = response.json()
                result["attempts"] = attempt + 1

                REQUEST_COUNT.labels(status="success").inc()
                REQUEST_LATENCY.observe(time.time() - start_time)
                return result
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            last_error = str(e)
            WORKER_FAILURES.labels(worker=worker_url).inc()
            continue

    REQUEST_COUNT.labels(status="failure").inc()
    REQUEST_LATENCY.observe(time.time() - start_time)
    return {"error": "all workers failed", "detail": last_error}

@app.get("/health")
def health():
    return {"status": "load balancer ok"}

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
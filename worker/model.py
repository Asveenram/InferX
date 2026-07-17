import time
import random

class MockModel:
    def __init__(self, worker_id: str):
        self.worker_id = worker_id

    def predict(self, data: dict) -> dict:
        # simulate inference time (0.1 to 0.5 seconds)
        time.sleep(random.uniform(0.1, 0.5))
        
        labels = ["cat", "dog", "car", "tree", "person"]
        return {
            "worker_id": self.worker_id,
            "input": data,
            "prediction": random.choice(labels),
            "confidence": round(random.uniform(0.7, 0.99), 2)
        }
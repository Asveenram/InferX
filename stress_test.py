import asyncio
import httpx
import time

URL = "http://localhost:8000/predict"
TOTAL_REQUESTS = 200
CONCURRENCY = 20

async def send_request(client, results):
    start = time.time()
    try:
        response = await client.post(URL, json={"data": {"image": "test.jpg"}})
        latency = time.time() - start
        results.append({"success": response.status_code == 200, "latency": latency})
    except Exception as e:
        latency = time.time() - start
        results.append({"success": False, "latency": latency})

async def main():
    results = []
    async with httpx.AsyncClient(timeout=10.0) as client:
        sem = asyncio.Semaphore(CONCURRENCY)

        async def bound_request():
            async with sem:
                await send_request(client, results)

        start_time = time.time()
        await asyncio.gather(*[bound_request() for _ in range(TOTAL_REQUESTS)])
        total_time = time.time() - start_time

    successes = [r for r in results if r["success"]]
    failures = [r for r in results if not r["success"]]
    latencies = sorted([r["latency"] for r in successes])

    print(f"\n--- InferX Stress Test Results ---")
    print(f"Total requests: {TOTAL_REQUESTS}")
    print(f"Concurrency: {CONCURRENCY}")
    print(f"Total time: {total_time:.2f}s")
    print(f"Throughput: {TOTAL_REQUESTS / total_time:.2f} req/sec")
    print(f"Success: {len(successes)} | Failures: {len(failures)}")
    if latencies:
        p50 = latencies[len(latencies)//2]
        p95 = latencies[int(len(latencies)*0.95)]
        p99 = latencies[int(len(latencies)*0.99)]
        print(f"Latency P50: {p50*1000:.0f}ms")
        print(f"Latency P95: {p95*1000:.0f}ms")
        print(f"Latency P99: {p99*1000:.0f}ms")

if __name__ == "__main__":
    asyncio.run(main())
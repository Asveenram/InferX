<div align="center">

# InferX

**A distributed ML inference framework — model-agnostic, fault-tolerant, observable.**

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![Prometheus](https://img.shields.io/badge/Prometheus-metrics-E6522C?logo=prometheus&logoColor=white)](https://prometheus.io/)
[![Grafana](https://img.shields.io/badge/Grafana-dashboard-F46800?logo=grafana&logoColor=white)](https://grafana.com/)
[![License](https://img.shields.io/badge/license-MIT-green)]()

</div>

---

## Why

Serving an ML model in production isn't `model.predict()` behind a single Flask route. Real systems — Ray Serve, NVIDIA Triton, BentoML — solve a harder problem: route concurrent traffic across many model replicas, survive node failure without dropping requests, and stay observable while doing it.

**InferX is a from-scratch, minimal implementation of that infrastructure layer** — built to understand and demonstrate it, not to replace those tools.

## Architecture

```
                    ┌─────────────┐
   Client  ───────▶ │ Load        │  round-robin
                    │ Balancer    │  + auto-retry
                    └──────┬──────┘
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │ Worker 1 │ │ Worker 2 │ │ Worker 3 │
        └──────────┘ └──────────┘ └──────────┘
              │            │            │
              └────────────┼────────────┘
                            ▼
                     ┌─────────────┐      ┌─────────┐
                     │ Prometheus  │ ───▶ │ Grafana │
                     └─────────────┘      └─────────┘
```

| Layer | Responsibility |
|---|---|
| **Worker** | FastAPI service wrapping a model behind a fixed `/predict` contract — swap the model, the framework doesn't care |
| **Load balancer** | Round-robin routing; on failure/timeout, retries the same request on the next healthy worker before giving up |
| **Prometheus** | Scrapes request count, latency histogram, and per-worker failure counts every 5s |
| **Grafana** | Live dashboard — request rate, average latency |
| **Docker Compose** | Single-command orchestration of all 6 containers on an isolated bridge network |

## Design decisions

<details>
<summary><b>Why round-robin and not least-connections?</b></summary>

Round-robin was implemented first as the baseline — stateless, zero overhead, even distribution under uniform load. Least-connections is the natural next step (tracking in-flight requests per worker) and is a documented extension below, not implemented here yet.
</details>

<details>
<summary><b>Why retry-on-failure instead of a circuit breaker?</b></summary>

At 3 workers, a bounded retry loop (max N-1 attempts) is simpler and sufficient — it can't cascade into a retry storm because the attempt ceiling is the worker count. A circuit breaker matters more at higher worker counts or with slow-failing dependencies; noted as a scaling consideration below.
</details>

<details>
<summary><b>Why is the model mocked?</b></summary>

The framework's job is to be model-agnostic. A mock model with randomized latency (0.1–0.5s) exercises the same code path as a real model — concurrency, timeouts, retries — without coupling the benchmark numbers to any one model's inference cost. Swapping in a real model means implementing one method (`predict`) — the serving layer is unchanged.
</details>

## Benchmark

Stress-tested with 200 requests at concurrency 20 (`stress_test.py`, async client):

| Metric | Result |
|---|---|
| Throughput | **51.1 req/sec** |
| Success rate | **100%** (0 failures) |
| Latency P50 | 345 ms |
| Latency P95 | 663 ms |
| Latency P99 | 781 ms |

Fault injection (worker killed mid-traffic): zero failed client requests — load balancer absorbed the failure via retry, visible as `attempts: 2` in affected responses.

## Quickstart

```bash
git clone https://github.com/vishnu-murukan/InferX.git
cd InferX
docker-compose up --build
```

| Service | URL |
|---|---|
| API | `http://localhost:8000` |
| Prometheus | `http://localhost:9090` |
| Grafana | `http://localhost:3000` (`admin` / `admin`) |

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"data": {"image": "test.jpg"}}'
```

```bash
python stress_test.py
```

## Project structure

```
inferx/
├── worker/              # FastAPI worker — model interface + inference endpoint
│   ├── main.py
│   ├── model.py
│   └── Dockerfile
├── load_balancer/        # Routing, retry logic, Prometheus metrics
│   ├── main.py
│   └── Dockerfile
├── prometheus.yml         # Scrape config
├── docker-compose.yml     # 6-container orchestration
└── stress_test.py          # Async load generator + latency percentiles
```

## Roadmap

- [ ] Least-connections load balancing strategy
- [ ] Redis-backed request queue for burst absorption
- [ ] Horizontal scaling — N workers via Compose profiles
- [ ] gRPC transport alongside REST
- [ ] Real model integration example (ONNX runtime)

## What this demonstrates

Distributed systems design · concurrency · fault tolerance · networking · systems performance benchmarking · observability tooling — applied to an ML serving context.

---



Architecture blueprint — RaceTracker (MVP)

High-level components
- Ingestion layer: WebSocket server (preferred) and HTTP batch endpoint. Entrypoint scales horizontally behind LB (nginx/ALB) and routes to telemetry service.
- Ingestion queue: a lightweight message broker (Kafka / Redis Streams / AWS Kinesis) to decouple validation/enrichment from ingestion.
- Enrichment/Processor: consumer service that map-matches, detects checkpoint crossings, applies anti-cheat heuristics, and writes derived events to Postgres and telemetry storage.
- API services: REST API for races, participants, results. Expose OpenAPI. Stateless, containerized.
- Frontend: React app (dashboard + participant views) connecting via REST and WebSocket for live updates.
- Storage: Postgres for canonical state, ClickHouse/TimescaleDB or S3+Parquet for raw telemetry, Redis for caching and leaderboards.

Data flow
1) Device -> WebSocket/HTTP -> Ingestion service -> Push to broker
2) Processor(s) consume broker -> validate/enrich -> write telemetry_point (raw store) + checkpoint_pass/lap events to Postgres
3) API reads Postgres and caches derived leaderboards in Redis; frontend subscribes to WebSocket channel for live updates

Scaling notes
- Use partitioned topics keyed by race_id to allow parallel processing.
- Autoscale ingestion pods based on connections and message rates; use sticky sessions when using WebSocket.
- Retention: keep raw telemetry in hot store for N days, then move to cold S3.

Security
- TLS everywhere; mTLS optional for device authentication. JWT for user auth. Device tokens for telemetry.
- Rate limiting and per-device quotas.

Operational
- CI: lint, tests, build, push image.
- Monitoring: Prometheus metrics on ingestion latency, processing lag, message backlog, and API error rates.

RaceTracker — Data model (MVP)

Overview
- Goal: canonical, auditable records for races, participants, checkpoints, telemetry, and results.
- Use Postgres as the transactional canonical store. Use a columnar/time-series store (ClickHouse / TimescaleDB) or S3+Parquet for high-volume raw telemetry.

Entities

1) race
- id: uuid PK
- name: text
- slug: text UNIQUE
- start_time: timestamptz
- end_time: timestamptz NULL
- timezone: text
- course_geojson: jsonb (polyline/course geometry)
- status: enum (draft, scheduled, running, finished, cancelled)
- metadata: jsonb

2) participant
- id: uuid PK
- race_id: uuid FK -> race(id)
- name: text
- bib_number: text
- team: text NULL
- country: text NULL
- device_id: text NULL (registered device identifier)
- status: enum (registered, started, finished, dnf)
- metadata: jsonb

3) checkpoint
- id: uuid PK
- race_id: uuid FK -> race(id)
- name: text
- sequence: integer (order on course)
- location: geography(Point,4326) or jsonb {lat,lon}
- radius_meters: integer (detection radius)

4) telemetry_point (raw ingest store - append-only)
- id: bigint or uuid PK
- race_id: uuid
- participant_id: uuid NULL
- device_id: text
- ts: timestamptz
- lat: double
- lon: double
- accuracy_m: float NULL
- speed_m_s: float NULL
- bearing_deg: float NULL
- received_at: timestamptz DEFAULT now()
- raw_payload: jsonb NULL

Notes: telemetry_point may be stored in a cheaper, high-throughput store and then streamed into Postgres as canonical events after enrichment.

5) lap / checkpoint_pass
- id: uuid PK
- race_id: uuid
- participant_id: uuid
- checkpoint_id: uuid
- ts: timestamptz (time of crossing)
- device_point_id: bigint NULL (reference to telemetry_point)
- method: enum (auto_mapmatch, manual_override)

6) race_result
- id: uuid PK
- race_id: uuid
- participant_id: uuid
- rank: integer NULL
- total_time: interval NULL
- laps: integer NULL
- status: enum (ok, dnf, dsq)
- computed_at: timestamptz
- details: jsonb

Indexes & constraints
- Index telemetry_point on (race_id, participant_id, ts DESC) for fast recent queries
- Index checkpoint on (race_id, sequence)
- Foreign keys for race -> checkpoints, participants -> race

Audit & immutability
- Keep raw telemetry immutable; derived tables (laps, results) may be recomputed and stored with computed_at and origin tag.

Privacy
- Avoid storing PII in telemetry_point.raw_payload; keep participant PII in participant table and restrict access via RBAC and column-level encryption if needed.

Migration hints
- Use sequential migrations: 1) create race/participant/checkpoint, 2) add telemetry ingest table, 3) add enrichment pipeline outputs.

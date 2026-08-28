# Urban Problem Hotspot Engine

An urban civic-problem analytics and municipal decision-support system.

## Core pipeline

Complaints → classification → spatial clustering → temporal analysis → problem relationships → priority scoring → explainable municipal recommendations → GIS dashboard.

## Project scope

The initial implementation targets Jabalpur using a 79-ward geographic base. Synthetic data is used only for controlled testing and is explicitly separated from publicly reported complaints.

## Repository structure

* `backend/` — API, services, database models and schemas
* `ml/` — analytics/ML engine
* `data/` — raw, processed and synthetic datasets
* `geo/` — ward boundaries and ward reference data
* `database/` — SQL schema, seed data and analytical queries
* `tests/` — unit and integration tests
* `docs/` — architecture and algorithm documentation


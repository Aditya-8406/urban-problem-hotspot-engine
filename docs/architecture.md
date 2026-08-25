# Architecture

## Pipeline

Complaints
→ classification
→ spatial clustering
→ temporal analysis
→ problem relationships
→ priority scoring
→ explainability
→ API
→ GIS dashboard.

## Layer responsibilities

- `frontend/`: presentation.
- `backend/`: API and application orchestration.
- `ml/`: analytical engine.
- `data/`: datasets.
- `geo/`: geographic reference assets.
- `database/`: persistence and spatial queries.

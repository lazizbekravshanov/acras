# ACRAS — AI Crash Report Automation System

Real-time traffic incident detection, reporting, and analytics using computer vision on public highway cameras.

## What It Does

ACRAS ingests live video feeds from publicly available DOT traffic cameras and:

1. **Detects** traffic incidents (crashes, stalls, debris, fire) using YOLOv8 + optical flow + a custom CNN classifier
2. **Classifies** severity (minor, moderate, severe, critical) in real-time
3. **Generates** structured crash reports automatically — no human in the loop
4. **Alerts** relevant parties via webhooks, email, and a live dashboard
5. **Analyzes** historical data to predict crash hotspots and patterns

**Target: <30 seconds from incident to report** (vs. 2-5 minutes for average 911 reporting).

## Architecture

```
DOT Cameras → Stream Manager → Frame Buffer (Redis)
    → YOLO Detection → Optical Flow → Crash Classifier → Severity Model
    → Incident Tracker (dedup + state machine)
    → Report Generator → Alert Dispatcher
    → PostgreSQL + PostGIS → Analytics Engine
    → Next.js Dashboard (live map + real-time feed)
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, FastAPI, SQLAlchemy 2.0, Celery |
| Frontend | Next.js 14, TypeScript, Tailwind CSS, Leaflet.js, Recharts |
| ML | YOLOv8 (ultralytics), PyTorch, OpenCV |
| Database | PostgreSQL 16 + PostGIS |
| Cache/Queue | Redis |
| Monitoring | Prometheus + Grafana |
| Container | Docker + Docker Compose |

## Quick Start

```bash
# Clone and setup
git clone https://github.com/yourusername/acras.git
cd acras
cp .env.example .env

# Start everything
make demo

# Open the dashboard
open http://localhost:3000

# API documentation
open http://localhost:8000/docs
```

## Development

```bash
# Start services
make dev

# Run backend tests
make test

# Run linting
make lint

# View logs
make logs

# Seed camera data
make seed

# Generate sample incidents for analytics
make sample-data
```

## Project Structure

```
acras/
├── backend/          # FastAPI backend + ML pipeline
│   ├── app/
│   │   ├── api/      # REST API endpoints
│   │   ├── ml/       # YOLO, optical flow, crash classifier, severity model
│   │   ├── models/   # SQLAlchemy ORM models
│   │   ├── services/ # Business logic (stream manager, detection, tracking, reporting)
│   │   └── tasks/    # Celery background tasks
│   └── tests/
├── frontend/         # Next.js dashboard
├── ml_training/      # Model training scripts and notebooks
├── scripts/          # Database seeding, simulation, sample data
├── data/             # Camera feed URLs, sample videos
└── monitoring/       # Prometheus + Grafana configuration
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/cameras` | List cameras (filterable) |
| POST | `/api/v1/cameras` | Add a camera |
| GET | `/api/v1/incidents` | List incidents (filterable) |
| GET | `/api/v1/incidents/{id}` | Incident detail |
| PATCH | `/api/v1/incidents/{id}` | Update incident status |
| GET | `/api/v1/reports` | List reports |
| GET | `/api/v1/analytics/summary` | Dashboard summary stats |
| GET | `/api/v1/analytics/heatmap` | Crash heatmap data |
| GET | `/api/v1/analytics/trends` | Incident trends |
| GET | `/api/v1/analytics/risk` | Location risk score |
| WS | `/api/v1/ws` | Real-time incident updates |

Full OpenAPI documentation available at `/docs` when the backend is running.

## Camera Sources

50+ cameras from 10 US states using publicly available DOT traffic camera feeds:

- Florida (FDOT), California (Caltrans), Texas (TxDOT)
- New York (NYSDOT), Ohio (ODOT), Virginia (VDOT)
- Georgia (GDOT), Illinois (IDOT), Washington (WSDOT), Colorado (CDOT)

## Detection Pipeline

1. **YOLOv8** detects vehicles, persons, fire, smoke, debris
2. **Optical Flow** (Farneback) detects sudden stops, erratic movement, stationary vehicles
3. **Crash Classifier** (ResNet18 CNN) classifies frames as crash vs. normal
4. **Severity Model** combines all signals into a 0-1 severity score
5. **Incident Tracker** handles deduplication, multi-frame confirmation, and state management

## License

MIT

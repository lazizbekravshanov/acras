# ACRAS Architecture

## System Overview

ACRAS is a multi-layer system for real-time traffic incident detection and reporting.

### Data Flow

```
Camera Feeds → Stream Manager → Redis Frame Buffer
  → Detection Engine (YOLO + Optical Flow + Crash Classifier + Severity)
  → Incident Tracker (Dedup + State Machine)
  → Report Generator → Alert Dispatcher
  → PostgreSQL (Incidents, Reports, Alerts)
  → Analytics Engine → Dashboard (WebSocket)
```

### Key Design Decisions

1. **1 FPS frame extraction** — Crashes don't happen between frames at 1 FPS. This keeps processing load manageable (50 cameras = 50 frames/sec).

2. **Multi-model detection** — No single model catches everything. YOLO handles object detection, optical flow catches motion anomalies, the classifier provides crash-specific confidence.

3. **Redis pub/sub for frames** — Decouples ingestion from processing. Allows multiple consumers (detection, recording, health checks) without bottlenecking.

4. **State machine for incidents** — Prevents duplicate alerts and provides a clear lifecycle: detected → confirmed → responding → clearing → resolved.

5. **Rule-based severity** (upgradeable to ML) — Start simple, validate with real data, then train a model. The pipeline is the same either way.

### Scaling Considerations

- **Horizontal camera scaling**: Each Stream Manager instance handles N cameras. Add instances for more cameras.
- **Detection scaling**: Celery workers can run on GPU nodes. Partition cameras across workers.
- **Database**: PostGIS indexes handle spatial queries efficiently. Materialized analytics snapshots prevent slow dashboard queries.

# ACRAS API Reference

Base URL: `http://localhost:8000`
Full interactive docs: `http://localhost:8000/docs`

## Authentication

All write operations require an API key in the `X-API-Key` header.

```bash
curl -H "X-API-Key: your-key" http://localhost:8000/api/v1/cameras
```

## Cameras

### List Cameras
```
GET /api/v1/cameras?page=1&page_size=50&status=active&state_code=FL&interstate=I-95
```

### Get Camera
```
GET /api/v1/cameras/{camera_id}
```

### Create Camera
```
POST /api/v1/cameras
Content-Type: application/json
X-API-Key: your-key

{
  "name": "I-95 NB @ MM 142",
  "stream_url": "https://example.com/feed.mjpeg",
  "stream_type": "mjpeg",
  "latitude": 29.1234,
  "longitude": -81.0567,
  "state_code": "FL",
  "interstate": "I-95",
  "direction": "NB"
}
```

### Bulk Import
```
POST /api/v1/cameras/bulk
Content-Type: application/json
X-API-Key: your-key

{
  "cameras": [...]
}
```

## Incidents

### List Incidents
```
GET /api/v1/incidents?status=confirmed&severity=severe&interstate=I-95&page=1
```

### Get Incident
```
GET /api/v1/incidents/{incident_id}
```

### Update Incident
```
PATCH /api/v1/incidents/{incident_id}
X-API-Key: your-key

{"status": "resolved"}
```

## Reports

### List Reports
```
GET /api/v1/reports?incident_id={uuid}
```

### Get Report
```
GET /api/v1/reports/{report_id}
```

## Analytics

### Summary
```
GET /api/v1/analytics/summary
```

### Heatmap
```
GET /api/v1/analytics/heatmap?start_date=2025-01-01&severity=severe
```

### Trends
```
GET /api/v1/analytics/trends?period=daily&days=30
```

### Risk Score
```
GET /api/v1/analytics/risk?lat=29.12&lon=-81.05
```

## Alerts

### Create Alert Config
```
POST /api/v1/alerts/configs
X-API-Key: your-key

{
  "name": "Severe Crash Webhook",
  "channel": "webhook",
  "recipient": "https://example.com/webhook",
  "min_severity": "severe",
  "incident_types": ["crash", "fire"]
}
```

### List Alert Configs
```
GET /api/v1/alerts/configs
```

### Alert History
```
GET /api/v1/alerts/history?incident_id={uuid}&status=sent
```

## WebSocket

```
WS /api/v1/ws
```

Messages from server:
```json
{"type": "incident.new", "data": {...}}
{"type": "incident.updated", "data": {...}}
{"type": "incident.resolved", "data": {...}}
{"type": "camera.status_change", "data": {...}}
```

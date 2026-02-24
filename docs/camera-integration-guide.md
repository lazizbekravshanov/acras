# Camera Integration Guide

## Supported Stream Types

| Type | Protocol | Description | Example |
|------|----------|-------------|---------|
| `rtsp` | RTSP | Real-Time Streaming Protocol | `rtsp://camera.dot.gov/stream1` |
| `mjpeg` | HTTP/MJPEG | Motion JPEG over HTTP | `http://camera.dot.gov/mjpeg` |
| `hls` | HLS | HTTP Live Streaming | `https://camera.dot.gov/stream.m3u8` |
| `http_image` | HTTP | Static image URL (refreshed periodically) | `https://dot.gov/cam.jpg` |

## Adding a New Camera

### Via API
```bash
curl -X POST http://localhost:8000/api/v1/cameras \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{
    "name": "I-95 NB @ MM 142",
    "stream_url": "https://fl511.com/camera/2046",
    "stream_type": "http_image",
    "latitude": 29.1234,
    "longitude": -81.0567,
    "state_code": "FL",
    "interstate": "I-95",
    "direction": "NB",
    "mile_marker": 142.3,
    "source_agency": "FDOT"
  }'
```

### Via Bulk Import
Add cameras to `data/camera_feeds.json` and run:
```bash
make seed
```

## Finding Public Camera Feeds

### State DOT 511 Systems
Most states operate 511 traveler information systems with public camera access:

- **Florida**: fl511.com — MJPEG and HTTP image feeds
- **California**: cwwp2.dot.ca.gov — HTTP image snapshots
- **Texas**: its.txdot.gov — HTTP image snapshots
- **New York**: 511ny.org — HTTP image feeds
- **Ohio**: ohgo.com — HTTP image feeds
- **Washington**: wsdot.wa.gov — HTTP image snapshots

### Tips for Finding Feeds
1. Visit the state's 511 website
2. Open browser DevTools → Network tab
3. Click on a camera to view its feed
4. Look for image URLs in the network requests
5. The URL pattern usually works for all cameras in that system

### Important Notes
- Only use publicly accessible feeds
- No authentication bypass
- These are taxpayer-funded public infrastructure cameras
- Respect rate limits (1 request/second per camera is sufficient)

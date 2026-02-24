# Deployment Guide

## Development

```bash
make dev  # Starts all services with docker-compose
```

Services:
- Backend API: http://localhost:8000
- Frontend Dashboard: http://localhost:3000
- PostgreSQL: localhost:5432
- Redis: localhost:6379
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001

## Production Deployment

### Prerequisites
- Docker and Docker Compose
- GPU server recommended for ML inference (NVIDIA with CUDA)
- Minimum: 4 CPU cores, 8GB RAM, 50GB disk

### Environment Configuration
1. Copy `.env.example` to `.env`
2. Set strong `API_KEY`
3. Configure SMTP for email alerts
4. Set `LOG_LEVEL=WARNING` for production
5. Configure `CORS_ORIGINS` for your domain

### Docker Production Build
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Database Migrations
```bash
docker compose exec backend alembic upgrade head
```

### Seeding Cameras
```bash
docker compose exec backend python -m scripts.seed_cameras
```

### Monitoring
- Prometheus scrapes backend metrics at `/metrics`
- Grafana dashboards available at port 3001
- Default Grafana credentials: admin/admin

### Health Checks
- `GET /health` — Basic liveness check
- `GET /ready` — Full readiness check (DB + Redis)

### Scaling
- Scale Celery workers: `docker compose scale celery_worker=4`
- For >100 cameras, consider dedicated GPU workers
- Use Redis Cluster for high-throughput frame pub/sub

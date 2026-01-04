# Docker Deployment Guide

## Quick Start

### 1. Setup Environment Variables

```bash
# Copy example env file
cp docker/.env.example .env

# Edit with your values
nano .env
```

### 2. Build and Start

```bash
# Build all services
docker-compose build

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

### 3. Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes data)
docker-compose down -v
```

## Services

| Service | Port | Description |
|---------|------|-------------|
| voice-bot | 5015, 5018 | Sara AI Voice Bot |
| dashboard-api | 5016 | Dashboard Backend API |
| dashboard-frontend | 5017 | Dashboard Frontend |
| mongodb | 27017 | MongoDB Database |

## Production Deployment

### Option 1: Use External MongoDB

1. Comment out `mongodb` service in `docker-compose.yml`
2. Set `MONGODB_URI` in `.env` to your external MongoDB

### Option 2: Use Production Override

```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Useful Commands

```bash
# View logs for specific service
docker-compose logs -f voice-bot
docker-compose logs -f dashboard-api
docker-compose logs -f dashboard-frontend

# Restart a service
docker-compose restart voice-bot

# Rebuild a service
docker-compose up -d --build dashboard-frontend

# Execute command in container
docker-compose exec voice-bot bash
docker-compose exec dashboard-api sh

# View resource usage
docker stats
```

## Troubleshooting

### MongoDB Connection Issues
- Check `MONGODB_URI` format
- Ensure MongoDB container is healthy: `docker-compose ps mongodb`
- Check logs: `docker-compose logs mongodb`

### Frontend Not Loading
- Rebuild frontend: `docker-compose up -d --build dashboard-frontend`
- Check API URL in browser console
- Verify `REACT_APP_API_URL` is set correctly

### Port Conflicts
- Change ports in `docker-compose.yml` if needed
- Check what's using ports: `sudo lsof -i :5015`

## Data Persistence

- MongoDB data: Stored in `mongodb_data` volume
- Logs: Mounted from `./logs` directory
- Audio files: Mounted from `./audio_files` directory

## Backup

```bash
# Backup MongoDB
docker-compose exec mongodb mongodump --out /data/backup

# Restore MongoDB
docker-compose exec mongodb mongorestore /data/backup
```


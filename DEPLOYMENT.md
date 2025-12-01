# Deployment Guide - Aadhaar Masking API with 5 Workers

## Quick Start (Docker - Recommended)

### 1. Build the Docker Image
```bash
docker build -t aadharmask:latest .
```

### 2. Run the Container
```bash
docker run -d -p 8000:8000 --name aadharmask aadharmask:latest
```

### 3. Verify It's Running
```bash
# Check health
curl http://localhost:8000/health

# View logs
docker logs -f aadharmask
```

## Alternative: Local Development (Without Docker)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run with 5 Workers
```bash
gunicorn main:app -w 5 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --timeout 120
```

### 3. Or Run Single Worker (Development)
```bash
python main.py
```

## Configuration Details

### Current Setup:
- **Workers**: 5 (handles up to 5 concurrent requests)
- **Worker Type**: Gunicorn + Uvicorn (async support)
- **Timeout**: 120 seconds (for slow YOLO inference)
- **Max Logs**: 1000 entries
- **Log Retention**: 7 days
- **File Locking**: ✅ Enabled (prevents log race conditions)

### Ports:
- **API**: http://localhost:8000
- **Health Check**: http://localhost:8000/health
- **Admin Panel**: http://localhost:8000/admin/login
- **API Docs**: http://localhost:8000/docs

### Default Credentials:
- **Username**: admin
- **Password**: gravitonadmin

> ⚠️ **IMPORTANT**: Change these in production via environment variables:
> - `ADMIN_USERNAME`
> - `ADMIN_PASSWORD`
> - `SECRET_KEY`

## Docker Commands Reference

```bash
# Build
docker build -t aadharmask:latest .

# Run (detached)
docker run -d -p 8000:8000 --name aadharmask aadharmask:latest

# Run (with environment variables)
docker run -d -p 8000:8000 \
  -e ADMIN_USERNAME=myadmin \
  -e ADMIN_PASSWORD=mypassword \
  -e SECRET_KEY=mysecretkey \
  --name aadharmask aadharmask:latest

# View logs
docker logs -f aadharmask

# Stop
docker stop aadharmask

# Remove
docker rm aadharmask

# Restart
docker restart aadharmask
```

## Testing Multi-Worker Performance

Send 5 concurrent requests:
```bash
for i in {1..5}; do
  curl -X POST -F "file=@test.jpg" \
    -H "Authorization: Bearer YOUR_TOKEN" \
    http://localhost:8000/api/aadhaar/upload &
done
wait
```

Check logs count:
```bash
# The request_logs.json should have all 5 entries
cat request_logs.json | grep timestamp | wc -l
```

## Troubleshooting

### Issue: Only partial logs saved (race condition)
**Solution**: ✅ Fixed with file locking in this version

### Issue: Out of memory
**Solution**: Reduce workers (each loads YOLO model ~500MB-1GB)

### Issue: Slow performance
**Solution**: 
- Check CPU cores (workers should ≈ CPU cores)
- Use `include_all_rotations=False` for faster processing

### Issue: Timeout errors
**Solution**: Increase timeout in Dockerfile:
```dockerfile
CMD [..., "--timeout", "180", ...]  # 3 minutes
```

## Production Recommendations

1. **Use HTTPS**: Put behind nginx/traefik with SSL
2. **Change Credentials**: Use strong passwords via env vars
3. **Monitor**: Track `/health` endpoint for system stats
4. **Log Rotation**: Consider database for logs beyond 1000 entries
5. **Resource Limits**: Set Docker memory limits based on workers:
   ```bash
   docker run -m 8g ...  # 8GB for 5 workers
   ```

## Files Overview

- `main.py` - FastAPI application with file-locked logging
- `aadhaar_processor.py` - YOLO model inference
- `requirements.txt` - Python dependencies (with filelock)
- `Dockerfile` - Production container with 5 workers
- `request_logs.json` - Log storage (auto-created)
- `request_logs.json.lock` - Lock file (auto-created)

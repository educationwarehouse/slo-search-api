# Self-Hosted Deployment Guide

Complete guide for hosting SLO Search API on your own infrastructure using Docker.

## Architecture

**Stack:**
- PostgreSQL 15+ with pgvector (vector similarity search)
- FastAPI application (Python 3.11)
- Nginx reverse proxy (SSL termination, rate limiting)
- Docker Compose orchestration

**Containers:**
- `postgres`: PostgreSQL + pgvector extension
- `api`: FastAPI app with sentence-transformers
- `nginx`: Reverse proxy with SSL

## Quick Start

```bash
# 1. Clone and configure
git clone <repo> slo-search
cd slo-search
cp .env.docker .env

# 2. Edit .env
nano .env  # Set POSTGRES_PASSWORD

# 3. Generate SSL certificates (development)
bash generate_ssl.sh

# 4. Start services
docker-compose up -d

# 5. Wait for database initialization (~30s)
docker-compose logs -f postgres

# 6. Run data ingestion (~5-10 minutes)
# IMPORTANT: Data directory must be accessible

# Option A: Local ingestion to Docker DB (recommended)
export DATABASE_URI="postgres://slo_user:YOUR_PASSWORD@localhost:5432/slo_search"
python ingest.py  # Run from host, writes to Docker DB

# Option B: Mount data in container (add to docker-compose.yml api service):
#   volumes:
#     - ../curriculum-fo:/data:ro
# Update config: export DATA_DIR=/data
# Then: docker compose exec api python ingest.py

# 7. Verify data loaded
curl "http://localhost/api/stats"
# Expected: {"doelzinnen": {"total": 2642, "embedded": 2642}, ...}
```

## Production Deployment

### 1. Server Requirements

**Minimum:**
- 2 CPU cores
- 4GB RAM (for embedding model)
- 20GB disk (PostgreSQL data + embeddings)
- Ubuntu 22.04 LTS / Debian 12

**Recommended:**
- 4 CPU cores
- 8GB RAM
- 50GB SSD
- Static IP address
- Domain name

### 2. Initial Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install docker-compose-plugin

# Logout and login for group changes
```

### 3. Application Setup

```bash
# Clone repository
git clone <repo> /opt/slo-search
cd /opt/slo-search

# Configure environment
cp .env.docker .env
nano .env  # Set strong POSTGRES_PASSWORD
```

### 4. SSL Setup (Let's Encrypt)

**Using Certbot:**

```bash
# Install certbot
sudo apt install certbot

# Stop nginx temporarily
docker-compose stop nginx

# Get certificate
sudo certbot certonly --standalone -d your-domain.com

# Certificates saved to:
# /etc/letsencrypt/live/your-domain.com/fullchain.pem
# /etc/letsencrypt/live/your-domain.com/privkey.pem

# Update nginx.conf to use real certificates
nano nginx.conf
```

Update nginx.conf SSL paths:
```nginx
ssl_certificate /etc/nginx/ssl/fullchain.pem;
ssl_certificate_key /etc/nginx/ssl/privkey.pem;
```

Update docker-compose.yml volumes:
```yaml
nginx:
  volumes:
    - /etc/letsencrypt:/etc/nginx/ssl:ro
```

**Auto-renewal:**
```bash
# Add to crontab
sudo crontab -e

# Add line:
0 0 * * 0 certbot renew --quiet && docker-compose -f /opt/slo-search/docker-compose.yml restart nginx
```

### 5. Start Production

```bash
# Build and start
docker-compose up -d --build

# Check status
docker-compose ps
docker-compose logs -f

# Run ingestion
docker-compose exec api python ingest.py

# Verify
curl "https://your-domain.com/api/stats"
```

## Configuration

### Environment Variables (.env)

```bash
# Required
POSTGRES_PASSWORD=strong_random_password_here

# Optional
DOMAIN=your-domain.com
```

### Docker Compose Override

For custom configurations, create `docker-compose.override.yml`:

```yaml
version: '3.8'

services:
  api:
    environment:
      DEFAULT_LIMIT: 20
      DEFAULT_THRESHOLD: 0.1
    deploy:
      resources:
        limits:
          memory: 4G
```

## Monitoring

### Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f postgres
docker-compose logs -f nginx

# Last 100 lines
docker-compose logs --tail=100
```

### Health Checks

```bash
# Container health
docker-compose ps

# API health
curl http://localhost/api/stats

# Database connections
docker-compose exec postgres psql -U slo_user -d slo_search -c "SELECT count(*) FROM pg_stat_activity;"
```

### Resource Usage

```bash
# Container stats
docker stats

# Disk usage
docker system df
df -h /var/lib/docker
```

## Backup & Restore

### Database Backup

```bash
# Automated backup script
cat > backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/backups/slo-search"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

docker-compose exec -T postgres pg_dump -U slo_user slo_search | gzip > $BACKUP_DIR/slo_search_$DATE.sql.gz

# Keep only last 7 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete
EOF

chmod +x backup.sh

# Add to crontab (daily at 2 AM)
0 2 * * * /opt/slo-search/backup.sh
```

### Restore

```bash
# Stop API
docker-compose stop api

# Restore database
gunzip -c backup.sql.gz | docker-compose exec -T postgres psql -U slo_user slo_search

# Restart
docker-compose start api
```

### Volume Backup

```bash
# Backup volumes
docker run --rm \
  -v slo-search_pgdata:/data \
  -v $(pwd):/backup \
  ubuntu tar czf /backup/pgdata_backup.tar.gz /data
```

## Updates

### Update Application

```bash
cd /opt/slo-search

# Pull latest code
git pull

# Rebuild and restart
docker-compose down
docker-compose up -d --build

# Check logs
docker-compose logs -f api
```

### Update Curriculum Data

```bash
# Update data repository
cd ../curriculum-fo
git pull

# Re-run ingestion
cd /opt/slo-search
docker-compose exec api python ingest.py
```

### Update Dependencies

```bash
# Edit requirements-vercel.txt
nano requirements-vercel.txt

# Rebuild
docker-compose build api
docker-compose up -d api
```

## Scaling

### Horizontal Scaling

```bash
# Scale API containers
docker-compose up -d --scale api=4

# Update nginx upstream
nano nginx.conf
```

nginx.conf:
```nginx
upstream api_backend {
    least_conn;
    server api:8000;
    server api:8001;
    server api:8002;
    server api:8003;
}
```

### Database Connection Pooling

Increase pool size in `models.py`:
```python
db = DAL(db_uri, migrate=True, pool_size=20)
```

### Caching

Add Redis for query caching:

```yaml
# docker-compose.yml
redis:
  image: redis:alpine
  restart: unless-stopped
```

## Security

### Firewall

```bash
# UFW
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### Database Security

```bash
# Change default password
docker-compose exec postgres psql -U postgres -c "ALTER USER slo_user PASSWORD 'new_strong_password';"

# Update .env
nano .env  # Update POSTGRES_PASSWORD
docker-compose restart api
```

### Rate Limiting

Already configured in nginx.conf (10 req/s). Adjust if needed:

```nginx
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=20r/s;
```

### Network Isolation

```yaml
# docker-compose.yml
services:
  postgres:
    networks:
      - backend
    # Remove ports section (no external access)
  
  api:
    networks:
      - backend
      - frontend
  
  nginx:
    networks:
      - frontend

networks:
  frontend:
  backend:
```

## Troubleshooting

### API not responding

```bash
# Check container status
docker-compose ps

# Check logs
docker-compose logs api

# Restart
docker-compose restart api
```

### Database connection errors

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check connection
docker-compose exec postgres pg_isready -U slo_user

# View connections
docker-compose exec postgres psql -U slo_user -d slo_search -c "SELECT * FROM pg_stat_activity;"

# Restart database
docker-compose restart postgres
```

### Out of memory

```bash
# Check usage
docker stats

# Increase limits in docker-compose.yml
# Reduce workers in Dockerfile CMD
# Add swap space
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Slow queries

```bash
# Enable query logging
docker-compose exec postgres psql -U postgres -c "ALTER SYSTEM SET log_min_duration_statement = 1000;"
docker-compose restart postgres

# View slow queries in logs
docker-compose logs postgres | grep "duration:"
```

## Performance Tuning

### PostgreSQL

```sql
-- Optimize for read-heavy workload
ALTER SYSTEM SET shared_buffers = '1GB';
ALTER SYSTEM SET effective_cache_size = '3GB';
ALTER SYSTEM SET maintenance_work_mem = '256MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;
ALTER SYSTEM SET work_mem = '16MB';
ALTER SYSTEM SET min_wal_size = '1GB';
ALTER SYSTEM SET max_wal_size = '4GB';
```

Restart: `docker-compose restart postgres`

### Vector Index Tuning

```sql
-- Rebuild index with more lists for better accuracy
DROP INDEX doelzin_embedding_idx;
CREATE INDEX doelzin_embedding_idx ON doelzin_embedding 
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 200);

-- Analyze
VACUUM ANALYZE doelzin_embedding;
```

## Monitoring Stack (Optional)

Add Prometheus + Grafana:

```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"
  
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: admin
```

## Cost Estimate

**VPS Hosting:**
- Hetzner Cloud CX21: €5.83/month (2 vCPU, 4GB RAM, 40GB SSD)
- DigitalOcean Basic: $12/month (2 vCPU, 4GB RAM, 80GB SSD)
- Linode Shared 4GB: $24/month (2 vCPU, 4GB RAM, 80GB SSD)

**Total monthly cost:** €5-25 depending on provider

**Comparison to Vercel + Supabase:**
- Free tier: Limited usage
- Paid tier: ~$45/month minimum

**Self-hosted advantage:** More resources for less cost + full control

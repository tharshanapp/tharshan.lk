# OpenGov AI Assistant - Production Deployment Guide

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Configuration](#configuration)
4. [SSL Certificate Setup](#ssl-certificate-setup)
5. [Docker Deployment](#docker-deployment)
6. [GitHub Deployment](#github-deployment)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

- Docker & Docker Compose
- Git
- Domain name (tharshan.lk) pointing to your server IP
- Gemini API Key (from https://makersuite.google.com/app/apikey)

---

## Quick Start

### 1. Clone and Setup

```bash
# Navigate to project directory
cd OpenGov_AI_Assistant

# Make SSL script executable
chmod +x ssl/generate-ssl.sh

# Generate SSL certificates (for testing)
./ssl/generate-ssl.sh
```

### 2. Configure Environment

```bash
# Edit backend/.env file
nano backend/.env

# IMPORTANT: Update these values:
# - GEMINI_API_KEY=your_actual_api_key_here
# - ADMIN_TOKEN=your_secure_random_token
```

### 3. Deploy with Docker

```bash
# Build and start all services
docker-compose up -d

# Check if services are running
docker-compose ps

# View logs
docker-compose logs -f
```

### 4. Verify Deployment

```bash
# Check health endpoint
curl http://localhost/health
curl https://localhost/health -k  # -k ignores SSL verification for self-signed certs

# Should return:
# {"status":"healthy","timestamp":"...","gemini_available":true}
```

---

## Configuration

### Environment Variables (.env)

| Variable | Description | Required |
|----------|-------------|----------|
| `GEMINI_API_KEY` | Google Gemini API key | ✅ Yes |
| `ADMIN_TOKEN` | Admin token for upload feature | ✅ Yes |
| `APP_ENV` | Environment (production/development) | No |
| `CORS_ORIGINS` | Allowed origins (comma-separated) | No |
| `CHUNK_SIZE` | Vector chunk size | No |
| `CHUNK_OVERLAP` | Chunk overlap | No |

### Important Notes

1. **Never commit .env file** - It's in .gitignore for security
2. **Change ADMIN_TOKEN** - Use a strong random token
3. **Set GEMINI_API_KEY** - Required for AI features to work

---

## SSL Certificate Setup

### Option 1: Self-Signed (Testing Only)

```bash
# Generate self-signed certificates
./ssl/generate-ssl.sh
```

⚠️ **Warning**: Self-signed certificates will show browser warnings. Use only for testing.

### Option 2: Let's Encrypt (Production - Recommended)

```bash
# Install certbot
sudo apt-get update
sudo apt-get install certbot

# Generate certificates (stop nginx first if running)
sudo systemctl stop nginx  # or docker-compose stop nginx
sudo certbot certonly --standalone -d tharshan.lk -d www.tharshan.lk

# Copy certificates to ssl directory
sudo cp /etc/letsencrypt/live/tharshan.lk/fullchain.pem ssl/certificate.crt
sudo cp /etc/letsencrypt/live/tharshan.lk/privkey.pem ssl/private.key

# Set permissions
sudo chmod 644 ssl/certificate.crt
sudo chmod 600 ssl/private.key

# Restart services
docker-compose restart nginx
```

### Auto-renewal for Let's Encrypt

```bash
# Add to crontab (sudo crontab -e)
0 3 * * * certbot renew --quiet && docker-compose restart nginx
```

---

## Docker Deployment

### Start Services

```bash
# Start all services (including nginx for production)
docker-compose --profile production up -d

# Start without nginx (development)
docker-compose up -d
```

### Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes data!)
docker-compose down -v
```

### View Logs

```bash
# All logs
docker-compose logs -f

# Specific service
docker-compose logs -f opengov-ai
docker-compose logs -f nginx
```

### Update Deployment

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose --profile production up -d --build
```

---

## GitHub Deployment

### 1. Push to GitHub

```bash
# Initialize git (if not already)
git init
git add .
git commit -m "Initial commit"

# Add remote and push
git remote add origin https://github.com/yourusername/OpenGov_AI_Assistant.git
git push -u origin main
```

### 2. GitHub Secrets (for CI/CD)

Add these secrets in GitHub repository settings:
- `GEMINI_API_KEY`
- `ADMIN_TOKEN`
- `DOCKER_USERNAME`
- `DOCKER_PASSWORD`

### 3. GitHub Actions (Optional)

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy via SSH
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd /path/to/OpenGov_AI_Assistant
            git pull
            docker-compose --profile production up -d --build
```

---

## Troubleshooting

### Connection Error

**Problem**: "Connection error" when accessing tharshan.lk

**Solutions**:

1. **Check if containers are running**
   ```bash
   docker-compose ps
   ```

2. **Check logs for errors**
   ```bash
   docker-compose logs opengov-ai
   docker-compose logs nginx
   ```

3. **Verify SSL certificates exist**
   ```bash
   ls -la ssl/
   # Should have: certificate.crt and private.key
   ```

4. **Test backend directly**
   ```bash
   # Access backend without nginx
   curl http://localhost:8000/health
   
   # If this works but nginx doesn't, check nginx config
   docker-compose exec nginx nginx -t
   ```

5. **Check DNS resolution**
   ```bash
   # Make sure tharshan.lk points to your server IP
   ping tharshan.lk
   nslookup tharshan.lk
   ```

6. **Check firewall ports**
   ```bash
   # Open required ports
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw status
   ```

### CORS Errors

**Problem**: Frontend can't connect to backend due to CORS

**Solution**: Update `backend/.env`:
```
CORS_ORIGINS=http://localhost:3000,http://localhost:8000,https://tharshan.lk,https://www.tharshan.lk,http://tharshan.lk,http://www.tharshan.lk
```

### SSL Certificate Errors

**Problem**: Browser shows SSL warnings

**Solution**: Use Let's Encrypt certificates instead of self-signed (see SSL setup section)

### Backend Not Starting

**Problem**: Backend container exits immediately

**Solutions**:

1. **Check logs**
   ```bash
   docker-compose logs opengov-ai
   ```

2. **Verify .env file exists**
   ```bash
   ls -la backend/.env
   ```

3. **Check if GEMINI_API_KEY is set**
   ```bash
   docker-compose exec opengov-ai env | grep GEMINI
   ```

### Nginx Proxy Errors

**Problem**: Nginx returns 502 Bad Gateway

**Solutions**:

1. **Check if backend is running**
   ```bash
   docker-compose ps opengov-ai
   ```

2. **Test nginx configuration**
   ```bash
   docker-compose exec nginx nginx -t
   ```

3. **Check nginx can reach backend**
   ```bash
   docker-compose exec nginx ping opengov-ai
   ```

---

## Production Checklist

- [ ] Set `GEMINI_API_KEY` in `.env`
- [ ] Change `ADMIN_TOKEN` to a secure random string
- [ ] Set up proper SSL certificates (Let's Encrypt)
- [ ] Configure DNS for tharshan.lk
- [ ] Open ports 80 and 443 in firewall
- [ ] Set up automatic SSL renewal
- [ ] Configure backup strategy for vector database
- [ ] Set up monitoring/logging
- [ ] Test all features (chat, upload, etc.)

---

## Support

For issues or questions:
1. Check logs: `docker-compose logs -f`
2. Verify configuration in `.env`
3. Test health endpoint: `https://tharshan.lk/health`
4. Review this deployment guide

---

**Version**: 1.0.0  
**Last Updated**: 2026-05-16
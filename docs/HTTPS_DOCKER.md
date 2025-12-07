# HTTPS Setup for Docker

This guide explains how HTTPS/SSL is configured for the Docker deployment.

## Overview

The application uses **Nginx as a reverse proxy** with SSL/TLS certificates to provide HTTPS access. This setup:

- ✅ Provides HTTPS on port 443
- ✅ Redirects HTTP (port 80) to HTTPS
- ✅ Uses self-signed certificates (for development/testing)
- ✅ Supports WebSocket and SSE over HTTPS
- ✅ Includes security headers (HSTS, etc.)

## Architecture

```
Internet → Nginx (443/HTTPS) → FastAPI (8000/HTTP) → PostgreSQL
           ↓
        SSL/TLS
    (Self-signed cert)
```

## Files Created

1. **`ssl/server.crt`** - SSL certificate (self-signed)
2. **`ssl/server.key`** - SSL private key
3. **`nginx-docker.conf`** - Nginx configuration for Docker
4. **Updated `.env`** - SSL settings enabled
5. **Updated `docker-compose.yml`** - Nginx service added

## Access Points

After starting with `docker-compose up -d`:

- **HTTPS**: https://localhost
- **HTTP**: http://localhost (redirects to HTTPS)
- **API Docs**: https://localhost/docs
- **Health Check**: https://localhost/health

## Browser Security Warning

Since we're using **self-signed certificates**, browsers will show a security warning:

1. Click **"Advanced"** or **"Show Details"**
2. Click **"Proceed to localhost (unsafe)"** or **"Accept the Risk and Continue"**

This is normal for self-signed certificates. The connection is still encrypted and secure.

## Certificate Details

- **Type**: Self-signed (X.509)
- **Validity**: 365 days
- **Key Size**: 2048 bits RSA
- **Subject**: CN=localhost
- **Location**: `ssl/server.crt` and `ssl/server.key`

## For Production

To use **Let's Encrypt certificates** in production:

1. Replace self-signed certificates with Let's Encrypt certificates
2. Update `nginx-docker.conf` certificate paths
3. Ensure domain name is configured
4. Set up auto-renewal

See [docs/SSL_SETUP.md](./SSL_SETUP.md) for Let's Encrypt setup.

## Troubleshooting

### Certificate Not Found

```bash
# Regenerate certificates
docker run --rm -v "${PWD}/ssl:/certs" alpine/openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /certs/server.key -out /certs/server.crt -subj "/C=US/ST=State/L=City/O=BlogPlatform/CN=localhost"
```

### Nginx Won't Start

Check logs:
```bash
docker-compose logs nginx
```

Verify certificate files exist:
```bash
ls -la ssl/
```

### HTTPS Not Working

1. Check Nginx is running: `docker-compose ps`
2. Check port 443 is not blocked
3. Verify certificates: `docker-compose exec nginx ls -la /etc/nginx/ssl/`

### Mixed Content Warnings

If your frontend uses HTTP while API uses HTTPS, update CORS_ORIGINS in `.env` to include both HTTP and HTTPS origins.

## Configuration Files

### nginx-docker.conf

This file configures:
- HTTP to HTTPS redirect
- SSL/TLS settings
- Reverse proxy to FastAPI
- WebSocket support
- SSE support
- Security headers

### docker-compose.yml

The Nginx service:
- Listens on ports 80 and 443
- Mounts SSL certificates
- Mounts Nginx configuration
- Depends on API service

## Security Features Enabled

- ✅ HTTPS enforced (HTTP redirects to HTTPS)
- ✅ HSTS header (Strict-Transport-Security)
- ✅ Security headers (X-Frame-Options, CSP, etc.)
- ✅ TLS 1.2 and 1.3 only
- ✅ Strong cipher suites

## Testing HTTPS

```bash
# Test HTTPS endpoint
curl -k https://localhost/health

# Test HTTP redirect
curl -I http://localhost/health

# Test with certificate validation (will fail with self-signed)
curl https://localhost/health
```

The `-k` flag in curl ignores certificate validation (needed for self-signed certs).

## Summary

✅ **HTTPS is fully configured and ready to use!**

Just run `docker-compose up -d` and access https://localhost


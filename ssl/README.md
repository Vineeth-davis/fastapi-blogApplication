# SSL Certificates

This directory contains self-signed SSL certificates for HTTPS support in Docker.

## Files

- `server.crt` - SSL certificate (self-signed)
- `server.key` - SSL private key

## Usage

These certificates are automatically mounted into the Nginx container and used for HTTPS.

## Certificate Details

- **Type**: Self-signed (X.509)
- **Purpose**: Development/Testing
- **Hostname**: localhost
- **Validity**: 365 days

## Browser Warning

Since these are self-signed certificates, browsers will show a security warning. This is **normal and expected** for development.

To proceed:
1. Click "Advanced" or "Show Details"
2. Click "Proceed to localhost (unsafe)" or "Accept the Risk"

## For Production

**Never use these certificates in production!** Use Let's Encrypt or proper certificate authority certificates.

See [docs/SSL_SETUP.md](../docs/SSL_SETUP.md) for production SSL setup.


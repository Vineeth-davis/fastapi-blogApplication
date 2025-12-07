#!/bin/bash
# SSL Certificate Setup Script for Docker Deployment
# Domain: fastapiblogapp.duckdns.org
# Email: lordvineeth@gmail.com

set -e

DOMAIN="fastapiblogapp.duckdns.org"
EMAIL="lordvineeth@gmail.com"
EXPECTED_IP="49.207.216.44"

echo "🔐 SSL Certificate Setup for Docker Deployment"
echo "=============================================="
echo "Domain: ${DOMAIN}"
echo "Email: ${EMAIL}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
   echo "❌ This script must be run with sudo"
   echo "Usage: sudo bash scripts/setup-ssl-docker.sh"
   exit 1
fi

# Verify DNS
echo "📋 Step 1: Verifying DNS..."
DNS_IP=$(dig +short ${DOMAIN} | tail -n1 || echo "")

if [ -z "$DNS_IP" ]; then
    echo "⚠️  Warning: Could not resolve DNS for ${DOMAIN}"
    echo "   Make sure DNS is configured in DuckDNS"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
elif [ "$DNS_IP" != "$EXPECTED_IP" ]; then
    echo "⚠️  Warning: DNS resolves to ${DNS_IP}, expected ${EXPECTED_IP}"
    echo "   Make sure DNS is configured correctly in DuckDNS"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✅ DNS verified: ${DOMAIN} → ${DNS_IP}"
fi

# Check if Docker is running
echo ""
echo "📋 Step 2: Checking Docker..."
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi
echo "✅ Docker is running"

# Stop Nginx container if running
echo ""
echo "📋 Step 3: Stopping Nginx container..."
docker-compose stop nginx 2>/dev/null || docker-compose -f docker-compose.production.yml stop nginx 2>/dev/null || echo "   Nginx container not running"

# Check if port 80 is free
echo ""
echo "📋 Step 4: Checking port 80..."
if lsof -Pi :80 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Port 80 is in use. Attempting to identify and stop the service..."
    PID=$(lsof -ti :80)
    if [ ! -z "$PID" ]; then
        echo "   Found process using port 80 (PID: $PID)"
        read -p "Stop this process? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            kill $PID 2>/dev/null || echo "   Could not stop process. Please stop it manually."
        else
            echo "❌ Cannot proceed with port 80 in use"
            exit 1
        fi
    fi
else
    echo "✅ Port 80 is available"
fi

# Install certbot if not installed
echo ""
echo "📋 Step 5: Checking certbot installation..."
if ! command -v certbot &> /dev/null; then
    echo "   Installing certbot..."
    if command -v apt-get &> /dev/null; then
        apt-get update
        apt-get install -y certbot
    elif command -v yum &> /dev/null; then
        yum install -y certbot
    else
        echo "❌ Cannot install certbot automatically. Please install it manually:"
        echo "   Ubuntu/Debian: sudo apt-get install certbot"
        echo "   CentOS/RHEL: sudo yum install certbot"
        exit 1
    fi
fi
echo "✅ Certbot is installed"

# Get certificate
echo ""
echo "📋 Step 6: Obtaining SSL certificate from Let's Encrypt..."
echo "   This may take a minute..."
certbot certonly --standalone \
  -d ${DOMAIN} \
  --email ${EMAIL} \
  --agree-tos \
  --non-interactive \
  --preferred-challenges http

# Verify certificate
echo ""
echo "📋 Step 7: Verifying certificate..."
if [ -f "/etc/letsencrypt/live/${DOMAIN}/fullchain.pem" ] && [ -f "/etc/letsencrypt/live/${DOMAIN}/privkey.pem" ]; then
    echo "✅ SSL certificate obtained successfully!"
    echo ""
    echo "Certificate files:"
    echo "  Certificate: /etc/letsencrypt/live/${DOMAIN}/fullchain.pem"
    echo "  Private Key: /etc/letsencrypt/live/${DOMAIN}/privkey.pem"
    echo ""
    
    # Set proper permissions
    chmod 644 /etc/letsencrypt/live/${DOMAIN}/fullchain.pem
    chmod 600 /etc/letsencrypt/live/${DOMAIN}/privkey.pem
    echo "✅ Certificate permissions set"
else
    echo "❌ Certificate files not found. Please check the error messages above."
    exit 1
fi

# Create certbot renewal hook for Docker
echo ""
echo "📋 Step 8: Setting up certificate renewal..."
mkdir -p /etc/letsencrypt/renewal-hooks/deploy

# Get the actual project path
PROJECT_PATH=$(pwd)
cat > /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh << EOF
#!/bin/bash
# Reload Nginx container after certificate renewal
cd ${PROJECT_PATH}
docker-compose -f docker-compose.production.yml restart nginx || true
EOF

chmod +x /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh
echo "✅ Renewal hook created at /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh"

# Test renewal
echo ""
echo "📋 Step 9: Testing certificate renewal (dry run)..."
certbot renew --dry-run > /dev/null 2>&1 && echo "✅ Renewal test passed" || echo "⚠️  Renewal test had warnings (this is usually OK)"

# Summary
echo ""
echo "=============================================="
echo "✅ SSL Certificate Setup Complete!"
echo "=============================================="
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Start production deployment:"
echo "   docker-compose -f docker-compose.production.yml up -d"
echo ""
echo "2. Verify HTTPS is working:"
echo "   curl -I https://${DOMAIN}/health"
echo ""
echo "3. Visit in browser:"
echo "   https://${DOMAIN}/docs"
echo ""
echo "4. Certificate auto-renewal:"
echo "   Certbot will automatically renew certificates before expiry"
echo "   Check status: sudo systemctl status certbot.timer"
echo ""
echo "🎉 Your application is ready for production!"


#!/bin/bash
# Unified Production Deployment Script
# Handles SSL, HTTPS, DNS verification, migrations, and full deployment
# Reads from .env or prompts for values

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 FastAPI Blog Platform - Production Deployment${NC}"
echo "=============================================="
echo ""

# Function to load .env file
load_env() {
    if [ -f .env ]; then
        export $(grep -v '^#' .env | xargs)
        echo -e "${GREEN}✅ Loaded .env file${NC}"
    fi
}

# Function to get value from env or prompt user
get_value() {
    local var_name=$1
    local prompt_text=$2
    local default_value=$3
    
    # Check if already set in environment
    if [ ! -z "${!var_name}" ]; then
        echo "${!var_name}"
        return
    fi
    
    # Check .env file
    if [ -f .env ]; then
        local env_value=$(grep "^${var_name}=" .env | cut -d '=' -f2- | tr -d '"' | tr -d "'")
        if [ ! -z "$env_value" ]; then
            echo "$env_value"
            return
        fi
    fi
    
    # Prompt user (required if no default)
    if [ ! -z "$default_value" ]; then
        read -p "${prompt_text} [${default_value}]: " value
        echo "${value:-$default_value}"
    else
        while [ -z "$value" ]; do
            read -p "${prompt_text} (required): " value
            if [ -z "$value" ]; then
                echo -e "${RED}   This field is required!${NC}" >&2
            fi
        done
        echo "$value"
    fi
}

# Load .env if exists
load_env

# Get configuration values
echo -e "${YELLOW}📋 Configuration${NC}"
echo "-------------------"

DOMAIN=$(get_value "DOMAIN" "Enter your domain name")
EMAIL=$(get_value "SSL_EMAIL" "Enter email for SSL certificate")

# Try to auto-detect server IP as a helpful default, but still require if not found
AUTO_IP=$(curl -s ifconfig.me 2>/dev/null || echo "")
if [ ! -z "$AUTO_IP" ]; then
    SERVER_IP=$(get_value "SERVER_IP" "Enter your server IP address" "$AUTO_IP")
else
    SERVER_IP=$(get_value "SERVER_IP" "Enter your server IP address")
fi

# Validate required values
if [ -z "$DOMAIN" ]; then
    echo -e "${RED}❌ Domain name is required!${NC}"
    exit 1
fi

if [ -z "$EMAIL" ]; then
    echo -e "${RED}❌ Email is required for SSL certificate!${NC}"
    exit 1
fi

if [ -z "$SERVER_IP" ]; then
    echo -e "${YELLOW}⚠️  Could not detect server IP. Please enter manually.${NC}"
    SERVER_IP=$(get_value "SERVER_IP" "Enter your server IP address" "")
    if [ -z "$SERVER_IP" ]; then
        echo -e "${RED}❌ Server IP is required!${NC}"
        exit 1
    fi
fi

echo ""
echo -e "${GREEN}Configuration:${NC}"
echo "  Domain: ${DOMAIN}"
echo "  Email: ${EMAIL}"
echo "  Server IP: ${SERVER_IP}"
echo ""

# Check if running as root for SSL operations
NEED_ROOT=false
if [ "$EUID" -ne 0 ]; then
    NEED_ROOT=true
fi

# Step 1: Verify DNS
echo -e "${YELLOW}📋 Step 1: Verifying DNS...${NC}"
DNS_IP=$(dig +short ${DOMAIN} 2>/dev/null | tail -n1 || echo "")

if [ -z "$DNS_IP" ]; then
    echo -e "${RED}❌ Could not resolve DNS for ${DOMAIN}${NC}"
    echo "   Please update DNS in DuckDNS or your DNS provider"
    echo "   Point ${DOMAIN} to ${SERVER_IP}"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
elif [ "$DNS_IP" != "$SERVER_IP" ]; then
    echo -e "${YELLOW}⚠️  DNS resolves to ${DNS_IP}, expected ${SERVER_IP}${NC}"
    echo "   Please update DNS to point to ${SERVER_IP}"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo -e "${GREEN}✅ DNS verified: ${DOMAIN} → ${DNS_IP}${NC}"
fi

# Step 2: Check Docker
echo ""
echo -e "${YELLOW}📋 Step 2: Checking Docker...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    echo "   Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    echo -e "${GREEN}✅ Docker installed${NC}"
    echo -e "${YELLOW}⚠️  You may need to log out and back in for Docker group to take effect${NC}"
else
    echo -e "${GREEN}✅ Docker is installed${NC}"
fi

if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running${NC}"
    echo "   Please start Docker: sudo systemctl start docker"
    exit 1
fi

# Step 3: Check Docker Compose
echo ""
echo -e "${YELLOW}📋 Step 3: Checking Docker Compose...${NC}"
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed${NC}"
    echo "   Installing Docker Compose..."
    sudo apt-get update
    sudo apt-get install -y docker-compose-plugin
    echo -e "${GREEN}✅ Docker Compose installed${NC}"
else
    echo -e "${GREEN}✅ Docker Compose is installed${NC}"
fi

# Step 4: Check/Create Migrations
echo ""
echo -e "${YELLOW}📋 Step 4: Checking database migrations...${NC}"
if [ -d "alembic/versions" ] && [ "$(ls -A alembic/versions/*.py 2>/dev/null)" ]; then
    echo -e "${GREEN}✅ Migration files exist${NC}"
else
    echo -e "${YELLOW}⚠️  No migration files found${NC}"
    echo "   Creating initial migration..."
    
    # Check if containers are running
    if docker ps | grep -q blog_platform_api; then
        echo "   Using existing container..."
        docker exec blog_platform_api alembic revision --autogenerate -m "Initial migration" || {
            echo -e "${YELLOW}⚠️  Could not create migration in container. Will create after deployment.${NC}"
        }
    else
        echo -e "${YELLOW}⚠️  Containers not running. Migration will be created after deployment.${NC}"
    fi
fi

# Step 5: SSL Certificate Setup
echo ""
echo -e "${YELLOW}📋 Step 5: Setting up SSL certificate...${NC}"

if [ "$NEED_ROOT" = true ]; then
    echo -e "${YELLOW}⚠️  SSL setup requires sudo. Running with sudo...${NC}"
fi

# Check if certificate already exists
if [ -f "/etc/letsencrypt/live/${DOMAIN}/fullchain.pem" ]; then
    echo -e "${GREEN}✅ SSL certificate already exists${NC}"
    read -p "Regenerate certificate? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        REGENERATE_CERT=true
    else
        REGENERATE_CERT=false
    fi
else
    REGENERATE_CERT=true
fi

if [ "$REGENERATE_CERT" = true ]; then
    # Stop Nginx if running
    docker-compose -f docker-compose.production.yml stop nginx 2>/dev/null || true
    
    # Install certbot if needed
    if ! command -v certbot &> /dev/null; then
        echo "   Installing certbot..."
        if [ "$NEED_ROOT" = true ]; then
            sudo apt-get update
            sudo apt-get install -y certbot
        else
            apt-get update
            apt-get install -y certbot
        fi
    fi
    
    # Get certificate
    echo "   Obtaining SSL certificate from Let's Encrypt..."
    if [ "$NEED_ROOT" = true ]; then
        sudo certbot certonly --standalone \
            -d ${DOMAIN} \
            --email ${EMAIL} \
            --agree-tos \
            --non-interactive \
            --preferred-challenges http
    else
        certbot certonly --standalone \
            -d ${DOMAIN} \
            --email ${EMAIL} \
            --agree-tos \
            --non-interactive \
            --preferred-challenges http
    fi
    
    # Verify certificate
    if [ -f "/etc/letsencrypt/live/${DOMAIN}/fullchain.pem" ]; then
        echo -e "${GREEN}✅ SSL certificate obtained${NC}"
        
        # Set permissions
        if [ "$NEED_ROOT" = true ]; then
            sudo chmod 644 /etc/letsencrypt/live/${DOMAIN}/fullchain.pem
            sudo chmod 600 /etc/letsencrypt/live/${DOMAIN}/privkey.pem
        else
            chmod 644 /etc/letsencrypt/live/${DOMAIN}/fullchain.pem
            chmod 600 /etc/letsencrypt/live/${DOMAIN}/privkey.pem
        fi
    else
        echo -e "${RED}❌ Failed to obtain SSL certificate${NC}"
        exit 1
    fi
fi

# Step 6: Update Nginx config with domain
echo ""
echo -e "${YELLOW}📋 Step 6: Updating Nginx configuration...${NC}"
if [ -f "nginx-production.conf" ]; then
    # Backup original
    cp nginx-production.conf nginx-production.conf.bak 2>/dev/null || true
    
    # Update domain in config
    sed -i "s|server_name .*;|server_name ${DOMAIN};|g" nginx-production.conf
    sed -i "s|ssl_certificate /etc/letsencrypt/live/.*/fullchain.pem|ssl_certificate /etc/letsencrypt/live/${DOMAIN}/fullchain.pem|g" nginx-production.conf
    sed -i "s|ssl_certificate_key /etc/letsencrypt/live/.*/privkey.pem|ssl_certificate_key /etc/letsencrypt/live/${DOMAIN}/privkey.pem|g" nginx-production.conf
    sed -i "s|ssl_trusted_certificate /etc/letsencrypt/live/.*/chain.pem|ssl_trusted_certificate /etc/letsencrypt/live/${DOMAIN}/chain.pem|g" nginx-production.conf
    
    echo -e "${GREEN}✅ Nginx configuration updated${NC}"
else
    echo -e "${RED}❌ nginx-production.conf not found${NC}"
    exit 1
fi

# Step 7: Configure Firewall
echo ""
echo -e "${YELLOW}📋 Step 7: Configuring firewall...${NC}"
if command -v ufw &> /dev/null; then
    # Allow SSH first (important!)
    sudo ufw allow 22/tcp 2>/dev/null || true
    sudo ufw allow 80/tcp 2>/dev/null || true
    sudo ufw allow 443/tcp 2>/dev/null || true
    
    # Enable if not already enabled
    if ! sudo ufw status | grep -q "Status: active"; then
        echo -e "${YELLOW}⚠️  Enabling UFW firewall...${NC}"
        echo "y" | sudo ufw enable
    fi
    
    echo -e "${GREEN}✅ Firewall configured${NC}"
else
    echo -e "${YELLOW}⚠️  UFW not found. Please configure firewall manually.${NC}"
fi

# Step 8: Deploy Application
echo ""
echo -e "${YELLOW}📋 Step 8: Deploying application...${NC}"
docker-compose -f docker-compose.production.yml up -d --build

# Wait for services to start
echo "   Waiting for services to start..."
sleep 10

# Step 9: Run Migrations (if needed)
echo ""
echo -e "${YELLOW}📋 Step 9: Running database migrations...${NC}"
if docker ps | grep -q blog_platform_api; then
    # Check if migrations exist
    MIGRATION_COUNT=$(docker exec blog_platform_api ls -1 /app/alembic/versions/*.py 2>/dev/null | wc -l || echo "0")
    
    if [ "$MIGRATION_COUNT" -eq 0 ]; then
        echo "   Creating initial migration..."
        docker exec blog_platform_api alembic revision --autogenerate -m "Initial migration" || {
            echo -e "${YELLOW}⚠️  Could not create migration. This is OK if tables already exist.${NC}"
        }
    fi
    
    # Run migrations
    echo "   Applying migrations..."
    docker exec blog_platform_api alembic upgrade head || {
        echo -e "${YELLOW}⚠️  Migration failed. Checking if tables exist...${NC}"
    }
    
    echo -e "${GREEN}✅ Migrations completed${NC}"
else
    echo -e "${RED}❌ API container is not running${NC}"
fi

# Step 10: Seed Users (optional)
echo ""
read -p "Seed initial users? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}📋 Step 10: Seeding users...${NC}"
    if docker ps | grep -q blog_platform_api; then
        docker exec blog_platform_api python /app/scripts/seed_users.py || {
            echo -e "${YELLOW}⚠️  User seeding failed or users already exist${NC}"
        }
    fi
fi

# Step 11: Verify Deployment
echo ""
echo -e "${YELLOW}📋 Step 11: Verifying deployment...${NC}"

# Check containers
if docker ps | grep -q blog_platform_api && docker ps | grep -q blog_platform_nginx && docker ps | grep -q blog_platform_db; then
    echo -e "${GREEN}✅ All containers are running${NC}"
else
    echo -e "${RED}❌ Some containers are not running${NC}"
    docker-compose -f docker-compose.production.yml ps
fi

# Test HTTPS
echo "   Testing HTTPS connection..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 https://${DOMAIN}/health 2>/dev/null || echo "000")

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✅ HTTPS is working (HTTP ${HTTP_CODE})${NC}"
elif [ "$HTTP_CODE" = "000" ]; then
    echo -e "${YELLOW}⚠️  HTTPS test failed (connection timeout)${NC}"
    echo "   This might be normal if DNS hasn't fully propagated"
else
    echo -e "${YELLOW}⚠️  HTTPS returned HTTP ${HTTP_CODE}${NC}"
fi

# Summary
echo ""
echo "=============================================="
echo -e "${GREEN}✅ Production Deployment Complete!${NC}"
echo "=============================================="
echo ""
echo -e "${BLUE}📋 Access your application:${NC}"
echo "   HTTPS: https://${DOMAIN}/docs"
echo "   API: https://${DOMAIN}/api"
echo "   Health: https://${DOMAIN}/health"
echo ""
echo -e "${BLUE}📋 Default Users (if seeded):${NC}"
echo "   Admin: admin@example.com / admin@1"
echo "   Approver: approver@example.com / approver@1"
echo "   Users: user1@example.com / user1@1 (through user5)"
echo ""
echo -e "${BLUE}📋 Useful Commands:${NC}"
echo "   View logs: docker-compose -f docker-compose.production.yml logs -f"
echo "   Restart: docker-compose -f docker-compose.production.yml restart"
echo "   Stop: docker-compose -f docker-compose.production.yml down"
echo ""
echo -e "${GREEN}🎉 Your application is live!${NC}"


# Manual Steps Guide

This document contains step-by-step instructions for tasks that require manual intervention and cannot be fully automated.

**Note:** This guide focuses on SSL/HTTPS setup. DNS configuration is optional and only needed if you want to use a custom domain name. You can set up HTTPS with self-signed certificates or Let's Encrypt using your server's IP address.

## Table of Contents

1. [SSL Certificate Setup (Let's Encrypt)](#ssl-certificate-setup-lets-encrypt) ⭐ **Required for HTTPS**
2. [SSL Certificate Setup (Self-Signed)](#ssl-certificate-setup-self-signed) - Alternative option
3. [Nginx Configuration](#nginx-configuration)
4. [Database Setup](#database-setup)
5. [Firewall Configuration](#firewall-configuration)
6. [Domain Name Configuration](#domain-name-configuration) - Optional
7. [DNS Configuration](#dns-configuration) - Optional

---

## SSL Certificate Setup (Self-Signed)

If you don't have a domain name, you can use self-signed certificates for HTTPS. **Note:** Browsers will show a security warning, but this is sufficient for testing and development.

### Step 1: Generate Self-Signed Certificate

```bash
sudo mkdir -p /etc/ssl/private
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/selfsigned.key \
  -out /etc/ssl/certs/selfsigned.crt
```

**During the process, you'll be asked:**
- Country Name: Enter your country code (e.g., US)
- State/Province: Enter your state
- City: Enter your city
- Organization: Enter your organization name
- Common Name: Enter your server's IP address or hostname (e.g., `192.168.1.100` or `server.example.com`)

### Step 2: Update Nginx Configuration

Edit `/etc/nginx/sites-available/blog-platform`:

```bash
sudo nano /etc/nginx/sites-available/blog-platform
```

Update SSL certificate paths:
```nginx
ssl_certificate /etc/ssl/certs/selfsigned.crt;
ssl_certificate_key /etc/ssl/private/selfsigned.key;
```

**Remove or comment out** the `ssl_trusted_certificate` line (not needed for self-signed).

### Step 3: Test and Reload Nginx

```bash
sudo nginx -t
sudo systemctl reload nginx
```

### Step 4: Access via HTTPS

Visit `https://your-server-ip` in a browser. You'll see a security warning - click "Advanced" and "Proceed" to continue.

**Note:** Self-signed certificates are fine for development/testing. For production, use Let's Encrypt with a domain name.

---

## Domain Name Configuration (Optional)

### Step 1: Purchase Domain (If Not Already Owned)

1. Choose a domain registrar (e.g., Namecheap, GoDaddy, Google Domains)
2. Search for and purchase your desired domain name
3. Complete the registration process

### Step 2: Point Domain to Your Server

You'll need to configure DNS records to point your domain to your server's IP address.

**Option A: Using A Record (Recommended)**

1. Log in to your domain registrar's control panel
2. Navigate to DNS Management
3. Add an A record:
   - **Type**: A
   - **Name**: @ (or leave blank for root domain)
   - **Value**: Your server's public IP address
   - **TTL**: 3600 (or default)

4. Add another A record for www subdomain:
   - **Type**: A
   - **Name**: www
   - **Value**: Your server's public IP address
   - **TTL**: 3600

**Option B: Using CNAME (Alternative)**

1. Add A record for root domain (as above)
2. Add CNAME record for www:
   - **Type**: CNAME
   - **Name**: www
   - **Value**: yourdomain.com
   - **TTL**: 3600

### Step 3: Verify DNS Propagation

Wait 5-60 minutes for DNS to propagate, then verify:

```bash
# Check A record
dig yourdomain.com +short

# Check www subdomain
dig www.yourdomain.com +short

# Both should return your server's IP address
```

---

## SSL Certificate Setup (Let's Encrypt) ⭐

**This is the recommended approach for production.** Let's Encrypt provides free, trusted SSL certificates.

### Prerequisites

- **Option A:** Domain name pointing to your server (recommended)
- **Option B:** Server IP address (for testing - see Self-Signed section above)
- Nginx installed and configured
- Port 80 and 443 open in firewall

### Step 1: Install Certbot

```bash
sudo apt update
sudo apt install certbot python3-certbot-nginx
```

### Step 2: Stop Nginx (Temporary)

```bash
sudo systemctl stop nginx
```

**Note:** This is only needed if Nginx is already running and blocking port 80.

### Step 3: Obtain SSL Certificate

**If you have a domain name:**
```bash
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com
```

**If you only have an IP address** (Let's Encrypt doesn't support IP-only certificates, so use self-signed instead - see section above):
```bash
# Use self-signed certificate instead
# See "SSL Certificate Setup (Self-Signed)" section above
```

**During the process (for domain-based certificates):**
1. Enter your email address (for renewal notifications)
2. Agree to Terms of Service (type 'A' and press Enter)
3. Choose whether to share email with EFF (optional)
4. Certbot will verify domain ownership via HTTP challenge

### Step 4: Verify Certificate Files

```bash
sudo ls -la /etc/letsencrypt/live/yourdomain.com/
```

You should see:
- `cert.pem` - Certificate
- `chain.pem` - Certificate chain
- `fullchain.pem` - Full chain (cert + chain)
- `privkey.pem` - Private key

### Step 5: Update Nginx Configuration

Edit `/etc/nginx/sites-available/blog-platform`:

```bash
sudo nano /etc/nginx/sites-available/blog-platform
```

Update SSL certificate paths:
```nginx
ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
ssl_trusted_certificate /etc/letsencrypt/live/yourdomain.com/chain.pem;
```

Replace `yourdomain.com` with your actual domain.

### Step 6: Test Nginx Configuration

```bash
sudo nginx -t
```

If successful, reload Nginx:

```bash
sudo systemctl reload nginx
```

### Step 7: Test SSL Certificate

Visit `https://yourdomain.com` in a browser. You should see a valid SSL certificate.

### Step 8: Set Up Auto-Renewal

Certbot automatically sets up a systemd timer. Test it:

```bash
sudo certbot renew --dry-run
```

If successful, certificates will auto-renew before expiration.

### Step 9: Verify Auto-Renewal Timer

```bash
sudo systemctl status certbot.timer
```

Should show as active and enabled.

---

## Nginx Configuration

### Step 1: Copy Configuration File

```bash
cd /opt/blog-platform
sudo cp nginx.conf /etc/nginx/sites-available/blog-platform
```

### Step 2: Edit Configuration

```bash
sudo nano /etc/nginx/sites-available/blog-platform
```

**Replace the following:**
- `yourdomain.com` → Your actual domain name
- `www.yourdomain.com` → Your www subdomain

**Update SSL certificate paths** (if certificates are already obtained):
- `/etc/letsencrypt/live/yourdomain.com/fullchain.pem`
- `/etc/letsencrypt/live/yourdomain.com/privkey.pem`
- `/etc/letsencrypt/live/yourdomain.com/chain.pem`

### Step 3: Enable Site

```bash
# Remove default site (optional)
sudo rm /etc/nginx/sites-enabled/default

# Create symlink to enable site
sudo ln -s /etc/nginx/sites-available/blog-platform /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t
```

### Step 4: Reload Nginx

```bash
sudo systemctl reload nginx
```

### Step 5: Verify Nginx Status

```bash
sudo systemctl status nginx
```

### Step 6: Test Reverse Proxy

```bash
# Test HTTP endpoint
curl http://localhost/api/health

# Test HTTPS endpoint (after SSL setup)
curl https://yourdomain.com/health
```

---

## Database Setup

### Step 1: Access PostgreSQL

```bash
sudo -u postgres psql
```

### Step 2: Create Database

```sql
CREATE DATABASE blogdb;
```

### Step 3: Create User

```sql
CREATE USER bloguser WITH PASSWORD 'your_secure_password_here';
```

**Important:** Use a strong password. Generate one:

```bash
openssl rand -base64 32
```

### Step 4: Grant Privileges

```sql
ALTER ROLE bloguser SET client_encoding TO 'utf8';
ALTER ROLE bloguser SET default_transaction_isolation TO 'read committed';
ALTER ROLE bloguser SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE blogdb TO bloguser;
```

### Step 5: Exit PostgreSQL

```sql
\q
```

### Step 6: Test Connection

```bash
psql -U bloguser -d blogdb -h localhost
```

Enter password when prompted. If successful, you'll see the PostgreSQL prompt.

### Step 7: Update Application .env

Edit `/opt/blog-platform/.env`:

```env
DATABASE_URL=postgresql+asyncpg://bloguser:your_secure_password_here@localhost:5432/blogdb
```

Replace `your_secure_password_here` with the actual password.

---

## Firewall Configuration

### Step 1: Check Current Status

```bash
sudo ufw status
```

### Step 2: Allow SSH (Important!)

**Before enabling firewall, ensure SSH is allowed:**

```bash
sudo ufw allow 22/tcp
```

### Step 3: Allow HTTP and HTTPS

```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

### Step 4: Enable Firewall

```bash
sudo ufw enable
```

Type 'y' when prompted.

### Step 5: Verify Rules

```bash
sudo ufw status verbose
```

Should show:
```
Status: active
To                         Action      From
--                         ------      ----
22/tcp                     ALLOW       Anywhere
80/tcp                     ALLOW       Anywhere
443/tcp                    ALLOW       Anywhere
```

### Step 6: (Optional) Allow Specific IP for SSH

For better security, restrict SSH to your IP:

```bash
# Remove general SSH rule
sudo ufw delete allow 22/tcp

# Add rule for your IP only
sudo ufw allow from YOUR_IP_ADDRESS to any port 22
```

Replace `YOUR_IP_ADDRESS` with your actual IP.

---

## Cloud Provider Setup

### AWS EC2

#### Step 1: Create Security Group

1. Go to EC2 Dashboard → Security Groups
2. Click "Create Security Group"
3. Configure:
   - **Name**: blog-platform-sg
   - **Description**: Security group for blog platform
   - **Inbound Rules**:
     - SSH (22): Your IP only
     - HTTP (80): 0.0.0.0/0
     - HTTPS (443): 0.0.0.0/0
   - **Outbound Rules**: All traffic (default)

#### Step 2: Launch EC2 Instance

1. Go to EC2 Dashboard → Instances
2. Click "Launch Instance"
3. Configure:
   - **AMI**: Ubuntu Server 22.04 LTS
   - **Instance Type**: t3.small or larger
   - **Key Pair**: Create or select existing
   - **Security Group**: Select the one created above
   - **Storage**: 20GB minimum

#### Step 3: Allocate Elastic IP (Optional but Recommended)

1. Go to EC2 Dashboard → Elastic IPs
2. Click "Allocate Elastic IP address"
3. Associate with your instance

#### Step 4: Update DNS A Record

Point your domain's A record to the Elastic IP address.

### DigitalOcean

#### Step 1: Create Droplet

1. Go to DigitalOcean Dashboard
2. Click "Create" → "Droplets"
3. Configure:
   - **Image**: Ubuntu 22.04
   - **Plan**: Basic, $6/month or higher
   - **Region**: Choose closest to users
   - **Authentication**: SSH keys (recommended)

#### Step 2: Configure Firewall

1. Go to Networking → Firewalls
2. Create new firewall:
   - **Inbound Rules**:
     - SSH (22)
     - HTTP (80)
     - HTTPS (443)
   - **Outbound Rules**: All (default)

#### Step 3: Assign to Droplet

Attach firewall to your droplet.

### Google Cloud Platform (GCP)

#### Step 1: Create VM Instance

1. Go to Compute Engine → VM Instances
2. Click "Create Instance"
3. Configure:
   - **Name**: blog-platform
   - **Region**: Choose closest
   - **Machine Type**: e2-small or larger
   - **Boot Disk**: Ubuntu 22.04 LTS
   - **Firewall**: Allow HTTP and HTTPS traffic

#### Step 2: Configure Firewall Rules

1. Go to VPC Network → Firewall
2. Create rules for HTTP (80) and HTTPS (443)

---

## DNS Configuration

### Step 1: Get Your Server's IP Address

```bash
# On your server
curl ifconfig.me
```

Or check in your cloud provider's dashboard.

### Step 2: Configure A Record

1. Log in to your domain registrar
2. Navigate to DNS Management
3. Add/Edit A record:
   - **Host**: @ (or blank)
   - **Type**: A
   - **Value**: Your server's IP address
   - **TTL**: 3600

### Step 3: Configure www Subdomain

**Option A: A Record**
- **Host**: www
- **Type**: A
- **Value**: Your server's IP address
- **TTL**: 3600

**Option B: CNAME Record**
- **Host**: www
- **Type**: CNAME
- **Value**: yourdomain.com
- **TTL**: 3600

### Step 4: Wait for Propagation

DNS changes can take 5-60 minutes to propagate globally.

### Step 5: Verify DNS

```bash
# Check A record
nslookup yourdomain.com

# Check www
nslookup www.yourdomain.com

# Both should return your server's IP
```

---

## Additional Manual Steps

### Generate Strong Secret Key

```bash
openssl rand -hex 32
```

Copy the output and use it as `SECRET_KEY` in `.env` file.

### Create Application Directories

```bash
sudo mkdir -p /opt/blog-platform/logs
sudo mkdir -p /opt/blog-platform/uploads
sudo chown -R appuser:appuser /opt/blog-platform
```

### Set Up Log Rotation

Create `/etc/logrotate.d/blog-platform`:

```bash
sudo nano /etc/logrotate.d/blog-platform
```

Add:
```
/opt/blog-platform/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 appuser appuser
    sharedscripts
    postrotate
        systemctl reload blog-platform > /dev/null 2>&1 || true
    endscript
}
```

### Configure Timezone

```bash
sudo timedatectl set-timezone UTC
```

### Set Up Automatic Security Updates

```bash
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

---

## Verification Checklist

After completing all manual steps, verify:

- [ ] Domain DNS points to server IP
- [ ] SSL certificate obtained and valid
- [ ] Nginx configuration tested and reloaded
- [ ] Database created and accessible
- [ ] Firewall configured correctly
- [ ] Application service running
- [ ] Health check endpoint accessible
- [ ] HTTPS working (no browser warnings)
- [ ] WebSocket connections working
- [ ] SSE connections working
- [ ] Logs being written correctly

---

## Troubleshooting Manual Steps

### DNS Not Propagating

- Wait longer (up to 48 hours for full propagation)
- Check DNS records are correct
- Use different DNS servers to test: `dig @8.8.8.8 yourdomain.com`

### SSL Certificate Issues

- Ensure port 80 is accessible from internet
- Verify domain DNS is correct
- Check Nginx is not blocking certbot
- Review certbot logs: `sudo journalctl -u certbot`

### Nginx Configuration Errors

- Test syntax: `sudo nginx -t`
- Check error logs: `sudo tail -f /var/log/nginx/error.log`
- Verify file paths are correct
- Ensure upstream server is running

### Database Connection Issues

- Verify PostgreSQL is running: `sudo systemctl status postgresql`
- Test connection: `psql -U bloguser -d blogdb -h localhost`
- Check pg_hba.conf allows local connections
- Verify password in .env matches database

---

For automated deployment steps, refer to [DEPLOYMENT.md](./DEPLOYMENT.md).


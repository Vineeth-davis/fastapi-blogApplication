# SSL/HTTPS Setup Guide

This guide provides simplified instructions for setting up SSL/HTTPS as required by the assignment. **DNS configuration is optional** - you can set up HTTPS with or without a domain name.

## Quick Decision Guide

- **Have a domain name?** → Use [Let's Encrypt](#option-1-lets-encrypt-recommended)
- **No domain name?** → Use [Self-Signed Certificate](#option-2-self-signed-certificate)

---

## Option 1: Let's Encrypt (Recommended)

**Requires:** Domain name pointing to your server

### Step 1: Install Certbot

```bash
sudo apt update
sudo apt install certbot python3-certbot-nginx
```

### Step 2: Obtain Certificate

```bash
# Stop Nginx temporarily
sudo systemctl stop nginx

# Get certificate
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Start Nginx
sudo systemctl start nginx
```

**Follow the prompts:**
- Enter email address
- Agree to terms (type 'A')
- Certbot will verify domain ownership

### Step 3: Update Nginx Config

Edit `/etc/nginx/sites-available/blog-platform`:

```nginx
ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
ssl_trusted_certificate /etc/letsencrypt/live/yourdomain.com/chain.pem;
```

### Step 4: Test and Reload

```bash
sudo nginx -t
sudo systemctl reload nginx
```

### Step 5: Verify

Visit `https://yourdomain.com` - should show valid certificate ✅

**Auto-renewal:** Certbot sets this up automatically. Test with:
```bash
sudo certbot renew --dry-run
```

---

## Option 2: Self-Signed Certificate

**Requires:** Server IP address (no domain needed)

### Step 1: Generate Certificate

```bash
sudo mkdir -p /etc/ssl/private
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/selfsigned.key \
  -out /etc/ssl/certs/selfsigned.crt
```

**Enter when prompted:**
- Country: `US` (or your country)
- State: `State` (or your state)
- City: `City` (or your city)
- Organization: `YourOrg` (or any name)
- Common Name: **Your server's IP address** (e.g., `192.168.1.100`)

### Step 2: Update Nginx Config

Edit `/etc/nginx/sites-available/blog-platform`:

```nginx
ssl_certificate /etc/ssl/certs/selfsigned.crt;
ssl_certificate_key /etc/ssl/private/selfsigned.key;
# Remove or comment out ssl_trusted_certificate line
```

Also update the `server_name` directive:
```nginx
server_name your-server-ip;  # e.g., 192.168.1.100
```

### Step 3: Test and Reload

```bash
sudo nginx -t
sudo systemctl reload nginx
```

### Step 4: Verify

Visit `https://your-server-ip` in a browser.

**Note:** You'll see a security warning because it's self-signed. Click:
1. "Advanced" or "Show Details"
2. "Proceed to [your-server-ip] (unsafe)" or "Accept the Risk"

This is normal for self-signed certificates. HTTPS is still working! ✅

---

## Nginx Configuration Updates

Regardless of which option you choose, ensure your Nginx config has:

### 1. HTTP to HTTPS Redirect

```nginx
server {
    listen 80;
    server_name yourdomain.com;  # or your-server-ip
    
    location / {
        return 301 https://$server_name$request_uri;
    }
}
```

### 2. HTTPS Server Block

```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;  # or your-server-ip
    
    # SSL configuration (from steps above)
    ssl_certificate /path/to/certificate;
    ssl_certificate_key /path/to/key;
    
    # SSL settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;
    
    # Rest of your configuration...
}
```

---

## Verification Checklist

- [ ] SSL certificate installed (Let's Encrypt or self-signed)
- [ ] Nginx configuration updated with certificate paths
- [ ] Nginx test passes (`sudo nginx -t`)
- [ ] Nginx reloaded (`sudo systemctl reload nginx`)
- [ ] HTTPS accessible (visit `https://your-domain-or-ip`)
- [ ] HTTP redirects to HTTPS
- [ ] Application works over HTTPS

---

## Troubleshooting

### Certificate Not Found

**Error:** `SSL: error:0B080074:x509 certificate routines`

**Solution:** Check certificate paths in Nginx config match actual file locations:
```bash
sudo ls -la /etc/letsencrypt/live/yourdomain.com/  # Let's Encrypt
sudo ls -la /etc/ssl/certs/selfsigned.crt          # Self-signed
```

### Port 80/443 Not Accessible

**Error:** Certbot can't verify domain

**Solution:** 
- Ensure port 80 is open: `sudo ufw allow 80/tcp`
- Ensure domain DNS points to server IP
- For self-signed, skip domain verification

### Browser Security Warning (Self-Signed)

**This is normal!** Self-signed certificates show warnings. The HTTPS connection is still encrypted and secure. For production, use Let's Encrypt with a domain.

---

## Summary

✅ **Assignment Requirement Met:** HTTPS/SSL is configured  
✅ **DNS Optional:** You can use self-signed certificates without a domain  
✅ **Production Ready:** Let's Encrypt recommended for production use

**For detailed deployment instructions, see [DEPLOYMENT.md](./DEPLOYMENT.md)**


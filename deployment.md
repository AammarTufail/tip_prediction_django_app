# Django ML Model Deployment Guide - Hostinger KVM VPS

## Prerequisites
- Hostinger KVM VPS account
  - Use this link to purchase and get a discount: [Hostinger KVM VPS Discounted Link](https://hostinger.com?REFERRALCODE=1MUHAMMAD0984)
- Domain name (optional but recommended)
  - Buy a domain from [Namecheap](https://www.namecheap.com) or [GoDaddy](https://www.godaddy.com) or [Hostinger](https://www.hostinger.com)
- Local Django project ready for deployment

## Step 1: Server Setup and Initial Configuration

### 1.1 Connect to Your VPS using SSH
```bash
ssh root@your_server_ip
```

You can see the following guide to use ssh via hostinger: [Hostinger SSH Guide](https://www.hostinger.com/support/5723772-how-to-connect-to-your-vps-via-ssh-at-hostinger/)

### 1.2 Update System Packages and Install Dependencies
```bash
# Update package lists
sudo apt update && sudo apt upgrade -y

# Install essential packages including uWSGI dependencies
sudo apt install -y gcc python3-dev python3.12-venv nginx postgresql libpq-dev
```

## Step 2: Create Application User

### 2.1 Create Dedicated Django User
```bash
# Create user with proper groups and shell
sudo useradd -m -s /bin/bash -G www-data django_user
# Set password for the user
sudo passwd django_user
#save the password

# give sudo permission to django_user
sudo usermod -aG sudo django_user


# Switch to django user
sudo su - django_user
```

### 2.2 Set Directory Permissions
```bash
# Set proper permissions for home directory (important for Nginx access)
chmod 711 /home/django_user
cd /home/django_user
```

## Step 3: Setup PostgreSQL Database

### 3.1 Configure PostgreSQL
```bash
# Switch to postgres user and access PostgreSQL
sudo -u postgres psql
```

```sql
CREATE DATABASE ml_model_db;
CREATE USER ml_user WITH PASSWORD 'Yourpasswrd';
ALTER ROLE ml_user SET client_encoding TO 'utf8';
ALTER ROLE ml_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE ml_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE ml_model_db TO ml_user;
```
> run the following commands:

```sql
\c ml_model_db;
```
> then run this

```sql
GRANT ALL PRIVILEGES ON SCHEMA public TO ml_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ml_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ml_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO ml_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO ml_user;
```

> press `\q` to exit.


## Step 4: Deploy Django Application

### 4.1 Clone Your Project
```bash
# Make sure you're in django_user home directory
sudo su django_user
cd
chmod 711 .
```

```bash
git clone https://github.com/AammarTufail/tip_prediction_django_app.git
```

### 4.2 Create Virtual Environment
```bash
# Create virtual environment in home directory (not in app directory)
python3 -m venv .venv
source .venv/bin/activate
```

### 4.3 Install Dependencies
```bash
pip install -r ./tip_prediction_django_app/requirements.txt
pip install uwsgi psycopg2-binary
```

### 4.4 Setup Auto-activation
```bash
# Edit .bashrc to auto-activate virtual environment
nano ~/.bashrc
```

Add these lines to .bashrc at the end to automatically load the virtual environment when you log in to django_user:
```bash
cd
source .venv/bin/activate
```
> press `Ctrl+D` and login again to django_user `sudo su django_user` you will see the virtual environment activated automatically.

### 4.5 Configure Django Settings for Production
```bash
cd ./tip_prediction_django_app/tip_prediction
nano tip_prediction/settings_prod.py
```

Add:
```python
from .settings import *
import os

DEBUG = False
ALLOWED_HOSTS = ['your_domain.com', '45.xx.xxx.x (your IP)', 'localhost']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'ml_model_db',
        'USER': 'ml_user',
        'PASSWORD': 'Yourpasswrd', # you can change this according to your needs
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

STATIC_ROOT = '/home/django_user/tip_prediction_django_app/tip_prediction/staticfiles'
MEDIA_ROOT = '/home/django_user/tip_prediction_django_app/tip_prediction/media'

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
```

### 4.6 Run Database Migrations and Collect Static Files
```bash
export DJANGO_SETTINGS_MODULE=tip_prediction.settings_prod
python manage.py collectstatic --noinput
python manage.py migrate
python manage.py createsuperuser
```
> save the credentials which will be used later.

## Step 5: Configure uWSGI

### 5.1 Create uWSGI Configuration
```bash
cd /home/django_user
nano uwsgi.ini
```

Add this configuration (corrected paths for your project structure):
```ini
[uwsgi]
chdir = /home/django_user/tip_prediction_django_app/tip_prediction
module = tip_prediction.wsgi:application
home = /home/django_user/.venv
env = DJANGO_SETTINGS_MODULE=tip_prediction.settings_prod

master = true
processes = 2
threads = 2

socket = /home/django_user/uwsgi.sock
chmod-socket = 660
chown-socket = django_user:www-data
vacuum = true
die-on-term = true

daemonize = /home/django_user/tip_prediction.log
pidfile = /home/django_user/tip_prediction.pid
```

### 5.2 Test uWSGI
```bash
# Clean start - stop any prior instance
[ -f /home/django_user/tip_prediction.pid ] && uwsgi --stop /home/django_user/tip_prediction.pid || true

# Start uWSGI
uwsgi --ini /home/django_user/uwsgi.ini
sleep 2
# Check if socket was created
ls -l /home/django_user/uwsgi.sock
# Check logs
tail -n60 /home/django_user/tip_prediction.log
```

## Step 6: Configure Nginx

```bash
sudo apt install -y nginx
```
### 6.1 Generate Self-Signed Certificate for IP
```bash
# Create self-signed certificate for IP address
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/ip-selfsigned.key \
  -out /etc/ssl/certs/ip-selfsigned.crt \
  -subj "/CN=45.xx.xxx.x (your IP)" \
  -addext "subjectAltName = IP:45.xx.xxx.x (your IP)"
```

### 6.2 Create Nginx Configuration
```bash
sudo nano /etc/nginx/conf.d/tip_prediction.conf
```

Add this configuration:
```nginx
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    listen 443 ssl;
    server_name 45.xx.xxx.x (your IP);

    ssl_certificate     /etc/ssl/certs/ip-selfsigned.crt;
    ssl_certificate_key /etc/ssl/private/ip-selfsigned.key;

    location / {
        include uwsgi_params;
        uwsgi_pass unix:/home/django_user/uwsgi.sock;
    }

    location /static/ {
        alias /home/django_user/tip_prediction_django_app/tip_prediction/staticfiles/;
    }

    location /media/ {
        alias /home/django_user/tip_prediction_django_app/tip_prediction/media/;
    }
}
```

### 6.3 Test and Start Nginx
```bash
# Test nginx configuration
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx
```

### 6.4 Fix Socket Permissions
```bash
# Ensure proper permissions for socket file
sudo chmod 711 /home/django_user
sudo chgrp www-data /home/django_user/uwsgi.sock
sudo chmod 660 /home/django_user/uwsgi.sock
```

## Step 7: SSL Certificate Setup

### 7.1 Generate Self-Signed Certificate for IP (if not done before)
```bash
# Create self-signed certificate for IP address
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/ip-selfsigned.key \
  -out /etc/ssl/certs/ip-selfsigned.crt \
  -subj "/CN=45.xx.xxx.x (your IP)" \
  -addext "subjectAltName = IP:45.xx.xxx.x (your IP)"
```

### 7.2 Install Certbot (for domain-based SSL later)
```bash
sudo apt install -y certbot python3-certbot-nginx
```

## Step 8: Final Testing

### 8.1 Test Application
```bash
# Test local connection
curl -I http://127.0.0.1

# Test external connection
curl -I http://45.xx.xxx.x (your IP)
```
> if 502 Bad Gateway error occurs, check the above logs for any errors.
> If 200 OK response is received, your application is working correctly.

**Visit your application at:**
- `http://45.xx.xxx.x (your IP)/` 
- `https://45.xx.xxx.x (your IP)/` (with self-signed certificate)
- For admin: `http://45.xx.xxx.x (your IP)/admin/`

### 8.2 Reload Application (when needed)
```bash
# Reload uWSGI gracefully
uwsgi --reload /home/django_user/tip_prediction.pid

# View logs
cat /home/django_user/tip_prediction.log
```

## Step 9: Maintenance and Updates

### 9.1 Update Application
```bash
# Switch to django user
sudo su - django_user
cd tip_prediction_django_app

# Update code
git pull origin main

# Update dependencies if needed
pip install -r requirements.txt

# Run migrations and collect static files
cd tip_prediction
export DJANGO_SETTINGS_MODULE=tip_prediction.settings_prod
python manage.py migrate
python manage.py collectstatic --noinput

# Reload application
cd /home/django_user
uwsgi --reload tip_prediction.pid
```

### 9.2 Monitor Logs
```bash
# uWSGI logs
tail -f /home/django_user/tip_prediction.log

# Nginx logs
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

## Troubleshooting

### Common Issues:

#### 1. **502 Bad Gateway**
```bash
# Check if uWSGI is running
ps aux | grep uwsgi

# Check socket file exists and has correct permissions
ls -la /home/django_user/uwsgi.sock

# Check uWSGI logs
tail -20 /home/django_user/tip_prediction.log

# Fix permissions if needed
sudo chmod 711 /home/django_user
sudo chgrp www-data /home/django_user/uwsgi.sock
sudo chmod 660 /home/django_user/uwsgi.sock

# Restart services
uwsgi --reload /home/django_user/tip_prediction.pid
sudo systemctl restart nginx
```

#### 2. **uWSGI Won't Start**
```bash
# Check if there's a stale PID file
ls -la /home/django_user/tip_prediction.pid

# Remove stale PID if exists
rm -f /home/django_user/tip_prediction.pid

# Start fresh
uwsgi --ini /home/django_user/uwsgi.ini

# Check logs for errors
tail -f /home/django_user/tip_prediction.log
```

#### 3. **Static Files Not Loading**
```bash
# Recollect static files
cd /home/django_user/tip_prediction_django_app/tip_prediction
source /home/django_user/.venv/bin/activate
export DJANGO_SETTINGS_MODULE=tip_prediction.settings_prod
python manage.py collectstatic --clear --noinput

# Check static files directory
ls -la /home/django_user/tip_prediction_django_app/tip_prediction/staticfiles/

# Restart nginx
sudo systemctl restart nginx
```

#### 4. **Permission Errors**
```bash
# Fix ownership and permissions
sudo chown -R django_user:www-data /home/django_user/tip_prediction_django_app
sudo chmod -R 755 /home/django_user/tip_prediction_django_app
sudo chmod 711 /home/django_user
```

## Security Best Practices

1. **Regular Updates**: Keep system and packages updated
2. **Firewall**: Configure UFW properly
3. **SSH Security**: Use key-based authentication
4. **Database Security**: Use strong passwords and limit access
5. **Django Security**: Follow Django security checklist
6. **SSL Certificate**: Use proper SSL certificates for production

## Quick Commands Reference

### Start/Stop/Reload uWSGI
```bash
# Start
uwsgi --ini /home/django_user/uwsgi.ini

# Stop
uwsgi --stop /home/django_user/tip_prediction.pid

# Reload
uwsgi --reload /home/django_user/tip_prediction.pid

# Check status
ps aux | grep uwsgi
```

### Nginx Commands
```bash
# Test configuration
sudo nginx -t

# Restart
sudo systemctl restart nginx

# Check status
sudo systemctl status nginx
```

This guide provides a complete deployment solution based on your working script for Django ML model application on Hostinger KVM VPS.

## Attach your domain to hostinger

1. Log in to your Hostinger account.
2. Go to the "Domains" section.
3. Click on "Add Domain" and enter your domain name.
4. Follow the instructions to point your domain to your VPS IP address.
5. Once the DNS changes propagate, you should be able to access your application via your domain.


## Connecting Hostinger Subdomain from Another Account

If you have a subdomain from another Hostinger account, you can point it to your VPS IP address by following these steps:

### Method 1: DNS Zone Management (Recommended)

#### Step 1: Access DNS Zone Editor
1. Log into the Hostinger account that owns the main domain
2. Go to **Hosting** → **Manage** → **DNS Zone Editor**
3. Find your domain in the list

#### Step 2: Add/Edit DNS Records
```bash
# Add these DNS records in the DNS Zone Editor:

# For subdomain (e.g., api.yourdomain.com)
Type: A Record
Name: app.yourdomain.com
Points to: 45.xx.xxx.x (your IP) (your VPS IP)
TTL: 3600

# Optional: Add AAAA record if you have IPv6
Type: AAAA Record  
Name: api
Points to: your_ipv6_address
TTL: 3600
```


#### Step 3: Update Django Settings
```bash
nano /home/django_user/tip_prediction_django_app/tip_prediction/tip_prediction/settings_prod.py
```

Add your subdomain to ALLOWED_HOSTS:
```python
ALLOWED_HOSTS = ['django.codanics.com', 'yourdomain.com', '45.xx.xxx.x (your IP)', 'localhost']
```

#### Step 5: Get SSL Certificate for Domain
```bash
# Stop nginx temporarily
sudo systemctl stop nginx

# Get SSL certificate for your domain
sudo apt install -y certbot python3-certbot-nginx
sudo ufw allow 'Nginx Full'
sudo certbot --nginx -d django.codanics.com


# Update nginx configuration to use real SSL
sudo nano /etc/nginx/conf.d/tip_prediction.conf
```

Update SSL configuration:
```nginx
server {
    if ($host = app.yourdomain.com) {
        return 301 https://$host$request_uri;
    } # managed by Certbot


    listen 80;
    server_name app.yourdomain.com;
    return 301 https://$server_name$request_uri;


}
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    listen 443 ssl;
    server_name app.yourdomain.com;
    ssl_certificate /etc/letsencrypt/live/app.yourdomain.com/fullchain.pem; # managed by Certbot
    ssl_certificate_key /etc/letsencrypt/live/app.yourdomain.com/privkey.pem; # managed by Certbot


    location / {
        include uwsgi_params;
        uwsgi_pass unix:/home/django_user/uwsgi.sock;
    }

    location /static/ {
        alias /home/django_user/tip_prediction_django_app/tip_prediction/staticfiles/;
    }

    location /media/ {
        alias /home/django_user/tip_prediction_django_app/tip_prediction/media/;
    }

}
```

#### Step 6: Restart Services
```bash
# Test nginx configuration
sudo nginx -t
sudo systemctl stop nginx
sudo systemctl stop nginx
sudo pkill -9 nginx
sudo rm -f /run/nginx.pid
sudo nginx -t
sudo systemctl start nginx
sudo systemctl status nginx
# Reload uWSGI
uwsgi --reload /home/django_user/tip_prediction.pid
```

### Verification Steps

```bash
# Check if DNS is working
nslookup django.codanics.com
dig django.codanics.com

# Should return your VPS IP: 45.xx.xxx.x (your IP)
```

#### Test Application Access
```bash
# Test HTTP
curl -I http://django.codanics.com

# Test HTTPS (if SSL configured)
curl -I https://django.codanics.com
```

### Important Notes

1. **DNS Propagation**: Changes can take 24-48 hours to fully propagate worldwide
2. **Access Required**: You need access to the DNS management of the domain/subdomain
3. **SSL Certificate**: You'll need to generate a new SSL certificate for the domain
4. **Multiple Domains**: You can point multiple subdomains to the same VPS

### Auto-SSL Renewal Setup
```bash
# Add cron job for auto SSL renewal
sudo crontab -e

# Add this line:
0 12 * * * /usr/bin/certbot renew --quiet && systemctl reload nginx
```

After completing these steps, your application will be accessible via your Hostinger subdomain!


### Add a cron job for automatic updates from github for the app

```bash
# Switch to django user
sudo su - django_user

# Create update script
nano ~/update_app.sh
```

Add this content to the script:
```bash
#!/bin/bash
# Auto-update script for Django app

# Log file
LOG_FILE="/home/django_user/update_app.log"
echo "$(date): Starting app update..." >> $LOG_FILE

# Change to app directory
cd /home/django_user/tip_prediction_django_app

# Pull latest changes
git pull origin main >> $LOG_FILE 2>&1

# Update dependencies if requirements changed
pip install -r requirements.txt >> $LOG_FILE 2>&1

# Run migrations and collect static files
cd tip_prediction
export DJANGO_SETTINGS_MODULE=tip_prediction.settings_prod
python manage.py migrate >> $LOG_FILE 2>&1
python manage.py collectstatic --noinput >> $LOG_FILE 2>&1

# Reload application
cd /home/django_user
uwsgi --reload tip_prediction.pid >> $LOG_FILE 2>&1

echo "$(date): App update completed" >> $LOG_FILE
```

Make the script executable:
```bash
chmod +x ~/update_app.sh
```

Add cron job (runs every day at 2 AM):
```bash
crontab -e

# Add this line:
0 2 * * * /home/django_user/update_app.sh
```

View update logs:
```bash
tail -f /home/django_user/update_app.log
```


## Refresh if some errors come

```bash
# Clean start - stop any prior instance
[ -f /home/django_user/tip_prediction.pid ] && uwsgi --stop /home/django_user/tip_prediction.pid || true

# Start uWSGI
uwsgi --ini /home/django_user/uwsgi.ini
sleep 2
# Check if socket was created
ls -l /home/django_user/uwsgi.sock
# Test nginx configuration
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx
```

# Reset everything and start from scratch

```bash
# Stop services
sudo systemctl stop nginx
sudo systemctl stop uwsgi

# Remove application files
sudo rm -rf /home/django_user/tip_prediction_django_app

# Remove virtual environment
sudo rm -rf /home/django_user/venvs/tip_prediction

# Remove logs
sudo rm -f /home/django_user/update_app.log

# Remove SSL certificates
sudo rm -f /etc/letsencrypt/live/app.yourdomain.com/fullchain.pem
sudo rm -f /etc/letsencrypt/live/app.yourdomain.com/privkey.pem

# Remove nginx configuration
sudo rm -f /etc/nginx/sites-available/app.yourdomain.com
sudo rm -f /etc/nginx/sites-enabled/app.yourdomain.com
sudo rm -f /etc/nginx/conf.d/tip_prediction.conf
# Remove uWSGI configuration
sudo rm -f /home/django_user/uwsgi.ini
# Remove PID and socket files
sudo rm -f /home/django_user/tip_prediction.pid
sudo rm -f /home/django_user/uwsgi.sock
# Remove django user
sudo userdel -r django_user
```

> The End.



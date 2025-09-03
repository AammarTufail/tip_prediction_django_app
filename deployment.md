# Django ML Model Deployment Guide - Hostinger KVM VPS

## Prerequisites
- Hostinger KVM VPS account
  - Use this link to purchase and get a discount:
    [Hostinger KVM VPS](https://hostinger.com?REFERRALCODE=1MUHAMMAD0984)
- Domain name (optional but recommended)
  - Buy a domain from [Namecheap](https://www.namecheap.com) or [GoDaddy](https://www.godaddy.com) or [Hostinger](https://www.hostinger.com)

- Local Django project ready for deployment

## Step 1: Server Setup and Initial Configuration

> server is your Hostinger KVM VPS

### 1.1 Connect to Your VPS using SSH
```bash
ssh root@your_server_ip
```

> You can also use server side via terminal inside hostinger VPS.

### 1.2 Update System Packages
```bash
sudo apt update && apt upgrade -y
```

### 1.3 Install Required Software
```bash
# Install Python, pip, and essential packages
sudo apt install python3 python3-pip python3-venv nginx supervisor postgresql postgresql-contrib git -y

# Install additional dependencies for ML libraries
sudo apt install build-essential python3-dev libpq-dev -y
```

## Step 2: Create Application User

### 2.1 Create Non-root User
```bash
adduser django_user
usermod -aG sudo django_user
su - django_user
```

## Step 3: Setup PostgreSQL Database

### 3.1 Configure PostgreSQL
```bash
sudo -u postgres psql
```

```sql
CREATE DATABASE ml_model_db;
CREATE USER ml_user WITH PASSWORD 'your_strong_password';
ALTER ROLE ml_user SET client_encoding TO 'utf8';
ALTER ROLE ml_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE ml_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE ml_model_db TO ml_user;
\q
```

> Note: Replace `your_strong_password` with a strong password of your choice.

## Step 4: Deploy Django Application

### 4.1 Clone Your Project
> 1. Start your git repository locally
> 2. Install pipreqs library and run this command to create a requirements.txt file with versions
```bash
pip install pipreqs
pipreqs /path/to/your/project
```
> 3. Add your files and commit changes
> 4. Push to the remote repository publically if you want to run git clone without any authentication
> 5. Clone the repository on your VPS


```bash
cd /home/django_user
git clone https://github.com/yourusername/your-repo.git
cd your-repo
```

### 4.2 Create Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4.3 Install Dependencies
```bash
pip install -r requirements.txt
pip install gunicorn psycopg2-binary
```
> `gunicorn` is used for serving the Django application in production as a WSGI server.
> `psycopg2-binary` is a PostgreSQL adapter for Python.

### 4.4 Configure Django Settings

Create a production settings file:
```bash
nano ml_model_django/settings_prod.py
```

Add production settings:
```python
from .settings import *

DEBUG = False
ALLOWED_HOSTS = ['your_domain.com', 'your_server_ip', 'localhost'] # add either your domain or server IP

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'ml_model_db', # we created this database
        'USER': 'ml_user', # we created this user
        'PASSWORD': 'your_strong_password', # we created this password
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

STATIC_ROOT = '/home/django_user/ml_model_django/staticfiles'
MEDIA_ROOT = '/home/django_user/ml_model_django/media'

# Security settings
SECURE_BROWSER_XSS_FILTER = True # Enable XSS filtering
SECURE_CONTENT_TYPE_NOSNIFF = True # Enable content type nosniff meaning browsers should not sniff the content type
X_FRAME_OPTIONS = 'DENY' # Protect against clickjacking
```

### 4.5 Configure Environment Variables
```bash
nano .env
```

Add your environment variables which you can reference in your Django settings:
```
SECRET_KEY=your_secret_key_here
DATABASE_URL=postgresql://ml_user:your_strong_password@localhost/ml_model_db
```
> You can find your secret key in the Django settings file by looking for the `SECRET_KEY` variable. You can create a new secret key using the following command:

```bash
python -c 'from django.core.management import utils; print(utils.get_random_secret_key())'
```

### 4.6 Run Django Commands
```bash
export DJANGO_SETTINGS_MODULE=ml_model_django.settings_prod
python manage.py collectstatic --noinput
python manage.py migrate
python manage.py createsuperuser
```

## Step 5: Configure Gunicorn

### 5.1 Test Gunicorn
```bash
gunicorn --bind 0.0.0.0:8000 ml_model_django.wsgi
```
> If this works, you should see output indicating that Gunicorn is running.

### 5.2 Create Gunicorn Socket
```bash
sudo nano /etc/systemd/system/gunicorn.socket
```

Add:
```ini
[Unit]
Description=gunicorn socket

[Socket]
ListenStream=/run/gunicorn.sock

[Install]
WantedBy=sockets.target
```

### 5.3 Create Gunicorn Service
```bash
sudo nano /etc/systemd/system/gunicorn.service
```

Add:
```ini
[Unit]
Description=gunicorn daemon
Requires=gunicorn.socket
After=network.target

[Service]
User=django_user
Group=www-data
WorkingDirectory=/home/django_user/ml_model_django
Environment="DJANGO_SETTINGS_MODULE=ml_model_django.settings_prod"
ExecStart=/home/django_user/ml_model_django/venv/bin/gunicorn \
          --access-logfile - \
          --workers 3 \
          --bind unix:/run/gunicorn.sock \
          ml_model_django.wsgi:application

[Install]
WantedBy=multi-user.target
```

### 5.4 Start and Enable Gunicorn
```bash
sudo systemctl start gunicorn.socket
sudo systemctl enable gunicorn.socket
sudo systemctl status gunicorn.socket
```

## Step 6: Configure Nginx
Nginx is used as a reverse proxy to forward requests to the Gunicorn server.

### 6.1 Create Nginx Configuration
```bash
sudo nano /etc/nginx/sites-available/ml_model_django
```

Add:
```nginx
server {
    listen 80;
    server_name your_domain.com your_server_ip;

    location = /favicon.ico { access_log off; log_not_found off; }
    location /static/ {
        root /home/django_user/ml_model_django;
    }
    
    location /media/ {
        root /home/django_user/ml_model_django;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/run/gunicorn.sock;
    }
}
```

### 6.2 Enable Site
```bash
sudo ln -s /etc/nginx/sites-available/ml_model_django /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

## Step 7: Configure Firewall

```bash
sudo ufw allow 'Nginx Full'
sudo ufw allow ssh
sudo ufw enable
```

## Step 8: SSL Certificate (Optional but Recommended)

### 8.1 Install Certbot
```bash
sudo apt install certbot python3-certbot-nginx -y
```

### 8.2 Obtain SSL Certificate
```bash
sudo certbot --nginx -d your_domain.com
```

## Step 9: Process Management with Supervisor

### 9.1 Install and Configure Supervisor
```bash
sudo nano /etc/supervisor/conf.d/ml_model_django.conf
```

Add:
```ini
[program:ml_model_django]
command=/home/django_user/ml_model_django/venv/bin/gunicorn ml_model_django.wsgi:application
directory=/home/django_user/ml_model_django
user=django_user
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/ml_model_django.log
environment=DJANGO_SETTINGS_MODULE="ml_model_django.settings_prod"
```

### 9.2 Update Supervisor
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start ml_model_django
```

## Step 10: Final Verification

### 10.1 Check Services Status
```bash
sudo systemctl status nginx
sudo systemctl status gunicorn
sudo supervisorctl status
```

### 10.2 Test Application
Visit your domain or server IP in a browser to verify the deployment.

## Step 11: Maintenance and Updates

### 11.1 Update Application
```bash
cd /home/django_user/ml_model_django
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo supervisorctl restart ml_model_django
```

### 11.2 Monitor Logs
```bash
# Application logs
tail -f /var/log/ml_model_django.log

# Nginx logs
tail -f /var/log/nginx/error.log
tail -f /var/log/nginx/access.log
```

## Troubleshooting

### Common Issues:
1. **Permission Errors**: Ensure proper ownership of files
```bash
sudo chown -R django_user:www-data /home/django_user/ml_model_django
```

2. **Static Files Not Loading**: Check nginx configuration and static file paths

3. **Database Connection Issues**: Verify PostgreSQL service and credentials

4. **ML Model Loading Issues**: Ensure all ML dependencies are installed and model files are accessible

### Performance Optimization:
- Adjust Gunicorn workers based on server resources
- Configure Redis for caching
- Use CDN for static files
- Optimize database queries

## Security Best Practices

1. **Regular Updates**: Keep system and packages updated
2. **Firewall**: Configure UFW properly
3. **SSH Security**: Use key-based authentication
4. **Database Security**: Use strong passwords and limit access
5. **Django Security**: Follow Django security checklist
6. **Backup Strategy**: Implement regular backups

## Backup Strategy

### 11.3 Database Backup
```bash
# Create backup script
nano /home/django_user/backup_db.sh
```

Add:
```bash
#!/bin/bash
pg_dump -U ml_user -h localhost ml_model_db > /home/django_user/backups/db_$(date +%Y%m%d_%H%M%S).sql
```

### 11.4 Automated Backups with Cron
```bash
crontab -e
```

Add:
```
0 2 * * * /home/django_user/backup_db.sh
```

This guide provides a complete deployment solution for your Django ML model application on Hostinger KVM VPS with production-ready configuration, security measures, and maintenance procedures.

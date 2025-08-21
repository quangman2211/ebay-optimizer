# 🚀 Deploy eBay Optimizer lên Ubuntu 22.04 VPS - econeatly.com

## 📋 Tổng quan

Hướng dẫn deploy **eBay Listing Optimizer** lên VPS Ubuntu 22.04 với domain **http://econeatly.com**

### 🎯 Kết quả sau khi deploy:
- **Frontend**: https://econeatly.com
- **API**: https://econeatly.com/api/v1
- **API Docs**: https://econeatly.com/api/v1/docs
- **SSL**: Let's Encrypt (free, auto-renewal)
- **Performance**: Production-ready với caching

---

## 🔧 Yêu cầu VPS

### Minimum Specs:
- **OS**: Ubuntu 22.04 LTS
- **RAM**: 2GB+
- **Storage**: 10GB+
- **CPU**: 1 vCPU+
- **Network**: Public IP
- **Access**: Root hoặc sudo user

### Recommended Providers:
- DigitalOcean ($6/month)
- Linode ($5/month)
- Vultr ($6/month)
- AWS EC2 t3.micro

---

## 🌐 Chuẩn bị Domain

### 1. Point Domain tới VPS
```bash
# Tại domain registrar, tạo A records:
@ (root)    →  YOUR_VPS_IP
www         →  YOUR_VPS_IP
```

### 2. Verify DNS propagation
```bash
# Kiểm tra DNS đã propagate chưa
nslookup econeatly.com
nslookup www.econeatly.com

# Hoặc dùng online tool:
# https://dnschecker.org
```

---

## 🖥️ BƯỚC 1: Setup Ubuntu Server

### 1.1. SSH vào VPS
```bash
ssh root@YOUR_VPS_IP
# Hoặc với user thường:
ssh username@YOUR_VPS_IP
```

### 1.2. Update hệ thống
```bash
# Update package list
sudo apt update && sudo apt upgrade -y

# Install essential packages
sudo apt install -y curl wget git unzip software-properties-common apt-transport-https ca-certificates gnupg lsb-release

# Reboot nếu cần
sudo reboot
```

### 1.3. Tạo deployment user (nếu dùng root)
```bash
# Tạo user mới
sudo adduser deploy
sudo usermod -aG sudo deploy
sudo usermod -aG docker deploy

# Chuyển sang user deploy
su - deploy
cd ~
```

### 1.4. Setup Firewall
```bash
# Enable UFW
sudo ufw enable

# Allow SSH
sudo ufw allow ssh
sudo ufw allow 22

# Allow HTTP/HTTPS
sudo ufw allow 80
sudo ufw allow 443

# Allow backend port (tạm thời)
sudo ufw allow 8000

# Check status
sudo ufw status
```

---

## 🐳 BƯỚC 2: Install Docker

### 2.1. Install Docker
```bash
# Add Docker's official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Add Docker repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Test Docker
docker --version
docker run hello-world
```

### 2.2. Install Docker Compose
```bash
# Docker Compose v2 đã có sẵn với docker-compose-plugin
docker compose version

# Nếu muốn Docker Compose v1 (optional)
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

---

## 📦 BƯỚC 3: Deploy Project

### 3.1. Clone project
```bash
cd /home/deploy
git clone https://github.com/quangman2211/ebay-optimizer.git
cd ebay-optimizer

# Check project structure
ls -la
```

### 3.2. Setup Environment
```bash
# Copy production environment
cp .env.production.example .env

# Edit environment variables
nano .env
```

### 3.3. Configure .env cho econeatly.com
```env
# Project Info
PROJECT_NAME="eBay Listing Optimizer - econeatly.com"
VERSION="1.0.0"

# Security
SECRET_KEY="your-super-secret-key-change-this-in-production"

# CORS Origins
BACKEND_CORS_ORIGINS="https://econeatly.com,https://www.econeatly.com,http://econeatly.com,http://www.econeatly.com"

# Database
DATABASE_URL="sqlite:///./data/ebay_optimizer.db"

# Google Sheets (nếu có)
GOOGLE_SHEETS_CREDENTIALS_PATH="credentials/google-service-account.json"
SPREADSHEET_ID=""

# API Settings
API_V1_STR="/api/v1"

# Production settings
ENVIRONMENT="production"
DEBUG="false"

# Domain
DOMAIN="econeatly.com"
```

### 3.4. Setup Directories
```bash
# Tạo thư mục cần thiết
mkdir -p data logs credentials ssl

# Set permissions
chmod 755 data logs
chmod 700 credentials ssl

# Copy Google Service Account (nếu có)
# Upload file google-service-account.json vào thư mục credentials/
```

### 3.5. Build và Start Containers
```bash
# Build containers
docker compose -f docker-compose.econeatly.yml build

# Start in background
docker compose -f docker-compose.econeatly.yml up -d

# Check containers
docker ps
docker compose -f docker-compose.econeatly.yml logs -f
```

### 3.6. Initialize Database
```bash
# Run database migration
docker exec -it ebay-optimizer-backend-prod python migrations/001_initial_schema.py

# Seed sample data (optional)
docker exec -it ebay-optimizer-backend-prod python seed_listings.py
docker exec -it ebay-optimizer-backend-prod python seed_orders.py
docker exec -it ebay-optimizer-backend-prod python seed_sources.py

# Verify database
docker exec -it ebay-optimizer-backend-prod sqlite3 data/ebay_optimizer.db ".tables"
```

---

## 🔒 BƯỚC 4: Setup SSL với Let's Encrypt

### 4.1. Install Certbot
```bash
# Install Certbot
sudo apt update
sudo apt install -y certbot python3-certbot-nginx

# Verify installation
certbot --version
```

### 4.2. Stop containers tạm thời
```bash
# Stop để free port 80/443
docker compose -f docker-compose.econeatly.yml down
```

### 4.3. Generate SSL Certificate
```bash
# Generate certificate cho econeatly.com
sudo certbot certonly --standalone \
  -d econeatly.com \
  -d www.econeatly.com \
  --email your-email@gmail.com \
  --agree-tos \
  --no-eff-email

# Certificates sẽ được lưu tại:
# /etc/letsencrypt/live/econeatly.com/fullchain.pem
# /etc/letsencrypt/live/econeatly.com/privkey.pem
```

### 4.4. Copy Certificates
```bash
# Copy certificates cho Docker containers
sudo cp /etc/letsencrypt/live/econeatly.com/fullchain.pem ssl/
sudo cp /etc/letsencrypt/live/econeatly.com/privkey.pem ssl/
sudo chown -R $USER:$USER ssl/

# Verify certificates
ls -la ssl/
```

### 4.5. Setup Auto-renewal
```bash
# Test renewal
sudo certbot renew --dry-run

# Add cron job cho auto-renewal
sudo crontab -e

# Add line sau vào crontab:
0 12 * * * /usr/bin/certbot renew --quiet --deploy-hook "cd /home/deploy/ebay-optimizer && docker compose -f docker-compose.econeatly.yml restart frontend"
```

---

## 🌐 BƯỚC 5: Configure Nginx với SSL

### 5.1. Update nginx config
```bash
# Edit nginx config
nano nginx.econeatly.conf
```

### 5.2. Start containers với SSL
```bash
# Start với SSL support
docker compose -f docker-compose.econeatly.yml --profile ssl up -d

# Check containers
docker ps
docker compose -f docker-compose.econeatly.yml logs nginx-proxy
```

---

## 🧪 BƯỚC 6: Test Deployment

### 6.1. Test Health Checks
```bash
# Test backend health
curl http://localhost:8000/health
curl https://econeatly.com/health

# Test frontend
curl https://econeatly.com/

# Test API
curl https://econeatly.com/api/v1/
```

### 6.2. Test SSL
```bash
# Check SSL certificate
curl -I https://econeatly.com

# Test SSL grade (online)
# https://www.ssllabs.com/ssltest/analyze.html?d=econeatly.com
```

### 6.3. Test Application
```bash
# Open browser:
# https://econeatly.com

# Login với:
# Email: test@ebayoptimizer.com
# Password: 123456

# Test các chức năng:
# - Dashboard loading
# - Orders page
# - Listings page  
# - Sync modal
```

---

## 📊 BƯỚC 7: Monitoring & Logs

### 7.1. Monitor Containers
```bash
# Check container status
docker ps
docker stats

# Check container health
docker compose -f docker-compose.econeatly.yml ps
```

### 7.2. View Logs
```bash
# All services
docker compose -f docker-compose.econeatly.yml logs -f

# Specific service
docker logs -f ebay-optimizer-backend-prod
docker logs -f ebay-optimizer-frontend-prod
docker logs -f nginx-proxy
```

### 7.3. Setup Log Rotation
```bash
# Create logrotate config
sudo nano /etc/logrotate.d/docker-ebay-optimizer

# Add content:
/home/deploy/ebay-optimizer/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    notifempty
    create 644 deploy deploy
    postrotate
        docker kill -s USR1 $(docker ps -q --filter ancestor=ebay-optimizer-backend)
    endscript
}
```

---

## 🔧 BƯỚC 8: Performance Optimization

### 8.1. System Optimization
```bash
# Increase file limits
echo '* soft nofile 65536' | sudo tee -a /etc/security/limits.conf
echo '* hard nofile 65536' | sudo tee -a /etc/security/limits.conf

# Optimize memory
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
echo 'vm.vfs_cache_pressure=50' | sudo tee -a /etc/sysctl.conf

# Apply changes
sudo sysctl -p
```

### 8.2. Docker Optimization
```bash
# Configure Docker daemon
sudo nano /etc/docker/daemon.json

# Add content:
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2"
}

# Restart Docker
sudo systemctl restart docker
```

### 8.3. Database Optimization
```bash
# Access database
docker exec -it ebay-optimizer-backend-prod sqlite3 data/ebay_optimizer.db

# Run optimization commands:
PRAGMA optimize;
PRAGMA vacuum;
PRAGMA integrity_check;
.quit
```

---

## 🔄 BƯỚC 9: Backup & Update Procedures

### 9.1. Setup Automated Backup
```bash
# Create backup script
nano backup.sh
chmod +x backup.sh

# Add to crontab
crontab -e

# Add line:
0 2 * * * /home/deploy/ebay-optimizer/backup.sh
```

### 9.2. Update Procedure
```bash
# Create update script
nano update.sh
chmod +x update.sh

# Manual update:
./update.sh
```

---

## 🚨 Troubleshooting

### Common Issues:

#### 1. Container won't start
```bash
# Check logs
docker compose -f docker-compose.econeatly.yml logs

# Check system resources
df -h
free -h
docker system df
```

#### 2. SSL Certificate issues
```bash
# Renew certificate manually
sudo certbot renew --force-renewal

# Check certificate validity
openssl x509 -in ssl/fullchain.pem -text -noout
```

#### 3. Domain not accessible
```bash
# Check DNS
nslookup econeatly.com

# Check firewall
sudo ufw status

# Check nginx
docker logs nginx-proxy
```

#### 4. Performance issues
```bash
# Check system load
htop
iostat 1

# Check container resources
docker stats

# Optimize database
docker exec -it ebay-optimizer-backend-prod python -c "
from app.db.database import engine
engine.execute('PRAGMA optimize')
"
```

#### 5. Database corruption
```bash
# Restore from backup
cp data/backup_$(date +%Y%m%d).db data/ebay_optimizer.db

# Or recreate
rm data/ebay_optimizer.db
docker exec -it ebay-optimizer-backend-prod python migrations/001_initial_schema.py
```

---

## 🎯 Final Checklist

### ✅ Deployment Checklist:
- [ ] VPS Ubuntu 22.04 setup
- [ ] Domain econeatly.com pointed to VPS
- [ ] Docker & Docker Compose installed
- [ ] Project cloned and configured
- [ ] Environment variables set
- [ ] Containers built and running
- [ ] Database initialized
- [ ] SSL certificate generated
- [ ] Nginx configured with SSL
- [ ] Health checks passing
- [ ] Application accessible at https://econeatly.com
- [ ] Backup procedures setup
- [ ] Monitoring configured

### 🔗 Important URLs:
- **Website**: https://econeatly.com
- **API**: https://econeatly.com/api/v1
- **API Docs**: https://econeatly.com/api/v1/docs
- **Health**: https://econeatly.com/health

### 🔑 Default Login:
```
Email: test@ebayoptimizer.com
Password: 123456
```

---

## 📞 Support

### Logs Location:
- **Application**: `/home/deploy/ebay-optimizer/logs/`
- **Docker**: `docker logs <container_name>`
- **System**: `/var/log/`

### Useful Commands:
```bash
# Restart all services
docker compose -f docker-compose.econeatly.yml restart

# View real-time logs
docker compose -f docker-compose.econeatly.yml logs -f

# Check container health
docker compose -f docker-compose.econeatly.yml ps

# Update application
git pull && docker compose -f docker-compose.econeatly.yml up -d --build
```

---

**🎉 Congratulations! eBay Optimizer đã deploy thành công lên https://econeatly.com! 🚀**
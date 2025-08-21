# 🚀 Deploy eBay Optimizer lên Bluehost

## 📋 Yêu cầu Bluehost

### Kiểm tra hosting plan:
- **VPS** hoặc **Dedicated Server** (có quyền root)
- **Docker support** (cần cài đặt)
- **Port access**: 80, 443, 8000
- **Memory**: Tối thiểu 2GB RAM
- **Storage**: Tối thiểu 5GB

## 🔧 Chuẩn bị trước khi deploy

### 1. Kiểm tra Bluehost có Docker chưa:
```bash
ssh username@yourdomain.com
docker --version
docker-compose --version
```

### 2. Nếu chưa có Docker, cài đặt:
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

## 📂 Upload project lên server

### Option 1: Clone từ GitHub (Khuyến nghị)
```bash
cd /home/username/
git clone https://github.com/quangman2211/ebay-optimizer.git
cd ebay-optimizer
```

### Option 2: Upload qua FTP/SFTP
```bash
# Nén project locally
tar -czf ebay-optimizer.tar.gz ebay-optimizer/

# Upload lên server qua FTP
# Rồi extract trên server:
tar -xzf ebay-optimizer.tar.gz
cd ebay-optimizer
```

## 🔐 Cấu hình credentials

### 1. Tạo environment file:
```bash
cp .env.example .env
nano .env
```

### 2. Cấu hình .env:
```env
PROJECT_NAME="eBay Listing Optimizer"
SECRET_KEY=your-very-secure-secret-key-here
BACKEND_CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
DATABASE_URL=sqlite:///./data/ebay_optimizer.db
GOOGLE_SHEETS_CREDENTIALS_PATH=credentials/google-service-account.json
```

### 3. Upload Google Service Account:
```bash
mkdir -p credentials
# Upload google-service-account.json vào thư mục credentials/
# Via SFTP hoặc copy content vào file
```

### 4. Tạo thư mục data:
```bash
mkdir -p data logs
chmod 755 data logs
```

## 🚀 Deploy với Docker

### 1. Build và start containers:
```bash
# Production deployment
docker-compose -f docker-compose.prod.yml up -d --build
```

### 2. Kiểm tra containers:
```bash
docker ps
docker logs ebay-optimizer-backend-prod
docker logs ebay-optimizer-frontend-prod
```

### 3. Initialize database:
```bash
# Run migration inside container
docker exec -it ebay-optimizer-backend-prod python migrations/001_initial_schema.py

# Seed sample data (optional)
docker exec -it ebay-optimizer-backend-prod python seed_listings.py
docker exec -it ebay-optimizer-backend-prod python seed_orders.py
```

## 🌐 Cấu hình domain

### 1. Point domain tới server IP:
```
A Record: @ -> YOUR_SERVER_IP
A Record: www -> YOUR_SERVER_IP
```

### 2. Update nginx config trong container:
```bash
# Edit docker-compose.prod.yml
# Thay "yourdomain.com" bằng domain thực của bạn
```

### 3. Restart với domain mới:
```bash
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d
```

## 🔒 Setup SSL (Optional but recommended)

### 1. Install Certbot:
```bash
sudo apt install certbot
```

### 2. Get SSL certificate:
```bash
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com
```

### 3. Copy certificates:
```bash
sudo mkdir -p ssl
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ssl/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ssl/
sudo chown -R $USER:$USER ssl/
```

### 4. Enable SSL profile:
```bash
docker-compose -f docker-compose.prod.yml --profile ssl up -d
```

## 📊 Kiểm tra deployment

### 1. Test các endpoints:
```bash
# Health check
curl http://yourdomain.com/api/v1/health

# Frontend
curl http://yourdomain.com/

# API docs
curl http://yourdomain.com/api/v1/docs
```

### 2. Login test:
- Truy cập: http://yourdomain.com
- Login: test@ebayoptimizer.com / 123456

### 3. Test Google Sheets sync:
- Vào Sync Modal
- Test connection
- Thử import/export

## 🔧 Troubleshooting

### Container không start:
```bash
# Check logs
docker logs ebay-optimizer-backend-prod
docker logs ebay-optimizer-frontend-prod

# Check resources
docker stats
free -h
df -h
```

### Database issues:
```bash
# Recreate database
docker exec -it ebay-optimizer-backend-prod rm -f ebay_optimizer.db
docker exec -it ebay-optimizer-backend-prod python migrations/001_initial_schema.py
```

### Permission issues:
```bash
# Fix permissions
sudo chown -R $USER:$USER /home/username/ebay-optimizer/
chmod -R 755 /home/username/ebay-optimizer/
```

### Port issues:
```bash
# Check ports
sudo netstat -tlnp | grep :80
sudo netstat -tlnp | grep :8000

# Kill existing processes if needed
sudo fuser -k 80/tcp
sudo fuser -k 8000/tcp
```

## 🔄 Updates và maintenance

### 1. Update từ GitHub:
```bash
cd /home/username/ebay-optimizer
git pull origin main
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build
```

### 2. Backup database:
```bash
# Create backup
docker exec ebay-optimizer-backend-prod cp ebay_optimizer.db /app/data/backup_$(date +%Y%m%d).db

# Download backup
scp username@yourdomain.com:/home/username/ebay-optimizer/data/backup_*.db ./
```

### 3. Monitor logs:
```bash
# Follow logs
docker-compose -f docker-compose.prod.yml logs -f

# Check specific service
docker logs -f ebay-optimizer-backend-prod
```

## 📞 Support

Nếu gặp vấn đề:
1. Check logs của containers
2. Verify port access trên Bluehost
3. Confirm Docker permissions
4. Test API endpoints manually

**Note**: Bluehost shared hosting KHÔNG support Docker. Cần VPS hoặc Dedicated server.
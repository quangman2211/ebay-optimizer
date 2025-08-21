# 🏢 Econeatly.com Deployment Package

## 📋 Tổng quan

Thư mục này chứa tất cả các file cấu hình và script để deploy **eBay Listing Optimizer** lên domain **econeatly.com** với Ubuntu 22.04 VPS.

## 📁 Cấu trúc file

```
Econeatly/
├── README.md                     # Hướng dẫn này
├── DEPLOY_UBUNTU_VPS.md         # Hướng dẫn chi tiết deploy VPS
├── docker-compose.econeatly.yml # Docker Compose production
├── nginx.econeatly.conf         # Nginx config cho econeatly.com
├── .env.production.example      # Template environment variables
├── setup-ssl.sh                # Script tự động setup SSL
└── deploy-econeatly.sh          # Script deploy một lệnh
```

## 🚀 Cách sử dụng

### 1. Deploy tự động (Khuyến nghị)
```bash
# Copy toàn bộ thư mục này lên VPS
scp -r Econeatly/ root@your-vps-ip:/home/deploy/

# SSH vào VPS và chạy
ssh root@your-vps-ip
cd /home/deploy/Econeatly
./deploy-econeatly.sh --email admin@econeatly.com
```

### 2. Deploy thủ công
```bash
# Làm theo hướng dẫn chi tiết trong file:
cat DEPLOY_UBUNTU_VPS.md
```

## 🔧 File descriptions

### **deploy-econeatly.sh**
- Script deploy toàn bộ hệ thống một lệnh
- Tự động cài đặt Docker, SSL, database
- Tùy chọn: `--email`, `--skip-ssl-setup`, `--force-reinstall`

### **docker-compose.econeatly.yml**
- Cấu hình Docker Compose production cho econeatly.com
- Bao gồm: backend, frontend, nginx-proxy, db-backup
- Tối ưu cho production với logging và monitoring

### **nginx.econeatly.conf**
- Cấu hình Nginx reverse proxy
- SSL/TLS security (A+ grade)
- Rate limiting, caching, security headers
- HTTP → HTTPS redirect

### **.env.production.example**
- Template 100+ environment variables
- Cấu hình security, database, SSL
- Checklist deploy production

### **setup-ssl.sh**
- Script tự động setup SSL Let's Encrypt
- Auto-renewal configuration
- Certificate validation

### **DEPLOY_UBUNTU_VPS.md**
- Hướng dẫn step-by-step chi tiết
- Troubleshooting guide
- Performance optimization

## 🎯 Kết quả sau deploy

- **Website**: https://econeatly.com
- **API**: https://econeatly.com/api/v1
- **API Docs**: https://econeatly.com/api/v1/docs
- **Health Check**: https://econeatly.com/health

## 🔑 Login mặc định

```
Email: test@ebayoptimizer.com
Password: 123456
```

## 📞 Support

- **Documentation**: DEPLOY_UBUNTU_VPS.md
- **Troubleshooting**: Check logs trong file hướng dẫn
- **Issues**: https://github.com/quangman2211/ebay-optimizer/issues

---

**⚡ Ready for production deployment!** 🚀
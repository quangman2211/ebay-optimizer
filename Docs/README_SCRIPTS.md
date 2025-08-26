# eBay Optimizer Server Management Scripts

## 📋 **Available Scripts**

### 🚀 `start_backend.sh`
**Chức năng**: Khởi động backend server ở port 8000 (chuẩn)

**Sử dụng**:
```bash
./start_backend.sh
```

**Tính năng**:
- ✅ Kiểm tra và kill process cũ nếu port đang được sử dụng
- ✅ Tự động activate virtual environment (nếu có)
- ✅ Kiểm tra và cài đặt dependencies
- ✅ Tạo backup log file
- ✅ Hiển thị thông tin server đầy đủ
- ✅ Logging vào file `backend.log`

**Output**:
- Local: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

---

### 🛑 `stop_backend.sh`
**Chức năng**: Dừng backend server một cách an toàn

**Sử dụng**:
```bash
./stop_backend.sh
```

**Tính năng**:
- ✅ Tìm và kill tất cả process liên quan
- ✅ Graceful shutdown trước, force kill nếu cần
- ✅ Kiểm tra port 8000 đã free chưa
- ✅ Thông báo trạng thái chi tiết

---

### 🔄 `restart_backend.sh`
**Chức năng**: Restart backend server (stop → wait → start)

**Sử dụng**:
```bash
./restart_backend.sh
```

**Workflow**:
1. Gọi `stop_backend.sh`
2. Đợi 3 giây
3. Gọi `start_backend.sh`

---

### 🎯 `dev_servers.sh` 
**Chức năng**: Khởi động cả frontend và backend cho development

**Sử dụng**:
```bash
./dev_servers.sh
```

**Tính năng**:
- ✅ Khởi động backend (port 8000)
- ✅ Khởi động frontend (port 3000) 
- ✅ Tự động cài đặt npm dependencies
- ✅ Health check và thông báo trạng thái
- ✅ Cleanup tự động khi Ctrl+C
- ✅ Hiển thị credentials và URLs

**Services**:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## 🔧 **Troubleshooting**

### ❓ Port đang được sử dụng
```bash
# Kiểm tra process đang sử dụng port
ss -tlnp | grep :8000

# Kill manual nếu cần
pkill -f "uvicorn.*8000"
```

### ❓ Permission denied
```bash
# Đảm bảo scripts có quyền thực thi
chmod +x *.sh
```

### ❓ Virtual environment issues
```bash
# Tạo virtual environment mới
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### ❓ Dependencies errors
```bash
# Cài đặt lại dependencies
pip install -r requirements.txt --force-reinstall
```

---

## 🚀 **Quick Start Guide**

### Development (Khuyến nghị)
```bash
# Khởi động cả frontend + backend
./dev_servers.sh

# Mở browser: http://localhost:3000
# Login: test@ebayoptimizer.com / 123456
```

### Backend Only
```bash
# Chỉ khởi động backend
./start_backend.sh

# Test API: http://localhost:8000/docs
```

### Production Deployment
```bash
# Sử dụng start_backend.sh với reverse proxy
./start_backend.sh

# Configure nginx/apache để proxy đến port 8000
```

---

## 📊 **Monitoring**

### Log Files
```bash
# Xem log real-time
tail -f backend.log

# Xem log cũ
ls -la *.log*
```

### Health Checks
```bash
# Health endpoint
curl http://localhost:8000/health

# API status
curl http://localhost:8000/api/v1/

# Authentication test
curl -X POST http://localhost:8000/api/v1/auth/login-json \
  -H "Content-Type: application/json" \
  -d '{"email": "test@ebayoptimizer.com", "password": "123456"}'
```

---

## 🎮 **Development Workflow**

### Typical Development Session
```bash
1. ./dev_servers.sh                 # Start everything
2. Open http://localhost:3000       # Access dashboard
3. Login: test@ebayoptimizer.com / 123456
4. Make changes to code             # Hot reload enabled
5. Ctrl+C                          # Stop when done
```

### Backend Development Only
```bash
1. ./start_backend.sh              # Start backend
2. Open http://localhost:8000/docs # API documentation
3. Test endpoints                  # Use Swagger UI
4. ./stop_backend.sh              # Stop when done
```

### Restart After Changes
```bash
# Quick restart backend
./restart_backend.sh

# Or restart everything
Ctrl+C                     # Stop dev_servers.sh
./dev_servers.sh          # Start again
```

---

## 🔐 **Default Credentials**

### Test Account
- **Email**: `test@ebayoptimizer.com`
- **Password**: `123456`
- **Role**: User

### Admin Account  
- **Email**: `admin@ebay.vn`
- **Password**: `admin123`
- **Role**: Admin

---

## 🌐 **Port Configuration**

| Service | Port | URL |
|---------|------|-----|
| Frontend | 3000 | http://localhost:3000 |
| Backend API | 8000 | http://localhost:8000 |
| API Docs | 8000 | http://localhost:8000/docs |
| Health Check | 8000 | http://localhost:8000/health |

---

## 💡 **Tips & Best Practices**

1. **Always use scripts**: Thay vì chạy uvicorn trực tiếp
2. **Check logs**: `tail -f backend.log` để debug
3. **Health check**: Luôn test `/health` endpoint trước
4. **Development mode**: Sử dụng `dev_servers.sh` cho development
5. **Clean shutdown**: Dùng `stop_backend.sh` thay vì kill -9
6. **Port conflicts**: Scripts sẽ tự động handle port conflicts
7. **Virtual env**: Scripts sẽ tự động activate venv nếu có

---

## 🎉 **Success Indicators**

### Backend Started Successfully
```
✅ Port 8000 is now free.
🎉 Backend server stopped successfully!
🌟 Starting FastAPI server with Uvicorn...
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Health Check OK
```bash
curl http://localhost:8000/health
# {"status":"healthy","service":"eBay Listing Optimizer","version":"1.0.0"}
```

### Login Test OK
```bash
curl -X POST http://localhost:8000/api/v1/auth/login-json \
  -d '{"email":"test@ebayoptimizer.com","password":"123456"}'
# {"access_token":"eyJ...","token_type":"bearer"}
```
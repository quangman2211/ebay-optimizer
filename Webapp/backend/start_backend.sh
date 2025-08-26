#!/bin/bash
#
# eBay Optimizer Backend Startup Script
# Khởi động backend server ở port 8000 (chuẩn)
#

echo "🚀 Starting eBay Optimizer Backend Server..."
echo "📍 Location: $(pwd)"
echo "🔌 Port: 8000 (Standard Port)"

# Kiểm tra nếu port 8000 đang được sử dụng
if ss -tlnp | grep -q ":8000 "; then
    echo "⚠️  Port 8000 is already in use. Checking for existing processes..."
    
    # Hiển thị process đang sử dụng port 8000
    PORT_PROCESS=$(ss -tlnp | grep ":8000 " | head -1)
    echo "📊 Current process: $PORT_PROCESS"
    
    read -p "🤔 Do you want to kill the existing process? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🔪 Killing existing process on port 8000..."
        pkill -f "uvicorn.*8000" 2>/dev/null || true
        sleep 2
    else
        echo "❌ Cannot start server. Port 8000 is occupied."
        exit 1
    fi
fi

# Kiểm tra xem có file requirements.txt không
if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt not found. Please run from backend directory."
    exit 1
fi

# Kiểm tra virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  No virtual environment detected."
    
    if [ -d "venv" ]; then
        echo "🔧 Activating virtual environment..."
        source venv/bin/activate
    else
        echo "💡 Tip: Consider creating a virtual environment:"
        echo "   python3 -m venv venv"
        echo "   source venv/bin/activate"
        echo "   pip install -r requirements.txt"
    fi
fi

# Kiểm tra dependencies
echo "🔍 Checking dependencies..."
if ! python3 -c "import uvicorn, fastapi" 2>/dev/null; then
    echo "📦 Installing/updating dependencies..."
    pip install -r requirements.txt
fi

# Tạo backup của log file cũ nếu có
if [ -f "backend.log" ]; then
    mv backend.log "backend.log.$(date +%Y%m%d_%H%M%S).bak"
fi

echo ""
echo "🌟 Starting FastAPI server with Uvicorn..."
echo "📋 Configuration:"
echo "   - Host: 0.0.0.0 (All interfaces)"
echo "   - Port: 8000 (Standard)"
echo "   - Reload: Enabled (Development mode)"
echo "   - Log file: backend.log"
echo ""
echo "🌐 Server will be available at:"
echo "   - Local: http://localhost:8000"
echo "   - Network: http://$(hostname -I | awk '{print $1}'):8000"
echo "   - API Docs: http://localhost:8000/docs"
echo "   - Health Check: http://localhost:8000/health"
echo ""
echo "💡 To stop the server: Ctrl+C or run ./stop_backend.sh"
echo "🔄 To restart: ./restart_backend.sh"
echo ""

# Khởi động server với logging
python3 -m uvicorn app.main:app \
    --reload \
    --host 0.0.0.0 \
    --port 8000 \
    --log-level info \
    --access-log \
    2>&1 | tee backend.log
#!/bin/bash
#
# eBay Optimizer Development Servers Script
# Khởi động cả frontend và backend cho development
#

echo "🚀 Starting eBay Optimizer Development Environment"
echo "================================================="

# Kiểm tra xem đang ở đúng thư mục backend không
if [ ! -f "app/main.py" ]; then
    echo "❌ Please run this script from the backend directory"
    echo "💡 Expected location: /path/to/ebay-optimizer/backend/"
    exit 1
fi

# Tìm thư mục frontend
FRONTEND_DIR="../frontend"
if [ ! -d "$FRONTEND_DIR" ]; then
    echo "❌ Frontend directory not found at: $FRONTEND_DIR"
    echo "💡 Expected structure:"
    echo "   ebay-optimizer/"
    echo "   ├── backend/     (current directory)"
    echo "   └── frontend/    (React app)"
    exit 1
fi

# Function để cleanup khi script bị interrupt
cleanup() {
    echo ""
    echo "🛑 Shutting down development servers..."
    
    # Kill background jobs
    jobs -p | xargs -r kill 2>/dev/null
    
    # Kill specific processes
    ./stop_backend.sh >/dev/null 2>&1
    
    # Kill npm start process
    pkill -f "npm start" 2>/dev/null || true
    
    echo "✅ Development environment stopped."
    exit 0
}

# Set up trap để cleanup khi nhận SIGINT (Ctrl+C)
trap cleanup SIGINT SIGTERM

echo ""
echo "🔧 Starting Backend Server (Port 8000)..."
echo "=========================================="

# Dừng bất kỳ backend process nào đang chạy
./stop_backend.sh >/dev/null 2>&1

# Khởi động backend trong background
./start_backend.sh &
BACKEND_PID=$!

# Đợi backend khởi động
echo "⏱️  Waiting for backend to start..."
sleep 5

# Kiểm tra backend đã khởi động chưa
if ! curl -s http://localhost:8000/health >/dev/null 2>&1; then
    echo "⚠️  Backend is still starting up..."
    sleep 5
fi

echo ""
echo "🎨 Starting Frontend Server (Port 3000)..."
echo "========================================="

# Chuyển đến thư mục frontend và khởi động
cd "$FRONTEND_DIR"

# Kiểm tra node_modules
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
fi

# Khởi động frontend trong background
npm start &
FRONTEND_PID=$!

# Quay lại thư mục backend
cd - >/dev/null

echo ""
echo "🎉 Development Environment Started!"
echo "=================================="
echo ""
echo "🌐 Services Available:"
echo "   📱 Frontend:     http://localhost:3000"
echo "   🔧 Backend API:  http://localhost:8000"
echo "   📖 API Docs:     http://localhost:8000/docs"
echo "   💚 Health Check: http://localhost:8000/health"
echo ""
echo "👤 Test Login Credentials:"
echo "   📧 Email:    test@ebayoptimizer.com"
echo "   🔑 Password: 123456"
echo ""
echo "🔧 Management Commands:"
echo "   🛑 Stop All:     Ctrl+C"
echo "   🔄 Restart Backend: ./restart_backend.sh (in another terminal)"
echo ""
echo "📄 Log Files:"
echo "   Backend: backend.log"
echo "   Frontend: Check npm terminal output"
echo ""
echo "💡 Tip: Open http://localhost:3000 in your browser to access the dashboard"
echo ""
echo "🎯 Ready for development! Press Ctrl+C to stop all servers."

# Đợi cho đến khi user nhấn Ctrl+C
wait
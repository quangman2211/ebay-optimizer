#!/bin/bash
#
# eBay Optimizer Backend Stop Script
# Dừng backend server một cách an toàn
#

echo "🛑 Stopping eBay Optimizer Backend Server..."

# Tìm và kill các process uvicorn liên quan đến app này
KILLED_PROCESSES=0

# Kill processes chạy trên port 8000
if ss -tlnp | grep -q ":8000 "; then
    echo "🔍 Found process on port 8000, stopping..."
    
    # Lấy PID của process
    PID=$(ss -tlnp | grep ":8000 " | grep -o 'pid=[0-9]*' | grep -o '[0-9]*' | head -1)
    
    if [ ! -z "$PID" ]; then
        echo "🔪 Killing process PID: $PID"
        kill $PID 2>/dev/null
        sleep 2
        
        # Kiểm tra xem process đã chết chưa
        if kill -0 $PID 2>/dev/null; then
            echo "💀 Force killing process PID: $PID"
            kill -9 $PID 2>/dev/null
        fi
        
        KILLED_PROCESSES=$((KILLED_PROCESSES + 1))
    fi
fi

# Kill bất kỳ uvicorn process nào khác liên quan đến app này
UVICORN_PIDS=$(pgrep -f "uvicorn.*app.main:app" 2>/dev/null)
if [ ! -z "$UVICORN_PIDS" ]; then
    echo "🔍 Found additional uvicorn processes: $UVICORN_PIDS"
    for PID in $UVICORN_PIDS; do
        echo "🔪 Killing uvicorn process PID: $PID"
        kill $PID 2>/dev/null
        sleep 1
        
        # Force kill nếu cần
        if kill -0 $PID 2>/dev/null; then
            echo "💀 Force killing PID: $PID"
            kill -9 $PID 2>/dev/null
        fi
        
        KILLED_PROCESSES=$((KILLED_PROCESSES + 1))
    done
fi

# Kiểm tra kết quả
if [ $KILLED_PROCESSES -eq 0 ]; then
    echo "ℹ️  No backend processes were running."
else
    echo "✅ Stopped $KILLED_PROCESSES backend process(es)."
fi

# Kiểm tra lại xem port 8000 đã free chưa
sleep 1
if ss -tlnp | grep -q ":8000 "; then
    echo "⚠️  Warning: Port 8000 is still occupied by another process."
    echo "📊 Process details:"
    ss -tlnp | grep ":8000 "
else
    echo "✅ Port 8000 is now free."
fi

echo "🎉 Backend server stopped successfully!"

# Hiển thị log file info nếu có
if [ -f "backend.log" ]; then
    echo ""
    echo "📄 Log file available: backend.log"
    echo "💡 To view logs: tail -f backend.log"
    echo "🗑️  To clear logs: rm backend.log"
fi
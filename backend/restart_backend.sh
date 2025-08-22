#!/bin/bash
#
# eBay Optimizer Backend Restart Script
# Restart backend server một cách an toàn
#

echo "🔄 Restarting eBay Optimizer Backend Server..."
echo "=========================================="

# Bước 1: Dừng server hiện tại
echo "📍 Step 1: Stopping current server..."
./stop_backend.sh

# Đợi một chút để đảm bảo process đã thực sự dừng
echo "⏱️  Waiting for clean shutdown..."
sleep 3

# Bước 2: Khởi động lại server
echo ""
echo "📍 Step 2: Starting server..."
./start_backend.sh
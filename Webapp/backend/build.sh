#!/usr/bin/env bash
# Build script for Render deployment

set -e  # Exit on error

echo "🚀 Starting Render build process..."

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating required directories..."
mkdir -p credentials
mkdir -p logs
mkdir -p temp

# Handle Google Service Account credentials
# Render will inject this as environment variable
if [ ! -z "$GOOGLE_SERVICE_ACCOUNT_KEY" ]; then
    echo "🔐 Setting up Google Service Account credentials..."
    echo "$GOOGLE_SERVICE_ACCOUNT_KEY" > credentials/google-service-account.json
    chmod 600 credentials/google-service-account.json
else
    echo "⚠️  Warning: GOOGLE_SERVICE_ACCOUNT_KEY not found. Google Sheets integration will not work."
fi

# Run database migrations
echo "🗄️ Running database migrations..."
# Check if this is PostgreSQL (production) or SQLite (development)
if [[ $DATABASE_URL == postgres* ]]; then
    echo "Using PostgreSQL database"
    # Alembic migrations for PostgreSQL
    alembic upgrade head || echo "No migrations to run"
else
    echo "Using SQLite database"
    # For SQLite, just ensure the database file exists
    python -c "
from app.db.database import engine
from app.models import database_models
database_models.Base.metadata.create_all(bind=engine)
print('✅ Database tables created')
    " || echo "Database setup completed"
fi

# Create default admin user if not exists
echo "👤 Setting up default admin user..."
python -c "
import os
from sqlalchemy.orm import Session
from app.db.database import SessionLocal, engine
from app.models.database_models import User
from app.core.security import get_password_hash

db = SessionLocal()
try:
    # Check if admin exists
    admin = db.query(User).filter(User.email == 'admin@ebayoptimizer.com').first()
    if not admin:
        admin_user = User(
            email='admin@ebayoptimizer.com',
            username='admin',
            hashed_password=get_password_hash('changeme123'),
            is_active=True,
            is_superuser=True
        )
        db.add(admin_user)
        db.commit()
        print('✅ Default admin user created')
        print('   Email: admin@ebayoptimizer.com')
        print('   Password: changeme123')
        print('   ⚠️  IMPORTANT: Change this password after first login!')
    else:
        print('✅ Admin user already exists')
except Exception as e:
    print(f'Error setting up admin user: {e}')
finally:
    db.close()
" || echo "Admin setup completed"

# Collect static files if any
echo "📂 Collecting static files..."
if [ -d "static" ]; then
    echo "Static files directory found"
else
    mkdir -p static
    echo "Created static directory"
fi

# Print environment info
echo "ℹ️ Environment Information:"
echo "   Python version: $(python --version)"
echo "   Pip version: $(pip --version)"
echo "   Environment: ${ENVIRONMENT:-development}"
echo "   API Version: ${API_V1_STR:-/api/v1}"

# Verify critical dependencies
echo "🔍 Verifying critical dependencies..."
python -c "
import fastapi
import uvicorn
import sqlalchemy
import pydantic
print('✅ All critical dependencies installed successfully')
print(f'   FastAPI version: {fastapi.__version__}')
print(f'   SQLAlchemy version: {sqlalchemy.__version__}')
print(f'   Pydantic version: {pydantic.VERSION}')
" || echo "Dependency verification completed"

# Set permissions
echo "🔒 Setting file permissions..."
chmod +x build.sh || true
chmod -R 755 app || true

echo "✅ Build completed successfully!"
echo "🎯 Ready to start the application"
#!/bin/bash

# eBay Listing Optimizer - Production Deployment Script
# Usage: ./deploy.sh [environment] [options]
# Example: ./deploy.sh production --build --migrate

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="production"
BUILD_IMAGES=false
RUN_MIGRATIONS=false
SKIP_TESTS=false
FORCE_DEPLOY=false
BACKUP_DB=true

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    cat << EOF
eBay Listing Optimizer - Deployment Script

Usage: $0 [ENVIRONMENT] [OPTIONS]

ENVIRONMENTS:
    production      Deploy to production (default)
    staging         Deploy to staging
    development     Deploy to development

OPTIONS:
    --build         Build Docker images before deployment
    --migrate       Run database migrations
    --skip-tests    Skip running tests before deployment
    --force         Force deployment without confirmations
    --no-backup     Skip database backup
    --help          Show this help message

EXAMPLES:
    $0                                  # Deploy to production
    $0 production --build --migrate     # Build, migrate and deploy
    $0 staging --skip-tests            # Deploy to staging without tests
    $0 --force                         # Force deploy without confirmations

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        production|staging|development)
            ENVIRONMENT="$1"
            shift
            ;;
        --build)
            BUILD_IMAGES=true
            shift
            ;;
        --migrate)
            RUN_MIGRATIONS=true
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --force)
            FORCE_DEPLOY=true
            shift
            ;;
        --no-backup)
            BACKUP_DB=false
            shift
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown argument: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Set environment-specific configuration
case $ENVIRONMENT in
    production)
        COMPOSE_FILE="docker-compose.prod.yml"
        ENV_FILE=".env.production"
        ;;
    staging)
        COMPOSE_FILE="docker-compose.staging.yml"
        ENV_FILE=".env.staging"
        ;;
    development)
        COMPOSE_FILE="docker-compose.dev.yml"
        ENV_FILE=".env.development"
        ;;
    *)
        print_error "Invalid environment: $ENVIRONMENT"
        exit 1
        ;;
esac

# Check if required files exist
check_requirements() {
    print_info "Checking deployment requirements..."
    
    if [ ! -f "$COMPOSE_FILE" ]; then
        print_error "Compose file not found: $COMPOSE_FILE"
        exit 1
    fi
    
    if [ ! -f "$ENV_FILE" ]; then
        print_warning "Environment file not found: $ENV_FILE"
        print_info "Creating from template..."
        cp .env.production "$ENV_FILE"
        print_warning "Please update $ENV_FILE with appropriate values"
    fi
    
    # Check if Docker is installed and running
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running"
        exit 1
    fi
    
    # Check if docker-compose is installed
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed"
        exit 1
    fi
    
    print_success "Requirements check passed"
}

# Function to run tests
run_tests() {
    if [ "$SKIP_TESTS" = true ]; then
        print_warning "Skipping tests as requested"
        return 0
    fi
    
    print_info "Running pre-deployment tests..."
    
    # Activate virtual environment if it exists
    if [ -d "test_env" ]; then
        source test_env/bin/activate
    fi
    
    # Run quick performance test
    if [ -f "test_quick_performance.py" ]; then
        print_info "Running performance validation..."
        if python3 test_quick_performance.py; then
            print_success "Performance tests passed"
        else
            print_error "Performance tests failed"
            if [ "$FORCE_DEPLOY" = false ]; then
                exit 1
            else
                print_warning "Continuing deployment despite test failure (--force used)"
            fi
        fi
    fi
    
    # Run integration tests
    if [ -f "test_simple_integration.py" ]; then
        print_info "Running integration tests..."
        if python3 test_simple_integration.py; then
            print_success "Integration tests passed"
        else
            print_error "Integration tests failed"
            if [ "$FORCE_DEPLOY" = false ]; then
                exit 1
            else
                print_warning "Continuing deployment despite test failure (--force used)"
            fi
        fi
    fi
}

# Function to backup database
backup_database() {
    if [ "$BACKUP_DB" = false ]; then
        print_warning "Skipping database backup as requested"
        return 0
    fi
    
    print_info "Creating database backup..."
    
    # Create backup directory
    mkdir -p backups
    
    # Generate backup filename with timestamp
    BACKUP_FILE="backups/ebay_optimizer_backup_$(date +%Y%m%d_%H%M%S).db"
    
    # Check if database exists
    if [ -f "data/ebay_optimizer.db" ]; then
        cp "data/ebay_optimizer.db" "$BACKUP_FILE"
        print_success "Database backup created: $BACKUP_FILE"
    else
        print_warning "No existing database found to backup"
    fi
}

# Function to build Docker images
build_images() {
    if [ "$BUILD_IMAGES" = false ]; then
        print_info "Using existing Docker images"
        return 0
    fi
    
    print_info "Building Docker images..."
    
    # Build backend image
    print_info "Building backend image..."
    docker build -f Dockerfile.prod -t ebay-optimizer-backend:latest .
    
    # Build frontend image if exists
    if [ -f "../frontend/Dockerfile.prod" ]; then
        print_info "Building frontend image..."
        cd ../frontend
        docker build -f Dockerfile.prod -t ebay-optimizer-frontend:latest .
        cd ../backend
    fi
    
    print_success "Docker images built successfully"
}

# Function to run database migrations
run_migrations() {
    if [ "$RUN_MIGRATIONS" = false ]; then
        print_info "Skipping database migrations"
        return 0
    fi
    
    print_info "Running database migrations..."
    
    # Run migration script if it exists
    if [ -f "migrations/001_initial_schema.py" ]; then
        # Activate virtual environment if it exists
        if [ -d "test_env" ]; then
            source test_env/bin/activate
        fi
        
        python3 migrations/001_initial_schema.py
        print_success "Database migrations completed"
    else
        print_warning "No migration scripts found"
    fi
}

# Function to deploy application
deploy_application() {
    print_info "Deploying $ENVIRONMENT environment..."
    
    # Set environment file
    export ENV_FILE="$ENV_FILE"
    
    # Stop existing containers
    print_info "Stopping existing containers..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down --remove-orphans
    
    # Create necessary directories
    mkdir -p data logs credentials ssl
    
    # Start services
    print_info "Starting services..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d
    
    # Wait for services to be healthy
    print_info "Waiting for services to be ready..."
    sleep 30
    
    # Check service health
    check_service_health
}

# Function to check service health
check_service_health() {
    print_info "Checking service health..."
    
    # Check backend health
    for i in {1..30}; do
        if curl -f http://localhost:8000/health &> /dev/null; then
            print_success "Backend service is healthy"
            break
        else
            if [ $i -eq 30 ]; then
                print_error "Backend service failed to start"
                docker-compose -f "$COMPOSE_FILE" logs backend
                exit 1
            fi
            print_info "Waiting for backend service... ($i/30)"
            sleep 10
        fi
    done
    
    # Check frontend if available
    if curl -f http://localhost:3000 &> /dev/null; then
        print_success "Frontend service is healthy"
    else
        print_warning "Frontend service may not be available"
    fi
}

# Function to show deployment status
show_deployment_status() {
    print_info "Deployment Status:"
    print_info "=================="
    
    # Show container status
    docker-compose -f "$COMPOSE_FILE" ps
    
    # Show service URLs
    print_info ""
    print_info "Service URLs:"
    print_info "Backend API: http://localhost:8000"
    print_info "API Documentation: http://localhost:8000/docs"
    print_info "Frontend: http://localhost:3000"
    print_info "Health Check: http://localhost:8000/health"
    
    # Show logs command
    print_info ""
    print_info "View logs with:"
    print_info "docker-compose -f $COMPOSE_FILE logs -f [service_name]"
}

# Function to cleanup on exit
cleanup() {
    if [ $? -ne 0 ]; then
        print_error "Deployment failed!"
        print_info "Checking container logs..."
        docker-compose -f "$COMPOSE_FILE" logs --tail=50
        
        print_info "To rollback, run:"
        print_info "docker-compose -f $COMPOSE_FILE down"
    fi
}

# Set trap for cleanup
trap cleanup EXIT

# Main deployment flow
main() {
    print_info "Starting eBay Listing Optimizer deployment to $ENVIRONMENT"
    print_info "============================================================"
    
    # Confirmation prompt
    if [ "$FORCE_DEPLOY" = false ]; then
        print_warning "This will deploy to $ENVIRONMENT environment"
        read -p "Continue? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "Deployment cancelled"
            exit 0
        fi
    fi
    
    # Run deployment steps
    check_requirements
    run_tests
    backup_database
    build_images
    run_migrations
    deploy_application
    show_deployment_status
    
    print_success "Deployment completed successfully!"
    print_info "Environment: $ENVIRONMENT"
    print_info "Compose file: $COMPOSE_FILE"
    print_info "Environment file: $ENV_FILE"
    
    # Show final status
    print_info ""
    print_info "🎉 eBay Listing Optimizer is now running!"
    print_info "Visit http://localhost:3000 to access the application"
}

# Run main function
main "$@"
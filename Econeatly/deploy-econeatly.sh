#!/bin/bash

# ========================================
# One-Command Deployment Script for econeatly.com
# eBay Optimizer Production Deployment
# Ubuntu 22.04 VPS
# ========================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
DOMAIN="econeatly.com"
PROJECT_NAME="ebay-optimizer"
PROJECT_DIR="/home/deploy/ebay-optimizer"
REPO_URL="https://github.com/quangman2211/ebay-optimizer.git"
COMPOSE_FILE="docker-compose.econeatly.yml"
ENV_FILE=".env"
ENV_EXAMPLE=".env.production.example"

# Default values (can be overridden with command line arguments)
SKIP_SYSTEM_UPDATE=false
SKIP_DOCKER_INSTALL=false
SKIP_SSL_SETUP=false
FORCE_REINSTALL=false
EMAIL=""

# Function to print colored output
print_header() {
    echo -e "${PURPLE}========================================"
    echo -e "$1"
    echo -e "========================================${NC}"
}

print_step() {
    echo -e "${CYAN}[STEP]${NC} $1"
}

print_status() {
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
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Options:"
    echo "  -e, --email EMAIL          Email for SSL certificate (required)"
    echo "  --skip-system-update       Skip system update"
    echo "  --skip-docker-install      Skip Docker installation"
    echo "  --skip-ssl-setup          Skip SSL certificate setup"
    echo "  --force-reinstall          Force reinstall everything"
    echo "  -h, --help                 Show this help message"
    echo
    echo "Examples:"
    echo "  $0 --email admin@econeatly.com"
    echo "  $0 --email admin@econeatly.com --skip-system-update"
    echo "  $0 --email admin@econeatly.com --force-reinstall"
    echo
}

# Function to parse command line arguments
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -e|--email)
                EMAIL="$2"
                shift 2
                ;;
            --skip-system-update)
                SKIP_SYSTEM_UPDATE=true
                shift
                ;;
            --skip-docker-install)
                SKIP_DOCKER_INSTALL=true
                shift
                ;;
            --skip-ssl-setup)
                SKIP_SSL_SETUP=true
                shift
                ;;
            --force-reinstall)
                FORCE_REINSTALL=true
                shift
                ;;
            -h|--help)
                show_usage
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # Validate required arguments
    if [ -z "$EMAIL" ]; then
        print_error "Email is required for SSL certificate"
        show_usage
        exit 1
    fi
}

# Function to check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        print_error "This script should not be run as root!"
        print_status "Please run as a regular user with sudo privileges"
        exit 1
    fi
}

# Function to check prerequisites
check_prerequisites() {
    print_step "Checking prerequisites..."
    
    # Check if sudo is available
    if ! command -v sudo &> /dev/null; then
        print_error "sudo is required but not installed"
        exit 1
    fi
    
    # Check if user has sudo privileges
    if ! sudo -n true 2>/dev/null; then
        print_error "User does not have sudo privileges"
        exit 1
    fi
    
    # Check internet connectivity
    if ! ping -c 1 google.com &> /dev/null; then
        print_error "No internet connectivity"
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Function to update system
update_system() {
    if [ "$SKIP_SYSTEM_UPDATE" = true ]; then
        print_status "Skipping system update"
        return 0
    fi
    
    print_step "Updating system packages..."
    
    sudo apt update
    sudo apt upgrade -y
    sudo apt install -y curl wget git unzip software-properties-common apt-transport-https ca-certificates gnupg lsb-release
    
    print_success "System updated successfully"
}

# Function to create deployment user
setup_deployment_user() {
    print_step "Setting up deployment user..."
    
    if id "deploy" &>/dev/null; then
        print_status "Deploy user already exists"
    else
        sudo adduser --disabled-password --gecos "" deploy
        sudo usermod -aG sudo deploy
        print_success "Deploy user created"
    fi
    
    # Switch to deploy user if not already
    if [ "$USER" != "deploy" ]; then
        print_status "Switching to deploy user..."
        sudo -u deploy bash << 'EOF'
            echo "Now running as: $(whoami)"
            cd /home/deploy
EOF
    fi
}

# Function to setup firewall
setup_firewall() {
    print_step "Configuring firewall..."
    
    # Enable UFW
    sudo ufw --force enable
    
    # Allow SSH
    sudo ufw allow ssh
    sudo ufw allow 22
    
    # Allow HTTP/HTTPS
    sudo ufw allow 80
    sudo ufw allow 443
    
    # Show status
    sudo ufw status
    
    print_success "Firewall configured"
}

# Function to install Docker
install_docker() {
    if [ "$SKIP_DOCKER_INSTALL" = true ]; then
        print_status "Skipping Docker installation"
        return 0
    fi
    
    print_step "Installing Docker..."
    
    # Check if Docker is already installed
    if command -v docker &> /dev/null && [ "$FORCE_REINSTALL" = false ]; then
        print_status "Docker is already installed"
        docker --version
        return 0
    fi
    
    # Remove old Docker installations
    sudo apt remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true
    
    # Add Docker's official GPG key
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    # Add Docker repository
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Install Docker
    sudo apt update
    sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    
    # Add user to docker group
    sudo usermod -aG docker $USER
    sudo usermod -aG docker deploy
    
    # Start and enable Docker
    sudo systemctl start docker
    sudo systemctl enable docker
    
    # Test Docker installation
    sudo docker run hello-world
    
    print_success "Docker installed successfully"
    docker --version
    docker compose version
}

# Function to clone project
clone_project() {
    print_step "Cloning project repository..."
    
    # Switch to deploy user home directory
    cd /home/deploy
    
    # Remove existing directory if force reinstall
    if [ "$FORCE_REINSTALL" = true ] && [ -d "$PROJECT_NAME" ]; then
        print_status "Removing existing project directory..."
        rm -rf "$PROJECT_NAME"
    fi
    
    # Clone project if not exists
    if [ ! -d "$PROJECT_NAME" ]; then
        git clone "$REPO_URL" "$PROJECT_NAME"
        print_success "Project cloned successfully"
    else
        print_status "Project directory already exists, pulling latest changes..."
        cd "$PROJECT_NAME"
        git pull origin main
        cd ..
    fi
    
    # Change to project directory
    cd "$PROJECT_NAME"
    
    # Verify project structure
    if [ -f "$COMPOSE_FILE" ] && [ -f "$ENV_EXAMPLE" ]; then
        print_success "Project structure verified"
    else
        print_error "Project structure is incomplete"
        print_status "Missing files: $COMPOSE_FILE or $ENV_EXAMPLE"
        exit 1
    fi
}

# Function to setup environment
setup_environment() {
    print_step "Setting up environment configuration..."
    
    # Create necessary directories
    mkdir -p data logs credentials ssl backups
    
    # Set permissions
    chmod 755 data logs backups
    chmod 700 credentials ssl
    
    # Setup environment file
    if [ ! -f "$ENV_FILE" ] || [ "$FORCE_REINSTALL" = true ]; then
        print_status "Creating environment file from template..."
        cp "$ENV_EXAMPLE" "$ENV_FILE"
        
        # Generate secure secret keys
        SECRET_KEY=$(openssl rand -base64 32)
        JWT_SECRET_KEY=$(openssl rand -base64 32)
        
        # Update environment file
        sed -i "s/your-super-secret-key-change-this-in-production-MUST-BE-32-CHARS-LONG!/$SECRET_KEY/" "$ENV_FILE"
        sed -i "s/your-jwt-secret-key-change-this-in-production-MUST-BE-STRONG!/$JWT_SECRET_KEY/" "$ENV_FILE"
        sed -i "s/your-email@gmail.com/$EMAIL/" "$ENV_FILE"
        
        print_success "Environment file configured with secure keys"
    else
        print_status "Environment file already exists"
    fi
    
    # Show current configuration
    print_status "Environment configuration:"
    grep -E "^(DOMAIN|PROJECT_NAME|ENVIRONMENT)" "$ENV_FILE" || true
}

# Function to build and start containers
build_containers() {
    print_step "Building and starting containers..."
    
    # Build containers
    docker compose -f "$COMPOSE_FILE" build --no-cache
    
    # Start containers without SSL first (for initial setup)
    docker compose -f "$COMPOSE_FILE" up -d backend frontend
    
    # Wait for containers to start
    sleep 10
    
    # Check container status
    print_status "Container status:"
    docker compose -f "$COMPOSE_FILE" ps
    
    print_success "Containers built and started"
}

# Function to initialize database
initialize_database() {
    print_step "Initializing database..."
    
    # Wait for backend to be ready
    print_status "Waiting for backend to be ready..."
    for i in {1..30}; do
        if docker exec ebay-optimizer-backend-prod curl -f http://localhost:8000/health &>/dev/null; then
            break
        fi
        sleep 2
        if [ $i -eq 30 ]; then
            print_error "Backend failed to start within 60 seconds"
            docker logs ebay-optimizer-backend-prod
            exit 1
        fi
    done
    
    # Initialize database schema
    print_status "Creating database schema..."
    docker exec ebay-optimizer-backend-prod python migrations/001_initial_schema.py
    
    # Seed sample data (optional)
    print_status "Seeding sample data..."
    docker exec ebay-optimizer-backend-prod python seed_listings.py || true
    docker exec ebay-optimizer-backend-prod python seed_orders.py || true
    docker exec ebay-optimizer-backend-prod python seed_sources.py || true
    
    # Verify database
    print_status "Verifying database..."
    docker exec ebay-optimizer-backend-prod sqlite3 data/ebay_optimizer.db ".tables"
    
    print_success "Database initialized successfully"
}

# Function to setup SSL
setup_ssl() {
    if [ "$SKIP_SSL_SETUP" = true ]; then
        print_status "Skipping SSL setup"
        return 0
    fi
    
    print_step "Setting up SSL certificate..."
    
    # Update the setup-ssl.sh script with the provided email
    sed -i "s/your-email@gmail.com/$EMAIL/" setup-ssl.sh
    
    # Make script executable and run
    chmod +x setup-ssl.sh
    ./setup-ssl.sh
    
    print_success "SSL setup completed"
}

# Function to setup monitoring
setup_monitoring() {
    print_step "Setting up monitoring and logging..."
    
    # Create log rotation configuration
    sudo tee /etc/logrotate.d/docker-ebay-optimizer > /dev/null << EOF
/home/deploy/ebay-optimizer/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    notifempty
    create 644 deploy deploy
    postrotate
        docker kill -s USR1 \$(docker ps -q --filter ancestor=ebay-optimizer-backend) 2>/dev/null || true
    endscript
}
EOF
    
    # Create backup script
    cat > backup.sh << 'EOF'
#!/bin/bash
# eBay Optimizer Database Backup Script

BACKUP_DIR="./backups"
DB_FILE="./data/ebay_optimizer.db"
DATE=$(date +"%Y%m%d_%H%M")
BACKUP_FILE="$BACKUP_DIR/ebay_optimizer_$DATE.db"

mkdir -p "$BACKUP_DIR"

if [ -f "$DB_FILE" ]; then
    cp "$DB_FILE" "$BACKUP_FILE"
    gzip "$BACKUP_FILE"
    echo "Database backed up to $BACKUP_FILE.gz"
    
    # Clean old backups (keep 30 days)
    find "$BACKUP_DIR" -name "*.gz" -mtime +30 -delete
else
    echo "Database file not found: $DB_FILE"
fi
EOF
    
    chmod +x backup.sh
    
    # Add backup cron job
    (crontab -l 2>/dev/null; echo "0 2 * * * cd /home/deploy/ebay-optimizer && ./backup.sh") | crontab -
    
    print_success "Monitoring and backup configured"
}

# Function to run tests
run_tests() {
    print_step "Running health checks and tests..."
    
    # Test backend health
    if docker exec ebay-optimizer-backend-prod curl -f http://localhost:8000/health; then
        print_success "Backend health check passed"
    else
        print_warning "Backend health check failed"
    fi
    
    # Test frontend
    if curl -f http://localhost/ &>/dev/null; then
        print_success "Frontend accessibility test passed"
    else
        print_warning "Frontend accessibility test failed"
    fi
    
    # Test API endpoints
    if curl -f http://localhost:8000/api/v1/ &>/dev/null; then
        print_success "API endpoint test passed"
    else
        print_warning "API endpoint test failed"
    fi
    
    print_success "Health checks completed"
}

# Function to display final information
display_final_info() {
    print_header "🎉 Deployment Complete!"
    
    echo -e "${GREEN}eBay Optimizer has been successfully deployed to econeatly.com!${NC}"
    echo
    echo "🌐 Access Information:"
    if [ "$SKIP_SSL_SETUP" = false ]; then
        echo "   Website: https://$DOMAIN"
        echo "   API: https://$DOMAIN/api/v1/"
        echo "   API Docs: https://$DOMAIN/api/v1/docs"
        echo "   Health Check: https://$DOMAIN/health"
    else
        echo "   Website: http://$DOMAIN"
        echo "   API: http://$DOMAIN:8000/api/v1/"
        echo "   API Docs: http://$DOMAIN:8000/api/v1/docs"
        echo "   Health Check: http://$DOMAIN:8000/health"
    fi
    echo
    echo "🔑 Default Login Credentials:"
    echo "   Email: test@ebayoptimizer.com"
    echo "   Password: 123456"
    echo
    echo "🐳 Docker Information:"
    docker compose -f "$COMPOSE_FILE" ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
    echo
    echo "📁 Important Files:"
    echo "   Project Directory: $PROJECT_DIR"
    echo "   Environment File: $ENV_FILE"
    echo "   Docker Compose: $COMPOSE_FILE"
    echo "   Database: ./data/ebay_optimizer.db"
    echo "   Logs: ./logs/"
    echo "   Backups: ./backups/"
    if [ "$SKIP_SSL_SETUP" = false ]; then
        echo "   SSL Certificates: ./ssl/"
    fi
    echo
    echo "🔧 Useful Commands:"
    echo "   View logs: docker compose -f $COMPOSE_FILE logs -f"
    echo "   Restart services: docker compose -f $COMPOSE_FILE restart"
    echo "   Stop services: docker compose -f $COMPOSE_FILE down"
    echo "   Update application: git pull && docker compose -f $COMPOSE_FILE up -d --build"
    echo "   Backup database: ./backup.sh"
    echo
    echo "📋 Next Steps:"
    echo "1. Test your website and ensure all features work"
    echo "2. Upload your Google Service Account credentials to ./credentials/"
    echo "3. Configure your Google Sheets integration in the admin panel"
    echo "4. Set up monitoring and alerting for production use"
    echo "5. Review and update environment variables as needed"
    echo
    if [ "$SKIP_SSL_SETUP" = false ]; then
        echo "🔒 SSL Information:"
        echo "   Certificate auto-renewal is enabled"
        echo "   Check certificate status: sudo certbot certificates"
        echo "   Test SSL grade: https://www.ssllabs.com/ssltest/analyze.html?d=$DOMAIN"
        echo
    fi
    echo "🆘 Support:"
    echo "   Documentation: ./DEPLOY_UBUNTU_VPS.md"
    echo "   Troubleshooting: Check logs and documentation"
    echo "   Issues: https://github.com/quangman2211/ebay-optimizer/issues"
    echo
    print_success "Deployment completed successfully! 🚀"
}

# Function to handle cleanup on exit
cleanup() {
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        print_error "Deployment failed with exit code $exit_code"
        print_status "Check the logs above for error details"
        print_status "You can re-run the script with --force-reinstall to start fresh"
    fi
}

# Set trap for cleanup
trap cleanup EXIT

# Main execution function
main() {
    print_header "🚀 eBay Optimizer Deployment for econeatly.com"
    
    print_status "Starting deployment with the following configuration:"
    echo "   Domain: $DOMAIN"
    echo "   Email: $EMAIL"
    echo "   Skip system update: $SKIP_SYSTEM_UPDATE"
    echo "   Skip Docker install: $SKIP_DOCKER_INSTALL"
    echo "   Skip SSL setup: $SKIP_SSL_SETUP"
    echo "   Force reinstall: $FORCE_REINSTALL"
    echo
    
    # Confirm before proceeding
    read -p "Continue with deployment? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_status "Deployment cancelled"
        exit 0
    fi
    
    # Execute deployment steps
    check_root
    check_prerequisites
    update_system
    setup_deployment_user
    setup_firewall
    install_docker
    clone_project
    setup_environment
    build_containers
    initialize_database
    setup_ssl
    setup_monitoring
    run_tests
    display_final_info
}

# Parse command line arguments and run main function
parse_arguments "$@"
main
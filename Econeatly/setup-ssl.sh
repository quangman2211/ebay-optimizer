#!/bin/bash

# ========================================
# SSL Setup Automation Script for econeatly.com
# Ubuntu 22.04 VPS Deployment
# ========================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOMAIN="econeatly.com"
EMAIL="your-email@gmail.com"  # Change this!
SSL_DIR="./ssl"
NGINX_CONF="./nginx.econeatly.conf"
COMPOSE_FILE="docker-compose.econeatly.yml"

# Function to print colored output
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
    print_status "Checking prerequisites..."
    
    # Check if sudo is available
    if ! command -v sudo &> /dev/null; then
        print_error "sudo is required but not installed"
        exit 1
    fi
    
    # Check if docker is installed
    if ! command -v docker &> /dev/null; then
        print_error "Docker is required but not installed"
        print_status "Please install Docker first using the deployment guide"
        exit 1
    fi
    
    # Check if docker compose is available
    if ! docker compose version &> /dev/null; then
        print_error "Docker Compose is required but not available"
        exit 1
    fi
    
    # Check if domain resolves to this server
    SERVER_IP=$(curl -s http://checkip.amazonaws.com/)
    DOMAIN_IP=$(nslookup $DOMAIN | grep -A1 "Name:" | grep "Address:" | awk '{print $2}' | head -1)
    
    if [ "$SERVER_IP" != "$DOMAIN_IP" ]; then
        print_warning "Domain $DOMAIN does not resolve to this server IP ($SERVER_IP)"
        print_warning "Current domain resolves to: $DOMAIN_IP"
        print_status "Please update your DNS records and wait for propagation"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    print_success "Prerequisites check passed"
}

# Function to install certbot
install_certbot() {
    print_status "Installing Certbot..."
    
    if command -v certbot &> /dev/null; then
        print_success "Certbot is already installed"
        certbot --version
        return 0
    fi
    
    # Update package list
    sudo apt update
    
    # Install certbot and nginx plugin
    sudo apt install -y certbot python3-certbot-nginx
    
    # Verify installation
    if command -v certbot &> /dev/null; then
        print_success "Certbot installed successfully"
        certbot --version
    else
        print_error "Failed to install Certbot"
        exit 1
    fi
}

# Function to stop containers if running
stop_containers() {
    print_status "Stopping containers to free ports 80/443..."
    
    if [ -f "$COMPOSE_FILE" ]; then
        # Stop containers if they exist
        docker compose -f "$COMPOSE_FILE" down 2>/dev/null || true
        print_success "Containers stopped"
    else
        print_warning "Docker compose file not found: $COMPOSE_FILE"
    fi
    
    # Kill any processes using port 80/443
    sudo fuser -k 80/tcp 2>/dev/null || true
    sudo fuser -k 443/tcp 2>/dev/null || true
    
    sleep 2
}

# Function to generate SSL certificate
generate_certificate() {
    print_status "Generating SSL certificate for $DOMAIN..."
    
    # Check if email is set
    if [ "$EMAIL" = "your-email@gmail.com" ]; then
        print_error "Please set your email address in the script"
        print_status "Edit this script and change EMAIL variable"
        exit 1
    fi
    
    # Generate certificate using standalone mode
    sudo certbot certonly \
        --standalone \
        --non-interactive \
        --agree-tos \
        --no-eff-email \
        --email "$EMAIL" \
        -d "$DOMAIN" \
        -d "www.$DOMAIN"
    
    if [ $? -eq 0 ]; then
        print_success "SSL certificate generated successfully"
    else
        print_error "Failed to generate SSL certificate"
        print_status "Common issues:"
        print_status "1. Domain not pointing to this server"
        print_status "2. Firewall blocking ports 80/443"
        print_status "3. Another service using port 80"
        exit 1
    fi
}

# Function to copy certificates
copy_certificates() {
    print_status "Copying certificates to project directory..."
    
    # Create SSL directory
    mkdir -p "$SSL_DIR"
    
    # Copy certificates
    sudo cp "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" "$SSL_DIR/"
    sudo cp "/etc/letsencrypt/live/$DOMAIN/privkey.pem" "$SSL_DIR/"
    
    # Change ownership to current user
    sudo chown -R $USER:$USER "$SSL_DIR/"
    
    # Set permissions
    chmod 600 "$SSL_DIR/privkey.pem"
    chmod 644 "$SSL_DIR/fullchain.pem"
    
    # Verify certificates exist
    if [ -f "$SSL_DIR/fullchain.pem" ] && [ -f "$SSL_DIR/privkey.pem" ]; then
        print_success "Certificates copied successfully"
        
        # Display certificate info
        print_status "Certificate information:"
        openssl x509 -in "$SSL_DIR/fullchain.pem" -text -noout | grep -E "(Subject:|Not After :)"
    else
        print_error "Failed to copy certificates"
        exit 1
    fi
}

# Function to setup auto-renewal
setup_renewal() {
    print_status "Setting up auto-renewal..."
    
    # Create renewal hook script
    HOOK_SCRIPT="/home/$USER/renew-ssl.sh"
    cat > "$HOOK_SCRIPT" << EOF
#!/bin/bash
# SSL Certificate Renewal Hook for $DOMAIN

cd /home/$USER/ebay-optimizer

# Copy renewed certificates
sudo cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem ssl/
sudo cp /etc/letsencrypt/live/$DOMAIN/privkey.pem ssl/
sudo chown -R $USER:$USER ssl/

# Restart nginx container
docker compose -f $COMPOSE_FILE restart nginx-proxy

echo "SSL certificates renewed and nginx restarted"
EOF
    
    chmod +x "$HOOK_SCRIPT"
    
    # Test renewal (dry run)
    print_status "Testing certificate renewal..."
    sudo certbot renew --dry-run
    
    if [ $? -eq 0 ]; then
        print_success "Certificate renewal test passed"
        
        # Add to crontab
        CRON_JOB="0 12 * * * /usr/bin/certbot renew --quiet --deploy-hook \"$HOOK_SCRIPT\""
        
        # Add cron job if not exists
        (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
        
        print_success "Auto-renewal cron job added"
        print_status "Certificates will auto-renew daily at 12:00 PM"
    else
        print_warning "Certificate renewal test failed"
        print_status "Manual renewal may be required"
    fi
}

# Function to create nginx configuration
create_nginx_config() {
    print_status "Verifying nginx configuration..."
    
    if [ ! -f "$NGINX_CONF" ]; then
        print_error "Nginx configuration file not found: $NGINX_CONF"
        print_status "Please ensure nginx.econeatly.conf exists"
        exit 1
    fi
    
    # Check if SSL paths are correct in nginx config
    if grep -q "/etc/nginx/ssl/" "$NGINX_CONF"; then
        print_success "Nginx SSL configuration looks correct"
    else
        print_warning "Please verify SSL paths in nginx configuration"
    fi
}

# Function to start containers with SSL
start_containers() {
    print_status "Starting containers with SSL support..."
    
    if [ ! -f "$COMPOSE_FILE" ]; then
        print_error "Docker compose file not found: $COMPOSE_FILE"
        exit 1
    fi
    
    # Start containers
    docker compose -f "$COMPOSE_FILE" up -d --build
    
    # Wait for containers to start
    sleep 10
    
    # Check container status
    print_status "Container status:"
    docker compose -f "$COMPOSE_FILE" ps
    
    # Check if nginx is healthy
    if docker ps | grep -q "nginx-proxy.*healthy"; then
        print_success "Nginx proxy is running and healthy"
    else
        print_warning "Nginx proxy may have issues, checking logs..."
        docker logs nginx-proxy
    fi
}

# Function to test SSL
test_ssl() {
    print_status "Testing SSL configuration..."
    
    # Wait for services to be ready
    sleep 5
    
    # Test HTTPS connection
    if curl -I -s "https://$DOMAIN" | grep -q "200 OK"; then
        print_success "HTTPS is working correctly"
    else
        print_warning "HTTPS test failed, checking status..."
        curl -I "https://$DOMAIN" || true
    fi
    
    # Test HTTP to HTTPS redirect
    HTTP_RESPONSE=$(curl -I -s "http://$DOMAIN" | head -1)
    if echo "$HTTP_RESPONSE" | grep -q "301\|302"; then
        print_success "HTTP to HTTPS redirect is working"
    else
        print_warning "HTTP redirect may not be working correctly"
    fi
    
    # Test API endpoint
    if curl -I -s "https://$DOMAIN/api/v1/" | grep -q "200\|404"; then
        print_success "API endpoint is accessible"
    else
        print_warning "API endpoint test failed"
    fi
}

# Function to display final information
display_final_info() {
    echo
    echo "========================================"
    echo -e "${GREEN}SSL Setup Complete!${NC}"
    echo "========================================"
    echo
    echo "🌐 Website: https://$DOMAIN"
    echo "🔗 API: https://$DOMAIN/api/v1/"
    echo "📚 API Docs: https://$DOMAIN/api/v1/docs"
    echo "🏥 Health Check: https://$DOMAIN/health"
    echo
    echo "🔒 SSL Certificate Details:"
    echo "   - Certificate: $SSL_DIR/fullchain.pem"
    echo "   - Private Key: $SSL_DIR/privkey.pem"
    echo "   - Auto-renewal: Enabled (daily at 12:00 PM)"
    echo
    echo "🐳 Docker Containers:"
    docker compose -f "$COMPOSE_FILE" ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
    echo
    echo "📋 Next Steps:"
    echo "1. Test your website: https://$DOMAIN"
    echo "2. Verify SSL grade: https://www.ssllabs.com/ssltest/analyze.html?d=$DOMAIN"
    echo "3. Check logs: docker compose -f $COMPOSE_FILE logs -f"
    echo "4. Monitor certificate expiry: sudo certbot certificates"
    echo
    echo "🆘 Troubleshooting:"
    echo "   - View logs: docker logs nginx-proxy"
    echo "   - Restart services: docker compose -f $COMPOSE_FILE restart"
    echo "   - Check certificate: openssl x509 -in $SSL_DIR/fullchain.pem -text -noout"
    echo
}

# Main execution
main() {
    echo "========================================"
    echo "🔒 SSL Setup for $DOMAIN"
    echo "========================================"
    echo
    
    # Prompt for email if not set
    if [ "$EMAIL" = "your-email@gmail.com" ]; then
        read -p "Enter your email address for Let's Encrypt: " EMAIL
        if [ -z "$EMAIL" ]; then
            print_error "Email address is required"
            exit 1
        fi
    fi
    
    check_root
    check_prerequisites
    install_certbot
    stop_containers
    generate_certificate
    copy_certificates
    setup_renewal
    create_nginx_config
    start_containers
    test_ssl
    display_final_info
    
    print_success "SSL setup completed successfully!"
}

# Handle script arguments
case "${1:-}" in
    --test)
        print_status "Running SSL test only..."
        test_ssl
        ;;
    --renew)
        print_status "Renewing certificates manually..."
        sudo certbot renew --force-renewal
        copy_certificates
        docker compose -f "$COMPOSE_FILE" restart nginx-proxy
        ;;
    --help|-h)
        echo "Usage: $0 [option]"
        echo "Options:"
        echo "  (none)    - Full SSL setup"
        echo "  --test    - Test SSL configuration only"
        echo "  --renew   - Force certificate renewal"
        echo "  --help    - Show this help"
        ;;
    *)
        main
        ;;
esac
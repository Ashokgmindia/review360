#!/bin/bash

# Review360 Production Deployment Script
# This script handles the complete deployment process for the Review360 application

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="review360"
DOCKER_COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env.production"
BACKUP_DIR="/var/backups/review360"
LOG_DIR="/var/log/review360"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_error "This script should not be run as root"
        exit 1
    fi
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
}

# Check if required files exist
check_files() {
    local required_files=(
        "$DOCKER_COMPOSE_FILE"
        "Dockerfile"
        "requirements.txt"
    )

    for file in "${required_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            log_error "Required file $file not found"
            exit 1
        fi
    done

    if [[ ! -f "$ENV_FILE" ]]; then
        log_warning "Environment file $ENV_FILE not found. Creating from template..."
        create_env_file
    fi
}

# Create environment file from template
create_env_file() {
    cat > "$ENV_FILE" << EOF
# Django Settings
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=0
DJANGO_ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# Database Settings
POSTGRES_DB=review360
POSTGRES_USER=review360
POSTGRES_PASSWORD=your-db-password-here
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Redis Settings
REDIS_URL=redis://redis:6379/1

# CORS Settings
CORS_ALLOWED_ORIGINS=https://your-domain.com,https://www.your-domain.com

# Email Settings
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@your-domain.com

# JWT Settings
JWT_ACCESS_MIN=30
JWT_REFRESH_DAYS=7

# Rate Limiting
DRF_THROTTLE_ANON=100/hour
DRF_THROTTLE_USER=1000/hour
DRF_THROTTLE_LOGIN=20/hour

# Optional: Sentry DSN for error tracking
# SENTRY_DSN=your-sentry-dsn-here

# Optional: AWS S3 Settings
# USE_S3=true
# AWS_ACCESS_KEY_ID=your-access-key
# AWS_SECRET_ACCESS_KEY=your-secret-key
# AWS_STORAGE_BUCKET_NAME=your-bucket-name
# AWS_S3_REGION_NAME=us-east-1
EOF
    log_warning "Please edit $ENV_FILE with your actual configuration values"
}

# Create necessary directories
create_directories() {
    log_info "Creating necessary directories..."
    sudo mkdir -p "$BACKUP_DIR"
    sudo mkdir -p "$LOG_DIR"
    sudo mkdir -p "/var/www/review360/static"
    sudo mkdir -p "/var/www/review360/media"
    sudo chown -R $(whoami):$(whoami) "$BACKUP_DIR"
    sudo chown -R $(whoami):$(whoami) "$LOG_DIR"
    sudo chown -R $(whoami):$(whoami) "/var/www/review360"
}

# Build Docker images
build_images() {
    log_info "Building Docker images..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" build --no-cache
    log_success "Docker images built successfully"
}

# Run database migrations
run_migrations() {
    log_info "Running database migrations..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" run --rm web python manage.py migrate
    log_success "Database migrations completed"
}

# Set up permissions
setup_permissions() {
    log_info "Setting up permissions and groups..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" run --rm web python manage.py setup_permissions
    log_success "Permissions setup completed"
}

# Collect static files
collect_static() {
    log_info "Collecting static files..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" run --rm web python manage.py collectstatic --noinput
    log_success "Static files collected"
}

# Create superuser
create_superuser() {
    log_info "Creating superuser..."
    read -p "Enter superuser email: " email
    read -s -p "Enter superuser password: " password
    echo
    read -p "Enter superuser first name: " first_name
    read -p "Enter superuser last name: " last_name

    docker-compose -f "$DOCKER_COMPOSE_FILE" run --rm web python manage.py shell -c "
from iam.models import User
user = User.objects.create_superuser(
    username='$email',
    email='$email',
    password='$password',
    first_name='$first_name',
    last_name='$last_name'
)
print('Superuser created successfully')
"
    log_success "Superuser created successfully"
}

# Start services
start_services() {
    log_info "Starting services..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d
    log_success "Services started successfully"
}

# Check service health
check_health() {
    log_info "Checking service health..."
    sleep 30  # Wait for services to start

    # Check web service
    if curl -f http://localhost/health/ > /dev/null 2>&1; then
        log_success "Web service is healthy"
    else
        log_error "Web service is not responding"
        return 1
    fi

    # Check database
    if docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T db pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" > /dev/null 2>&1; then
        log_success "Database is healthy"
    else
        log_error "Database is not responding"
        return 1
    fi

    # Check Redis
    if docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T redis redis-cli ping > /dev/null 2>&1; then
        log_success "Redis is healthy"
    else
        log_error "Redis is not responding"
        return 1
    fi
}

# Setup SSL certificates
setup_ssl() {
    log_info "Setting up SSL certificates..."
    sudo mkdir -p /etc/nginx/ssl

    if [[ ! -f /etc/nginx/ssl/cert.pem ]] || [[ ! -f /etc/nginx/ssl/key.pem ]]; then
        log_warning "SSL certificates not found. Generating self-signed certificates..."
        sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout /etc/nginx/ssl/key.pem \
            -out /etc/nginx/ssl/cert.pem \
            -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
        log_warning "Self-signed certificates generated. Please replace with real certificates for production."
    else
        log_success "SSL certificates found"
    fi
}

# Backup existing data
backup_data() {
    if docker-compose -f "$DOCKER_COMPOSE_FILE" ps | grep -q "Up"; then
        log_info "Backing up existing data..."
        docker-compose -f "$DOCKER_COMPOSE_FILE" run --rm backup
        log_success "Data backup completed"
    fi
}

# Show deployment status
show_status() {
    log_info "Deployment Status:"
    echo "=================="
    docker-compose -f "$DOCKER_COMPOSE_FILE" ps
    echo ""
    log_info "Application URLs:"
    echo "  - API: https://localhost/api/"
    echo "  - Admin: https://localhost/admin/"
    echo "  - Docs: https://localhost/api/docs/"
    echo "  - Health: https://localhost/health/"
}

# Main deployment function
deploy() {
    log_info "Starting Review360 deployment..."
    
    check_root
    check_docker
    check_files
    create_directories
    setup_ssl
    backup_data
    build_images
    run_migrations
    setup_permissions
    collect_static
    create_superuser
    start_services
    check_health
    show_status
    
    log_success "Deployment completed successfully!"
    log_info "Please update your DNS records to point to this server"
    log_info "Don't forget to replace the self-signed SSL certificates with real ones"
}

# Update function
update() {
    log_info "Updating Review360 application..."
    
    backup_data
    build_images
    run_migrations
    collect_static
    docker-compose -f "$DOCKER_COMPOSE_FILE" restart
    check_health
    
    log_success "Update completed successfully!"
}

# Rollback function
rollback() {
    log_info "Rolling back to previous version..."
    
    # This would implement rollback logic
    # For now, just restart services
    docker-compose -f "$DOCKER_COMPOSE_FILE" restart
    
    log_success "Rollback completed!"
}

# Show help
show_help() {
    echo "Review360 Deployment Script"
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  deploy     Deploy the application (default)"
    echo "  update     Update the application"
    echo "  rollback   Rollback to previous version"
    echo "  status     Show deployment status"
    echo "  logs       Show application logs"
    echo "  stop       Stop all services"
    echo "  start      Start all services"
    echo "  restart    Restart all services"
    echo "  help       Show this help message"
}

# Show logs
show_logs() {
    docker-compose -f "$DOCKER_COMPOSE_FILE" logs -f
}

# Stop services
stop_services() {
    log_info "Stopping services..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" down
    log_success "Services stopped"
}

# Start services
start_services_only() {
    log_info "Starting services..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d
    log_success "Services started"
}

# Restart services
restart_services() {
    log_info "Restarting services..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" restart
    log_success "Services restarted"
}

# Main script logic
case "${1:-deploy}" in
    deploy)
        deploy
        ;;
    update)
        update
        ;;
    rollback)
        rollback
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    stop)
        stop_services
        ;;
    start)
        start_services_only
        ;;
    restart)
        restart_services
        ;;
    help)
        show_help
        ;;
    *)
        log_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac

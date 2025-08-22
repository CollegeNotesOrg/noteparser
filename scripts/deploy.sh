#!/bin/bash

# NoteParser Production Deployment Script
# Usage: ./scripts/deploy.sh [environment] [version]

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ENVIRONMENT="${1:-production}"
VERSION="${2:-latest}"
DEPLOY_TYPE="${3:-docker-compose}"  # docker-compose, kubernetes, or docker-swarm

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $*${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARN: $*${NC}" >&2
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $*${NC}" >&2
    exit 1
}

success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] SUCCESS: $*${NC}"
}

# Pre-deployment checks
check_prerequisites() {
    log "Checking prerequisites for $DEPLOY_TYPE deployment..."
    
    case $DEPLOY_TYPE in
        "docker-compose")
            command -v docker >/dev/null 2>&1 || error "Docker is not installed"
            command -v docker-compose >/dev/null 2>&1 || error "Docker Compose is not installed"
            ;;
        "kubernetes")
            command -v kubectl >/dev/null 2>&1 || error "kubectl is not installed"
            command -v helm >/dev/null 2>&1 || error "Helm is not installed"
            ;;
        "docker-swarm")
            command -v docker >/dev/null 2>&1 || error "Docker is not installed"
            docker info | grep -q "Swarm: active" || error "Docker Swarm is not initialized"
            ;;
        *)
            error "Unsupported deployment type: $DEPLOY_TYPE"
            ;;
    esac
    
    # Check if .env file exists
    if [[ ! -f "$PROJECT_DIR/.env.$ENVIRONMENT" ]]; then
        warn "Environment file .env.$ENVIRONMENT not found"
        if [[ ! -f "$PROJECT_DIR/.env" ]]; then
            error "No environment configuration found"
        fi
    fi
    
    success "Prerequisites check passed"
}

# Environment setup
setup_environment() {
    log "Setting up environment for $ENVIRONMENT..."
    
    cd "$PROJECT_DIR"
    
    # Load environment variables
    if [[ -f ".env.$ENVIRONMENT" ]]; then
        source ".env.$ENVIRONMENT"
        log "Loaded environment from .env.$ENVIRONMENT"
    elif [[ -f ".env" ]]; then
        source ".env"
        log "Loaded environment from .env"
    fi
    
    # Generate secrets if they don't exist
    if [[ -z "${SECRET_KEY:-}" ]]; then
        export SECRET_KEY=$(openssl rand -hex 32)
        warn "Generated new SECRET_KEY"
    fi
    
    if [[ -z "${JWT_SECRET:-}" ]]; then
        export JWT_SECRET=$(openssl rand -hex 32)
        warn "Generated new JWT_SECRET"
    fi
    
    if [[ -z "${DB_PASSWORD:-}" ]]; then
        export DB_PASSWORD=$(openssl rand -base64 32)
        warn "Generated new DB_PASSWORD"
    fi
    
    success "Environment setup complete"
}

# Build application
build_application() {
    log "Building NoteParser application..."
    
    cd "$PROJECT_DIR"
    
    case $DEPLOY_TYPE in
        "docker-compose"|"docker-swarm")
            # Build Docker images
            docker build -t noteparser:$VERSION -f Dockerfile.prod .
            
            # Tag for registry if needed
            if [[ -n "${DOCKER_REGISTRY:-}" ]]; then
                docker tag noteparser:$VERSION $DOCKER_REGISTRY/noteparser:$VERSION
                docker push $DOCKER_REGISTRY/noteparser:$VERSION
                log "Pushed image to registry: $DOCKER_REGISTRY/noteparser:$VERSION"
            fi
            ;;
        "kubernetes")
            # Build and push for Kubernetes
            if [[ -z "${DOCKER_REGISTRY:-}" ]]; then
                error "DOCKER_REGISTRY must be set for Kubernetes deployment"
            fi
            
            docker build -t $DOCKER_REGISTRY/noteparser:$VERSION -f Dockerfile.prod .
            docker push $DOCKER_REGISTRY/noteparser:$VERSION
            ;;
    esac
    
    success "Application build complete"
}

# Database migrations
run_migrations() {
    log "Running database migrations..."
    
    # Check if AI services are running (needed for some migrations)
    if [[ -d "../noteparser-ai-services" ]]; then
        cd ../noteparser-ai-services
        if ! docker-compose ps | grep -q "Up"; then
            log "Starting AI services for migrations..."
            docker-compose up -d
            sleep 10
        fi
        cd "$PROJECT_DIR"
    fi
    
    case $DEPLOY_TYPE in
        "docker-compose")
            docker-compose -f docker-compose.prod.yml run --rm noteparser python -m noteparser.db.migrate
            ;;
        "kubernetes")
            kubectl run noteparser-migrate --image=$DOCKER_REGISTRY/noteparser:$VERSION --rm -it --restart=Never -- python -m noteparser.db.migrate
            ;;
        "docker-swarm")
            docker service create --name noteparser-migrate --restart-condition none $DOCKER_REGISTRY/noteparser:$VERSION python -m noteparser.db.migrate
            ;;
    esac
    
    success "Database migrations complete"
}

# Deploy application
deploy_application() {
    log "Deploying NoteParser $VERSION to $ENVIRONMENT..."
    
    cd "$PROJECT_DIR"
    
    case $DEPLOY_TYPE in
        "docker-compose")
            # Stop existing services
            docker-compose -f docker-compose.prod.yml down
            
            # Deploy new version
            VERSION=$VERSION docker-compose -f docker-compose.prod.yml up -d
            
            # Wait for services to be healthy
            log "Waiting for services to be healthy..."
            timeout 300 bash -c '
                until docker-compose -f docker-compose.prod.yml ps | grep -q "healthy"; do
                    echo "Waiting for health check..."
                    sleep 10
                done
            ' || error "Services failed to become healthy"
            ;;
            
        "kubernetes")
            # Apply Kubernetes configurations
            kubectl apply -f k8s/namespace.yml
            kubectl apply -f k8s/configmap.yml
            kubectl apply -f k8s/secret.yml
            kubectl apply -f k8s/postgres.yml
            kubectl apply -f k8s/redis.yml
            kubectl apply -f k8s/noteparser.yml
            kubectl apply -f k8s/ingress.yml
            
            # Wait for deployment to be ready
            kubectl rollout status deployment/noteparser -n noteparser-$ENVIRONMENT --timeout=300s
            ;;
            
        "docker-swarm")
            # Deploy stack
            docker stack deploy -c docker-compose.prod.yml noteparser-$ENVIRONMENT
            
            # Wait for services to converge
            log "Waiting for services to converge..."
            timeout 300 bash -c '
                until docker service ls | grep noteparser-$ENVIRONMENT | grep -q "1/1"; do
                    echo "Waiting for service convergence..."
                    sleep 10
                done
            ' || error "Services failed to converge"
            ;;
    esac
    
    success "Deployment complete"
}

# Health checks
run_health_checks() {
    log "Running health checks..."
    
    local base_url
    case $DEPLOY_TYPE in
        "docker-compose")
            base_url="http://localhost:5000"
            ;;
        "kubernetes")
            # Get service URL from Kubernetes
            base_url=$(kubectl get service noteparser -n noteparser-$ENVIRONMENT -o jsonpath='{.status.loadBalancer.ingress[0].ip}:5000' 2>/dev/null || echo "http://localhost:5000")
            ;;
        "docker-swarm")
            base_url="http://localhost:5000"
            ;;
    esac
    
    # Test basic health endpoint
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -sf "$base_url/health" >/dev/null 2>&1; then
            success "Basic health check passed"
            break
        else
            log "Health check attempt $attempt/$max_attempts failed, retrying in 10s..."
            sleep 10
            ((attempt++))
        fi
    done
    
    if [[ $attempt -gt $max_attempts ]]; then
        error "Health check failed after $max_attempts attempts"
    fi
    
    # Test AI services health
    if curl -sf "$base_url/api/ai/health" >/dev/null 2>&1; then
        success "AI services health check passed"
    else
        warn "AI services health check failed - this may be expected if AI services are not running"
    fi
    
    # Test database connectivity
    if curl -sf "$base_url/api/index/refresh" -X POST >/dev/null 2>&1; then
        success "Database connectivity check passed"
    else
        warn "Database connectivity check failed"
    fi
    
    success "Health checks complete"
}

# Backup before deployment
backup_data() {
    log "Creating backup before deployment..."
    
    local backup_dir="$PROJECT_DIR/backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"
    
    case $DEPLOY_TYPE in
        "docker-compose")
            # Backup database
            docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U noteparser noteparser > "$backup_dir/database.sql"
            
            # Backup volumes
            docker run --rm -v noteparser_postgres-data:/data -v "$backup_dir:/backup" alpine tar czf /backup/postgres-data.tar.gz -C /data .
            docker run --rm -v noteparser_noteparser-data:/data -v "$backup_dir:/backup" alpine tar czf /backup/noteparser-data.tar.gz -C /data .
            ;;
    esac
    
    success "Backup created at $backup_dir"
}

# Rollback function
rollback() {
    local previous_version="${1:-}"
    
    if [[ -z "$previous_version" ]]; then
        error "Previous version not specified for rollback"
    fi
    
    warn "Rolling back to version $previous_version..."
    
    case $DEPLOY_TYPE in
        "docker-compose")
            VERSION=$previous_version docker-compose -f docker-compose.prod.yml up -d
            ;;
        "kubernetes")
            kubectl rollout undo deployment/noteparser -n noteparser-$ENVIRONMENT
            ;;
        "docker-swarm")
            # Redeploy with previous version
            VERSION=$previous_version docker stack deploy -c docker-compose.prod.yml noteparser-$ENVIRONMENT
            ;;
    esac
    
    success "Rollback to version $previous_version complete"
}

# Cleanup old resources
cleanup() {
    log "Cleaning up old resources..."
    
    case $DEPLOY_TYPE in
        "docker-compose")
            # Remove unused images
            docker image prune -f
            
            # Remove old volumes (be careful with this)
            # docker volume prune -f
            ;;
        "kubernetes")
            # Clean up completed jobs
            kubectl delete jobs --field-selector=status.successful=1 -n noteparser-$ENVIRONMENT
            ;;
    esac
    
    success "Cleanup complete"
}

# Main deployment function
main() {
    log "Starting NoteParser deployment..."
    log "Environment: $ENVIRONMENT"
    log "Version: $VERSION"
    log "Deployment Type: $DEPLOY_TYPE"
    
    # Run deployment steps
    check_prerequisites
    setup_environment
    backup_data
    build_application
    run_migrations
    deploy_application
    run_health_checks
    cleanup
    
    success "NoteParser $VERSION deployed successfully to $ENVIRONMENT!"
    
    # Print access information
    log "Access Information:"
    case $DEPLOY_TYPE in
        "docker-compose")
            log "  Application: http://localhost:5000"
            log "  AI Dashboard: http://localhost:5000/ai"
            log "  Prometheus: http://localhost:9090"
            log "  Grafana: http://localhost:3000"
            ;;
    esac
}

# Handle script arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "rollback")
        rollback "${2:-}"
        ;;
    "health-check")
        run_health_checks
        ;;
    "backup")
        backup_data
        ;;
    "cleanup")
        cleanup
        ;;
    *)
        echo "Usage: $0 [deploy|rollback|health-check|backup|cleanup] [version]"
        echo ""
        echo "Commands:"
        echo "  deploy      - Deploy the application (default)"
        echo "  rollback    - Rollback to a previous version"
        echo "  health-check - Run health checks"
        echo "  backup      - Create a backup"
        echo "  cleanup     - Clean up old resources"
        echo ""
        echo "Environment variables:"
        echo "  ENVIRONMENT - deployment environment (default: production)"
        echo "  VERSION     - application version (default: latest)"
        echo "  DEPLOY_TYPE - deployment type: docker-compose, kubernetes, docker-swarm"
        exit 1
        ;;
esac
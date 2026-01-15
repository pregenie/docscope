#!/bin/bash
# DocScope Deployment Script

set -e

# Configuration
NAMESPACE="docscope"
REGISTRY="your-registry.com"
IMAGE_TAG="${1:-latest}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_requirements() {
    log_info "Checking requirements..."
    
    # Check for required tools
    command -v docker >/dev/null 2>&1 || { log_error "Docker is required but not installed."; exit 1; }
    command -v kubectl >/dev/null 2>&1 || { log_error "kubectl is required but not installed."; exit 1; }
    
    # Check kubectl connection
    kubectl cluster-info >/dev/null 2>&1 || { log_error "kubectl is not connected to a cluster."; exit 1; }
    
    log_info "All requirements met!"
}

build_image() {
    log_info "Building Docker image..."
    docker build -t docscope:${IMAGE_TAG} .
    
    if [ ! -z "$REGISTRY" ]; then
        docker tag docscope:${IMAGE_TAG} ${REGISTRY}/docscope:${IMAGE_TAG}
        log_info "Tagged image as ${REGISTRY}/docscope:${IMAGE_TAG}"
    fi
}

push_image() {
    if [ ! -z "$REGISTRY" ]; then
        log_info "Pushing image to registry..."
        docker push ${REGISTRY}/docscope:${IMAGE_TAG}
    else
        log_warn "No registry configured, skipping push"
    fi
}

create_namespace() {
    log_info "Creating namespace..."
    kubectl apply -f kubernetes/namespace.yaml
}

deploy_secrets() {
    log_info "Deploying secrets..."
    
    # Check if secrets already exist
    if kubectl get secret docscope-secrets -n ${NAMESPACE} >/dev/null 2>&1; then
        log_warn "Secrets already exist, skipping..."
    else
        kubectl apply -f kubernetes/secrets.yaml
        log_warn "Default secrets deployed - UPDATE THESE IN PRODUCTION!"
    fi
}

deploy_config() {
    log_info "Deploying configuration..."
    kubectl apply -f kubernetes/configmap.yaml
}

deploy_storage() {
    log_info "Deploying storage..."
    kubectl apply -f kubernetes/pvc.yaml
}

deploy_database() {
    log_info "Deploying database..."
    kubectl apply -f kubernetes/statefulset.yaml
    
    # Wait for database to be ready
    log_info "Waiting for database to be ready..."
    kubectl wait --for=condition=ready pod -l component=database -n ${NAMESPACE} --timeout=300s
}

deploy_application() {
    log_info "Deploying application..."
    
    # Update image tag in deployment
    kubectl set image deployment/docscope docscope=${REGISTRY}/docscope:${IMAGE_TAG} -n ${NAMESPACE} || true
    
    # Apply deployment
    kubectl apply -f kubernetes/deployment.yaml
    kubectl apply -f kubernetes/service.yaml
    kubectl apply -f kubernetes/rbac.yaml
}

deploy_ingress() {
    log_info "Deploying ingress..."
    kubectl apply -f kubernetes/ingress.yaml
}

run_migrations() {
    log_info "Running database migrations..."
    
    # Run migrations as a job
    kubectl run docscope-migrate \
        --image=${REGISTRY}/docscope:${IMAGE_TAG} \
        --restart=Never \
        --rm -it \
        -n ${NAMESPACE} \
        -- python -m docscope migrate
}

check_deployment() {
    log_info "Checking deployment status..."
    
    # Wait for deployment to be ready
    kubectl rollout status deployment/docscope -n ${NAMESPACE}
    
    # Show pod status
    kubectl get pods -n ${NAMESPACE}
    
    # Show service endpoints
    kubectl get svc -n ${NAMESPACE}
    
    # Show ingress
    kubectl get ingress -n ${NAMESPACE}
}

# Main execution
main() {
    log_info "Starting DocScope deployment..."
    
    check_requirements
    build_image
    push_image
    create_namespace
    deploy_secrets
    deploy_config
    deploy_storage
    deploy_database
    deploy_application
    deploy_ingress
    run_migrations
    check_deployment
    
    log_info "Deployment complete!"
    log_info "Access DocScope at: https://docscope.example.com"
}

# Run if not sourced
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    main "$@"
fi
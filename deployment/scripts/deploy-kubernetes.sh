#!/bin/bash
# Kubernetes deployment script for Organigramma Web App

set -e

# Configuration
NAMESPACE="organigramma"
DEPLOYMENT_DIR="$(dirname "$0")/../kubernetes"
HELM_CHART_DIR="$(dirname "$0")/../helm/organigramma"

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

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed or not in PATH"
        exit 1
    fi
    
    # Check helm (optional)
    if command -v helm &> /dev/null; then
        HELM_AVAILABLE=true
        log_info "Helm is available"
    else
        HELM_AVAILABLE=false
        log_warn "Helm is not available, will use kubectl for deployment"
    fi
    
    # Check cluster connection
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    log_info "Prerequisites check passed"
}

deploy_with_kubectl() {
    log_info "Deploying with kubectl..."
    
    # Create namespace
    log_info "Creating namespace..."
    kubectl apply -f "$DEPLOYMENT_DIR/namespace.yaml"
    
    # Apply configurations
    log_info "Applying ConfigMap..."
    kubectl apply -f "$DEPLOYMENT_DIR/configmap.yaml"
    
    log_info "Applying Secret..."
    kubectl apply -f "$DEPLOYMENT_DIR/secret.yaml"
    
    # Apply persistent volumes (if using local storage)
    if [[ "${STORAGE_CLASS:-local-storage}" == "local-storage" ]]; then
        log_info "Applying Persistent Volumes..."
        kubectl apply -f "$DEPLOYMENT_DIR/persistent-volume.yaml"
    fi
    
    log_info "Applying Persistent Volume Claims..."
    kubectl apply -f "$DEPLOYMENT_DIR/persistent-volume-claim.yaml"
    
    # Deploy application
    log_info "Deploying application..."
    kubectl apply -f "$DEPLOYMENT_DIR/deployment.yaml"
    
    log_info "Creating service..."
    kubectl apply -f "$DEPLOYMENT_DIR/service.yaml"
    
    # Apply ingress if enabled
    if [[ "${ENABLE_INGRESS:-true}" == "true" ]]; then
        log_info "Applying Ingress..."
        kubectl apply -f "$DEPLOYMENT_DIR/ingress.yaml"
    fi
    
    # Apply backup CronJob if enabled
    if [[ "${ENABLE_BACKUP:-true}" == "true" ]]; then
        log_info "Applying backup CronJob..."
        kubectl apply -f "$DEPLOYMENT_DIR/backup-cronjob.yaml"
    fi
}

deploy_with_helm() {
    log_info "Deploying with Helm..."
    
    # Check if release exists
    if helm list -n "$NAMESPACE" | grep -q "organigramma"; then
        log_info "Upgrading existing Helm release..."
        helm upgrade organigramma "$HELM_CHART_DIR" \
            --namespace "$NAMESPACE" \
            --create-namespace \
            --values "${VALUES_FILE:-$HELM_CHART_DIR/values.yaml}" \
            --wait \
            --timeout 10m
    else
        log_info "Installing new Helm release..."
        helm install organigramma "$HELM_CHART_DIR" \
            --namespace "$NAMESPACE" \
            --create-namespace \
            --values "${VALUES_FILE:-$HELM_CHART_DIR/values.yaml}" \
            --wait \
            --timeout 10m
    fi
}

wait_for_deployment() {
    log_info "Waiting for deployment to be ready..."
    
    kubectl wait --for=condition=available \
        --timeout=600s \
        deployment/organigramma-app \
        -n "$NAMESPACE"
    
    log_info "Deployment is ready!"
}

verify_deployment() {
    log_info "Verifying deployment..."
    
    # Check pods
    log_info "Pod status:"
    kubectl get pods -n "$NAMESPACE" -l app=organigramma-web-app
    
    # Check services
    log_info "Service status:"
    kubectl get services -n "$NAMESPACE"
    
    # Check ingress (if enabled)
    if [[ "${ENABLE_INGRESS:-true}" == "true" ]]; then
        log_info "Ingress status:"
        kubectl get ingress -n "$NAMESPACE"
    fi
    
    # Test health endpoint
    log_info "Testing health endpoint..."
    if kubectl get service organigramma-service -n "$NAMESPACE" &> /dev/null; then
        kubectl port-forward service/organigramma-service 8080:80 -n "$NAMESPACE" &
        PORT_FORWARD_PID=$!
        sleep 5
        
        if curl -f http://localhost:8080/api/health &> /dev/null; then
            log_info "Health check passed!"
        else
            log_warn "Health check failed"
        fi
        
        kill $PORT_FORWARD_PID 2>/dev/null || true
    fi
}

cleanup() {
    log_info "Cleaning up..."
    kill $PORT_FORWARD_PID 2>/dev/null || true
}

show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help              Show this help message"
    echo "  -n, --namespace NAME    Kubernetes namespace (default: organigramma)"
    echo "  -f, --values-file FILE  Helm values file (only for Helm deployment)"
    echo "  --use-kubectl           Force use of kubectl instead of Helm"
    echo "  --storage-class CLASS   Storage class for persistent volumes"
    echo "  --no-ingress           Disable ingress deployment"
    echo "  --no-backup            Disable backup CronJob deployment"
    echo "  --dry-run              Show what would be deployed without applying"
    echo ""
    echo "Environment variables:"
    echo "  NAMESPACE              Kubernetes namespace"
    echo "  VALUES_FILE            Helm values file path"
    echo "  STORAGE_CLASS          Storage class for PVs"
    echo "  ENABLE_INGRESS         Enable/disable ingress (true/false)"
    echo "  ENABLE_BACKUP          Enable/disable backup (true/false)"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_usage
            exit 0
            ;;
        -n|--namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        -f|--values-file)
            VALUES_FILE="$2"
            shift 2
            ;;
        --use-kubectl)
            FORCE_KUBECTL=true
            shift
            ;;
        --storage-class)
            STORAGE_CLASS="$2"
            shift 2
            ;;
        --no-ingress)
            ENABLE_INGRESS=false
            shift
            ;;
        --no-backup)
            ENABLE_BACKUP=false
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Main execution
trap cleanup EXIT

log_info "Starting Organigramma Web App deployment to Kubernetes..."
log_info "Namespace: $NAMESPACE"
log_info "Storage Class: ${STORAGE_CLASS:-local-storage}"
log_info "Ingress: ${ENABLE_INGRESS:-true}"
log_info "Backup: ${ENABLE_BACKUP:-true}"

check_prerequisites

if [[ "$DRY_RUN" == "true" ]]; then
    log_info "DRY RUN MODE - No changes will be applied"
    if [[ "$HELM_AVAILABLE" == "true" && "$FORCE_KUBECTL" != "true" ]]; then
        helm template organigramma "$HELM_CHART_DIR" \
            --namespace "$NAMESPACE" \
            --values "${VALUES_FILE:-$HELM_CHART_DIR/values.yaml}"
    else
        log_info "Would apply the following files:"
        find "$DEPLOYMENT_DIR" -name "*.yaml" | sort
    fi
    exit 0
fi

# Deploy
if [[ "$HELM_AVAILABLE" == "true" && "$FORCE_KUBECTL" != "true" ]]; then
    deploy_with_helm
else
    deploy_with_kubectl
fi

wait_for_deployment
verify_deployment

log_info "Deployment completed successfully!"
log_info "You can access the application at:"
if [[ "${ENABLE_INGRESS:-true}" == "true" ]]; then
    log_info "  https://organigramma.yourdomain.com (configure your domain)"
fi
log_info "  kubectl port-forward service/organigramma-service 8080:80 -n $NAMESPACE"
log_info "  Then visit http://localhost:8080"
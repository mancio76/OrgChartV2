#!/bin/bash
# Deployment validation script for Organigramma Web App
# Validates deployment across different environments

set -e

# Configuration
DEFAULT_TIMEOUT=30
DEFAULT_RETRIES=3

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

log_debug() {
    if [[ "$DEBUG" == "true" ]]; then
        echo -e "${BLUE}[DEBUG]${NC} $1"
    fi
}

# Test HTTP endpoint with retries
test_endpoint() {
    local url="$1"
    local expected_status="${2:-200}"
    local timeout="${3:-$DEFAULT_TIMEOUT}"
    local retries="${4:-$DEFAULT_RETRIES}"
    local description="${5:-$url}"
    
    log_info "Testing endpoint: $description"
    log_debug "URL: $url"
    log_debug "Expected status: $expected_status"
    
    for ((i=1; i<=retries; i++)); do
        log_debug "Attempt $i/$retries"
        
        if response=$(curl -s -w "%{http_code}" --max-time "$timeout" "$url" 2>/dev/null); then
            status_code="${response: -3}"
            body="${response%???}"
            
            log_debug "Status code: $status_code"
            
            if [[ "$status_code" == "$expected_status" ]]; then
                log_info "✅ $description - OK ($status_code)"
                return 0
            else
                log_warn "❌ $description - Unexpected status: $status_code (expected: $expected_status)"
            fi
        else
            log_warn "❌ $description - Connection failed (attempt $i/$retries)"
        fi
        
        if [[ $i -lt $retries ]]; then
            sleep 2
        fi
    done
    
    log_error "❌ $description - Failed after $retries attempts"
    return 1
}

# Test JSON endpoint
test_json_endpoint() {
    local url="$1"
    local expected_field="$2"
    local expected_value="$3"
    local description="${4:-$url}"
    
    log_info "Testing JSON endpoint: $description"
    
    if response=$(curl -s --max-time "$DEFAULT_TIMEOUT" "$url" 2>/dev/null); then
        if echo "$response" | jq -e ".$expected_field" >/dev/null 2>&1; then
            actual_value=$(echo "$response" | jq -r ".$expected_field")
            if [[ "$actual_value" == "$expected_value" ]]; then
                log_info "✅ $description - JSON field '$expected_field' = '$actual_value'"
                return 0
            else
                log_warn "❌ $description - JSON field '$expected_field' = '$actual_value' (expected: '$expected_value')"
            fi
        else
            log_warn "❌ $description - JSON field '$expected_field' not found"
        fi
    else
        log_error "❌ $description - Failed to fetch JSON"
    fi
    
    return 1
}

# Validate Kubernetes deployment
validate_kubernetes() {
    local namespace="${1:-organigramma}"
    local service_name="${2:-organigramma-service}"
    
    log_info "Validating Kubernetes deployment in namespace: $namespace"
    
    # Check if kubectl is available
    if ! command -v kubectl >/dev/null 2>&1; then
        log_error "kubectl not found - cannot validate Kubernetes deployment"
        return 1
    fi
    
    # Check namespace
    if ! kubectl get namespace "$namespace" >/dev/null 2>&1; then
        log_error "Namespace '$namespace' not found"
        return 1
    fi
    
    log_info "✅ Namespace '$namespace' exists"
    
    # Check deployment
    if kubectl get deployment organigramma-app -n "$namespace" >/dev/null 2>&1; then
        ready_replicas=$(kubectl get deployment organigramma-app -n "$namespace" -o jsonpath='{.status.readyReplicas}')
        desired_replicas=$(kubectl get deployment organigramma-app -n "$namespace" -o jsonpath='{.spec.replicas}')
        
        if [[ "$ready_replicas" == "$desired_replicas" ]]; then
            log_info "✅ Deployment ready: $ready_replicas/$desired_replicas replicas"
        else
            log_warn "❌ Deployment not ready: $ready_replicas/$desired_replicas replicas"
            return 1
        fi
    else
        log_error "Deployment 'organigramma-app' not found"
        return 1
    fi
    
    # Check service
    if kubectl get service "$service_name" -n "$namespace" >/dev/null 2>&1; then
        log_info "✅ Service '$service_name' exists"
        
        # Get service endpoint
        service_port=$(kubectl get service "$service_name" -n "$namespace" -o jsonpath='{.spec.ports[0].port}')
        
        # Test service via port-forward
        log_info "Testing service via port-forward..."
        kubectl port-forward service/"$service_name" 8080:"$service_port" -n "$namespace" >/dev/null 2>&1 &
        PORT_FORWARD_PID=$!
        
        sleep 5
        
        if test_endpoint "http://localhost:8080/api/health" "200" "10" "3" "Health check via port-forward"; then
            log_info "✅ Service health check passed"
        else
            log_warn "❌ Service health check failed"
        fi
        
        kill $PORT_FORWARD_PID 2>/dev/null || true
    else
        log_error "Service '$service_name' not found"
        return 1
    fi
    
    # Check ingress (if exists)
    if kubectl get ingress organigramma-ingress -n "$namespace" >/dev/null 2>&1; then
        ingress_host=$(kubectl get ingress organigramma-ingress -n "$namespace" -o jsonpath='{.spec.rules[0].host}')
        log_info "✅ Ingress exists for host: $ingress_host"
        
        # Test ingress endpoint (if accessible)
        if [[ -n "$ingress_host" ]]; then
            test_endpoint "https://$ingress_host/api/health" "200" "30" "2" "Ingress health check"
        fi
    else
        log_info "ℹ️  No ingress found (optional)"
    fi
    
    return 0
}

# Validate AWS ECS deployment
validate_aws_ecs() {
    local cluster_name="${1:-organigramma-cluster}"
    local service_name="${2:-organigramma-web-app}"
    local region="${3:-${AWS_REGION:-us-east-1}}"
    
    log_info "Validating AWS ECS deployment"
    log_info "Cluster: $cluster_name"
    log_info "Service: $service_name"
    log_info "Region: $region"
    
    # Check if AWS CLI is available
    if ! command -v aws >/dev/null 2>&1; then
        log_error "AWS CLI not found - cannot validate ECS deployment"
        return 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity --region "$region" >/dev/null 2>&1; then
        log_error "AWS credentials not configured or invalid"
        return 1
    fi
    
    # Check cluster
    if aws ecs describe-clusters --clusters "$cluster_name" --region "$region" >/dev/null 2>&1; then
        cluster_status=$(aws ecs describe-clusters --clusters "$cluster_name" --region "$region" --query 'clusters[0].status' --output text)
        if [[ "$cluster_status" == "ACTIVE" ]]; then
            log_info "✅ ECS cluster '$cluster_name' is active"
        else
            log_warn "❌ ECS cluster '$cluster_name' status: $cluster_status"
            return 1
        fi
    else
        log_error "ECS cluster '$cluster_name' not found"
        return 1
    fi
    
    # Check service
    if aws ecs describe-services --cluster "$cluster_name" --services "$service_name" --region "$region" >/dev/null 2>&1; then
        service_status=$(aws ecs describe-services --cluster "$cluster_name" --services "$service_name" --region "$region" --query 'services[0].status' --output text)
        running_count=$(aws ecs describe-services --cluster "$cluster_name" --services "$service_name" --region "$region" --query 'services[0].runningCount' --output text)
        desired_count=$(aws ecs describe-services --cluster "$cluster_name" --services "$service_name" --region "$region" --query 'services[0].desiredCount' --output text)
        
        if [[ "$service_status" == "ACTIVE" ]]; then
            log_info "✅ ECS service '$service_name' is active"
            
            if [[ "$running_count" == "$desired_count" ]]; then
                log_info "✅ Service tasks: $running_count/$desired_count running"
            else
                log_warn "❌ Service tasks: $running_count/$desired_count running"
                return 1
            fi
        else
            log_warn "❌ ECS service '$service_name' status: $service_status"
            return 1
        fi
    else
        log_error "ECS service '$service_name' not found"
        return 1
    fi
    
    # Check load balancer (if CloudFormation stack exists)
    if [[ -n "$STACK_NAME" ]]; then
        if aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$region" >/dev/null 2>&1; then
            lb_dns=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$region" --query 'Stacks[0].Outputs[?OutputKey==`LoadBalancerDNS`].OutputValue' --output text)
            
            if [[ -n "$lb_dns" ]]; then
                log_info "✅ Load balancer DNS: $lb_dns"
                test_endpoint "http://$lb_dns/api/health" "200" "30" "3" "Load balancer health check"
            fi
        fi
    fi
    
    return 0
}

# Validate Docker Compose deployment
validate_docker_compose() {
    local compose_file="${1:-docker-compose.yml}"
    local service_name="${2:-app}"
    
    log_info "Validating Docker Compose deployment"
    
    # Check if docker-compose is available
    if ! command -v docker-compose >/dev/null 2>&1; then
        log_error "docker-compose not found"
        return 1
    fi
    
    # Check if compose file exists
    if [[ ! -f "$compose_file" ]]; then
        log_error "Docker Compose file not found: $compose_file"
        return 1
    fi
    
    log_info "✅ Docker Compose file found: $compose_file"
    
    # Check service status
    if docker-compose -f "$compose_file" ps "$service_name" | grep -q "Up"; then
        log_info "✅ Service '$service_name' is running"
        
        # Get service port
        service_port=$(docker-compose -f "$compose_file" port "$service_name" 8000 2>/dev/null | cut -d: -f2)
        
        if [[ -n "$service_port" ]]; then
            test_endpoint "http://localhost:$service_port/api/health" "200" "10" "3" "Docker Compose health check"
        else
            log_warn "❌ Could not determine service port"
            return 1
        fi
    else
        log_error "Service '$service_name' is not running"
        return 1
    fi
    
    return 0
}

# Comprehensive application tests
test_application_endpoints() {
    local base_url="$1"
    
    log_info "Testing application endpoints at: $base_url"
    
    # Health checks
    test_endpoint "$base_url/api/health" "200" "10" "3" "Basic health check"
    test_endpoint "$base_url/api/health/ready" "200" "10" "3" "Readiness check"
    test_endpoint "$base_url/api/health/live" "200" "10" "3" "Liveness check"
    
    # Test JSON response
    test_json_endpoint "$base_url/api/health" "status" "ok" "Health status JSON"
    
    # Main application endpoints
    test_endpoint "$base_url/" "200" "15" "2" "Home page"
    test_endpoint "$base_url/units" "200" "15" "2" "Units page"
    test_endpoint "$base_url/persons" "200" "15" "2" "Persons page"
    test_endpoint "$base_url/job-titles" "200" "15" "2" "Job titles page"
    test_endpoint "$base_url/assignments" "200" "15" "2" "Assignments page"
    test_endpoint "$base_url/orgchart" "200" "15" "2" "Orgchart page"
    
    # API endpoints
    test_endpoint "$base_url/api/units" "200" "10" "2" "Units API"
    test_endpoint "$base_url/api/persons" "200" "10" "2" "Persons API"
    test_endpoint "$base_url/api/job-titles" "200" "10" "2" "Job titles API"
    
    # Static files
    test_endpoint "$base_url/static/css/base.css" "200" "10" "2" "Base CSS"
    test_endpoint "$base_url/static/js/base.js" "200" "10" "2" "Base JavaScript"
    
    # Error pages
    test_endpoint "$base_url/nonexistent-page" "404" "10" "2" "404 error page"
}

# Performance tests
test_performance() {
    local base_url="$1"
    local concurrent_requests="${2:-10}"
    local total_requests="${3:-100}"
    
    log_info "Running performance tests"
    log_info "Concurrent requests: $concurrent_requests"
    log_info "Total requests: $total_requests"
    
    if command -v ab >/dev/null 2>&1; then
        log_info "Running Apache Bench test..."
        ab_result=$(ab -n "$total_requests" -c "$concurrent_requests" "$base_url/api/health" 2>/dev/null)
        
        if [[ $? -eq 0 ]]; then
            requests_per_second=$(echo "$ab_result" | grep "Requests per second" | awk '{print $4}')
            time_per_request=$(echo "$ab_result" | grep "Time per request" | head -1 | awk '{print $4}')
            
            log_info "✅ Performance test completed"
            log_info "   Requests per second: $requests_per_second"
            log_info "   Time per request: ${time_per_request}ms"
        else
            log_warn "❌ Performance test failed"
        fi
    else
        log_info "ℹ️  Apache Bench (ab) not available - skipping performance tests"
    fi
}

# Security tests
test_security() {
    local base_url="$1"
    
    log_info "Running basic security tests"
    
    # Test HTTPS redirect (if applicable)
    if [[ "$base_url" == https://* ]]; then
        http_url="${base_url/https:/http:}"
        if response=$(curl -s -I --max-time 10 "$http_url" 2>/dev/null); then
            if echo "$response" | grep -q "301\|302"; then
                log_info "✅ HTTP to HTTPS redirect working"
            else
                log_warn "❌ HTTP to HTTPS redirect not working"
            fi
        fi
    fi
    
    # Test security headers
    if response=$(curl -s -I --max-time 10 "$base_url/" 2>/dev/null); then
        if echo "$response" | grep -qi "x-frame-options"; then
            log_info "✅ X-Frame-Options header present"
        else
            log_warn "❌ X-Frame-Options header missing"
        fi
        
        if echo "$response" | grep -qi "x-content-type-options"; then
            log_info "✅ X-Content-Type-Options header present"
        else
            log_warn "❌ X-Content-Type-Options header missing"
        fi
    fi
    
    # Test SQL injection protection (basic)
    test_endpoint "$base_url/api/units?id=1';DROP TABLE units;--" "400" "10" "1" "SQL injection protection"
}

# Show usage
show_usage() {
    echo "Usage: $0 [OPTIONS] DEPLOYMENT_TYPE [BASE_URL]"
    echo ""
    echo "Deployment types:"
    echo "  kubernetes          Validate Kubernetes deployment"
    echo "  aws-ecs            Validate AWS ECS deployment"
    echo "  docker-compose     Validate Docker Compose deployment"
    echo "  url                Validate application at specific URL"
    echo ""
    echo "Options:"
    echo "  -h, --help              Show this help message"
    echo "  -n, --namespace NAME    Kubernetes namespace (default: organigramma)"
    echo "  -c, --cluster NAME      ECS cluster name (default: organigramma-cluster)"
    echo "  -s, --service NAME      Service name"
    echo "  -r, --region REGION     AWS region (default: us-east-1)"
    echo "  --stack-name NAME       CloudFormation stack name"
    echo "  --skip-performance      Skip performance tests"
    echo "  --skip-security         Skip security tests"
    echo "  --debug                 Enable debug output"
    echo ""
    echo "Examples:"
    echo "  $0 kubernetes"
    echo "  $0 aws-ecs --region us-west-2"
    echo "  $0 docker-compose"
    echo "  $0 url http://localhost:8000"
    echo "  $0 url https://organigramma.yourdomain.com"
}

# Parse command line arguments
NAMESPACE="organigramma"
CLUSTER_NAME="organigramma-cluster"
SERVICE_NAME=""
REGION="us-east-1"
STACK_NAME=""
SKIP_PERFORMANCE=false
SKIP_SECURITY=false
DEBUG=false

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
        -c|--cluster)
            CLUSTER_NAME="$2"
            shift 2
            ;;
        -s|--service)
            SERVICE_NAME="$2"
            shift 2
            ;;
        -r|--region)
            REGION="$2"
            shift 2
            ;;
        --stack-name)
            STACK_NAME="$2"
            shift 2
            ;;
        --skip-performance)
            SKIP_PERFORMANCE=true
            shift
            ;;
        --skip-security)
            SKIP_SECURITY=true
            shift
            ;;
        --debug)
            DEBUG=true
            shift
            ;;
        -*)
            log_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
        *)
            break
            ;;
    esac
done

# Get deployment type and base URL
DEPLOYMENT_TYPE="$1"
BASE_URL="$2"

if [[ -z "$DEPLOYMENT_TYPE" ]]; then
    log_error "Deployment type is required"
    show_usage
    exit 1
fi

# Main execution
log_info "Starting deployment validation..."
log_info "Deployment type: $DEPLOYMENT_TYPE"

case "$DEPLOYMENT_TYPE" in
    "kubernetes")
        if validate_kubernetes "$NAMESPACE" "${SERVICE_NAME:-organigramma-service}"; then
            log_info "Kubernetes deployment validation passed"
        else
            log_error "Kubernetes deployment validation failed"
            exit 1
        fi
        ;;
    "aws-ecs")
        if validate_aws_ecs "$CLUSTER_NAME" "${SERVICE_NAME:-organigramma-web-app}" "$REGION"; then
            log_info "AWS ECS deployment validation passed"
        else
            log_error "AWS ECS deployment validation failed"
            exit 1
        fi
        ;;
    "docker-compose")
        if validate_docker_compose "docker-compose.yml" "${SERVICE_NAME:-app}"; then
            log_info "Docker Compose deployment validation passed"
        else
            log_error "Docker Compose deployment validation failed"
            exit 1
        fi
        ;;
    "url")
        if [[ -z "$BASE_URL" ]]; then
            log_error "Base URL is required for URL validation"
            show_usage
            exit 1
        fi
        
        log_info "Validating application at: $BASE_URL"
        ;;
    *)
        log_error "Unknown deployment type: $DEPLOYMENT_TYPE"
        show_usage
        exit 1
        ;;
esac

# Run application tests if we have a base URL
if [[ -n "$BASE_URL" ]] || [[ "$DEPLOYMENT_TYPE" == "url" ]]; then
    test_application_endpoints "$BASE_URL"
    
    if [[ "$SKIP_PERFORMANCE" != "true" ]]; then
        test_performance "$BASE_URL"
    fi
    
    if [[ "$SKIP_SECURITY" != "true" ]]; then
        test_security "$BASE_URL"
    fi
fi

log_info "Deployment validation completed successfully! ✅"
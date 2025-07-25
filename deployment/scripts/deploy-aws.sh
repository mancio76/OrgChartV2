#!/bin/bash
# AWS ECS deployment script for Organigramma Web App

set -e

# Configuration
AWS_REGION="${AWS_REGION:-us-east-1}"
CLUSTER_NAME="organigramma-cluster"
SERVICE_NAME="organigramma-web-app"
TASK_FAMILY="organigramma-web-app"
ECR_REPOSITORY="organigramma-web-app"
STACK_NAME="organigramma-infrastructure"

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
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI is not installed or not in PATH"
        exit 1
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS credentials not configured or invalid"
        exit 1
    fi
    
    # Get account ID
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    log_info "AWS Account ID: $ACCOUNT_ID"
    
    log_info "Prerequisites check passed"
}

create_ecr_repository() {
    log_info "Creating ECR repository..."
    
    if aws ecr describe-repositories --repository-names "$ECR_REPOSITORY" --region "$AWS_REGION" &> /dev/null; then
        log_info "ECR repository already exists"
    else
        aws ecr create-repository \
            --repository-name "$ECR_REPOSITORY" \
            --region "$AWS_REGION" \
            --image-scanning-configuration scanOnPush=true
        log_info "ECR repository created"
    fi
    
    ECR_URI="$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY"
}

build_and_push_image() {
    log_info "Building and pushing Docker image..."
    
    # Build image
    log_info "Building Docker image..."
    docker build -t "$ECR_REPOSITORY:latest" .
    
    # Tag for ECR
    docker tag "$ECR_REPOSITORY:latest" "$ECR_URI:latest"
    docker tag "$ECR_REPOSITORY:latest" "$ECR_URI:$(date +%Y%m%d-%H%M%S)"
    
    # Login to ECR
    log_info "Logging in to ECR..."
    aws ecr get-login-password --region "$AWS_REGION" | \
        docker login --username AWS --password-stdin "$ECR_URI"
    
    # Push image
    log_info "Pushing image to ECR..."
    docker push "$ECR_URI:latest"
    docker push "$ECR_URI:$(date +%Y%m%d-%H%M%S)"
    
    log_info "Image pushed successfully"
}

deploy_infrastructure() {
    log_info "Deploying infrastructure with CloudFormation..."
    
    # Check if stack exists
    if aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$AWS_REGION" &> /dev/null; then
        log_info "Updating existing CloudFormation stack..."
        aws cloudformation update-stack \
            --stack-name "$STACK_NAME" \
            --template-body file://deployment/aws/cloudformation-template.yaml \
            --parameters \
                ParameterKey=VpcId,ParameterValue="$VPC_ID" \
                ParameterKey=PrivateSubnetIds,ParameterValue="$PRIVATE_SUBNET_IDS" \
                ParameterKey=PublicSubnetIds,ParameterValue="$PUBLIC_SUBNET_IDS" \
                ParameterKey=DomainName,ParameterValue="$DOMAIN_NAME" \
                ParameterKey=CertificateArn,ParameterValue="$CERTIFICATE_ARN" \
                ParameterKey=ImageUri,ParameterValue="$ECR_URI:latest" \
            --capabilities CAPABILITY_NAMED_IAM \
            --region "$AWS_REGION"
        
        OPERATION="update"
    else
        log_info "Creating new CloudFormation stack..."
        aws cloudformation create-stack \
            --stack-name "$STACK_NAME" \
            --template-body file://deployment/aws/cloudformation-template.yaml \
            --parameters \
                ParameterKey=VpcId,ParameterValue="$VPC_ID" \
                ParameterKey=PrivateSubnetIds,ParameterValue="$PRIVATE_SUBNET_IDS" \
                ParameterKey=PublicSubnetIds,ParameterValue="$PUBLIC_SUBNET_IDS" \
                ParameterKey=DomainName,ParameterValue="$DOMAIN_NAME" \
                ParameterKey=CertificateArn,ParameterValue="$CERTIFICATE_ARN" \
                ParameterKey=ImageUri,ParameterValue="$ECR_URI:latest" \
            --capabilities CAPABILITY_NAMED_IAM \
            --region "$AWS_REGION"
        
        OPERATION="create"
    fi
    
    # Wait for stack operation to complete
    log_info "Waiting for CloudFormation stack $OPERATION to complete..."
    aws cloudformation wait stack-${OPERATION}-complete \
        --stack-name "$STACK_NAME" \
        --region "$AWS_REGION"
    
    log_info "Infrastructure deployment completed"
}

deploy_service() {
    log_info "Deploying ECS service..."
    
    # Update task definition with new image
    TASK_DEFINITION=$(cat deployment/aws/ecs-task-definition.json | \
        sed "s|ACCOUNT_ID|$ACCOUNT_ID|g" | \
        sed "s|REGION|$AWS_REGION|g")
    
    # Register new task definition
    log_info "Registering new task definition..."
    TASK_DEFINITION_ARN=$(echo "$TASK_DEFINITION" | \
        aws ecs register-task-definition \
            --cli-input-json file:///dev/stdin \
            --region "$AWS_REGION" \
            --query 'taskDefinition.taskDefinitionArn' \
            --output text)
    
    log_info "Task definition registered: $TASK_DEFINITION_ARN"
    
    # Update service
    log_info "Updating ECS service..."
    aws ecs update-service \
        --cluster "$CLUSTER_NAME" \
        --service "$SERVICE_NAME" \
        --task-definition "$TASK_DEFINITION_ARN" \
        --region "$AWS_REGION" \
        --query 'service.serviceName' \
        --output text
    
    # Wait for service to stabilize
    log_info "Waiting for service to stabilize..."
    aws ecs wait services-stable \
        --cluster "$CLUSTER_NAME" \
        --services "$SERVICE_NAME" \
        --region "$AWS_REGION"
    
    log_info "Service deployment completed"
}

verify_deployment() {
    log_info "Verifying deployment..."
    
    # Get service status
    SERVICE_STATUS=$(aws ecs describe-services \
        --cluster "$CLUSTER_NAME" \
        --services "$SERVICE_NAME" \
        --region "$AWS_REGION" \
        --query 'services[0].status' \
        --output text)
    
    log_info "Service status: $SERVICE_STATUS"
    
    # Get running tasks
    RUNNING_TASKS=$(aws ecs describe-services \
        --cluster "$CLUSTER_NAME" \
        --services "$SERVICE_NAME" \
        --region "$AWS_REGION" \
        --query 'services[0].runningCount' \
        --output text)
    
    log_info "Running tasks: $RUNNING_TASKS"
    
    # Get load balancer DNS
    if [[ -n "$STACK_NAME" ]]; then
        LB_DNS=$(aws cloudformation describe-stacks \
            --stack-name "$STACK_NAME" \
            --region "$AWS_REGION" \
            --query 'Stacks[0].Outputs[?OutputKey==`LoadBalancerDNS`].OutputValue' \
            --output text)
        
        if [[ -n "$LB_DNS" ]]; then
            log_info "Load Balancer DNS: $LB_DNS"
            log_info "Testing health endpoint..."
            
            # Wait a bit for load balancer to be ready
            sleep 30
            
            if curl -f "http://$LB_DNS/api/health" &> /dev/null; then
                log_info "Health check passed!"
            else
                log_warn "Health check failed - service may still be starting"
            fi
        fi
    fi
}

show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help                    Show this help message"
    echo "  -r, --region REGION           AWS region (default: us-east-1)"
    echo "  --vpc-id VPC_ID              VPC ID for deployment"
    echo "  --private-subnets SUBNETS     Private subnet IDs (comma-separated)"
    echo "  --public-subnets SUBNETS      Public subnet IDs (comma-separated)"
    echo "  --domain DOMAIN               Domain name for the application"
    echo "  --certificate-arn ARN         ACM certificate ARN"
    echo "  --skip-build                  Skip Docker build and push"
    echo "  --skip-infrastructure         Skip infrastructure deployment"
    echo "  --dry-run                     Show what would be deployed"
    echo ""
    echo "Required environment variables:"
    echo "  VPC_ID                        VPC ID for deployment"
    echo "  PRIVATE_SUBNET_IDS            Private subnet IDs (comma-separated)"
    echo "  PUBLIC_SUBNET_IDS             Public subnet IDs (comma-separated)"
    echo "  DOMAIN_NAME                   Domain name for the application"
    echo "  CERTIFICATE_ARN               ACM certificate ARN"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_usage
            exit 0
            ;;
        -r|--region)
            AWS_REGION="$2"
            shift 2
            ;;
        --vpc-id)
            VPC_ID="$2"
            shift 2
            ;;
        --private-subnets)
            PRIVATE_SUBNET_IDS="$2"
            shift 2
            ;;
        --public-subnets)
            PUBLIC_SUBNET_IDS="$2"
            shift 2
            ;;
        --domain)
            DOMAIN_NAME="$2"
            shift 2
            ;;
        --certificate-arn)
            CERTIFICATE_ARN="$2"
            shift 2
            ;;
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        --skip-infrastructure)
            SKIP_INFRASTRUCTURE=true
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

# Validate required parameters
if [[ -z "$VPC_ID" || -z "$PRIVATE_SUBNET_IDS" || -z "$PUBLIC_SUBNET_IDS" || -z "$DOMAIN_NAME" || -z "$CERTIFICATE_ARN" ]]; then
    log_error "Missing required parameters. Please set VPC_ID, PRIVATE_SUBNET_IDS, PUBLIC_SUBNET_IDS, DOMAIN_NAME, and CERTIFICATE_ARN"
    show_usage
    exit 1
fi

# Main execution
log_info "Starting Organigramma Web App deployment to AWS ECS..."
log_info "Region: $AWS_REGION"
log_info "VPC ID: $VPC_ID"
log_info "Domain: $DOMAIN_NAME"

check_prerequisites
create_ecr_repository

if [[ "$DRY_RUN" == "true" ]]; then
    log_info "DRY RUN MODE - No changes will be applied"
    log_info "Would deploy to:"
    log_info "  ECR Repository: $ECR_URI"
    log_info "  ECS Cluster: $CLUSTER_NAME"
    log_info "  ECS Service: $SERVICE_NAME"
    log_info "  CloudFormation Stack: $STACK_NAME"
    exit 0
fi

if [[ "$SKIP_BUILD" != "true" ]]; then
    build_and_push_image
fi

if [[ "$SKIP_INFRASTRUCTURE" != "true" ]]; then
    deploy_infrastructure
fi

deploy_service
verify_deployment

log_info "Deployment completed successfully!"
log_info "Application should be available at: https://$DOMAIN_NAME"
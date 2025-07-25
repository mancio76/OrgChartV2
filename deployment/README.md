# Deployment Guide for Organigramma Web App

This directory contains comprehensive deployment configurations and scripts for the Organigramma Web App, supporting multiple deployment targets including Kubernetes, AWS ECS, and Docker Compose.

## Overview

The deployment infrastructure supports:

- **Production-ready ASGI server** with Gunicorn and multiple workers
- **Database backup and migration** scripts with automated scheduling
- **Cloud-native deployment** configurations for Kubernetes and AWS
- **Security-by-design** with proper secret management and HTTPS enforcement
- **Monitoring and health checks** for production environments
- **Horizontal scaling** and load balancing capabilities

## Deployment Options

### 1. Docker Compose (Development/Testing)

The simplest deployment option using Docker Compose:

```bash
# Production deployment
docker-compose --profile production up -d

# Development deployment
docker-compose --profile development up -d

# Testing
docker-compose --profile testing up
```

### 2. Kubernetes Deployment

#### Prerequisites

- Kubernetes cluster (1.19+)
- kubectl configured
- Helm 3.x (optional but recommended)
- Ingress controller (nginx recommended)
- Cert-manager for SSL certificates

#### Quick Deployment with Helm

```bash
# Deploy with Helm
./deployment/scripts/deploy-kubernetes.sh

# Custom values file
./deployment/scripts/deploy-kubernetes.sh -f my-values.yaml

# Different namespace
./deployment/scripts/deploy-kubernetes.sh -n my-namespace
```

#### Manual Deployment with kubectl

```bash
# Apply all Kubernetes manifests
kubectl apply -f deployment/kubernetes/

# Or use the script with kubectl
./deployment/scripts/deploy-kubernetes.sh --use-kubectl
```

#### Configuration

Edit `deployment/helm/organigramma/values.yaml` to customize:

- Domain name and SSL certificates
- Resource limits and requests
- Storage configuration
- Security settings
- Backup schedule

### 3. AWS ECS Fargate Deployment

#### Prerequisites

- AWS CLI configured
- Docker installed
- VPC with public and private subnets
- ACM certificate for your domain
- Route 53 hosted zone (optional)

#### Deployment

```bash
# Set required environment variables
export VPC_ID="vpc-xxxxxxxxx"
export PRIVATE_SUBNET_IDS="subnet-xxxxxxxx,subnet-yyyyyyyy"
export PUBLIC_SUBNET_IDS="subnet-aaaaaaaa,subnet-bbbbbbbb"
export DOMAIN_NAME="organigramma.yourdomain.com"
export CERTIFICATE_ARN="arn:aws:acm:region:account:certificate/xxxxxxxx"

# Deploy to AWS
./deployment/scripts/deploy-aws.sh
```

#### CloudFormation Stack

The deployment creates a complete infrastructure stack including:

- ECS Fargate cluster with auto-scaling
- Application Load Balancer with SSL termination
- EFS file system for persistent storage
- CloudWatch logging and monitoring
- Secrets Manager for sensitive configuration
- Security groups and IAM roles

## Configuration Management

### Environment Variables

All deployments support environment-based configuration:

```bash
# Application settings
APP_TITLE="Organigramma Web App"
ENVIRONMENT=production
TIMEZONE="Europe/Rome"

# Server configuration
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
WORKERS=4

# Database configuration
DATABASE_URL=sqlite:///data/orgchart.db
DATABASE_BACKUP_ENABLED=true

# Security settings
SECRET_KEY=your-secure-secret-key
ALLOWED_HOSTS=yourdomain.com
HTTPS_ONLY=true
```

### Secrets Management

#### Kubernetes

Secrets are managed through Kubernetes Secret objects:

```bash
# Create secret for production
kubectl create secret generic organigramma-secret \
  --from-literal=SECRET_KEY=your-secure-key \
  -n organigramma
```

#### AWS

Secrets are managed through AWS Secrets Manager:

```bash
# Create secret
aws secretsmanager create-secret \
  --name organigramma/secret-key \
  --secret-string '{"SECRET_KEY":"your-secure-key"}'
```

## Database Management

### Backup Configuration

Automated backups are configured through:

- **Kubernetes**: CronJob runs daily at 2 AM
- **AWS ECS**: Scheduled task with CloudWatch Events
- **Docker Compose**: Backup service container

### Manual Backup Operations

```bash
# Create backup
python scripts/backup_db.py create --compress

# List backups
python scripts/backup_db.py list

# Restore backup
python scripts/backup_db.py restore --backup-path /path/to/backup

# Cleanup old backups
python scripts/backup_db.py cleanup --retention-days 30
```

### Database Migrations

```bash
# Apply pending migrations
python scripts/migrate_db.py apply-all

# Create new migration
python scripts/migrate_db.py create --name "add_new_feature"

# Check migration status
python scripts/migrate_db.py status
```

## Monitoring and Health Checks

### Health Endpoints

The application provides health check endpoints:

- `/api/health` - Basic health check
- `/api/health/detailed` - Detailed system status

### Monitoring Integration

#### Kubernetes

- Liveness and readiness probes configured
- Prometheus metrics available (if enabled)
- Grafana dashboards for visualization

#### AWS

- CloudWatch metrics and alarms
- ECS service health monitoring
- Application Load Balancer health checks

## Security Considerations

### Production Security Checklist

- [ ] Generate secure SECRET_KEY (64+ characters)
- [ ] Configure ALLOWED_HOSTS for your domain
- [ ] Enable HTTPS_ONLY in production
- [ ] Set up proper firewall rules
- [ ] Configure security groups (AWS) or network policies (K8s)
- [ ] Enable audit logging
- [ ] Regular security updates
- [ ] Database encryption at rest
- [ ] Secrets rotation policy

### SSL/TLS Configuration

#### Kubernetes with cert-manager

```yaml
annotations:
  cert-manager.io/cluster-issuer: "letsencrypt-prod"
```

#### AWS with ACM

SSL certificates are automatically managed through AWS Certificate Manager.

## Scaling and Performance

### Horizontal Scaling

#### Kubernetes

```bash
# Scale deployment
kubectl scale deployment organigramma-app --replicas=5 -n organigramma

# Enable auto-scaling
kubectl autoscale deployment organigramma-app \
  --cpu-percent=70 \
  --min=3 \
  --max=10 \
  -n organigramma
```

#### AWS ECS

Auto-scaling is configured through CloudFormation template with target tracking policies.

### Performance Tuning

- **Gunicorn workers**: Adjust based on CPU cores (2 * cores + 1)
- **Database connections**: Configure connection pooling
- **Static files**: Use CDN for production
- **Caching**: Implement Redis for session storage

## Troubleshooting

### Common Issues

#### Deployment Failures

```bash
# Check pod logs (Kubernetes)
kubectl logs -f deployment/organigramma-app -n organigramma

# Check ECS task logs (AWS)
aws logs tail /ecs/organigramma-web-app --follow
```

#### Database Issues

```bash
# Check database connectivity
python scripts/test_database_setup.py

# Validate configuration
python scripts/validate_config.py
```

#### SSL Certificate Issues

```bash
# Check certificate status (Kubernetes)
kubectl describe certificate organigramma-tls -n organigramma

# Check ACM certificate (AWS)
aws acm describe-certificate --certificate-arn your-cert-arn
```

### Log Analysis

#### Kubernetes

```bash
# Application logs
kubectl logs -f deployment/organigramma-app -n organigramma

# Backup job logs
kubectl logs job/organigramma-backup -n organigramma
```

#### AWS

```bash
# Application logs
aws logs tail /ecs/organigramma-web-app --follow

# CloudFormation events
aws cloudformation describe-stack-events --stack-name organigramma-infrastructure
```

## Maintenance

### Regular Maintenance Tasks

1. **Security Updates**: Keep base images and dependencies updated
2. **Backup Verification**: Regularly test backup restoration
3. **Certificate Renewal**: Monitor SSL certificate expiration
4. **Log Rotation**: Ensure log files don't consume excessive disk space
5. **Performance Monitoring**: Monitor resource usage and response times

### Upgrade Procedures

#### Application Updates

```bash
# Kubernetes
helm upgrade organigramma deployment/helm/organigramma

# AWS ECS
./deployment/scripts/deploy-aws.sh --skip-infrastructure
```

#### Infrastructure Updates

```bash
# Update CloudFormation stack
aws cloudformation update-stack \
  --stack-name organigramma-infrastructure \
  --template-body file://deployment/aws/cloudformation-template.yaml
```

## Support and Documentation

For additional support:

- Check application logs for error details
- Review configuration settings
- Consult the main application documentation
- Monitor health check endpoints
- Review security best practices

## File Structure

```
deployment/
├── aws/                          # AWS ECS deployment
│   ├── cloudformation-template.yaml
│   ├── ecs-task-definition.json
│   └── ecs-service.json
├── helm/                         # Helm chart
│   └── organigramma/
│       ├── Chart.yaml
│       ├── values.yaml
│       └── templates/
├── kubernetes/                   # Raw Kubernetes manifests
│   ├── namespace.yaml
│   ├── configmap.yaml
│   ├── secret.yaml
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   └── backup-cronjob.yaml
└── scripts/                      # Deployment scripts
    ├── deploy-kubernetes.sh
    └── deploy-aws.sh
```
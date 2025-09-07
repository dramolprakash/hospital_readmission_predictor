#!/bin/bash

# Hospital Readmission Predictor - AWS Deployment Script
# Usage: ./deploy.sh [environment] [region]

set -e

# Default values
ENVIRONMENT=${1:-prod}
AWS_REGION=${2:-us-east-1}
SERVICE_NAME="readmission-predictor"
ECR_REPOSITORY="${SERVICE_NAME}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if AWS CLI is configured
check_aws_cli() {
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI not found. Please install and configure AWS CLI."
        exit 1
    fi
    
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS CLI not configured. Please run 'aws configure'."
        exit 1
    fi
    
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    print_status "AWS Account ID: $ACCOUNT_ID"
}

# Function to check if Docker is running
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker not found. Please install Docker."
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        print_error "Docker daemon not running. Please start Docker."
        exit 1
    fi
    
    print_status "Docker is running"
}

# Function to create ECR repository if it doesn't exist
create_ecr_repository() {
    print_status "Checking ECR repository..."
    
    if ! aws ecr describe-repositories --repository-names $ECR_REPOSITORY --region $AWS_REGION &> /dev/null; then
        print_status "Creating ECR repository: $ECR_REPOSITORY"
        aws ecr create-repository \
            --repository-name $ECR_REPOSITORY \
            --region $AWS_REGION \
            --image-scanning-configuration scanOnPush=true
    else
        print_status "ECR repository already exists: $ECR_REPOSITORY"
    fi
}

# Function to build and push Docker image
build_and_push_image() {
    print_status "Building Docker image..."
    
    # Build the image
    docker build -t $SERVICE_NAME:latest \
        --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
        --build-arg VCS_REF=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown") \
        .
    
    # Tag for ECR
    ECR_URI="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}"
    docker tag $SERVICE_NAME:latest $ECR_URI:latest
    docker tag $SERVICE_NAME:latest $ECR_URI:$(date +%Y%m%d-%H%M%S)
    
    # Login to ECR
    print_status "Logging in to ECR..."
    aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_URI
    
    # Push images
    print_status "Pushing Docker images to ECR..."
    docker push $ECR_URI:latest
    docker push $ECR_URI:$(date +%Y%m%d-%H%M%S)
    
    echo "ECR_IMAGE_URI=${ECR_URI}:latest" > .env.deploy
}

# Function to deploy CloudFormation stack
deploy_cloudformation() {
    print_status "Deploying CloudFormation stack..."
    
    STACK_NAME="${SERVICE_NAME}-${ENVIRONMENT}"
    
    # Check if we have VPC information
    if [ -z "$VPC_ID" ]; then
        print_warning "VPC_ID not set. Using default VPC..."
        VPC_ID=$(aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" --query 'Vpcs[0].VpcId' --output text --region $AWS_REGION)
        
        if [ "$VPC_ID" = "None" ]; then
            print_error "No default VPC found. Please set VPC_ID environment variable."
            exit 1
        fi
    fi
    
    # Get subnet IDs
    PRIVATE_SUBNETS=$(aws ec2 describe-subnets \
        --filters "Name=vpc-id,Values=$VPC_ID" "Name=tag:Name,Values=*Private*" \
        --query 'Subnets[].SubnetId' --output text --region $AWS_REGION | tr '\t' ',')
    
    PUBLIC_SUBNETS=$(aws ec2 describe-subnets \
        --filters "Name=vpc-id,Values=$VPC_ID" "Name=tag:Name,Values=*Public*" \
        --query 'Subnets[].SubnetId' --output text --region $AWS_REGION | tr '\t' ',')
    
    # If no tagged subnets found, use all subnets
    if [ -z "$PRIVATE_SUBNETS" ]; then
        ALL_SUBNETS=$(aws ec2 describe-subnets \
            --filters "Name=vpc-id,Values=$VPC_ID" \
            --query 'Subnets[].SubnetId' --output text --region $AWS_REGION | tr '\t' ',')
        PRIVATE_SUBNETS=$ALL_SUBNETS
        PUBLIC_SUBNETS=$ALL_SUBNETS
        print_warning "Using all subnets for both private and public"
    fi
    
    # Deploy the stack
    aws cloudformation deploy \
        --template-file aws/cloudformation.yml \
        --stack-name $STACK_NAME \
        --parameter-overrides \
            ServiceName=$SERVICE_NAME \
            Environment=$ENVIRONMENT \
            ImageURI="${ECR_URI}:latest" \
            VpcId=$VPC_ID \
            SubnetIds=$PRIVATE_SUBNETS \
            PublicSubnetIds=$PUBLIC_SUBNETS \
        --capabilities CAPABILITY_NAMED_IAM \
        --region $AWS_REGION \
        --tags \
            Environment=$ENVIRONMENT \
            Service=$SERVICE_NAME \
            ManagedBy=CloudFormation
    
    # Get the load balancer URL
    LB_URL=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --query 'Stacks[0].Outputs[?OutputKey==`LoadBalancerURL`].OutputValue' \
        --output text --region $AWS_REGION)
    
    print_status "Deployment completed!"
    print_status "Load Balancer URL: $LB_URL"
    
    echo "LOAD_BALANCER_URL=$LB_URL" >> .env.deploy
}

# Function to run health check
health_check() {
    if [ -f .env.deploy ]; then
        source .env.deploy
        
        if [ -n "$LOAD_BALANCER_URL" ]; then
            print_status "Running health check..."
            
            # Wait for service to be ready
            for i in {1..30}; do
                if curl -f $LOAD_BALANCER_URL/health &> /dev/null; then
                    print_status "✅ Service is healthy!"
                    curl -s $LOAD_BALANCER_URL/health | python -m json.tool
                    break
                else
                    print_warning "Waiting for service to be ready... ($i/30)"
                    sleep 10
                fi
            done
        fi
    fi
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [environment] [region]"
    echo ""
    echo "Arguments:"
    echo "  environment    Environment name (dev, staging, prod) [default: prod]"
    echo "  region         AWS region [default: us-east-1]"
    echo ""
    echo "Environment Variables:"
    echo "  VPC_ID         VPC ID for deployment (optional, will use default VPC)"
    echo ""
    echo "Examples:"
    echo "  $0                     # Deploy to prod in us-east-1"
    echo "  $0 staging us-west-2   # Deploy to staging in us-west-2"
    echo "  VPC_ID=vpc-12345 $0    # Deploy with specific VPC"
}

# Main execution
main() {
    print_status "Starting deployment for $SERVICE_NAME to $ENVIRONMENT in $AWS_REGION"
    
    # Pre-flight checks
    check_aws_cli
    check_docker
    
    # Deployment steps
    create_ecr_repository
    build_and_push_image
    deploy_cloudformation
    health_check
    
    print_status "🚀 Deployment completed successfully!"
    print_status "API Documentation: $LOAD_BALANCER_URL/docs"
    print_status "Health Check: $LOAD_BALANCER_URL/health"
    print_status "Model Info: $LOAD_BALANCER_URL/model/info"
}

# Check for help flag
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    show_usage
    exit 0
fi

# Run main function
main "$@"
# Hospital Readmission Predictor - Deployment Guide

## 🚀 Quick Deployment

### Prerequisites
- AWS CLI configured with appropriate permissions
- Docker installed and running
- Git repository cloned locally

### One-Command Deployment
```bash
./deploy.sh prod us-east-1
```

This will:
1. Create ECR repository
2. Build and push Docker image
3. Deploy CloudFormation stack
4. Run health checks

---

## 🏗️ Architecture Overview

```
Internet → ALB → ECS Fargate → FastAPI → ML Model
                    ↓
              CloudWatch Logs & Metrics
                    ↓
              Auto Scaling (2-10 instances)
```

### Components
- **Application Load Balancer (ALB)**: Routes traffic and handles SSL termination
- **ECS Fargate**: Serverless container orchestration
- **ECR**: Container image registry
- **CloudWatch**: Logging and monitoring
- **Auto Scaling**: Automatic scaling based on CPU/memory

---

## 📋 Detailed Deployment Steps

### 1. Prerequisites Setup

```bash
# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Configure AWS credentials
aws configure
```

### 2. Environment Variables (Optional)

```bash
export VPC_ID=vpc-12345678        # Specify VPC (optional)
export AWS_REGION=us-east-1       # Default region
export ENVIRONMENT=prod           # Environment name
```

### 3. Deploy to AWS

```bash
# Make deployment script executable
chmod +x deploy.sh

# Deploy to production
./deploy.sh prod us-east-1

# Deploy to staging with specific VPC
VPC_ID=vpc-12345678 ./deploy.sh staging us-west-2
```

### 4. Verify Deployment

The deployment script will automatically run health checks. You can also manually verify:

```bash
# Get the load balancer URL from the deployment output
curl -f http://your-alb-url.com/health

# Test prediction endpoint
python test_sample.py
```

---

## 🐳 Local Development

### Using Docker Compose

```bash
# Build and start services
docker-compose up --build

# With monitoring stack
docker-compose --profile monitoring up --build

# Access API
curl http://localhost:8000/health
```

### Direct Python Execution

```bash
# Install dependencies
pip install -r api/requirements.txt

# Run the API
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# Access API documentation
open http://localhost:8000/docs
```

---

## 🔧 Configuration Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | INFO |
| `MODEL_PATH` | Path to model artifacts | /app/models |
| `AWS_DEFAULT_REGION` | AWS region for services | us-east-1 |

### CloudFormation Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `ServiceName` | Name for the service | readmission-predictor |
| `Environment` | Environment (dev/staging/prod) | prod |
| `ImageURI` | ECR image URI | Auto-generated |
| `VpcId` | VPC ID for deployment | Required |
| `SubnetIds` | Private subnet IDs | Required |

---

## 📊 Monitoring & Observability

### CloudWatch Logs
- Log group: `/ecs/readmission-predictor-{environment}`
- Retention: 30 days
- Access: AWS Console → CloudWatch → Log groups

### CloudWatch Metrics
- CPU utilization
- Memory utilization
- Request count
- Error rate
- Response time

### Health Checks
- Load balancer health check: `/health`
- Container health check: Built-in
- Interval: 30 seconds

### Prometheus Monitoring (Optional)

```bash
# Start with monitoring stack
docker-compose --profile monitoring up

# Access Prometheus
open http://localhost:9090

# Access Grafana
open http://localhost:3000
# Login: admin/admin
```

---

## 🔒 Security Considerations

### Network Security
- ALB accepts traffic only on ports 80/443
- ECS tasks in private subnets
- Security groups restrict access between components

### Container Security
- Non-root user execution
- Multi-stage Docker build
- Minimal base image (python:3.9-slim)
- No secrets in image

### AWS Security
- IAM roles with least-privilege access
- VPC isolation
- CloudWatch encryption at rest

### HIPAA Compliance Notes
- Enable ALB access logs to S3
- Use HTTPS/TLS 1.2+ (configure SSL certificate)
- Enable VPC Flow Logs
- Configure CloudTrail for audit logging

---

## 🚨 Troubleshooting

### Common Issues

#### 1. Model Loading Errors
```bash
# Check logs
aws logs tail /ecs/readmission-predictor-prod --follow

# Common causes:
# - Missing model files in /models directory
# - Incorrect file paths
# - Memory issues during loading
```

#### 2. Service Won't Start
```bash
# Check ECS service events
aws ecs describe-services --cluster readmission-predictor-prod --services readmission-predictor-prod

# Check task definition
aws ecs describe-task-definition --task-definition readmission-predictor-prod
```

#### 3. Health Check Failures
```bash
# Test health endpoint directly
curl -v http://your-alb-url.com/health

# Check container logs
aws logs tail /ecs/readmission-predictor-prod --follow
```

#### 4. Deployment Failures
```bash
# Check CloudFormation events
aws cloudformation describe-stack-events --stack-name readmission-predictor-prod

# Common causes:
# - Insufficient permissions
# - VPC/subnet misconfigurations  
# - Resource limits exceeded
```

### Debug Commands

```bash
# Connect to running container
aws ecs execute-command --cluster readmission-predictor-prod \
  --task TASK_ID --container readmission-api-container \
  --command "/bin/bash" --interactive

# View service logs
aws logs tail /ecs/readmission-predictor-prod --follow

# Check service status
aws ecs describe-services --cluster readmission-predictor-prod \
  --services readmission-predictor-prod
```

---

## 📈 Scaling & Performance

### Auto Scaling Configuration
- **Target CPU**: 70%
- **Target Memory**: 80%
- **Scale Out Cooldown**: 5 minutes
- **Scale In Cooldown**: 5 minutes
- **Min Instances**: 2
- **Max Instances**: 10

### Performance Tuning

```bash
# For high-traffic scenarios, adjust:
# 1. Increase CPU/Memory resources
# 2. Increase max instances
# 3. Enable ALB sticky sessions if needed

# Update CloudFormation parameters:
aws cloudformation update-stack \
  --stack-name readmission-predictor-prod \
  --template-body file://aws/cloudformation.yml \
  --parameters ParameterKey=MaxInstances,ParameterValue=20
```

### Load Testing

```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Run load test
ab -n 1000 -c 10 -H "Content-Type: application/json" \
   -p test_patient.json \
   http://your-alb-url.com/predict
```

---

## 🔄 CI/CD Integration

### GitHub Actions Example

```yaml
name: Deploy to AWS
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v1
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: us-east-1
    - name: Deploy to AWS
      run: ./deploy.sh prod us-east-1
```

---

## 📚 API Usage Examples

### Single Prediction

```python
import requests

response = requests.post('http://your-alb-url.com/predict', json={
    "age_at_admission": 75.0,
    "gender": 2,
    "los_calculated": 5,
    "chronic_condition_count": 3,
    # ... other required fields
})

print(response.json())
```

### Batch Prediction

```python
patients = [
    {"age_at_admission": 75.0, ...},
    {"age_at_admission": 68.0, ...}
]

response = requests.post('http://your-alb-url.com/predict/batch', json=patients)
```

---

## 🛠️ Maintenance & Updates

### Model Updates
1. Replace model files in `/models` directory
2. Rebuild Docker image
3. Deploy using `./deploy.sh`

### Application Updates
1. Update code in `/api` directory
2. Test locally using `docker-compose up`
3. Deploy using `./deploy.sh`

### Rolling Updates
ECS automatically performs rolling updates with zero downtime when you deploy new versions.

---

## 📞 Support

For deployment issues:
1. Check CloudWatch logs: `/ecs/readmission-predictor-{environment}`
2. Review CloudFormation events
3. Test locally using Docker Compose
4. Run `test_sample.py` for API validation

For model questions:
- Review model metadata: `/model/info` endpoint
- Check feature requirements: `models/feature_names.txt`
- Validate input ranges using API docs: `/docs`
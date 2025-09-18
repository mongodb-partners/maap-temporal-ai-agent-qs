# Configuration Guide

## Overview

This document provides comprehensive configuration details for the AI-Powered Transaction Processing System. All configuration is managed through environment variables, with sensible defaults for PoV evaluation.

## Quick Configuration

### Minimal Required Configuration

Create a `.env` file with these essential settings:

```bash
# MongoDB Atlas (Required)
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/

# AWS Bedrock (Required for AI features)
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_REGION=us-east-1
```

### Copy from Template

```bash
cp .env.example .env
# Edit .env with your credentials
```

## Complete Configuration Reference

### MongoDB Configuration

| Variable | Description | Default | Required | Example |
|----------|-------------|---------|----------|---------|
| `MONGODB_URI` | MongoDB Atlas connection string | - | ✅ | `mongodb+srv://user:pass@cluster.mongodb.net/` |
| `MONGODB_DB_NAME` | Database name | `transaction_ai_poc` | ❌ | `production_db` |
| `MONGODB_MAX_POOL_SIZE` | Connection pool size | `50` | ❌ | `100` |
| `MONGODB_MIN_POOL_SIZE` | Minimum pool size | `10` | ❌ | `20` |
| `MONGODB_SERVER_SELECTION_TIMEOUT` | Connection timeout (ms) | `5000` | ❌ | `10000` |
| `MONGODB_SOCKET_TIMEOUT` | Socket timeout (ms) | `30000` | ❌ | `60000` |

**MongoDB Atlas Setup:**
1. Create free cluster at [mongodb.com/atlas](https://mongodb.com/atlas)
2. Configure network access (whitelist IP or 0.0.0.0/0 for PoV)
3. Create database user with read/write permissions
4. Get connection string from "Connect" → "Connect your application"

### Temporal Configuration

| Variable | Description | Default | Required | Example |
|----------|-------------|---------|----------|---------|
| `TEMPORAL_HOST` | Temporal server address | `localhost:7233` | ❌ | `temporal:7233` |
| `TEMPORAL_NAMESPACE` | Workflow namespace | `default` | ❌ | `production` |
| `TEMPORAL_TASK_QUEUE` | Task queue name | `transaction-processing-queue` | ❌ | `high-priority-queue` |
| `TEMPORAL_WORKFLOW_TIMEOUT` | Max workflow duration | `300` | ❌ | `600` |
| `TEMPORAL_ACTIVITY_TIMEOUT` | Activity timeout (seconds) | `30` | ❌ | `60` |
| `TEMPORAL_RETRY_MAX_ATTEMPTS` | Max retry attempts | `5` | ❌ | `10` |
| `TEMPORAL_RETRY_BACKOFF` | Initial backoff (seconds) | `1` | ❌ | `2` |

**Docker vs Local:**
- Local development: `TEMPORAL_HOST=localhost:7233`
- Docker deployment: `TEMPORAL_HOST=temporal:7233`

### AWS Bedrock Configuration

| Variable | Description | Default | Required | Example |
|----------|-------------|---------|----------|---------|
| `AWS_REGION` | AWS region | `us-east-1` | ✅ | `us-west-2` |
| `AWS_ACCESS_KEY_ID` | AWS access key | - | ✅ | `AKIA...` |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | - | ✅ | `secret...` |
| `AWS_SESSION_TOKEN` | Session token (if using STS) | - | ❌ | `token...` |
| `BEDROCK_MODEL_VERSION` | Claude model version | `us.anthropic.claude-opus-4-1-20250805-v1:0` | ❌ | `claude-3-sonnet` |
| `BEDROCK_EMBEDDING_MODEL` | Embedding model | `cohere.embed-english-v3` | ❌ | `cohere.embed-multilingual-v3` |
| `BEDROCK_MAX_TOKENS` | Max response tokens | `4096` | ❌ | `8192` |
| `BEDROCK_TEMPERATURE` | Model temperature | `0.3` | ❌ | `0.7` |
| `BEDROCK_TIMEOUT` | API timeout (seconds) | `30` | ❌ | `60` |
| `USE_MOCK_AI` | Use mock AI for testing | `false` | ❌ | `true` |

**AWS Bedrock Setup:**
1. Enable Bedrock in AWS Console
2. Request access to Claude and Cohere models
3. Create IAM user with Bedrock permissions
4. Generate access keys

### Application Configuration

| Variable | Description | Default | Required | Example |
|----------|-------------|---------|----------|---------|
| `APP_ENV` | Environment name | `development` | ❌ | `production` |
| `LOG_LEVEL` | Logging verbosity | `INFO` | ❌ | `DEBUG` |
| `API_BASE_URL` | API server URL | `http://localhost:8000/api` | ❌ | `https://api.example.com` |
| `API_PORT` | API server port | `8000` | ❌ | `3000` |
| `DASHBOARD_PORT` | Dashboard port | `8501` | ❌ | `8080` |
| `ENABLE_METRICS` | Enable metrics collection | `true` | ❌ | `false` |
| `METRICS_INTERVAL` | Metrics collection interval (s) | `60` | ❌ | `30` |

### Business Logic Configuration

| Variable | Description | Default | Required | Example |
|----------|-------------|---------|----------|---------|
| `CONFIDENCE_THRESHOLD_APPROVE` | Min confidence for auto-approval (%) | `85` | ❌ | `90` |
| `CONFIDENCE_THRESHOLD_ESCALATE` | Min confidence to avoid rejection (%) | `70` | ❌ | `75` |
| `AUTO_APPROVAL_LIMIT` | Max amount for auto-approval ($) | `50000` | ❌ | `100000` |
| `MANAGER_APPROVAL_THRESHOLD` | Amount requiring manager ($) | `50000` | ❌ | `75000` |
| `HIGH_RISK_AMOUNT` | High risk transaction amount ($) | `10000` | ❌ | `25000` |
| `VELOCITY_CHECK_WINDOW` | Velocity check window (seconds) | `3600` | ❌ | `1800` |
| `VELOCITY_CHECK_LIMIT` | Max transactions in window | `5` | ❌ | `3` |
| `SIMILAR_TRANSACTION_LIMIT` | Number of similar transactions to fetch | `10` | ❌ | `20` |
| `VECTOR_SIMILARITY_THRESHOLD` | Min similarity score | `0.85` | ❌ | `0.90` |

### Risk Assessment Configuration

| Variable | Description | Default | Required | Example |
|----------|-------------|---------|----------|---------|
| `HIGH_RISK_COUNTRIES` | Comma-separated list | `IR,KP,SY,CU` | ❌ | `IR,KP,SY,CU,VE` |
| `SUSPICIOUS_PATTERNS` | Regex patterns (JSON) | See below | ❌ | Custom patterns |
| `FRAUD_KEYWORDS` | Comma-separated keywords | `casino,gambling,crypto` | ❌ | `casino,lottery,bitcoin` |
| `ENABLE_SANCTIONS_CHECK` | Enable sanctions screening | `true` | ❌ | `false` |
| `ENABLE_PEP_CHECK` | Enable PEP screening | `true` | ❌ | `false` |
| `RISK_SCORE_WEIGHTS` | JSON weight configuration | See below | ❌ | Custom weights |

**Default Suspicious Patterns:**
```json
{
  "patterns": [
    ".*casino.*",
    ".*gambling.*",
    ".*lottery.*",
    ".*cryptocurrency.*"
  ]
}
```

**Default Risk Score Weights:**
```json
{
  "amount": 0.3,
  "geography": 0.25,
  "velocity": 0.2,
  "history": 0.15,
  "pattern": 0.1
}
```

### Notification Configuration

| Variable | Description | Default | Required | Example |
|----------|-------------|---------|----------|---------|
| `ENABLE_NOTIFICATIONS` | Enable email notifications | `false` | ❌ | `true` |
| `SMTP_HOST` | SMTP server host | - | ❌* | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP server port | `587` | ❌ | `465` |
| `SMTP_USERNAME` | SMTP username | - | ❌* | `user@example.com` |
| `SMTP_PASSWORD` | SMTP password | - | ❌* | `password` |
| `SMTP_FROM_EMAIL` | From email address | - | ❌* | `noreply@example.com` |
| `NOTIFICATION_RECIPIENTS` | Comma-separated emails | - | ❌ | `admin@example.com,manager@example.com` |
| `SLACK_WEBHOOK_URL` | Slack webhook for alerts | - | ❌ | `https://hooks.slack.com/...` |

*Required if `ENABLE_NOTIFICATIONS=true`

### Performance Tuning

| Variable | Description | Default | Required | Example |
|----------|-------------|---------|----------|---------|
| `WORKER_CONCURRENCY` | Concurrent workflow executions | `10` | ❌ | `20` |
| `ACTIVITY_CONCURRENCY` | Concurrent activities | `20` | ❌ | `50` |
| `BATCH_SIZE` | Batch processing size | `100` | ❌ | `500` |
| `CACHE_TTL` | Cache TTL (seconds) | `300` | ❌ | `600` |
| `ENABLE_CACHE` | Enable caching | `false` | ❌ | `true` |
| `CONNECTION_POOL_SIZE` | HTTP connection pool | `10` | ❌ | `25` |
| `REQUEST_TIMEOUT` | HTTP request timeout (s) | `30` | ❌ | `60` |

### Security Configuration

| Variable | Description | Default | Required | Example |
|----------|-------------|---------|----------|---------|
| `ENABLE_AUTH` | Enable authentication | `false` | ❌ | `true` |
| `JWT_SECRET` | JWT signing secret | - | ❌* | `your-secret-key` |
| `JWT_EXPIRY` | Token expiry (seconds) | `3600` | ❌ | `7200` |
| `API_KEY` | API key for external access | - | ❌ | `sk-...` |
| `ENABLE_RATE_LIMITING` | Enable rate limiting | `false` | ❌ | `true` |
| `RATE_LIMIT_REQUESTS` | Requests per window | `100` | ❌ | `1000` |
| `RATE_LIMIT_WINDOW` | Window size (seconds) | `60` | ❌ | `300` |
| `ALLOWED_ORIGINS` | CORS origins | `*` | ❌ | `https://example.com` |

*Required if `ENABLE_AUTH=true`

## Environment-Specific Configurations

### Development Environment

```bash
# .env.development
APP_ENV=development
LOG_LEVEL=DEBUG
TEMPORAL_HOST=localhost:7233
API_BASE_URL=http://localhost:8000/api
USE_MOCK_AI=false
ENABLE_AUTH=false
ENABLE_NOTIFICATIONS=false
```

### Docker Environment

```bash
# .env.docker
APP_ENV=docker
TEMPORAL_HOST=temporal:7233
API_BASE_URL=http://api:8000/api
MONGODB_URI=mongodb://mongo:27017/
```

### Production Environment

```bash
# .env.production
APP_ENV=production
LOG_LEVEL=WARNING
ENABLE_AUTH=true
ENABLE_RATE_LIMITING=true
ENABLE_NOTIFICATIONS=true
WORKER_CONCURRENCY=50
USE_MOCK_AI=false
```

## Configuration Validation

### Validation Script

Run the configuration validator:

```bash
python -m utils.validate_config

# Expected output:
# ✅ MongoDB connection: Valid
# ✅ AWS credentials: Valid
# ✅ Temporal connection: Valid
# ✅ Required variables: All present
# ⚠️  Optional features: Notifications disabled
```

### Health Check Endpoints

Verify configuration via health endpoints:

```bash
# API health with config status
curl http://localhost:8000/health/detailed

# Response:
{
  "status": "healthy",
  "config": {
    "mongodb": "connected",
    "temporal": "connected",
    "bedrock": "configured",
    "notifications": "disabled"
  }
}
```

## Configuration Best Practices

### 1. Security

- Never commit `.env` files to version control
- Use AWS IAM roles in production instead of keys
- Rotate secrets regularly
- Use environment-specific configurations

### 2. Performance

- Adjust pool sizes based on load testing
- Enable caching for read-heavy workloads
- Tune worker concurrency for your hardware
- Monitor and adjust timeout values

### 3. Reliability

- Set appropriate retry policies
- Configure reasonable timeouts
- Use connection pooling
- Enable circuit breakers for external services

### 4. Monitoring

- Enable detailed logging in development
- Use WARNING level in production
- Configure metrics collection
- Set up alerting thresholds

## Docker Compose Configuration

### Override Configuration

Create `docker-compose.override.yml`:

```yaml
version: '3.8'

services:
  api:
    environment:
      - LOG_LEVEL=DEBUG
      - WORKER_CONCURRENCY=5

  worker:
    environment:
      - ACTIVITY_CONCURRENCY=10
      - TEMPORAL_HOST=temporal:7233

  dashboard:
    environment:
      - API_BASE_URL=http://api:8000/api
```

### Environment File Loading

```yaml
# docker-compose.yml
services:
  api:
    env_file:
      - .env
      - .env.docker  # Docker-specific overrides
```

## Kubernetes Configuration

### ConfigMap Example

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  APP_ENV: "production"
  LOG_LEVEL: "INFO"
  TEMPORAL_HOST: "temporal-service:7233"
  API_BASE_URL: "http://api-service:8000/api"
```

### Secret Example

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
type: Opaque
stringData:
  MONGODB_URI: "mongodb+srv://user:pass@cluster.mongodb.net/"
  AWS_ACCESS_KEY_ID: "AKIA..."
  AWS_SECRET_ACCESS_KEY: "secret..."
  JWT_SECRET: "your-jwt-secret"
```

## Troubleshooting Configuration Issues

### Common Problems

| Issue | Solution |
|-------|----------|
| MongoDB connection timeout | Check IP whitelist, verify URI format |
| Bedrock access denied | Verify AWS credentials and model access |
| Temporal connection failed | Ensure Temporal is running, check host/port |
| Environment variables not loading | Check .env file location and format |
| Docker can't find services | Use service names (temporal, api) not localhost |

### Debug Configuration

Enable debug mode to see loaded configuration:

```bash
LOG_LEVEL=DEBUG python -m api.main

# Logs will show:
# INFO: Loading configuration from .env
# DEBUG: MONGODB_URI=mongodb+srv://***
# DEBUG: TEMPORAL_HOST=localhost:7233
# DEBUG: CONFIDENCE_THRESHOLD_APPROVE=85
```

## Migration from Development to Production

### Checklist

- [ ] Replace mock credentials with production values
- [ ] Enable authentication and rate limiting
- [ ] Configure production MongoDB cluster
- [ ] Set up notification endpoints
- [ ] Adjust concurrency settings for load
- [ ] Enable metrics and monitoring
- [ ] Configure backup and recovery
- [ ] Set up secret management system
- [ ] Review and adjust all thresholds
- [ ] Test failover scenarios

### Production-Ready Configuration Template

```bash
# Production Configuration Template
APP_ENV=production
LOG_LEVEL=WARNING

# Secure MongoDB with SSL
MONGODB_URI=mongodb+srv://prod-user:${MONGODB_PASSWORD}@prod-cluster.mongodb.net/?ssl=true&authSource=admin

# Use IAM roles instead of keys
AWS_REGION=us-east-1
# AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY from IAM role

# Production Temporal cluster
TEMPORAL_HOST=temporal.production.internal:7233
TEMPORAL_NAMESPACE=production
TEMPORAL_TASK_QUEUE=prod-transaction-queue

# Performance tuning
WORKER_CONCURRENCY=50
ACTIVITY_CONCURRENCY=100
CONNECTION_POOL_SIZE=25

# Security
ENABLE_AUTH=true
JWT_SECRET=${JWT_SECRET}  # From secret manager
ENABLE_RATE_LIMITING=true
ALLOWED_ORIGINS=https://app.example.com

# Monitoring
ENABLE_METRICS=true
METRICS_INTERVAL=30

# Business logic
CONFIDENCE_THRESHOLD_APPROVE=90
AUTO_APPROVAL_LIMIT=100000

# Notifications
ENABLE_NOTIFICATIONS=true
SMTP_HOST=smtp.sendgrid.net
SMTP_USERNAME=apikey
SMTP_PASSWORD=${SENDGRID_API_KEY}
```

---

For additional configuration support, consult the technical documentation or contact the development team.
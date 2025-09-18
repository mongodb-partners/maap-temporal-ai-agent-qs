# Troubleshooting Guide

## Quick Diagnostics

### System Health Check

Run this command to check all services:

```bash
# Quick health check script
python -c "
import requests
import pymongo
from temporalio.client import Client
import asyncio

print('Checking services...')

# API
try:
    r = requests.get('http://localhost:8000/health')
    print('✅ API: Running' if r.status_code == 200 else '❌ API: Not responding')
except:
    print('❌ API: Not running')

# Temporal
try:
    r = requests.get('http://localhost:8080')
    print('✅ Temporal UI: Running' if r.status_code == 200 else '❌ Temporal UI: Not responding')
except:
    print('❌ Temporal: Not running')

# Dashboard
try:
    r = requests.get('http://localhost:8501')
    print('✅ Dashboard: Running' if r.status_code == 200 else '❌ Dashboard: Not responding')
except:
    print('❌ Dashboard: Not running')
"
```

## Common Issues and Solutions

### 1. MongoDB Connection Issues

#### Problem: "ServerSelectionTimeoutError"

**Symptoms:**
```
pymongo.errors.ServerSelectionTimeoutError: cluster.mongodb.net:27017: [Errno 8] nodename nor servname provided, or not known
```

**Solutions:**

1. **Check MongoDB URI format:**
```bash
# Correct format
mongodb+srv://username:password@cluster.mongodb.net/

# Common mistakes
mongodb://username:password@cluster.mongodb.net/  # Missing +srv
mongodb+srv://username:password@cluster/          # Missing .mongodb.net
```

2. **Verify IP whitelist:**
- Go to MongoDB Atlas → Network Access
- Add your IP or use 0.0.0.0/0 for PoV
- Wait 60 seconds for changes to propagate

3. **Test connection:**
```bash
python -c "
from pymongo import MongoClient
import os
client = MongoClient(os.getenv('MONGODB_URI'))
print(client.server_info()['version'])
"
```

4. **Check network connectivity:**
```bash
# Test DNS resolution
nslookup cluster.mongodb.net

# Test network path
traceroute cluster.mongodb.net
```

#### Problem: "Authentication failed"

**Solutions:**

1. **Verify credentials:**
```bash
# Check username/password in .env
grep MONGODB_URI .env

# Test with mongosh
mongosh "mongodb+srv://cluster.mongodb.net/" --username user
```

2. **Check database user permissions:**
- Atlas → Database Access
- Ensure user has "readWrite" on database
- Verify password doesn't contain special characters or URL-encode them

### 2. Temporal Workflow Issues

#### Problem: "Worker not processing workflows"

**Symptoms:**
- Workflows stuck in "Running" state
- No activity execution in logs

**Solutions:**

1. **Check worker is running:**
```bash
# Check process
ps aux | grep run_worker

# Check logs
tail -f worker.log

# Restart worker
pkill -f run_worker
python -m temporal.run_worker
```

2. **Verify task queue name:**
```python
# In .env
TEMPORAL_TASK_QUEUE=transaction-processing-queue

# Must match in worker and workflow
```

3. **Check Temporal server:**
```bash
# Local Temporal
docker ps | grep temporal
docker logs temporal

# Restart if needed
cd docker-compose && docker-compose restart temporal
```

#### Problem: "Workflow execution failed"

**Solutions:**

1. **Check Temporal UI for errors:**
- Open http://localhost:8080
- Find workflow execution
- Check "History" tab for failures

2. **Review activity errors:**
```python
# Add debug logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

3. **Reset workflow state:**
```bash
# Terminate stuck workflow
temporal workflow terminate --workflow-id <id>

# Retry workflow
curl -X POST http://localhost:8000/api/transactions/retry/<id>
```

### 3. AWS Bedrock Issues

#### Problem: "AccessDeniedException"

**Symptoms:**
```
botocore.exceptions.ClientError: An error occurred (AccessDeniedException) when calling the InvokeModel operation
```

**Solutions:**

1. **Verify AWS credentials:**
```bash
# Check credentials
aws configure list

# Test Bedrock access
aws bedrock list-foundation-models --region us-east-1
```

2. **Check model access:**
- AWS Console → Bedrock → Model access
- Request access to Claude and Cohere
- Wait for approval (can take 1-2 minutes)

3. **Verify IAM permissions:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": "*"
    }
  ]
}
```

4. **Use mock mode for testing:**
```bash
# In .env
USE_MOCK_AI=true
```

#### Problem: "Model timeout"

**Solutions:**

1. **Increase timeout:**
```bash
# In .env
BEDROCK_TIMEOUT=60
```

2. **Reduce token limit:**
```bash
BEDROCK_MAX_TOKENS=2048
```

3. **Check AWS region:**
```bash
# Ensure using correct region
AWS_REGION=us-east-1  # or us-west-2
```

### 4. API Server Issues

#### Problem: "Port already in use"

**Symptoms:**
```
ERROR: [Errno 48] Address already in use
```

**Solutions:**

1. **Find and kill process:**
```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>

# Or use different port
uvicorn api.main:app --port 8001
```

2. **Check for multiple instances:**
```bash
ps aux | grep uvicorn
pkill -f uvicorn
```

#### Problem: "Module not found"

**Solutions:**

1. **Activate virtual environment:**
```bash
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Check Python path:**
```bash
python -c "import sys; print(sys.path)"
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### 5. Dashboard Issues

#### Problem: "Dashboard not updating"

**Solutions:**

1. **Check API connection:**
```python
# In app.py, verify API_BASE_URL
import os
print(os.getenv('API_BASE_URL', 'http://localhost:8000/api'))
```

2. **Clear Streamlit cache:**
```bash
# Stop dashboard
# Delete cache
rm -rf ~/.streamlit/cache

# Restart
streamlit run app.py
```

3. **Check browser console:**
- Open Developer Tools (F12)
- Check Console for errors
- Check Network tab for failed requests

#### Problem: "Session state errors"

**Solutions:**

1. **Refresh browser:**
- Hard refresh: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)

2. **Clear cookies:**
- Clear site data for localhost:8501

3. **Restart Streamlit:**
```bash
pkill -f streamlit
streamlit run app.py --server.runOnSave true
```

### 6. Docker Issues

#### Problem: "Cannot connect to Docker daemon"

**Solutions:**

1. **Start Docker Desktop:**
- Open Docker Desktop application
- Wait for "Docker Desktop is running"

2. **Check Docker service:**
```bash
# Mac/Windows
docker version

# Linux
sudo systemctl start docker
sudo usermod -aG docker $USER
```

#### Problem: "Container name conflicts"

**Solutions:**

1. **Remove existing containers:**
```bash
docker-compose down
docker rm -f $(docker ps -aq)
docker-compose up -d
```

2. **Clean Docker system:**
```bash
docker system prune -a
docker volume prune
```

### 7. Vector Search Issues

#### Problem: "No similar transactions found"

**Solutions:**

1. **Check vector index exists:**
```javascript
// In MongoDB Atlas
db.transactions.getIndexes()

// Should show vector index
{
  "name": "transaction_vector_index",
  "type": "vectorSearch"
}
```

2. **Rebuild vector index:**
```bash
python -m scripts.setup_mongodb --rebuild-indexes
```

3. **Verify embeddings are stored:**
```python
from database.connection import get_database
db = get_database()
doc = db.transactions.find_one({"embedding": {"$exists": True}})
print(f"Embedding dimension: {len(doc['embedding'])}")  # Should be 1024
```

4. **Check similarity threshold:**
```bash
# In .env
VECTOR_SIMILARITY_THRESHOLD=0.85  # Lower for more matches
```

### 8. Performance Issues

#### Problem: "Slow transaction processing"

**Solutions:**

1. **Check system resources:**
```bash
# CPU and memory
top
htop

# Disk I/O
iostat -x 1

# Network
netstat -i
```

2. **Optimize configuration:**
```bash
# Increase concurrency
WORKER_CONCURRENCY=20
ACTIVITY_CONCURRENCY=40

# Increase connection pools
MONGODB_MAX_POOL_SIZE=100
CONNECTION_POOL_SIZE=25
```

3. **Enable caching:**
```bash
ENABLE_CACHE=true
CACHE_TTL=600
```

4. **Profile slow queries:**
```javascript
// MongoDB profiler
db.setProfilingLevel(1, { slowms: 100 })
db.system.profile.find().limit(5).sort({ ts: -1 })
```

## Debugging Tools

### 1. Application Logs

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Tail logs
tail -f logs/app.log

# Search for errors
grep ERROR logs/app.log

# Filter by component
grep "workflow" logs/app.log
```

### 2. Temporal CLI

```bash
# List workflows
temporal workflow list

# Describe workflow
temporal workflow describe --workflow-id <id>

# Show workflow history
temporal workflow show --workflow-id <id>

# Query workflow state
temporal workflow query --workflow-id <id> --name get_status
```

### 3. MongoDB Shell

```javascript
// Connect to MongoDB
mongosh $MONGODB_URI

// Check collections
show collections

// Count documents
db.transactions.countDocuments()

// Find recent errors
db.audit_events.find({level: "ERROR"}).sort({timestamp: -1}).limit(10)

// Check indexes
db.transactions.getIndexes()
```

### 4. Python Debug Console

```python
# Interactive debugging
python -i debug_console.py

# Or in code
import pdb; pdb.set_trace()

# Or with IPython
from IPython import embed; embed()
```

## Error Messages Reference

### Critical Errors

| Error | Meaning | Action |
|-------|---------|--------|
| `ConnectionError` | Service unreachable | Check service is running |
| `AuthenticationError` | Invalid credentials | Verify username/password |
| `TimeoutError` | Operation timed out | Increase timeout, check network |
| `PermissionError` | Insufficient access | Check IAM/database permissions |
| `ValidationError` | Invalid input data | Check request format |

### Warning Messages

| Warning | Meaning | Action |
|---------|---------|--------|
| `Retry attempt X` | Transient failure | Monitor, may self-resolve |
| `Connection pool full` | High load | Increase pool size |
| `Slow query` | Performance issue | Add index, optimize query |
| `Cache miss` | Cache expired | Normal, will repopulate |

## Recovery Procedures

### 1. Full System Restart

```bash
# Stop everything
docker-compose down
pkill -f python

# Clean up
rm -rf logs/*.log
docker system prune -f

# Start fresh
docker-compose up -d
python -m scripts.setup_mongodb
./scripts/start_all.sh
```

### 2. Database Recovery

```bash
# Backup current data
mongodump --uri=$MONGODB_URI --out=backup/

# Clean database
python -c "
from database.connection import get_database
db = get_database()
for collection in db.list_collection_names():
    if collection != 'rules':
        db[collection].delete_many({})
"

# Restore or reinitialize
mongorestore --uri=$MONGODB_URI backup/
# OR
python -m scripts.setup_mongodb
```

### 3. Workflow Recovery

```bash
# List stuck workflows
temporal workflow list --query='ExecutionStatus="Running"'

# Terminate all stuck workflows
temporal workflow list --query='ExecutionStatus="Running"' \
  | grep WORKFLOW_ID \
  | awk '{print $2}' \
  | xargs -I {} temporal workflow terminate --workflow-id {}

# Restart worker
python -m temporal.run_worker
```

## Getting Help

### Diagnostic Information to Collect

When reporting issues, include:

1. **Environment details:**
```bash
python --version
pip list | grep -E "temporal|pymongo|fastapi|streamlit"
docker version
```

2. **Configuration (sanitized):**
```bash
cat .env | sed 's/=.*/=***/'
```

3. **Error logs:**
```bash
tail -n 100 logs/app.log
docker logs temporal
```

4. **System resources:**
```bash
df -h
free -m
ulimit -a
```

### Support Channels

- **GitHub Issues:** Create issue with logs


## Preventive Measures

### Daily Checks

1. Monitor disk space: `df -h`
2. Check service health: `curl http://localhost:8000/health`
3. Review error logs: `grep ERROR logs/*.log`
4. Verify backups: `ls -la backups/`

### Weekly Maintenance

1. Restart services: `docker-compose restart`
2. Clean old logs: `find logs/ -mtime +7 -delete`
3. Update indexes: `python -m scripts.optimize_indexes`
4. Review metrics: Check dashboard statistics

### Before Demo/Evaluation

1. Run full system test: `python -m scripts.advanced_scenarios`
2. Clear and reload test data: `python -m scripts.setup_mongodb --clean`
3. Verify all services: Check each service is running
4. Test critical paths manually
5. Have fallback plan (mock mode) ready

---

For issues not covered in this guide, check the [GitHub repository](https://github.com/mongodb-partners/maap-temporal-ai-agent-qs) or contact the development team.
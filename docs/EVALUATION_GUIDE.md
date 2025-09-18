# Evaluation Guide

## Executive Summary

This guide provides structured evaluation procedures for the AI-Powered Transaction Processing System PoV. Follow these scenarios to validate the system's fraud detection capabilities, performance, and business value propositions.

**Evaluation Duration:** 2-4 hours
**Success Criteria:** 8/10 scenarios passing
**Business Value Target:** Demonstrate automated decision-making and manual review reduction

## Pre-Evaluation Checklist

### System Requirements Verification

- [ ] MongoDB Atlas account configured with connection string
- [ ] AWS Bedrock credentials set with Claude and Cohere access
- [ ] Docker Desktop running with 8GB+ RAM allocated
- [ ] Python 3.11+ installed
- [ ] All three services running (Worker, API, Dashboard)
- [ ] Test data loaded via `setup_mongodb.py`

### Service Health Checks

```bash
# Verify all services are running
curl http://localhost:8000/health          # API health
curl http://localhost:8080                 # Temporal UI
curl http://localhost:8501                 # Streamlit dashboard

# Check MongoDB connection
python -c "from database.connection import get_database; print(get_database().list_collection_names())"
```

## Using the Dashboard UI

### Accessing the Dashboard

1. **Start the Streamlit Dashboard:**
   ```bash
   streamlit run app.py
   ```

2. **Open in Browser:**
   - Navigate to http://localhost:8501
   - Dashboard auto-refreshes every 30 seconds

### UI Components Overview

![Dashboard Main View](images/ui-dashboard-main.png)

**Key Sections:**
- **Scenario Launcher** (Left Sidebar) - Run pre-configured test scenarios
- **Dashboard Tab** - System metrics and overview
- **Active Workflows Tab** - Monitor processing in real-time
- **Scenario Results Tab** - View test execution outcomes
- **Human Review Tab** - Manage escalated transactions
- **Search Methods Demo Tab** - Understand hybrid search capabilities

### Running Test Scenarios via UI

1. **Select Scenario:**
   - Use dropdown in left sidebar
   - Available scenarios:
     - Fraud Ring Detection - Structuring Pattern
     - Velocity Check - Rapid Fire Transactions
     - High-Value Wire Transfer
     - Legitimate Business Transaction

2. **Execute Test:**
   - Click "Run Scenario" button
   - Watch transaction count increase
   - Monitor progress in Active Workflows tab

3. **Review Results:**
   - Switch to Scenario Results tab
   - View decision, confidence, and risk scores
   - Verify expected vs actual outcomes

### Human Review Workflow

![Human Review Interface](images/ui-human-review-detail.png)

**Review Process:**
1. Navigate to Human Review tab
2. Click on pending transaction
3. Review transaction details (left panel)
4. Read AI recommendation (right panel)
5. Make decision: Approve / Reject / Hold
6. Add review notes for audit trail

## Evaluation Scenarios

### Scenario 1: Basic Transaction Approval (Low Risk)

**Objective:** Validate automatic approval for legitimate low-risk transactions

**Test Steps:**
1. Submit a standard domestic transfer:
```bash
curl -X POST http://localhost:8000/api/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "EVAL-001",
    "amount": 2500,
    "currency": "USD",
    "type": "ach_transfer",
    "source_account": "ACC-EVAL-001",
    "destination_account": "ACC-EVAL-002",
    "description": "Payroll deposit"
  }'
```

2. Monitor in dashboard (http://localhost:8501)
3. Verify decision in Temporal UI (http://localhost:8080)

**Expected Results:**
- ✅ Transaction approved automatically
- ✅ High confidence score
- ✅ Status shows "approved" in dashboard
- ✅ Audit trail created in MongoDB

**Success Metrics:**
- Automatic processing
- Confidence-based decision
- Decision: APPROVED

### Scenario 2: Fraud Ring Detection

**Objective:** Detect coordinated fraud network through graph analysis

**Test Steps:**

**Option A: Using the UI (Recommended)**
1. Open dashboard at http://localhost:8501
2. Select "Fraud Ring Detection - Structuring Pattern" from Scenario Launcher
3. Click "Run Scenario"
4. Navigate to Active Workflows tab to see processing
5. Check Scenario Results tab for outcomes

![Scenario Results](images/ui-scenario-results.png)

**Option B: Using Command Line**
```bash
python -m scripts.advanced_scenarios
# This runs pre-configured fraud detection scenarios
```

6. Check dashboard for network visualization
7. Review AI reasoning for pattern detection

**Expected Results:**
- ✅ Multiple related transactions flagged
- ✅ Graph traversal identifies connected accounts
- ✅ Risk score > 80 for all transactions
- ✅ Automatic rejection or escalation

**Success Metrics:**
- Network depth detected: 3+ levels
- Accounts flagged: 5+
- False positive rate: < 10%

### Scenario 3: High-Value Transaction Escalation

**Objective:** Validate manager approval workflow for high-value transfers

**Test Steps:**
1. Submit transaction > $50,000:
```bash
curl -X POST http://localhost:8000/api/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "EVAL-HIGH-001",
    "amount": 75000,
    "currency": "USD",
    "type": "wire_transfer",
    "source_account": "ACC-CORP-001",
    "destination_account": "ACC-VENDOR-001",
    "description": "Q4 vendor payment"
  }'
```

2. Check "Pending Manager Approval" queue in dashboard
3. Approve via dashboard interface
4. Verify workflow completion

**Expected Results:**
- ✅ Transaction routed to manager queue
- ✅ Dashboard shows pending status
- ✅ Manual approval updates workflow
- ✅ Notification sent after decision

**Success Metrics:**
- Escalation triggered: Amount > $50,000
- Queue update time: < 2 seconds
- Manual approval processing: < 5 seconds

### Scenario 4: Velocity Check (Rapid Transactions)

**Objective:** Detect unusual transaction velocity patterns

**Test Steps:**
1. Submit 5 transactions within 60 seconds:
```bash
for i in {1..5}; do
  curl -X POST http://localhost:8000/api/transactions \
    -H "Content-Type: application/json" \
    -d "{
      \"transaction_id\": \"EVAL-VEL-$i\",
      \"amount\": 1000,
      \"currency\": \"USD\",
      \"type\": \"debit_card\",
      \"source_account\": \"ACC-VELOCITY-TEST\",
      \"destination_account\": \"ACC-MERCHANT-$i\",
      \"description\": \"Purchase $i\"
    }"
  sleep 10
done
```

2. Monitor risk scores in dashboard
3. Check for velocity rule triggers

**Expected Results:**
- ✅ Velocity rule triggered after 3rd transaction
- ✅ Risk score increases with each transaction
- ✅ Later transactions flagged for review
- ✅ AI identifies unusual pattern

**Success Metrics:**
- Velocity detection: After 3 transactions
- Risk score increase: > 20 points
- Pattern recognition: Within 60 seconds

### Scenario 5: Sanctions Screening

**Objective:** Test compliance checks for high-risk countries

**Test Steps:**
1. Submit transaction with high-risk country:
```bash
curl -X POST http://localhost:8000/api/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "EVAL-SANC-001",
    "amount": 5000,
    "currency": "USD",
    "type": "international_wire",
    "source_account": "ACC-US-001",
    "destination_account": "ACC-FOREIGN-001",
    "destination_country": "IR",
    "description": "International transfer"
  }'
```

2. Verify immediate rejection
3. Check compliance flag in decision

**Expected Results:**
- ✅ Transaction rejected immediately
- ✅ Compliance violation flagged
- ✅ Non-retryable error in Temporal
- ✅ Audit log shows rejection reason

**Success Metrics:**
- Rejection time: < 200ms
- Compliance check: 100% accuracy
- Audit completeness: All fields logged

### Scenario 6: Vector Similarity Search

**Objective:** Validate AI-powered similar transaction matching

**Test Steps:**
1. Submit a transaction with specific pattern:
```bash
curl -X POST http://localhost:8000/api/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "EVAL-VEC-001",
    "amount": 3500,
    "currency": "USD",
    "type": "ach_transfer",
    "source_account": "ACC-TEST-001",
    "destination_account": "ACC-CASINO-001",
    "description": "Gaming payment"
  }'
```

2. Check similar transactions in dashboard
3. Verify vector search results

**Expected Results:**
- ✅ 5+ similar transactions found
- ✅ Similarity score > 0.85
- ✅ Pattern matching identifies gambling
- ✅ Risk assessment includes historical context

**Success Metrics:**
- Vector search time: < 50ms
- Similarity threshold: > 0.85
- Relevant matches: > 80% accuracy

### Scenario 7: System Resilience Test

**Objective:** Validate Temporal's failure recovery mechanisms

**Test Steps:**
1. Start a long-running transaction:
```bash
curl -X POST http://localhost:8000/api/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "EVAL-RESIL-001",
    "amount": 10000,
    "currency": "USD",
    "type": "wire_transfer",
    "source_account": "ACC-TEST-RESIL",
    "destination_account": "ACC-DEST-RESIL"
  }'
```

2. Kill the worker process:
```bash
# Find and kill the worker process
ps aux | grep "run_worker"
kill -9 [PID]
```

3. Restart the worker:
```bash
python -m temporal.run_worker
```

4. Verify transaction completes

**Expected Results:**
- ✅ Workflow continues after restart
- ✅ No data loss
- ✅ Transaction completes successfully
- ✅ Retry attempts visible in Temporal UI

**Success Metrics:**
- Recovery time: < 30 seconds
- Data integrity: 100%
- Workflow completion: Guaranteed

### Scenario 8: Human Review Workflow

**Objective:** Test manual review queue and decision process

**Test Steps:**
1. Submit medium-confidence transaction:
```bash
curl -X POST http://localhost:8000/api/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "EVAL-REVIEW-001",
    "amount": 8000,
    "currency": "USD",
    "type": "wire_transfer",
    "source_account": "ACC-NEW-001",
    "destination_account": "ACC-OFFSHORE-001",
    "description": "Investment transfer"
  }'
```

2. Navigate to Review Queue in dashboard
3. Review AI analysis and recommendations
4. Submit manual decision with notes

**Expected Results:**
- ✅ Transaction appears in queue
- ✅ AI reasoning displayed clearly
- ✅ Manual decision updates workflow
- ✅ Decision stored with reviewer info

**Success Metrics:**
- Queue update: Real-time
- Decision processing: < 2 seconds
- Audit trail: Complete with reviewer notes

### Scenario 9: Batch Processing Performance

**Objective:** Test system performance under load

**Test Steps:**
1. Run batch submission script:
```bash
# Submit multiple transactions via API
for i in {1..20}; do
  curl -X POST http://localhost:8000/api/transactions \
    -H "Content-Type: application/json" \
    -d "{\"transaction_id\": \"BATCH-$i\", \"amount\": $((RANDOM % 10000)), \"type\": \"ach_transfer\", \"source_account\": \"ACC-$i\", \"destination_account\": \"ACC-DEST-$i\"}"
done
```

2. Monitor dashboard metrics
3. Check Temporal workflow list
4. Verify all transactions processed

**Expected Results:**
- ✅ 100 transactions processed
- ✅ Average latency < 500ms
- ✅ No failed workflows
- ✅ Dashboard remains responsive

**Success Metrics:**
- Throughput: > 10 TPS
- Success rate: > 99%
- P99 latency: < 1 second

### Scenario 10: Cost Analysis Validation

**Objective:** Verify cost savings calculations

**Test Steps:**
1. Process 50 mixed transactions:
```bash
# Process mixed transaction types
python -m scripts.advanced_scenarios
# Monitor metrics in dashboard at http://localhost:8501
```

2. Check cost metrics in dashboard
3. Review decision distribution
4. Calculate savings

**Expected Results:**
- ✅ Auto-approval for low-risk transactions
- ✅ Manual review for high-risk transactions
- ✅ Decision distribution visible in dashboard
- ✅ Cost optimization through automation

**Success Metrics:**
- Auto-approval: > 70%
- Cost reduction: > 75%
- ROI calculation: Positive

## Performance Benchmarks

### Expected Performance Metrics

| Metric | Target | Actual | Pass/Fail |
|--------|--------|--------|-----------|
| Metric | What to Observe | Pass/Fail |
|--------|----------------|-----------|
| API Response | Requests complete successfully | ⬜ |
| Workflow Execution | Transactions process end-to-end | ⬜ |
| Vector Search | Similar transactions found | ⬜ |
| AI Decisions | Reasoning provided for decisions | ⬜ |
| Dashboard Updates | Real-time status changes | ⬜ |
| Auto-Approval | Low-risk transactions approved | ⬜ |
| Manual Review Queue | High-risk transactions queued | ⬜ |
| Audit Trail | All decisions logged | ⬜ |

## Search Methods Demonstration

### Understanding Hybrid Search

Navigate to the "Search Methods Demo" tab to see how the system combines multiple search techniques:

![Search Methods](images/ui-search-methods.png)

**Multi-Layer Search Strategy:**
1. **Vector Similarity Search** - Semantic understanding using AI embeddings
2. **Traditional Index Search** - Fast exact and range matching
3. **Feature-Based Scoring** - Multi-dimensional similarity calculation
4. **Graph Traversal** - Network analysis for fraud rings

**Method Effectiveness Table:**
- Shows individual detection rates (85-95%)
- Combined approach achieves superior accuracy
- Demonstrates the power of hybrid search

## Dashboard Validation

### Key Dashboard Features to Test

1. **Real-time Updates**
   - Transaction status changes
   - Queue depth monitoring
   - Metric refresh rates

2. **Visualization Components**
   - Decision distribution pie chart
   - Transaction timeline
   - Risk score histogram
   - Cost savings calculator

3. **Interactive Features**
   - Human review interface
   - Transaction detail drill-down
   - Filter and search capabilities
   - Export functionality

## API Testing

### Swagger UI Testing

1. Navigate to http://localhost:8000/docs
2. Test each endpoint:
   - `POST /api/transactions` - Submit transaction
   - `GET /api/transactions/{id}` - Get status
   - `GET /api/workflows` - List workflows
   - `POST /api/reviews/{id}/decision` - Submit review

### Postman Collection

Import the provided Postman collection:
```bash
# Location: ./tests/postman/transaction-api.json
```

Test scenarios include:
- Happy path flows
- Error handling
- Edge cases
- Performance tests

## MongoDB Verification

### Data Integrity Checks

```javascript
// Connect to MongoDB and run these queries

// Check transaction count
db.transactions.countDocuments()

// Verify embeddings are stored
db.transactions.findOne({embedding: {$exists: true}})

// Check decision distribution
db.transaction_decisions.aggregate([
  {$group: {_id: "$decision", count: {$sum: 1}}}
])

// Verify audit trail
db.audit_events.find().sort({timestamp: -1}).limit(10)

// Check vector index
db.transactions.getIndexes()
```

## Success Criteria Summary

### Minimum Requirements for PoV Success

- [ ] 8/10 evaluation scenarios pass
- [ ] Transactions process successfully
- [ ] Fraud detection identifies risky patterns
- [ ] Auto-approval works for low-risk transactions
- [ ] Zero data loss during failure recovery
- [ ] Dashboard provides real-time insights
- [ ] Clear demonstration of automation benefits

### Bonus Achievements

- [ ] All 10 scenarios pass
- [ ] Consistent performance
- [ ] Effective fraud detection
- [ ] High automation rate
- [ ] Smooth batch processing

## Evaluation Report Template

```markdown
# PoV Evaluation Report

**Date:** [Date]
**Evaluator:** [Name]
**Environment:** [Dev/Test/Demo]

## Executive Summary
[Brief summary of evaluation results]

## Scenarios Tested
- Scenario 1: [Pass/Fail] - [Notes]
- Scenario 2: [Pass/Fail] - [Notes]
...

## Performance Metrics
[Table of metrics vs targets]

## Business Value Assessment
- Cost Savings: $[Amount] per transaction
- Efficiency Gain: [X]% reduction in manual review
- Accuracy Improvement: [X]% better than baseline

## Recommendations
1. [Recommendation 1]
2. [Recommendation 2]

## Next Steps
[Proposed next steps based on results]
```

## Troubleshooting During Evaluation

### Common Issues and Quick Fixes

| Issue | Quick Fix |
|-------|-----------|
| Transactions not processing | Check worker is running: `ps aux \| grep worker` |
| Dashboard not updating | Refresh browser, check API connection |
| MongoDB connection errors | Verify IP whitelist in Atlas |
| AI timeouts | Check AWS credentials and Bedrock access |
| Vector search no results | Run `python -m scripts.setup_mongodb` to rebuild index |

## Post-Evaluation Steps

1. **Export Results**
   - Dashboard metrics screenshot
   - Temporal workflow history export
   - MongoDB query results
   - Performance benchmark data

2. **Document Findings**
   - Complete evaluation report
   - List any issues encountered
   - Note improvement suggestions
   - Calculate ROI metrics

3. **Share Feedback**
   - Present to stakeholders
   - Discuss production requirements
   - Plan next phase timeline
   - Identify resource needs

## Contact Support

For evaluation assistance:
- Technical Issues: Create issue at https://github.com/mongodb-partners/maap-temporal-ai-agent-qs/issues
- Architecture Questions: Contact Solution Architecture team
- Business Value Discussion: Schedule a review meeting

---

**Ready to start?** Begin with [Scenario 1](#scenario-1-basic-transaction-approval-low-risk) and work through each test case systematically.
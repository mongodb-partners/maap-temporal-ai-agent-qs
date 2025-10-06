"""AI prompt templates for transaction analysis."""

from typing import Dict, List
from database.schemas import TransactionType
from utils.config import config

def create_transaction_analysis_prompt(
    transaction: Dict,
    similar_cases: List[Dict],
    customer_history: Dict
) -> str:
    """Create prompt for transaction analysis."""
    
    # Import Decimal128 handler
    from utils.decimal_utils import from_decimal128

    # Format similar cases
    similar_cases_text = ""
    if similar_cases:
        similar_cases_text = "SIMILAR HISTORICAL CASES:\n"
        for case in similar_cases[:5]:
            amount = float(from_decimal128(case.get('amount', 0)))
            similar_cases_text += f"- Amount: ${amount:,.2f}, "
            similar_cases_text += f"Decision: {case.get('decision', 'unknown')}, "
            similar_cases_text += f"Risk Score: {case.get('risk_score', 0):.1f}\n"
    else:
        similar_cases_text = "No similar historical cases found.\n"
    
    # Transaction type specific context
    type_context = ""
    if transaction['transaction_type'] == TransactionType.WIRE_TRANSFER.value:
        type_context = """
This is a WIRE TRANSFER - consider:
- Irreversible nature (high risk)
- Immediate settlement
- Common for high-value B2B payments
- Higher fraud risk"""
    elif transaction['transaction_type'] == TransactionType.ACH.value:
        type_context = """
This is an ACH TRANSFER - consider:
- Batch processing (lower risk)
- Reversible within 2 business days
- Common for payroll and recurring payments
- Lower individual transaction risk"""
    elif transaction['transaction_type'] == TransactionType.INTERNATIONAL.value:
        type_context = """
This is an INTERNATIONAL TRANSFER - consider:
- Cross-border regulations
- Sanctions screening requirements
- Currency conversion risks
- Enhanced due diligence requirements"""
    
    prompt = f"""You are an AI agent specialized in financial transaction fraud detection and compliance.
Analyze the following transaction and provide a decision with detailed reasoning.

TRANSACTION DETAILS:
- Transaction ID: {transaction['transaction_id']}
- Type: {transaction['transaction_type']}
- Amount: ${float(from_decimal128(transaction['amount'])):,.2f} {transaction['currency']}
- Sender: {transaction['sender'].get('name', 'Unknown')} (Country: {transaction['sender'].get('country', 'Unknown')})
- Recipient: {transaction['recipient'].get('name', 'Unknown')} (Country: {transaction['recipient'].get('country', 'Unknown')})
- Reference: {transaction.get('reference_number', 'None')}
- Risk Flags: {', '.join(transaction.get('risk_flags', ['None']))}

{type_context}

CUSTOMER HISTORY:
- Total Transactions (90 days): {customer_history.get('total_transactions', 0)}
- Average Transaction Amount: ${float(from_decimal128(customer_history.get('avg_amount', 0))):,.2f}
- Total Volume: ${float(from_decimal128(customer_history.get('total_amount', 0))):,.2f}
- Previous Risk Incidents: {customer_history.get('risk_incidents', 0)}

{similar_cases_text}

ANALYSIS REQUIREMENTS:
1. Consider transaction type specific risks
2. Evaluate against money laundering patterns (including structuring/smurfing)
3. Check for sanctions and compliance concerns
4. Assess customer behavior patterns
5. Identify any anomalies or red flags
6. CRITICAL: Check for STRUCTURING patterns:
   - Multiple transactions just under $5,000 (typical reporting threshold)
   - Transactions between $4,900-$4,999 are highly suspicious
   - Same recipient receiving multiple similar amounts
   - Pattern of avoiding reporting thresholds
7. Check for FRAUD RING indicators:
   - Related entities sending to same recipient
   - Circular transaction patterns
   - Rapid sequential transfers

Provide your response in the following JSON format:
{{
    "decision": "approve|reject|escalate",
    "confidence": <0-100>,
    "reasoning": "Detailed explanation of your decision",
    "risk_factors": ["List", "of", "identified", "risk", "factors"],
    "compliance_notes": "Any relevant compliance considerations"
}}

Decision Guidelines:
- APPROVE: High confidence (>={config.CONFIDENCE_THRESHOLD_APPROVE}%), no significant risks
- REJECT: Clear fraud or compliance violations detected (e.g., sanctioned countries, confirmed fraud)
- ESCALATE: Medium confidence (<{config.CONFIDENCE_THRESHOLD_APPROVE}%) OR suspicious patterns requiring human investigation

IMPORTANT: Transactions showing potential structuring patterns (amounts between $4,900-$4,999) should be ESCALATED for human review with medium confidence (~65%). While suspicious, these patterns require human investigation to distinguish between intentional structuring and legitimate business transactions to avoid false positives.

Be conservative - when in doubt, escalate for human review."""
    
    return prompt

def create_risk_assessment_prompt(transaction: Dict) -> str:
    """Create prompt for risk assessment."""

    # Import Decimal128 handler
    from utils.decimal_utils import from_decimal128

    return f"""Assess the risk level of this financial transaction:

Transaction Type: {transaction['transaction_type']}
Amount: ${float(from_decimal128(transaction['amount'])):,.2f}
Sender Country: {transaction['sender'].get('country', 'Unknown')}
Recipient Country: {transaction['recipient'].get('country', 'Unknown')}

Provide a risk score from 0-100 where:
- 0-25: Low risk
- 26-50: Medium risk  
- 51-75: High risk
- 76-100: Very high risk

Consider factors like transaction type, amount, countries involved, and typical fraud patterns.

Respond with a JSON object containing:
{{
    "risk_score": <0-100>,
    "risk_level": "low|medium|high|very_high",
    "key_risk_factors": ["list", "of", "factors"]
}}"""

"""Advanced test scenarios showcasing MongoDB Atlas and Temporal features."""

import asyncio
import httpx
from typing import Dict, List
from datetime import datetime, timezone
import uuid
import random
from utils.config import config

class AdvancedScenarios:
    """Advanced transaction scenarios demonstrating system capabilities."""

    def __init__(self, api_url: str = None):
        self.api_url = api_url or config.API_BASE_URL
        
    def generate_scenarios(self) -> List[Dict]:
        """Generate advanced test scenarios."""
        return [
            # Scenario 1: Pattern Recognition - Fraud Ring Detection
            {
                "name": "Fraud Ring Detection - Structuring Pattern",
                "description": "Detects potential money structuring using hybrid search (vector, traditional, graph). Multiple wire transfers just under $5000 from related entities trigger compliance alerts for human review",
                "transactions": [
                    self._create_transaction(
                        amount=4999,
                        sender_name="John Smith LLC",
                        recipient_name="Offshore Holdings Inc",
                        transaction_type="wire_transfer",
                        metadata={"ip_address": "192.168.1.100", "device_id": "device_001"}
                    ),
                    self._create_transaction(
                        amount=4998,
                        sender_name="J Smith Enterprises",
                        recipient_name="Offshore Holdings Inc",
                        transaction_type="wire_transfer",
                        metadata={"ip_address": "192.168.1.101", "device_id": "device_001"}
                    ),
                    self._create_transaction(
                        amount=4997,
                        sender_name="Smith John Co",
                        recipient_name="Offshore Holdings Inc",
                        transaction_type="wire_transfer",
                        metadata={"ip_address": "192.168.1.102", "device_id": "device_001"}
                    )
                ],
                "expected_outcome": "ESCALATE - Suspicious pattern under $5000 threshold requires human review to distinguish intentional structuring from legitimate transactions"
            },
            
            # Scenario 2: Time-Based Anomaly Detection
            {
                "name": "Velocity Check - Rapid Fire Transactions",
                "description": "Tests velocity-based fraud detection with multiple high-value ACH transfers in rapid succession. System detects unusual transaction frequency patterns",
                "transactions": [
                    self._create_transaction(
                        amount=25000,
                        sender_name="ABC Corp",
                        recipient_name="Supplier One",
                        transaction_type="ach",
                        metadata={"batch_id": "batch_001", "timestamp": datetime.now(timezone.utc).isoformat()}
                    ),
                    self._create_transaction(
                        amount=30000,
                        sender_name="ABC Corp",
                        recipient_name="Supplier Two",
                        transaction_type="ach",
                        metadata={"batch_id": "batch_001", "timestamp": datetime.now(timezone.utc).isoformat()}
                    ),
                    self._create_transaction(
                        amount=35000,
                        sender_name="ABC Corp",
                        recipient_name="Supplier Three",
                        transaction_type="ach",
                        metadata={"batch_id": "batch_001", "timestamp": datetime.now(timezone.utc).isoformat()}
                    )
                ],
                "expected_outcome": "ESCALATE - High velocity pattern exceeds thresholds but requires human assessment to confirm fraud intent"
            },
            
            # Scenario 3: Cross-Border High-Risk
            {
                "name": "High-Risk Geography - Sanctions Violation",
                "description": "Tests compliance controls with international wire transfer to a sanctioned country. Demonstrates automatic rejection for sanctions violations",
                "transactions": [
                    self._create_transaction(
                        amount=150000,
                        sender_name="Global Trade Inc",
                        recipient_name="International Partners Ltd",
                        recipient_country="RU",  # High risk
                        transaction_type="international",
                        metadata={"purpose": "equipment_purchase", "swift_code": "TEST123"}
                    )
                ],
                "expected_outcome": "REJECT - Automatic rejection for sanctions violation. Transactions to a sanctioned country trigger immediate compliance block"
            },
            
            # Scenario 4: Money Mule Detection
            {
                "name": "Money Mule Pattern Detection",
                "description": "Detects money mule patterns by analyzing receive-and-forward transactions with fee deductions. Classic money laundering behavior triggers alerts",
                "transactions": [
                    self._create_transaction(
                        amount=10000,
                        sender_name="Unknown Sender 1",
                        recipient_name="Middle Account",
                        transaction_type="wire_transfer",
                        metadata={"inbound": True}
                    ),
                    self._create_transaction(
                        amount=9500,  # Minus fee
                        sender_name="Middle Account",
                        recipient_name="Final Destination",
                        transaction_type="wire_transfer",
                        metadata={"outbound": True}
                    )
                ],
                "expected_outcome": "ESCALATE - Money mule pattern requires human review. Receive-and-forward with fee deduction is suspicious but needs investigation to confirm intent"
            },
            
            # Scenario 5: Positive Test - Low Risk Transaction
            {
                "name": "Low-Risk Domestic ACH",
                "description": "Tests automatic approval for low-risk domestic ACH between verified customers with good KYC status and established relationships",
                "transactions": [
                    self._create_transaction(
                        amount=2500,  # Low amount to avoid triggering rules
                        sender_name="Verified Business LLC",
                        recipient_name="Regular Supplier Inc",
                        transaction_type="ach",  # ACH to avoid wire transfer rules
                        metadata={
                            "customer_tier": "standard",
                            "kyc_status": "approved",
                            "relationship_years": 3,
                            "unusual_time": False
                        }
                    )
                ],
                "expected_outcome": "APPROVE - Low-risk domestic ACH automatically approved with high confidence based on verified customers and clean history"
            },
            
            # Scenario 5b: Negative Test - High Amount Wire Transfer
            {
                "name": "High Amount Wire Transfer",
                "description": "Tests mandatory review rule for wire transfers over $50,000. Business rules override AI confidence for high-value transactions",
                "transactions": [
                    self._create_transaction(
                        amount=75000,  # Above $50K threshold
                        sender_name="Fortune 500 Corp",
                        recipient_name="Trusted Vendor Inc",
                        transaction_type="wire_transfer",  # Will trigger wire transfer rule
                        metadata={
                            "customer_tier": "platinum",
                            "kyc_status": "approved",
                            "relationship_years": 10
                        }
                    )
                ],
                "expected_outcome": "ESCALATE - Wire transfer over $50K requires manual approval per business rules, regardless of AI confidence"
            },
            
            # Scenario 6: Complex Fraud Pattern with ML Detection
            {
                "name": "Advanced Fraud - Synthetic Identity",
                "description": "AI detects synthetic identity fraud: new account, VOIP phone, temp email, mail drop address, attempting large crypto transfer",
                "transactions": [
                    self._create_transaction(
                        amount=75000,
                        sender_name="NewCo Enterprises 2024",
                        recipient_name="Crypto Exchange XYZ",
                        transaction_type="wire_transfer",
                        metadata={
                            "account_age_days": 2,
                            "phone_carrier": "VOIP",
                            "email_domain": "tempmail.com",
                            "address_type": "mail_drop"
                        }
                    )
                ],
                "expected_outcome": "REJECT - Multiple synthetic identity red flags trigger automatic rejection. New account with suspicious attributes blocked"
            },
            
            # Scenario 7: Workflow Resilience Demo
            {
                "name": "Temporal Workflow Resilience",
                "description": "Demonstrates Temporal's durable execution guarantees. Even if the system experiences interruptions, the workflow state is preserved and processing completes successfully",
                "transactions": [
                    self._create_transaction(
                        amount=15000,
                        sender_name="Reliable Processing Corp",
                        recipient_name="Trusted Vendor",
                        transaction_type="ach",
                        metadata={"demonstrate_durability": True, "workflow_test": "resilience"}
                    )
                ],
                "expected_outcome": "APPROVE - Low-risk transaction processed successfully. Temporal's durable execution ensures completion even if workers restart"
            },
            
            # Scenario 8: Hybrid Search Pattern Matching
            {
                "name": "Similar Historical Pattern Match",
                "description": "Demonstrates hybrid search matching known fraud patterns using vector embeddings, traditional indexes, and behavioral correlation",
                "transactions": [
                    self._create_transaction(
                        amount=49999,  # Just under 50k limit
                        sender_name="Suspicious Corp Variant",
                        recipient_name="Known Bad Actor LLC",
                        transaction_type="wire_transfer",
                        metadata={
                            "similarity_test": True,
                            "match_previous_fraud": True
                        }
                    )
                ],
                "expected_outcome": "REJECT - High similarity to known fraud patterns detected by hybrid search triggers automatic rejection"
            }
        ]
    
    def _create_transaction(
        self,
        amount: float,
        sender_name: str,
        recipient_name: str,
        transaction_type: str = "wire_transfer",
        recipient_country: str = "US",
        metadata: Dict = None
    ) -> Dict:
        """Create a transaction object."""
        return {
            "transaction_id": f"TXN_{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:8].upper()}",
            "amount": amount,
            "currency": "USD",
            "transaction_type": transaction_type,
            "sender": {
                "name": sender_name,
                "account_number": f"ACC{random.randint(100000, 999999)}",
                "routing_number": "121000248",
                "country": "US"
            },
            "recipient": {
                "name": recipient_name,
                "account_number": f"ACC{random.randint(100000, 999999)}",
                "routing_number": "121000248",
                "country": recipient_country
            },
            "reference_number": f"REF{uuid.uuid4().hex[:12].upper()}",
            "metadata": metadata or {}
        }
    
    async def run_scenario(self, scenario: Dict) -> Dict:
        """Execute a single scenario."""
        results = {
            "scenario_name": scenario["name"],
            "description": scenario["description"],
            "expected": scenario["expected_outcome"],
            "transactions": [],
            "start_time": datetime.now(timezone.utc).isoformat(),
            "workflow_ids": []
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for transaction in scenario["transactions"]:
                try:
                    # Submit transaction
                    response = await client.post(
                        f"{self.api_url}/transaction",
                        json=transaction
                    )
                    
                    if response.status_code in [200, 201, 202]:
                        result = response.json()
                        results["transactions"].append({
                            "transaction_id": transaction["transaction_id"],
                            "status": "submitted",
                            "workflow_id": result.get("workflow_id"),
                            "amount": transaction["amount"]
                        })
                        results["workflow_ids"].append(result.get("workflow_id"))
                    else:
                        results["transactions"].append({
                            "transaction_id": transaction["transaction_id"],
                            "status": "failed",
                            "error": response.text
                        })
                        
                except Exception as e:
                    results["transactions"].append({
                        "transaction_id": transaction["transaction_id"],
                        "status": "error",
                        "error": str(e)
                    })
                
                # Small delay between transactions in a scenario
                await asyncio.sleep(0.5)
        
        results["end_time"] = datetime.now(timezone.utc).isoformat()
        return results
    
    async def check_results(self, workflow_ids: List[str]) -> List[Dict]:
        """Check the results of submitted transactions."""
        results = []
        async with httpx.AsyncClient(timeout=10.0) as client:
            for workflow_id in workflow_ids:
                # Extract transaction_id from workflow_id
                # Format: txn-processing-TXN_20250908_XXXXX
                parts = workflow_id.split("-")
                if len(parts) >= 3:
                    transaction_id = "-".join(parts[2:])
                    
                    try:
                        response = await client.get(
                            f"{self.api_url}/transaction/{transaction_id}"
                        )
                        if response.status_code == 200:
                            results.append(response.json())
                        else:
                            results.append({
                                "transaction_id": transaction_id,
                                "status": "pending"
                            })
                    except Exception as e:
                        results.append({
                            "transaction_id": transaction_id,
                            "error": str(e)
                        })
        
        return results


async def main():
    """Run all advanced scenarios."""
    print("\n" + "="*80)
    print("🚀 ADVANCED TRANSACTION PROCESSING SCENARIOS")
    print("="*80)
    print(f"Demonstrating MongoDB Atlas Vector Search + Temporal Workflows")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    scenarios = AdvancedScenarios()
    test_scenarios = scenarios.generate_scenarios()
    
    print(f"\n📋 Scenarios to execute: {len(test_scenarios)}")
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"  {i}. {scenario['name']}")
    
    print("\n" + "-"*80)
    
    all_workflow_ids = []
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n🎯 Scenario {i}/{len(test_scenarios)}: {scenario['name']}")
        print(f"   Description: {scenario['description']}")
        print(f"   Expected: {scenario['expected_outcome']}")
        print(f"   Transactions: {len(scenario['transactions'])}")
        
        result = await scenarios.run_scenario(scenario)
        all_workflow_ids.extend(result["workflow_ids"])
        
        print(f"   ✅ Submitted {len(result['transactions'])} transactions")
        for txn in result["transactions"]:
            print(f"      - {txn['transaction_id']}: {txn['status']}")
        
        # Wait between scenarios
        if i < len(test_scenarios):
            print("\n⏳ Waiting 2 seconds before next scenario...")
            await asyncio.sleep(2)
    
    # Wait for processing
    print("\n" + "="*80)
    print("⏰ Waiting 15 seconds for all workflows to complete...")
    await asyncio.sleep(15)
    
    # Check results
    print("\n📊 Checking results...")
    results = await scenarios.check_results(all_workflow_ids)
    
    print("\n" + "="*80)
    print("📈 FINAL RESULTS")
    print("="*80)
    
    approved = [r for r in results if r.get("decision") == "approve"]
    rejected = [r for r in results if r.get("decision") == "reject"]
    escalated = [r for r in results if r.get("decision") == "escalate"]
    pending = [r for r in results if r.get("status") == "pending"]
    
    print(f"\n✅ Approved: {len(approved)}")
    print(f"❌ Rejected: {len(rejected)}")
    print(f"⚠️  Escalated: {len(escalated)}")
    print(f"⏳ Still Processing: {len(pending)}")
    
    print("\n" + "="*80)
    print("✨ Scenario execution complete!")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
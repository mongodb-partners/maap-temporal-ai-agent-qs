"""Transaction processing workflow definition."""

from datetime import timedelta
from typing import Dict, Any
from temporalio import workflow
from temporalio.common import RetryPolicy
from temporalio.exceptions import ActivityError, ApplicationError

# Use unsafe imports for non-deterministic code
with workflow.unsafe.imports_passed_through():
    from temporal.shared import (
        TransactionDetails,
        ProcessingResult
    )
    from temporal.activities import TransactionActivities
    from utils.config import config

@workflow.defn
class TransactionProcessingWorkflow:
    """Workflow for AI-powered transaction processing."""
    
    def __init__(self):
        self.transaction_id = None
        self.decision = None
        self.awaiting_approval = False
        self.approved_by = None
        self.manual_override = None
    
    @workflow.run
    async def run(self, transaction_details: TransactionDetails) -> ProcessingResult:
        """
        Process a financial transaction through AI analysis and decision making.
        
        Args:
            transaction_details: Details of the transaction to process
            
        Returns:
            ProcessingResult with decision and details
        """
        self.transaction_id = transaction_details.transaction_id
        hold_id = None  # Initialize hold_id for cleanup in exception handlers
        
        # Configure retry policy
        retry_policy = RetryPolicy(
            maximum_attempts=5,
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=60),
            backoff_coefficient=2
        )
        
        activities = TransactionActivities()
        
        try:
            # Step 1: Validate funds and place hold
            funds_validation = await workflow.execute_activity(
                activities.validate_and_hold_funds,
                transaction_details,
                start_to_close_timeout=timedelta(seconds=60),
                retry_policy=retry_policy
            )
            
            hold_id = funds_validation.get("hold_id")
            
            # Step 2: Enrich transaction data
            enriched_data = await workflow.execute_activity(
                activities.enrich_transaction_data,
                transaction_details,
                start_to_close_timeout=timedelta(seconds=120),
                retry_policy=retry_policy
            )
            
            # Step 2: Perform risk assessment
            risk_assessment = await workflow.execute_activity(
                activities.perform_risk_assessment,
                enriched_data,
                start_to_close_timeout=timedelta(seconds=120),
                retry_policy=retry_policy
            )
            
            # Step 3: Find similar historical transactions
            similar_cases = await workflow.execute_activity(
                activities.find_similar_transactions,
                enriched_data,
                start_to_close_timeout=timedelta(seconds=20),
                retry_policy=retry_policy
            )

            # Step 3.5: Analyze fraud network patterns
            network_analysis = await workflow.execute_activity(
                activities.analyze_fraud_network,
                enriched_data,
                start_to_close_timeout=timedelta(seconds=120),
                retry_policy=retry_policy
            )

            # Incorporate network analysis into risk assessment
            if network_analysis.get("network_analysis_performed"):
                network_risk_score = network_analysis.get("network_risk_score", 0)
                if network_risk_score > 50:
                    risk_assessment.risk_score = min(100, risk_assessment.risk_score + network_risk_score / 4)
                    risk_assessment.risk_factors.extend(network_analysis.get("network_risk_factors", []))
                    enriched_data["network_analysis"] = network_analysis

            # Step 4: AI decision analysis
            ai_result = await workflow.execute_activity(
                activities.ai_decision_analysis,
                args=[enriched_data, risk_assessment, similar_cases],
                start_to_close_timeout=timedelta(seconds=120),
                retry_policy=retry_policy
            )
            
            # Check if transaction requires manager approval (using direct config value)
            auto_approval_limit = 50000.0  # Default value if config not available
            try:
                auto_approval_limit = config.AUTO_APPROVAL_LIMIT
            except:
                pass
            
            if (transaction_details.amount > auto_approval_limit and 
                ai_result["decision"] == "approve"):
                self.awaiting_approval = True
                workflow.logger.info(f"Transaction {self.transaction_id} requires manager approval")
                
                # Wait for approval (with timeout)
                try:
                    approval_received = await workflow.wait_condition(
                        lambda: not self.awaiting_approval,
                        timeout=timedelta(hours=24)
                    )
                except TimeoutError:
                    approval_received = False
                
                if not approval_received:
                    ai_result["decision"] = "escalate"
                    ai_result["reasoning"] += " | Approval timeout - escalated to human review"
            
            # Check for manual override
            if self.manual_override:
                ai_result["decision"] = self.manual_override["decision"]
                ai_result["reasoning"] += f" | Manual override by {self.manual_override['user']}"
            
            # Determine confidence threshold (with defaults)
            confidence_threshold = 85.0  # Default
            try:
                confidence_threshold = config.CONFIDENCE_THRESHOLD_APPROVE
            except:
                pass
            
            # Step 5: Always store decision first
            decision_id = await workflow.execute_activity(
                activities.store_decision,
                args=[
                    transaction_details.transaction_id,
                    ai_result,
                    workflow.info().workflow_id,
                    workflow.info().run_id
                ],
                start_to_close_timeout=timedelta(seconds=60),
                retry_policy=retry_policy
            )
            
            # Step 6: Queue for review if needed
            if ai_result["confidence"] < confidence_threshold and ai_result["decision"] != "reject":
                # Low confidence - also queue for human review
                review_id = await workflow.execute_activity(
                    activities.queue_for_human_review,
                    args=[transaction_details.transaction_id, ai_result],
                    start_to_close_timeout=timedelta(seconds=60),
                    retry_policy=retry_policy
                )
                
                result = ProcessingResult(
                    success=True,
                    decision="escalate",
                    confidence=ai_result["confidence"],
                    message=f"Transaction escalated for human review (confidence: {ai_result['confidence']:.1f}%)",
                    decision_id=decision_id,  # Use decision_id not review_id
                    risk_score=risk_assessment.risk_score,
                    processing_time_ms=ai_result.get("processing_time_ms", 0),
                    workflow_id=workflow.info().workflow_id
                )
            else:
                # High confidence or reject - use AI decision
                
                # Step 6a: Execute fund transfer if approved
                if ai_result["decision"] == "approve":
                    transfer_success = await workflow.execute_activity(
                        activities.execute_fund_transfer,
                        args=[
                            transaction_details.transaction_id,
                            transaction_details.sender.get("account_number"),
                            transaction_details.recipient.get("account_number"),
                            transaction_details.amount,
                            hold_id
                        ],
                        start_to_close_timeout=timedelta(seconds=120),
                        retry_policy=retry_policy
                    )
                    
                    if not transfer_success:
                        ai_result["decision"] = "reject"
                        ai_result["reasoning"] += " | Fund transfer failed"
                else:
                    # Release hold if not approved - use cleanup activity
                    try:
                        await workflow.execute_activity(
                            activities.cleanup_hold,
                            hold_id,
                            start_to_close_timeout=timedelta(seconds=60),
                            retry_policy=retry_policy
                        )
                    except:
                        workflow.logger.warning(f"Failed to cleanup hold {hold_id}")
                
                result = ProcessingResult(
                    success=True,
                    decision=ai_result["decision"],
                    confidence=ai_result["confidence"],
                    message=f"Transaction {ai_result['decision']} with {ai_result['confidence']:.1f}% confidence",
                    decision_id=decision_id,
                    risk_score=risk_assessment.risk_score,
                    processing_time_ms=ai_result.get("processing_time_ms", 0),
                    workflow_id=workflow.info().workflow_id
                )
            
            # Step 7: Send notification
            await workflow.execute_activity(
                activities.send_notification,
                args=[
                    transaction_details.transaction_id,
                    result.decision,
                    result.message
                ],
                start_to_close_timeout=timedelta(seconds=60),
                retry_policy=RetryPolicy(maximum_attempts=3)
            )
            
            self.decision = result
            return result

        except ApplicationError as e:
            # Check if it's an InsufficientFundsError wrapped in ApplicationError
            if "InsufficientFundsError" in str(e) or "Insufficient funds" in str(e):
                workflow.logger.error(f"Insufficient funds: {e}")
                
                result = ProcessingResult(
                    success=False,
                    decision="reject",
                    confidence=100,
                    message=f"Transaction rejected: {str(e)}",
                    risk_score=100
                )
                
                # Store rejection due to insufficient funds
                await workflow.execute_activity(
                    activities.store_decision,
                    args=[
                        transaction_details.transaction_id,
                        {
                            "decision": "reject",
                            "confidence": 100,
                            "reasoning": f"Insufficient funds: {str(e)}",
                            "risk_factors": ["insufficient_funds"]
                        },
                        workflow.info().workflow_id,
                        workflow.info().run_id
                    ],
                    start_to_close_timeout=timedelta(seconds=60),
                    retry_policy=retry_policy
                )
                
                self.decision = result
                return result
            else:
                raise
            
        except ActivityError as e:
            workflow.logger.error(f"Activity error in transaction processing: {e}")
            
            # Cleanup hold if exists
            if hold_id:
                try:
                    await workflow.execute_activity(
                        activities.cleanup_hold,
                        hold_id,
                        start_to_close_timeout=timedelta(seconds=5),
                        retry_policy=RetryPolicy(maximum_attempts=3)
                    )
                except:
                    pass  # Best effort cleanup
            
            raise ApplicationError(
                f"Failed to process transaction: {str(e)}",
                non_retryable=True
            )
        except Exception as e:
            workflow.logger.error(f"Unexpected error: {e}")
            
            # Cleanup hold if exists
            if hold_id:
                try:
                    await workflow.execute_activity(
                        activities.cleanup_hold,
                        hold_id,
                        start_to_close_timeout=timedelta(seconds=5),
                        retry_policy=RetryPolicy(maximum_attempts=3)
                    )
                except:
                    pass  # Best effort cleanup
            
            raise ApplicationError(
                f"System error during transaction processing: {str(e)}",
                non_retryable=True
            )
    
    @workflow.signal
    def approve(self, manager_name: str) -> None:
        """Approve a transaction awaiting manager approval."""
        self.approved_by = manager_name
        self.awaiting_approval = False
        workflow.logger.info(f"Transaction approved by {manager_name}")
    
    @workflow.signal
    def override_decision(self, decision: str, user: str, reason: str) -> None:
        """Override the AI decision manually."""
        self.manual_override = {
            "decision": decision,
            "user": user,
            "reason": reason
        }
        workflow.logger.info(f"Decision overridden to {decision} by {user}")
    
    @workflow.query
    def get_status(self) -> Dict[str, Any]:
        """Get the current workflow status."""
        status_dict = {
            "transaction_id": self.transaction_id,
            "awaiting_approval": self.awaiting_approval,
            "approved_by": self.approved_by,
            "decision": None
        }
        
        if self.decision:
            # Convert ProcessingResult to dict safely
            try:
                status_dict["decision"] = {
                    "success": self.decision.success,
                    "decision": self.decision.decision,
                    "confidence": self.decision.confidence,
                    "message": self.decision.message,
                    "decision_id": self.decision.decision_id,
                    "risk_score": self.decision.risk_score,
                    "processing_time_ms": self.decision.processing_time_ms,
                    "workflow_id": self.decision.workflow_id
                }
            except:
                status_dict["decision"] = str(self.decision)
        
        return status_dict
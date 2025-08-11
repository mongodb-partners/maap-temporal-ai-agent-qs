"""Money transfer workflow definition."""

from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy
from temporalio.exceptions import ActivityError, ApplicationError
from shared import PaymentDetails
from activities import BankingActivities

@workflow.defn
class MoneyTransfer:
    """Workflow for transferring money between accounts."""

    def __init__(self):
        # identifies whether the transfer requires manager approval
        self.awaiting_approval = False

        # name of the manager who approved the transfer
        self.approved_by = None

    @workflow.run
    async def run(self, payment_details: PaymentDetails) -> str:
        """
        Transfers money between a source account and a target account,
        as specified by the input parameter.
        
        Args:
            payment_details: Details of the payment to process
            
        Returns:
            Success message with transaction IDs
            
        Raises:
            InsufficientFundsError: If source account lacks sufficient funds
            Exception: For other unrecoverable errors
        """
        # Configure retry policy for activities
        retry_policy = RetryPolicy(
            maximum_interval=timedelta(seconds=5),
            non_retryable_error_types=[
                "InvalidAccountError",
                "InsufficientFundsError"
            ]
        )

        activities = BankingActivities()

        # Transfers of $500 or more require manager approval
        if payment_details.amount > 50000:
            self.awaiting_approval = True

        # If approval is required, this blocks until it has been approved
        await workflow.wait_condition(lambda: not self.awaiting_approval)

        # Withdraw money from source account
        withdraw_transaction_id = await workflow.execute_activity(
            activities.withdraw,
            payment_details,
            start_to_close_timeout=timedelta(minutes=1),
            retry_policy=retry_policy
        )
        
        # Deposit money to target account
        try:
            deposit_transaction_id = await workflow.execute_activity(
                activities.deposit,
                payment_details,
                start_to_close_timeout=timedelta(minutes=1),
                retry_policy=retry_policy
            )

            # Deposit was successful, return a confirmation
            return (
                f"Transfer complete (transaction IDs: "
                f"{withdraw_transaction_id}, {deposit_transaction_id})"
            )
        except ActivityError as deposit_err:
            # Deposit failed, refund money to source acccount to compensate
            workflow.logger.warning(f"Deposit failed: {deposit_err}. Initiating refund.")

            try:
                refund_transaction_id = await workflow.execute_activity(
                    activities.refund,
                    payment_details,
                    start_to_close_timeout=timedelta(minutes=1),
                    retry_policy=retry_policy
                )

                # Refund was successful, return a confirmation
                return (
                    f"Deposit failed: {deposit_err}. "
                    f"Money returned to {payment_details.source_account} "
                    f"(refund transaction ID: {refund_transaction_id})"
                )
            except ActivityError as refund_err:
                workflow.logger.warning(
                    f"Refund also failed: {refund_err}. This will require intervention."
                )

                # Raise a non-retryable error, since this siutation will require manual
                # intervention outside the system to resolve
                raise ApplicationError(
                    f"Refund failed: {refund_err}, manual intervention required",
                    type="RefundFailedError",
                    non_retryable=True,
                )

    @workflow.signal
    def approve(self, manager_name: str) -> None:
        """
        Approves a transaction that is blocked awaiting manual approval
        by a manager.
        
        Args:
            manager_name: Name of the manager approving the transaction
        """
        self.approved_by = manager_name
        self.awaiting_approval = False

    @workflow.query
    def awaiting_approval(self) -> bool:
        """
        Allows the caller to determine if this Workflow Execution is
        blocked as it awaits manager approval.
        
        Returns:
            True if it's blocked awaiting approval, or False otherwise
        """
        return self.awaiting_approval

    @workflow.query
    def approved_by(self) -> str:
        """
        Allows the caller to determine who approved the transaction.
        
        Returns:
            The name previously supplied to the approve function.
        """
        return self.approved_by

"""Banking activities for the money transfer workflow."""

import random
import string
from typing import Optional
from temporalio import activity
from shared import PaymentDetails, InvalidAccountError, InsufficientFundsError

class BankingActivities:
    """Banking activities that simulate banking operations."""

    @activity.defn
    async def withdraw(self, payment_details: PaymentDetails) -> str:
        """
        Withdraw money from the source account.
        
        Args:
            payment_details: Payment details containing source account and amount
            
        Returns:
            Transaction ID for the withdrawal
            
        Raises:
            InsufficientFundsError: If withdrawal amount exceeds $5000
        """
        # Simulate insufficient funds error for amounts over $5000
        if payment_details.amount > 500000:  # $5000 in cents
            raise InsufficientFundsError(
                f"Insufficient funds in account {payment_details.source_account}. "
                f"Cannot withdraw ${payment_details.amount / 100:.2f}"
            )
        
        # Generate a mock transaction ID
        transaction_id = self._generate_transaction_id("w")
        
        activity.logger.info(
            f"Withdrew ${payment_details.amount / 100:.2f} from account "
            f"{payment_details.source_account}. Transaction ID: {transaction_id}"
        )
        
        return transaction_id

    @activity.defn
    async def deposit(self, payment_details: PaymentDetails) -> str:
        """
        Deposit money into the target account.
        
        Args:
            payment_details: Payment details containing target account and amount
            
        Returns:
            Transaction ID for the deposit
            
        Raises:
            InvalidAccountError: If target account is B5555
        """
        # Simulate invalid account error for account B5555
        if payment_details.target_account == "B5555":
            raise InvalidAccountError(
                f"Invalid account: {payment_details.target_account}"
            )
        
        # Generate a mock transaction ID
        transaction_id = self._generate_transaction_id("d")
        
        activity.logger.info(
            f"Deposited ${payment_details.amount / 100:.2f} into account "
            f"{payment_details.target_account}. Transaction ID: {transaction_id}"
        )
        
        return transaction_id

    @activity.defn
    async def refund(self, payment_details: PaymentDetails) -> str:
        """
        Refund money back to the source account (compensation activity).
        
        Args:
            payment_details: Payment details containing source account and amount
            
        Returns:
            Transaction ID for the refund
        """
        # Generate a mock transaction ID
        transaction_id = self._generate_transaction_id("r")
        
        activity.logger.info(
            f"Refunded ${payment_details.amount / 100:.2f} to account "
            f"{payment_details.source_account}. Transaction ID: {transaction_id}"
        )
        return transaction_id

    def _generate_transaction_id(self, prefix: str) -> str:
        """Generate a random transaction ID with the given prefix."""
        suffix = ''.join(random.choices(string.digits, k=10))
        return f"{prefix}{suffix}"

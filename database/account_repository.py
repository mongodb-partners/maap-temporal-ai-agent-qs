"""Account repository with ACID transaction support."""

from typing import Dict, Optional, List, Any, Tuple
from datetime import datetime, timezone, timedelta
from pymongo import MongoClient, errors
from pymongo.client_session import ClientSession
from database.account_schemas import Account, BalanceHold, BalanceUpdate, TransactionJournal
from database.connection import db, get_sync_db
from utils.config import config
from utils.logger import transaction_logger, logger
import uuid

class InsufficientFundsError(Exception):
    """Raised when account has insufficient funds."""
    pass

class AccountNotFoundError(Exception):
    """Raised when account is not found."""
    pass

class AccountRepository:
    """Repository for account operations with ACID support."""
    
    @staticmethod
    def get_or_create_account_sync(account_number: str, customer_name: str, initial_balance: float = 10000.0) -> Account:
        """Get or create an account."""
        db_sync = get_sync_db()
        
        existing = db_sync[config.ACCOUNTS_COLLECTION].find_one({"account_number": account_number})
        if existing:
            return Account(**existing)
        
        # Create new account with initial balance
        account = Account(
            account_number=account_number,
            customer_id=f"CUST_{uuid.uuid4().hex[:8].upper()}",
            customer_name=customer_name,
            balance=initial_balance,
            available_balance=initial_balance,
            kyc_verified=True  # For demo purposes
        )
        
        db_sync[config.ACCOUNTS_COLLECTION].insert_one(account.model_dump())
        logger.info(f"Created new account {account_number} with balance ${initial_balance:.2f}")
        
        return account
    
    @staticmethod
    def check_sufficient_funds_sync(account_number: str, amount: float) -> Tuple[bool, float]:
        """Check if account has sufficient funds."""
        db_sync = get_sync_db()
        
        account = db_sync[config.ACCOUNTS_COLLECTION].find_one({"account_number": account_number})
        if not account:
            raise AccountNotFoundError(f"Account {account_number} not found")
        
        available = account.get("available_balance", 0)
        overdraft_limit = account.get("overdraft_limit", 0)
        
        # Check if amount can be covered including overdraft
        has_funds = available + overdraft_limit >= amount
        
        if not has_funds:
            transaction_logger.log_insufficient_funds(
                account_number=account_number,
                transaction_id="CHECK",
                requested_amount=amount,
                available_balance=available
            )
        
        return has_funds, available
    
    @staticmethod
    def execute_transfer_with_acid(
        sender_account: str,
        recipient_account: str,
        amount: float,
        transaction_id: str,
        description: str = "Transfer"
    ) -> bool:
        """Execute a transfer between accounts using MongoDB ACID transactions."""
        db_sync = get_sync_db()
        client = db_sync.client
        
        session_id = f"SESSION_{uuid.uuid4().hex[:8].upper()}"
        
        transaction_logger.log_acid_transaction(
            session_id=session_id,
            operation="TRANSFER_START",
            status="INITIATED",
            details={
                "from": sender_account,
                "to": recipient_account,
                "amount": amount,
                "transaction_id": transaction_id
            }
        )
        
        # Start a client session for ACID transaction
        with client.start_session() as session:
            try:
                # Define the transaction
                def callback(session):
                    accounts_collection = db_sync[config.ACCOUNTS_COLLECTION]
                    journal_collection = db_sync[config.JOURNAL_COLLECTION]
                    balance_updates_collection = db_sync[config.BALANCE_UPDATES_COLLECTION]
                    
                    # 1. Get sender account with lock
                    sender = accounts_collection.find_one(
                        {"account_number": sender_account},
                        session=session
                    )
                    if not sender:
                        raise AccountNotFoundError(f"Sender account {sender_account} not found")
                    
                    # 2. Check sufficient funds
                    if sender["available_balance"] < amount:
                        raise InsufficientFundsError(
                            f"Insufficient funds: Available ${sender['available_balance']:.2f}, "
                            f"Requested ${amount:.2f}"
                        )
                    
                    # 3. Get recipient account
                    recipient = accounts_collection.find_one(
                        {"account_number": recipient_account},
                        session=session
                    )
                    if not recipient:
                        raise AccountNotFoundError(f"Recipient account {recipient_account} not found")
                    
                    # 4. Update sender balance (debit)
                    new_sender_balance = sender["balance"] - amount
                    new_sender_available = sender["available_balance"] - amount
                    
                    accounts_collection.update_one(
                        {"account_number": sender_account},
                        {
                            "$set": {
                                "balance": new_sender_balance,
                                "available_balance": new_sender_available,
                                "last_transaction_at": datetime.now(timezone.utc),
                                "updated_at": datetime.now(timezone.utc)
                            },
                            "$inc": {
                                "transaction_count": 1,
                                "total_withdrawals": amount
                            }
                        },
                        session=session
                    )
                    
                    # Log sender balance update
                    sender_update = BalanceUpdate(
                        account_number=sender_account,
                        transaction_id=transaction_id,
                        operation="debit",
                        amount=amount,
                        previous_balance=sender["balance"],
                        new_balance=new_sender_balance,
                        session_id=session_id
                    )
                    balance_updates_collection.insert_one(
                        sender_update.model_dump(),
                        session=session
                    )
                    
                    # 5. Update recipient balance (credit)
                    new_recipient_balance = recipient["balance"] + amount
                    new_recipient_available = recipient["available_balance"] + amount
                    
                    accounts_collection.update_one(
                        {"account_number": recipient_account},
                        {
                            "$set": {
                                "balance": new_recipient_balance,
                                "available_balance": new_recipient_available,
                                "last_transaction_at": datetime.now(timezone.utc),
                                "updated_at": datetime.now(timezone.utc)
                            },
                            "$inc": {
                                "transaction_count": 1,
                                "total_deposits": amount
                            }
                        },
                        session=session
                    )
                    
                    # Log recipient balance update
                    recipient_update = BalanceUpdate(
                        account_number=recipient_account,
                        transaction_id=transaction_id,
                        operation="credit",
                        amount=amount,
                        previous_balance=recipient["balance"],
                        new_balance=new_recipient_balance,
                        session_id=session_id
                    )
                    balance_updates_collection.insert_one(
                        recipient_update.model_dump(),
                        session=session
                    )
                    
                    # 6. Create journal entry for double-entry bookkeeping
                    journal_entry = TransactionJournal(
                        transaction_id=transaction_id,
                        debit_account=sender_account,
                        debit_amount=amount,
                        credit_account=recipient_account,
                        credit_amount=amount,
                        description=description,
                        status="completed",
                        session_id=session_id,
                        committed=True
                    )
                    journal_collection.insert_one(
                        journal_entry.model_dump(),
                        session=session
                    )
                    
                    # Log balance updates
                    transaction_logger.log_balance_update(
                        account_number=sender_account,
                        transaction_id=transaction_id,
                        old_balance=sender["balance"],
                        new_balance=new_sender_balance,
                        amount=amount,
                        operation="DEBIT"
                    )
                    
                    transaction_logger.log_balance_update(
                        account_number=recipient_account,
                        transaction_id=transaction_id,
                        old_balance=recipient["balance"],
                        new_balance=new_recipient_balance,
                        amount=amount,
                        operation="CREDIT"
                    )
                    
                    return True
                
                # Execute the transaction with retries
                result = session.with_transaction(
                    callback,
                    read_preference=None,
                    write_concern=None,
                    max_commit_time_ms=10000
                )
                
                transaction_logger.log_acid_transaction(
                    session_id=session_id,
                    operation="TRANSFER_COMPLETE",
                    status="SUCCESS",
                    details={
                        "transaction_id": transaction_id,
                        "committed": True
                    }
                )
                
                return result
                
            except InsufficientFundsError as e:
                transaction_logger.log_acid_transaction(
                    session_id=session_id,
                    operation="TRANSFER_FAILED",
                    status="INSUFFICIENT_FUNDS",
                    details={
                        "transaction_id": transaction_id,
                        "error": str(e)
                    }
                )
                raise
                
            except Exception as e:
                transaction_logger.log_acid_transaction(
                    session_id=session_id,
                    operation="TRANSFER_FAILED",
                    status="ERROR",
                    details={
                        "transaction_id": transaction_id,
                        "error": str(e)
                    }
                )
                logger.error(f"ACID transaction failed: {e}")
                raise
    
    @staticmethod
    def place_hold_sync(
        account_number: str,
        amount: float,
        transaction_id: str,
        reason: str = "Transaction processing",
        duration_hours: int = 24
    ) -> str:
        """Place a hold on account funds."""
        db_sync = get_sync_db()
        
        # Check available balance
        account = db_sync[config.ACCOUNTS_COLLECTION].find_one({"account_number": account_number})
        if not account:
            raise AccountNotFoundError(f"Account {account_number} not found")
        
        if account["available_balance"] < amount:
            raise InsufficientFundsError(f"Insufficient available balance for hold")
        
        # Create hold
        hold = BalanceHold(
            account_number=account_number,
            transaction_id=transaction_id,
            amount=amount,
            reason=reason,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=duration_hours)
        )
        
        # Update available balance
        db_sync[config.ACCOUNTS_COLLECTION].update_one(
            {"account_number": account_number},
            {
                "$inc": {"available_balance": -amount},
                "$push": {"holds": hold.model_dump()}
            }
        )
        
        # Store hold record
        db_sync[config.HOLDS_COLLECTION].insert_one(hold.model_dump())
        
        logger.info(f"Placed hold {hold.hold_id} for ${amount:.2f} on account {account_number}")
        
        return hold.hold_id
    
    @staticmethod
    def release_hold_sync(hold_id: str) -> bool:
        """Release a hold on account funds."""
        db_sync = get_sync_db()
        
        # Find the hold
        hold = db_sync[config.HOLDS_COLLECTION].find_one({"hold_id": hold_id})
        if not hold or hold.get("released"):
            return False
        
        # Release the hold
        db_sync[config.HOLDS_COLLECTION].update_one(
            {"hold_id": hold_id},
            {
                "$set": {
                    "released": True,
                    "released_at": datetime.now(timezone.utc)
                }
            }
        )
        
        # Update account available balance
        db_sync[config.ACCOUNTS_COLLECTION].update_one(
            {"account_number": hold["account_number"]},
            {
                "$inc": {"available_balance": hold["amount"]},
                "$pull": {"holds": {"hold_id": hold_id}}
            }
        )
        
        logger.info(f"Released hold {hold_id} for ${hold['amount']:.2f} on account {hold['account_number']}")
        
        return True
    
    @staticmethod
    def get_account_balance_sync(account_number: str) -> Dict[str, float]:
        """Get account balances."""
        db_sync = get_sync_db()
        
        account = db_sync[config.ACCOUNTS_COLLECTION].find_one(
            {"account_number": account_number},
            {"balance": 1, "available_balance": 1, "overdraft_limit": 1}
        )
        
        if not account:
            raise AccountNotFoundError(f"Account {account_number} not found")
        
        return {
            "balance": account.get("balance", 0),
            "available_balance": account.get("available_balance", 0),
            "overdraft_limit": account.get("overdraft_limit", 0)
        }
    
    @staticmethod
    def get_account_sync(account_number: str) -> Account:
        """Get account details including holds."""
        db_sync = get_sync_db()
        account_doc = db_sync[config.ACCOUNTS_COLLECTION].find_one(
            {"account_number": account_number}
        )
        
        if not account_doc:
            raise AccountNotFoundError(f"Account {account_number} not found")
        
        # Convert document to Account model
        return Account(**account_doc)
    
    @staticmethod
    def get_transaction_history_sync(account_number: str, limit: int = 10) -> List[Dict]:
        """Get transaction history for an account."""
        db_sync = get_sync_db()
        
        # Get balance updates
        updates = list(db_sync[config.BALANCE_UPDATES_COLLECTION].find(
            {"account_number": account_number}
        ).sort("timestamp", -1).limit(limit))
        
        return updates
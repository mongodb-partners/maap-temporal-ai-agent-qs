"""Risk assessment engine for transactions."""

from typing import Dict, List, Any
from database.schemas import TransactionType, RiskLevel
from utils.config import config

class RiskEngine:
    """Engine for calculating transaction risk scores."""
    
    @staticmethod
    def calculate_base_risk(transaction_type: TransactionType, amount: float) -> float:
        """Calculate base risk score based on transaction type and amount."""
        
        # Base risk by transaction type
        type_risk = {
            TransactionType.ACH: 10,
            TransactionType.WIRE_TRANSFER: 30,
            TransactionType.INTERNATIONAL: 50
        }
        
        base_score = type_risk.get(transaction_type, 25)
        
        # Adjust for amount
        if amount > 100000:
            base_score += 30
        elif amount > 50000:
            base_score += 20
        elif amount > 10000:
            base_score += 10
        
        return min(base_score, 100)
    
    @staticmethod
    def apply_risk_factors(base_score: float, risk_flags: List[str]) -> float:
        """Apply risk factor adjustments to base score."""
        
        risk_adjustments = {
            "high_risk_country": 25,
            "new_recipient": 15,
            "unusual_time": 10,
            "structuring": 30,
            "rapid_movement": 20,
            "round_amount_below_threshold": 15
        }
        
        adjusted_score = base_score
        
        for flag in risk_flags:
            if flag in risk_adjustments:
                adjusted_score += risk_adjustments[flag]
        
        return min(adjusted_score, 100)
    
    @staticmethod
    def determine_risk_level(risk_score: float) -> RiskLevel:
        """Determine risk level from score."""
        if risk_score <= 25:
            return RiskLevel.LOW
        elif risk_score <= 50:
            return RiskLevel.MEDIUM
        elif risk_score <= 75:
            return RiskLevel.HIGH
        else:
            return RiskLevel.VERY_HIGH
    
    @staticmethod
    def check_patterns(transaction: Dict[str, Any], history: List[Dict[str, Any]]) -> List[str]:
        """Check for suspicious patterns in transaction history."""
        patterns = []
        
        # Check for velocity
        recent_count = sum(1 for t in history if t.get("days_ago", 999) <= 1)
        if recent_count > 5:
            patterns.append("high_velocity")
        
        # Check for splitting
        similar_amounts = sum(
            1 for t in history 
            if abs(t.get("amount", 0) - transaction["amount"]) < transaction["amount"] * 0.1
        )
        if similar_amounts > 3:
            patterns.append("potential_splitting")
        
        return patterns

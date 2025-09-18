"""Rule engine for transaction processing."""

from typing import Dict, List, Any, Optional
from datetime import datetime
from database.repositories import RuleRepository
from database.schemas import Rule, RuleStatus
import logging
import re

logger = logging.getLogger(__name__)

class RuleEngine:
    """Engine for evaluating transaction rules."""
    
    @staticmethod
    def evaluate_condition(condition: Dict, transaction: Dict) -> bool:
        """Evaluate a single rule condition."""
        try:
            operator = condition.get("operator", "equals")
            field = condition.get("field")
            value = condition.get("value")
            
            # Navigate nested fields
            actual_value = transaction
            for part in field.split("."):
                if isinstance(actual_value, dict):
                    actual_value = actual_value.get(part)
                else:
                    return False
            
            # Evaluate based on operator
            if operator == "equals":
                return actual_value == value
            elif operator == "not_equals":
                return actual_value != value
            elif operator == "greater_than":
                return float(actual_value) > float(value)
            elif operator == "less_than":
                return float(actual_value) < float(value)
            elif operator == "greater_or_equal":
                return float(actual_value) >= float(value)
            elif operator == "less_or_equal":
                return float(actual_value) <= float(value)
            elif operator == "in":
                return actual_value in value
            elif operator == "not_in":
                return actual_value not in value
            elif operator == "contains":
                return value in str(actual_value)
            elif operator == "regex":
                return bool(re.match(value, str(actual_value)))
            elif operator == "exists":
                return actual_value is not None
            elif operator == "not_exists":
                return actual_value is None
            else:
                return False
                
        except Exception as e:
            logger.error(f"Error evaluating condition: {e}")
            return False
    
    @staticmethod
    def evaluate_rule(rule: Dict, transaction: Dict) -> bool:
        """Evaluate a complete rule against a transaction."""
        try:
            conditions = rule.get("conditions", {})
            
            # Handle AND/OR logic
            logic_operator = conditions.get("operator", "AND")
            rule_conditions = conditions.get("conditions", [])
            
            if not rule_conditions:
                return False
            
            if logic_operator == "AND":
                return all(
                    RuleEngine.evaluate_condition(cond, transaction)
                    for cond in rule_conditions
                )
            elif logic_operator == "OR":
                return any(
                    RuleEngine.evaluate_condition(cond, transaction)
                    for cond in rule_conditions
                )
            else:
                return False
                
        except Exception as e:
            logger.error(f"Error evaluating rule {rule.get('rule_id')}: {e}")
            return False
    
    @staticmethod
    def apply_rules(transaction: Dict) -> Dict[str, Any]:
        """Apply all active rules to a transaction."""
        try:
            # Get active rules
            rules = RuleRepository.get_active_rules_sync()
            
            triggered_rules = []
            risk_flags = []
            actions = []
            
            for rule in rules:
                if RuleEngine.evaluate_rule(rule, transaction):
                    triggered_rules.append(rule["rule_id"])
                    
                    # Add risk flag
                    if rule.get("category"):
                        risk_flags.append(f"rule_{rule['category']}")
                    
                    # Collect actions
                    action = rule.get("action")
                    if action:
                        actions.append({
                            "rule_id": rule["rule_id"],
                            "action": action,
                            "priority": rule.get("priority", 0)
                        })
                    
                    logger.info(f"Rule triggered: {rule['name']} for transaction {transaction.get('transaction_id')}")
            
            # Determine final action based on highest priority
            final_action = None
            if actions:
                actions.sort(key=lambda x: x["priority"], reverse=True)
                final_action = actions[0]["action"]
            
            return {
                "triggered_rules": triggered_rules,
                "risk_flags": risk_flags,
                "recommended_action": final_action,
                "rule_count": len(triggered_rules)
            }
            
        except Exception as e:
            logger.error(f"Error applying rules: {e}")
            return {
                "triggered_rules": [],
                "risk_flags": [],
                "recommended_action": None,
                "rule_count": 0
            }
    
    @staticmethod
    def get_default_rules() -> List[Rule]:
        """Get default rules for initial setup."""
        return [
            Rule(
                name="High Amount Wire Transfer",
                description="Flag wire transfers above $50,000",
                category="amount",
                conditions={
                    "operator": "AND",
                    "conditions": [
                        {"field": "transaction_type", "operator": "equals", "value": "wire_transfer"},
                        {"field": "amount", "operator": "greater_than", "value": 50000}
                    ]
                },
                action="escalate",  # Changed from "flag" to valid decision type
                priority=50
            ),
            Rule(
                name="International High Risk Country",
                description="Escalate transactions to/from high risk countries",
                category="geography",
                conditions={
                    "operator": "OR",
                    "conditions": [
                        {"field": "recipient.country", "operator": "in", "value": ["RU","IR", "KP", "SY", "AF", "YE"]},
                        {"field": "sender.country", "operator": "in", "value": ["RU","IR", "KP", "SY", "AF", "YE"]}
                    ]
                },
                action="escalate",
                priority=80
            ),
            Rule(
                name="Suspicious Round Amount",
                description="Flag amounts just below reporting thresholds",
                category="pattern",
                conditions={
                    "operator": "OR",
                    "conditions": [
                        {"field": "amount", "operator": "equals", "value": 9999},
                        {"field": "amount", "operator": "equals", "value": 99999}
                    ]
                },
                action="escalate",  # Changed from "flag" to valid decision type
                priority=60
            ),
            Rule(
                name="After Hours Large Transaction",
                description="Flag large transactions outside business hours",
                category="pattern",
                conditions={
                    "operator": "AND",
                    "conditions": [
                        {"field": "amount", "operator": "greater_than", "value": 25000},
                        {"field": "metadata.unusual_time", "operator": "equals", "value": True}
                    ]
                },
                action="escalate",
                priority=70
            ),
            Rule(
                name="Rapid Movement Pattern",
                description="Detect rapid fund movement patterns",
                category="velocity",
                conditions={
                    "operator": "OR",
                    "conditions": [
                        # Escalate if more than 2 transactions in 1 hour with significant amount
                        {
                            "operator": "AND",
                            "conditions": [
                                {"field": "metadata.velocity_1h", "operator": "greater_than", "value": 2},
                                {"field": "amount", "operator": "greater_than", "value": 20000}
                            ]
                        },
                        # Escalate if total amount in 1 hour exceeds threshold
                        {"field": "metadata.total_amount_1h", "operator": "greater_than", "value": 75000}
                    ]
                },
                action="escalate",  # Changed from reject to escalate for review
                priority=90
            ),
            Rule(
                name="Structuring Pattern Detection",
                description="Detect potential money structuring to avoid $5000 reporting threshold",
                category="pattern",
                conditions={
                    "operator": "AND",
                    "conditions": [
                        {"field": "amount", "operator": "greater_than", "value": 4900},
                        {"field": "amount", "operator": "less_than", "value": 5000},
                        {"field": "transaction_type", "operator": "equals", "value": "wire_transfer"}
                    ]
                },
                action="escalate",  # Escalate for human review to confirm structuring
                priority=95
            ),
            Rule(
                name="Multiple Structuring Pattern",
                description="Detect multiple transactions to same recipient just under threshold",
                category="pattern",
                conditions={
                    "operator": "AND",
                    "conditions": [
                        {"field": "amount", "operator": "greater_than", "value": 4800},
                        {"field": "amount", "operator": "less_than", "value": 5000},
                        {"field": "recipient.name", "operator": "regex", "value": "Offshore.*"}
                    ]
                },
                action="escalate",  # Escalate suspicious patterns to offshore entities for review
                priority=96
            )
        ]
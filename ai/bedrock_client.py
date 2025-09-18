"""AWS Bedrock client for AI operations."""

import boto3
import json
from typing import List, Dict, Any
import logging
from utils.config import config

logger = logging.getLogger(__name__)

class BedrockClient:
    def __init__(self):
        self.client = boto3.client(
            'bedrock-runtime',
            region_name=config.AWS_REGION,
            aws_access_key_id=config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY
        )
    
    async def get_embedding(self, text: str) -> List[float]:
        """Generate embedding using Cohere via Bedrock."""
        try:
            response = self.client.invoke_model(
                modelId='cohere.embed-english-v3',
                body=json.dumps({
                    "texts": [text],
                    "input_type": "search_document",
                    "truncate": "END"
                })
            )
            
            result = json.loads(response['body'].read())
            return result['embeddings'][0]
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise e
    
    async def analyze_transaction(self, prompt: str) -> Dict[str, Any]:
        """Analyze transaction using Claude via Bedrock."""
        try:
            response = self.client.invoke_model(
                modelId=config.BEDROCK_MODEL_VERSION,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 1000,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.3,
                    "top_p": 0.9
                })
            )
            
            result = json.loads(response['body'].read())
            return self._parse_claude_response(result['content'][0]['text'])
        except Exception as e:
            logger.error(f"Error analyzing transaction: {e}")
            raise e
    
    def _parse_claude_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Claude's response into structured format."""
        try:
            # Check if response contains JSON within markdown code blocks
            if "```json" in response_text:
                # Extract JSON from markdown code blocks
                start_idx = response_text.find("```json") + 7
                end_idx = response_text.find("```", start_idx)
                json_str = response_text[start_idx:end_idx].strip()
                parsed = json.loads(json_str)
            else:
                # Try direct JSON parsing
                parsed = json.loads(response_text)
            
            # Map any invalid decision types to valid ones
            if parsed.get("decision") == "flag":
                parsed["decision"] = "escalate"
            
            # Ensure confidence is a number, not a string
            if isinstance(parsed.get("confidence"), str):
                parsed["confidence"] = float(parsed["confidence"].rstrip('%'))
            
            return parsed
        except Exception as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            # Fallback parsing
            lines = response_text.strip().split('\n')
            result = {
                "decision": "escalate",
                "confidence": 50,
                "reasoning": response_text,
                "risk_factors": [],
                "compliance_notes": ""
            }
            
            for line in lines:
                if "DECISION:" in line.upper():
                    decision_text = line.split(":")[-1].strip().lower()
                    if "approve" in decision_text:
                        result["decision"] = "approve"
                    elif "reject" in decision_text:
                        result["decision"] = "reject"
                    elif "flag" in decision_text:
                        result["decision"] = "escalate"  # Map flag to escalate
                    else:
                        result["decision"] = "escalate"
                elif "CONFIDENCE:" in line.upper():
                    try:
                        result["confidence"] = float(line.split(":")[-1].strip().rstrip('%'))
                    except:
                        pass
            
            return result

# Singleton instance
bedrock_client = BedrockClient()

"""Groq client for AI operations."""

import json
from typing import List, Dict, Any, Optional
import logging
from groq import Groq, AsyncGroq
import asyncio
from utils.config import config

logger = logging.getLogger(__name__)

class GroqClient:
    def __init__(self):
        """Initialize Groq client with API key from config."""
        self.client = Groq(
            api_key=config.GROQ_API_KEY
        )
        self.async_client = AsyncGroq(
            api_key=config.GROQ_API_KEY
        )
        self.model_id = getattr(config, 'GROQ_MODEL_ID', 'openai/gpt-oss-120b')  # Default model
    
    async def analyze_transaction(self, prompt: str) -> Dict[str, Any]:
        """Analyze transaction using Groq's LLM."""
        try:         
            response = await self.async_client.chat.completions.create(
                model=self.model_id,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=1000,
                top_p=0.9,
                response_format={"type": "json_object"}  # Request JSON response
            )
            
            result_text = response.choices[0].message.content
            return self._parse_llm_response(result_text)
            
        except Exception as e:
            logger.error(f"Error analyzing transaction with Groq: {e}")
            raise e
    
    def analyze_transaction_sync(self, prompt: str) -> Dict[str, Any]:
        """Synchronous version of analyze_transaction."""
        try:
            system_message = """You are a financial transaction analyzer. 
            Always respond with a JSON object containing:
            - decision: "approve", "reject", or "escalate"
            - confidence: number between 0 and 100
            - reasoning: explanation of your decision
            - risk_factors: array of identified risks
            - compliance_notes: relevant compliance considerations
            """
            
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=[
                    {
                        "role": "system",
                        "content": system_message
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=1000,
                top_p=0.9,
                response_format={"type": "json_object"}
            )
            
            result_text = response.choices[0].message.content
            return self._parse_llm_response(result_text)
            
        except Exception as e:
            logger.error(f"Error analyzing transaction with Groq: {e}")
            raise e
    
    async def generate_completion(self, 
                                prompt: str, 
                                system_prompt: Optional[str] = None,
                                temperature: float = 0.7,
                                max_tokens: int = 1000) -> str:
        """Generate a general completion using Groq."""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = await self.async_client.chat.completions.create(
                model=self.model_id,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating completion with Groq: {e}")
            raise e
    
    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """Parse LLM response into structured format."""
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
            
            # Normalize and validate the response
            # Map any invalid decision types to valid ones
            if parsed.get("decision") == "flag":
                parsed["decision"] = "escalate"
            
            # Ensure decision is valid
            valid_decisions = ["approve", "reject", "escalate"]
            if parsed.get("decision") not in valid_decisions:
                logger.warning(f"Invalid decision: {parsed.get('decision')}. Defaulting to escalate.")
                parsed["decision"] = "escalate"
            
            # Ensure confidence is a number
            if isinstance(parsed.get("confidence"), str):
                parsed["confidence"] = float(parsed["confidence"].rstrip('%'))
            elif "confidence" not in parsed:
                parsed["confidence"] = 50  # Default confidence
            
            # Ensure required fields exist
            parsed.setdefault("reasoning", "No reasoning provided")
            parsed.setdefault("risk_factors", [])
            parsed.setdefault("compliance_notes", "")
            
            return parsed
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            # Fallback parsing for non-JSON responses
            return self._fallback_parse(response_text)
        except Exception as e:
            logger.error(f"Unexpected error parsing response: {e}")
            return self._fallback_parse(response_text)
    
    def _fallback_parse(self, response_text: str) -> Dict[str, Any]:
        """Fallback parsing when JSON parsing fails."""
        lines = response_text.strip().split('\n')
        result = {
            "decision": "escalate",
            "confidence": 50,
            "reasoning": response_text,
            "risk_factors": [],
            "compliance_notes": ""
        }
        
        for line in lines:
            line_upper = line.upper()
            if "DECISION:" in line_upper:
                decision_text = line.split(":")[-1].strip().lower()
                if "approve" in decision_text:
                    result["decision"] = "approve"
                elif "reject" in decision_text:
                    result["decision"] = "reject"
                else:
                    result["decision"] = "escalate"
            elif "CONFIDENCE:" in line_upper:
                try:
                    confidence_text = line.split(":")[-1].strip()
                    result["confidence"] = float(confidence_text.rstrip('%'))
                except ValueError:
                    pass
            elif "RISK" in line_upper and ":" in line:
                # Try to extract risk factors
                risk_text = line.split(":")[-1].strip()
                if risk_text:
                    result["risk_factors"] = [r.strip() for r in risk_text.split(",")]
        
        return result
    
    async def stream_completion(self, 
                               prompt: str, 
                               system_prompt: Optional[str] = None,
                               temperature: float = 0.7,
                               max_tokens: int = 1000):
        """Stream a completion response from Groq."""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            stream = await self.async_client.chat.completions.create(
                model=self.model_id,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"Error streaming completion from Groq: {e}")
            raise e

# Singleton instance
groq_client = GroqClient()
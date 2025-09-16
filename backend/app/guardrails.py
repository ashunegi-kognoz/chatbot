import os
from typing import Dict, Tuple, Optional
from dotenv import load_dotenv
from nemoguardrails import LLMRails, RailsConfig

load_dotenv()

class GuardrailsService:
    def __init__(self):
        """Initialize NeMo Guardrails with OpenAI integration"""
        try:
            # Create RailsConfig from the config directory
            config = RailsConfig.from_path("./config")
            

            # Create the rails instance
            self.rails = LLMRails(config)
             
            print("NeMo Guardrails initialized successfully")
            
        except Exception as e:
            print(f"Failed to initialize NeMo Guardrails: {e}")
            self.rails = None

    def check_input_safety(self, user_query: str) -> Tuple[bool, str, Dict]:
        """
        Check if user input is safe and within scope using NeMo Guardrails
        Returns: (is_safe, message, guardrails_result)
        """
        if not self.rails:
            return False, "Guardrails not initialized", {}
        
        try:
            # Generate response through guardrails
            response = self.rails.generate(messages=[{
                "role": "user", 
                "content": user_query
            }])
            
            # Check if the response indicates the query was blocked
            response_content = response.get("content", "")
            
            # Define patterns that indicate blocking
            blocking_patterns = [
                "I'm here to assist you with the Foundational Learning Program",
                "I cannot help with",
                "I'm designed to assist with the Petronas",
                "For questions outside this program",
                "I can only provide information based on the available learning materials"
            ]
            
            # Check if any blocking pattern is present
            is_blocked = any(pattern in response_content for pattern in blocking_patterns)
            
            if is_blocked:
                return False, "Query is out of scope or inappropriate", {
                    "blocked": True,
                    "reason": "out_of_scope_or_inappropriate",
                    "response": response_content
                }
            
            return True, "Query is safe and within scope", {
                "blocked": False,
                "response": response_content
            }
            
        except Exception as e:
            # If guardrails fails, err on the side of caution
            return False, f"Guardrails check failed: {str(e)}", {}

    def check_output_safety(self, llm_response: str) -> Tuple[bool, str, Dict]:
        """
        Check if LLM output is safe using NeMo Guardrails
        Returns: (is_safe, message, guardrails_result)
        """
        if not self.rails:
            return False, "Guardrails not initialized", {}
        
        try:
            # Create a test conversation to check the output
            messages = [
                {"role": "user", "content": "Test query"},
                {"role": "assistant", "content": llm_response}
            ]
            
            # Generate response through guardrails
            response = self.rails.generate(messages=messages)
            
            # Check if the response indicates the output was blocked
            response_content = response.get("content", "")
            
            # Define patterns that indicate output blocking
            blocking_patterns = [
                "I cannot provide that response",
                "I'm designed to assist with the Petronas",
                "I can only provide information based on the available learning materials"
            ]
            
            # Check if any blocking pattern is present
            is_blocked = any(pattern in response_content for pattern in blocking_patterns)
            
            if is_blocked:
                return False, "Response contains inappropriate content", {
                    "blocked": True,
                    "reason": "inappropriate_content",
                    "response": response_content
                }
            
            return True, "Response is safe", {
                "blocked": False,
                "response": response_content
            }
            
        except Exception as e:
            # If guardrails fails, err on the side of caution
            return False, f"Guardrails check failed: {str(e)}", {}

    def get_safe_response(self, original_response: str) -> str:
        """
        Return a safe fallback response when content is flagged
        """
        return "I'm here to assist you with the Foundational Learning Program at Petronas. For questions outside this program, you might want to explore other resources or speak with the appropriate professionals."

    def generate_guarded_response(self, user_query: str, context: str = "") -> Tuple[str, bool]:
        """
        Generate a response through guardrails that automatically handles safety checks
        Returns: (response_content, is_safe)
        """
        if not self.rails:
            return self.get_safe_response(""), False
        
        try:
            # Build the input with context if provided
            if context:
                query_with_context = f"Context: {context}\n\nQuery: {user_query}"
            else:
                query_with_context = user_query
            
            # Generate response through guardrails
            response = self.rails.generate(messages=[{
                "role": "user", 
                "content": query_with_context
            }])
            
            response_content = response.get("content", "")
            
            # Check if the response indicates blocking
            blocking_patterns = [
                "I'm here to assist you with the Foundational Learning Program",
                "I cannot help with",
                "I'm designed to assist with the Petronas",
                "For questions outside this program"
            ]
            
            is_blocked = any(pattern in response_content for pattern in blocking_patterns)
            
            return response_content, not is_blocked
            
        except Exception as e:
            print(f"Error in guarded response generation: {e}")
            return self.get_safe_response(""), False

# Global instance
guardrails = GuardrailsService()
import asyncio
import aiohttp
import re
from methods.mas_base import MAS

class MATEval_Simple(MAS):
    """
    Simple MATEval implementation for MASlab
    Uses 3 API calls per problem: Mike evaluation -> John evaluation -> Final decision
    """
    
    def __init__(self, general_config, method_config_name=None):
        config_name = method_config_name if method_config_name is not None else "config_simple"
        super().__init__(general_config, method_config_name=config_name)
        self.evaluation_dimensions = [
            'Mathematical Correctness',
            'Logical Consistency', 
            'Clarity of Explanation',
            'Completeness of Solution',
            'Pedagogical Value'
        ]
    
    def inference(self, sample):
        """
        Main inference method for MATEval Simple
        Expected sample format:
        {
            "query": "Complete judge instruction with question and both responses embedded"
        }
        """
        query = sample.get("query", "")
        
        if not query:
            return {"response": "Error: Missing required field (query)"}
        
        # Run async evaluation
        try:
            result = asyncio.run(self._evaluate_responses(query))
            return {"response": result}
        except Exception as e:
            return {"response": f"Error in evaluation: {str(e)}"}
    
    async def _evaluate_responses(self, query):
        """Async evaluation using multi-agent approach"""
        
        # Mike's evaluation
        mike_eval = self._mike_evaluation(query)
        
        # John's evaluation based on Mike's analysis
        john_eval = self._john_evaluation(query, mike_eval)
        
        # Final decision synthesis
        final_decision = self._final_decision(query, mike_eval, john_eval)
        
        # Extract choice
        choice = self._extract_decision(final_decision)
        
        result = {
            "mike_evaluation": mike_eval,
            "john_evaluation": john_eval, 
            "final_decision": final_decision,
            "choice": choice
        }
        
        return str(result)
    
    def _mike_evaluation(self, query):
        """Mike's initial evaluation"""
        prompt = f"""You are Mike, a mathematical expert. Analyze this judge task:

{query}

Evaluate based on mathematical correctness, clarity, and completeness. 
Which response is better and why?"""

        return self.call_llm(
            system_prompt="You are an expert mathematical evaluator.",
            prompt=prompt
        )
    
    def _john_evaluation(self, query, mike_analysis):
        """John's evaluation considering Mike's analysis"""
        prompt = f"""You are John, another mathematical expert. Here's a judge task:

{query}

Mike's evaluation: {mike_analysis}

Provide your own analysis. Do you agree with Mike? Give your assessment."""

        return self.call_llm(
            system_prompt="You are an expert mathematical evaluator.",
            prompt=prompt
        )
    
    def _final_decision(self, query, mike_eval, john_eval):
        """Final decision based on both evaluations"""
        prompt = f"""Based on these two expert evaluations, make a final decision:

{query}

Mike's evaluation: {mike_eval}

John's evaluation: {john_eval}

Choose A or B and explain briefly. Format: DECISION: [A or B]"""

        return self.call_llm(
            system_prompt="You make final evaluation decisions.",
            prompt=prompt
        )
    
    def _extract_decision(self, text):
        """Extract A or B from decision text"""
        patterns = [
            r'DECISION:\s*([AB])',
            r'Choice:\s*([AB])',
            r'Answer:\s*([AB])',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).upper()
        
        # Simple fallback
        if 'Response A' in text and 'Response B' not in text:
            return 'A'
        elif 'Response B' in text and 'Response A' not in text:
            return 'B'
        
        return None 
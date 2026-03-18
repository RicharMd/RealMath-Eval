import asyncio
import re
from methods.mas_base import MAS

class MATEval_Full(MAS):
    """
    Full MATEval implementation for MASlab
    Uses 10 API calls per problem with Self-Reflection (SR) + Chain of Thought (COT) + Feedback (FB)
    """
    
    def __init__(self, general_config, method_config_name=None):
        config_name = method_config_name if method_config_name is not None else "config_full"
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
        Main inference method for MATEval Full
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
            result = asyncio.run(self._full_evaluation(query))
            return {"response": result}
        except Exception as e:
            return {"response": f"Error in evaluation: {str(e)}"}
    
    async def _full_evaluation(self, query):
        """Complete MATEval evaluation with multiple rounds and reflection"""
        
        # Round 1: Initial evaluations with self-reflection
        mike_eval_r1 = self._mike_initial_evaluation(query)
        mike_reflection_r1 = self._mike_self_reflection(mike_eval_r1)
        
        john_eval_r1 = self._john_evaluation(query, mike_eval_r1, mike_reflection_r1)
        john_reflection_r1 = self._john_self_reflection(john_eval_r1, mike_eval_r1)
        
        # Coordinator feedback
        coordinator_feedback = self._coordinator_feedback(
            query, mike_eval_r1, mike_reflection_r1, john_eval_r1, john_reflection_r1
        )
        
        # Round 2: Improved evaluations with feedback
        mike_eval_r2 = self._mike_round2_evaluation(coordinator_feedback, mike_eval_r1)
        mike_reflection_r2 = self._mike_self_reflection(mike_eval_r2)
        
        john_eval_r2 = self._john_round2_evaluation(coordinator_feedback, john_eval_r1, mike_eval_r2)
        john_reflection_r2 = self._john_self_reflection(john_eval_r2, mike_eval_r2)
        
        # Final consensus
        final_consensus = self._final_consensus(
            query, mike_eval_r1, mike_reflection_r1, john_eval_r1, john_reflection_r1,
            coordinator_feedback, mike_eval_r2, mike_reflection_r2, john_eval_r2, john_reflection_r2
        )
        
        # Extract choice
        choice = self._extract_decision(final_consensus)
        
        result = {
            "round1_mike_eval": mike_eval_r1,
            "round1_mike_reflection": mike_reflection_r1,
            "round1_john_eval": john_eval_r1,
            "round1_john_reflection": john_reflection_r1,
            "coordinator_feedback": coordinator_feedback,
            "round2_mike_eval": mike_eval_r2,
            "round2_mike_reflection": mike_reflection_r2,
            "round2_john_eval": john_eval_r2,
            "round2_john_reflection": john_reflection_r2,
            "final_consensus": final_consensus,
            "choice": choice
        }
        
        return str(result)
    
    def _mike_initial_evaluation(self, query):
        """Mike's initial evaluation with Chain of Thought reasoning"""
        prompt = f"""You are Mike, an expert mathematical evaluator. You need to assess a judge task using systematic Chain of Thought reasoning.

{query}

Please evaluate these responses step by step using the following dimensions:

1. **Mathematical Correctness**: Are the mathematical steps and final answers correct?
2. **Logical Consistency**: Is the reasoning logical and coherent throughout?
3. **Clarity of Explanation**: Is the solution clearly explained and easy to follow?
4. **Completeness of Solution**: Does the response fully address all aspects of the problem?
5. **Pedagogical Value**: How helpful would this be for someone learning the concept?

**Chain of Thought Analysis:**
- First, analyze Response A systematically across all dimensions
- Then, analyze Response B systematically across all dimensions  
- Compare the responses dimension by dimension
- Identify the most significant differences

Focus on identifying the TWO most critical differences between these responses. Provide detailed step-by-step analysis with clear reasoning.

Think carefully and provide your comprehensive evaluation."""

        return self.call_llm(
            system_prompt="You are an expert mathematical evaluator using systematic Chain of Thought reasoning.",
            prompt=prompt
        )
    
    def _mike_self_reflection(self, previous_evaluation):
        """Mike's self-reflection on his evaluation"""
        prompt = f"""Please carefully reflect on your previous mathematical evaluation:

Previous Evaluation: {previous_evaluation}

**Self-Reflection Questions:**
1. Did I thoroughly analyze all five evaluation dimensions?
2. Are there mathematical aspects I might have overlooked or misunderstood?
3. Did I provide sufficient evidence for my assessments?
4. Are there alternative interpretations of the mathematical solutions?
5. Could my reasoning be biased toward certain solution styles?

**Reflection Process:**
- Review each dimension of your evaluation
- Consider if you missed any important mathematical details
- Think about whether your comparisons were fair and comprehensive
- Identify any areas where you could provide stronger analysis

Please provide your reflection and any corrections or additional insights. If you find errors in your previous evaluation, clearly state them."""

        return self.call_llm(
            system_prompt="You are reflecting on your mathematical evaluation to ensure accuracy and completeness.",
            prompt=prompt
        )
    
    def _john_evaluation(self, query, mike_analysis, mike_reflection):
        """John's evaluation considering Mike's analysis and reflection"""
        prompt = f"""You are John, a second expert mathematical evaluator. You need to provide your own independent assessment while considering Mike's analysis.

{query}

Mike's Initial Analysis: {mike_analysis}

Mike's Self-Reflection: {mike_reflection}

**Your Task:**
Provide your own comprehensive evaluation using Chain of Thought reasoning. Consider:

1. Do you agree with Mike's assessment across the five dimensions?
2. Are there mathematical aspects Mike might have missed?
3. Do you interpret any solutions differently?
4. What additional insights can you provide?

**Evaluation Dimensions:**
1. Mathematical Correctness
2. Logical Consistency  
3. Clarity of Explanation
4. Completeness of Solution
5. Pedagogical Value

**Chain of Thought Process:**
- Independently analyze both responses
- Compare your findings with Mike's analysis
- Highlight agreements and disagreements
- Provide your own reasoning for any differences

Be thorough and provide specific examples to support your evaluation."""

        return self.call_llm(
            system_prompt="You are an expert mathematical evaluator providing independent assessment.",
            prompt=prompt
        )
    
    def _john_self_reflection(self, john_evaluation, mike_analysis):
        """John's self-reflection on his evaluation"""
        prompt = f"""Please reflect on your evaluation in the context of the collaborative discussion:

Your Evaluation: {john_evaluation}

Mike's Analysis: {mike_analysis}

**Reflection Questions:**
1. Did I provide a balanced and fair assessment?
2. Are there points where I should reconsider my analysis?
3. Did I adequately address differences with Mike's perspective?
4. Are there mathematical nuances I should explore further?
5. How can I improve the collaborative evaluation process?

**Collaborative Reflection:**
- Consider how your analysis complements Mike's
- Identify areas of agreement and disagreement
- Reflect on the strength of your mathematical reasoning
- Think about how to better synthesize different perspectives

Provide your reflection and any refinements to your evaluation."""

        return self.call_llm(
            system_prompt="You are reflecting on your evaluation in a collaborative context.",
            prompt=prompt
        )
    
    def _coordinator_feedback(self, query, mike_eval, mike_reflection, john_eval, john_reflection):
        """Coordinator provides feedback on the evaluation process"""
        prompt = f"""You are the Coordinator overseeing the mathematical evaluation process. Review the evaluations and provide constructive feedback.

{query}

**Mike's Evaluation**: {mike_eval}
**Mike's Reflection**: {mike_reflection}
**John's Evaluation**: {john_eval}
**John's Reflection**: {john_reflection}

**Your Task:**
Analyze the evaluation process and provide feedback on:

1. **Evaluation Quality**: How thorough and accurate are the evaluations?
2. **Areas of Agreement**: Where do Mike and John agree, and why is this significant?
3. **Areas of Disagreement**: Where do they disagree, and what might resolve these differences?
4. **Missing Perspectives**: What important aspects might have been overlooked?
5. **Improvement Suggestions**: How can the evaluators improve their analysis?

**Feedback Format:**
STRENGTHS: [What was done well in the evaluations]
AREAS_FOR_IMPROVEMENT: [Specific areas that need more attention]
RESOLUTION_GUIDANCE: [Suggestions for resolving disagreements]
ADDITIONAL_CONSIDERATIONS: [Important aspects that should be examined]

Provide constructive feedback to help improve the final evaluation."""

        return self.call_llm(
            system_prompt="You are coordinating the evaluation process and providing constructive feedback.",
            prompt=prompt
        )
    
    def _mike_round2_evaluation(self, feedback, previous_evaluation):
        """Mike's improved evaluation based on coordinator feedback"""
        prompt = f"""Based on the coordinator's feedback, please provide an improved evaluation:

Coordinator Feedback: {feedback}

Your Previous Evaluation: {previous_evaluation}

**Round 2 Improvement Task:**
1. Address the specific gaps and suggestions from the coordinator
2. Reconsider areas where you disagreed with John
3. Provide more detailed analysis where needed
4. Strengthen your mathematical reasoning
5. Focus on the most critical evaluation aspects

**Improved Analysis:**
Please provide your enhanced evaluation, clearly indicating:
- What aspects you're reconsidering
- How you're addressing the coordinator's feedback
- Any changes in your assessment
- Stronger evidence for your conclusions

Make your evaluation more comprehensive and rigorous."""

        return self.call_llm(
            system_prompt="You are improving your mathematical evaluation based on feedback.",
            prompt=prompt
        )
    
    def _john_round2_evaluation(self, feedback, previous_evaluation, mike_round2):
        """John's improved evaluation based on feedback and Mike's Round 2"""
        prompt = f"""Based on the coordinator's feedback and Mike's improved analysis, provide your enhanced evaluation:

Coordinator Feedback: {feedback}

Your Previous Evaluation: {previous_evaluation}

Mike's Round 2 Analysis: {mike_round2}

**Round 2 Enhancement Task:**
1. Address the coordinator's specific suggestions
2. Consider Mike's improved analysis
3. Refine areas where you had disagreements
4. Provide deeper mathematical insights
5. Strengthen your overall assessment

**Enhanced Evaluation:**
Please provide your improved evaluation, clearly showing:
- How you're incorporating the feedback
- Your response to Mike's Round 2 analysis
- Any adjustments to your previous assessment
- More rigorous mathematical reasoning

Focus on reaching a well-reasoned, comprehensive evaluation."""

        return self.call_llm(
            system_prompt="You are enhancing your mathematical evaluation based on feedback and collaboration.",
            prompt=prompt
        )
    
    def _final_consensus(self, query, mike_r1, mike_ref1, john_r1, john_ref1,
                         feedback, mike_r2, mike_ref2, john_r2, john_ref2):
        """Final consensus based on all evaluations and reflections"""
        prompt = f"""You are tasked with reaching a final consensus based on comprehensive multi-round evaluations.

{query}

**Round 1 Evaluations:**
Mike's Evaluation: {mike_r1}
Mike's Reflection: {mike_ref1}
John's Evaluation: {john_r1}
John's Reflection: {john_ref1}

**Coordinator Feedback:** {feedback}

**Round 2 Evaluations:**
Mike's Improved Evaluation: {mike_r2}
Mike's Second Reflection: {mike_ref2}
John's Improved Evaluation: {john_r2}
John's Second Reflection: {john_ref2}

**Final Decision Task:**
Synthesize all the information to make a definitive choice between Response A and Response B.

Consider:
1. The evolution of thinking across both rounds
2. How the coordinator feedback was addressed
3. Areas of consistent agreement between evaluators
4. Resolution of initial disagreements
5. The most compelling mathematical arguments

**Decision Format:**
SYNTHESIS: [Your comprehensive synthesis of all evaluations]
FINAL_DECISION: [A or B]
CONFIDENCE: [High/Medium/Low]
KEY_REASONING: [The most important factors in your decision]

Make your final decision now."""

        return self.call_llm(
            system_prompt="You are making the final consensus decision based on comprehensive multi-round evaluation.",
            prompt=prompt
        )
    
    def _extract_decision(self, text):
        """Extract A or B from decision text"""
        patterns = [
            r'DECISION:\s*([AB])',
            r'Choice:\s*([AB])',
            r'Answer:\s*([AB])',
            r'Final.*?:\s*([AB])',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).upper()
        
        # Fallback patterns
        if 'Response A' in text and 'Response B' not in text:
            return 'A'
        elif 'Response B' in text and 'Response A' not in text:
            return 'B'
        
        return None 
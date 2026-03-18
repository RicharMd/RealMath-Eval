import asyncio
import aiohttp
import re
from methods.mas_base import MAS

class MATEval_Enhanced(MAS):
    """
    Enhanced MATEval implementation for MASlab
    Uses DeepSeek Prover V2 as Mathematical Expert + DeepSeek V3 as General Evaluators
    """
    
    def __init__(self, general_config, method_config_name=None):
        config_name = method_config_name if method_config_name is not None else "config_enhanced"
        super().__init__(general_config, method_config_name=config_name)
        self.evaluation_dimensions = [
            'Mathematical Correctness',
            'Logical Consistency', 
            'Clarity of Explanation',
            'Completeness of Solution',
            'Pedagogical Value'
        ]
        
        # API configurations for different models
        self.prover_model = "deepseek-prover-v2"
        self.general_model = "gpt5-mini"
    
    def inference(self, sample):
        """
        Main inference method for MATEval Enhanced
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
            result = asyncio.run(self._enhanced_evaluation(query))
            return {"response": result}
        except Exception as e:
            return {"response": f"Error in evaluation: {str(e)}"}
    
    async def _enhanced_evaluation(self, query):
        """Enhanced evaluation with mathematical expert and general evaluators"""
        
        # Mathematical Expert Analysis (DeepSeek Prover V2)
        expert_analysis = self._mathematical_expert_analysis(query)
        
        # General Evaluators (DeepSeek V3)
        evaluator1_assessment = self._general_evaluator_1(query, expert_analysis)
        evaluator2_assessment = self._general_evaluator_2(query, expert_analysis)
        
        # Final Coordinator Decision
        final_decision = self._coordinator_decision(
            query, expert_analysis, evaluator1_assessment, evaluator2_assessment
        )
        
        # Extract choice
        choice = self._extract_decision(final_decision)
        
        result = {
            "mathematical_expert_analysis": expert_analysis,
            "evaluator1_assessment": evaluator1_assessment,
            "evaluator2_assessment": evaluator2_assessment,
            "final_decision": final_decision,
            "choice": choice
        }
        
        return str(result)
    
    def _mathematical_expert_analysis(self, query):
        """Mathematical expert performs rigorous mathematical analysis"""
        prompt = f"""You are a mathematical proof and reasoning expert specializing in rigorous mathematical analysis.

Your task is to provide a detailed mathematical analysis to help other judges give a better evaluation.

{query}

Please provide your expert analysis focusing on:
1. **Mathematical Correctness**: Are the mathematical statements, calculations, and reasoning correct?
2. **Proof Rigor**: How rigorous are the mathematical arguments and proofs?
3. **Logical Structure**: Is the logical flow coherent and well-structured?
4. **Mathematical Completeness**: Are all necessary steps and justifications provided?
5. **Formal Accuracy**: Are mathematical notations and formulations accurate?

Provide your analysis in this format:
EXPERT_ANALYSIS:
[Your detailed mathematical analysis comparing both responses]

KEY_MATHEMATICAL_INSIGHTS:
[Key mathematical insights that other judges should consider]

RIGOR_ASSESSMENT:
Response A: [High/Medium/Low rigor assessment with brief explanation]
Response B: [High/Medium/Low rigor assessment with brief explanation]"""

        return self.call_llm(
            system_prompt="You are a rigorous mathematical expert focused on proof verification and mathematical reasoning analysis.",
            prompt=prompt,
            model_name=self.prover_model
        )
    
    def _general_evaluator_1(self, query, expert_analysis):
        """First general evaluator focusing on clarity and pedagogy"""
        prompt = f"""You are Evaluator 1, specializing in clarity and educational value assessment.

{query}

**Mathematical Expert Analysis**:
{expert_analysis}

Your task is to evaluate which response is better based on your expertise in clarity and educational value.

Consider the mathematical expert analysis, but also apply your own judgment on:
- Clarity and readability
- Educational value and pedagogical effectiveness
- Completeness of explanation
- Overall accessibility to learners

Provide your evaluation in this format:
EVALUATION:
[Your detailed evaluation comparing both responses]

PRELIMINARY_PREFERENCE:
[A or B] - [Brief reason for your preference]"""

        return self.call_llm(
            system_prompt="You are a careful evaluator focusing on clarity and educational value.",
            prompt=prompt,
            model_name=self.general_model
        )
    
    def _general_evaluator_2(self, query, expert_analysis):
        """Second general evaluator focusing on completeness and logical consistency"""
        prompt = f"""You are Evaluator 2, specializing in completeness and logical consistency assessment.

{query}

**Mathematical Expert Analysis**:
{expert_analysis}

Your task is to evaluate which response is better based on your expertise in completeness and logical consistency.

Consider the mathematical expert analysis, but also apply your own judgment on:
- Completeness of the solution approach
- Logical flow and consistency
- Thoroughness of reasoning
- Overall structural quality

Provide your evaluation in this format:
EVALUATION:
[Your detailed evaluation comparing both responses]

PRELIMINARY_PREFERENCE:
[A or B] - [Brief reason for your preference]"""

        return self.call_llm(
            system_prompt="You are a careful evaluator focusing on completeness and logical consistency.",
            prompt=prompt,
            model_name=self.general_model
        )
    
    def _coordinator_decision(self, query, expert_analysis, eval1_assessment, eval2_assessment):
        """Coordinator makes final decision based on expert analysis and evaluator opinions"""
        prompt = f"""You are the Coordinator, tasked with making the final decision based on expert analysis and multiple evaluations.

{query}

**Mathematical Expert Analysis**:
{expert_analysis}

**Evaluator 1 Assessment**:
{eval1_assessment}

**Evaluator 2 Assessment**:
{eval2_assessment}

Your task is to synthesize all the information and make a final decision. Consider:
1. The mathematical expert's rigorous analysis
2. The evaluators' different perspectives on clarity and completeness
3. The overall quality and correctness of each response

Provide your final decision in this format:
SYNTHESIS:
[Your synthesis of all the analyses and evaluations]

FINAL_DECISION: [A or B]

REASONING:
[Clear reasoning for your final choice]"""

        return self.call_llm(
            system_prompt="You are making the final decision by synthesizing expert mathematical analysis with general evaluations.",
            prompt=prompt,
            model_name=self.general_model
        )
    
    def _extract_decision(self, text):
        """Extract A or B from decision text"""
        patterns = [
            r'FINAL_DECISION:\s*([AB])',
            r'DECISION:\s*([AB])',
            r'Choice:\s*([AB])',
            r'Answer:\s*([AB])',
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
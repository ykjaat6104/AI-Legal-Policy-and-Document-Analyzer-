from typing import List
from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from ai_legal_analyzer.utils.config import Config
from .models import RiskClause
from .rules import RiskRuleEngine

class RiskScorer:
    """
    Combines LLM-based risk assessment with deterministic rules.
    """
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model=Config.LLM_MODEL,
            google_api_key=Config.GOOGLE_API_KEY,
            temperature=0
        )
        self.rule_engine = RiskRuleEngine()
        self.parser = PydanticOutputParser(pydantic_object=RiskClause)
        
        self.prompt = PromptTemplate(
            template="""
            You are an expert AI Legal Analyst. Analyze the following contract clause for potential risks.
            
            Clause ID: {clause_id}
            Clause Text:
            {clause_text}
            
            Identify the type of clause.
            Assign a risk score from 1 (Low) to 10 (High).
            Provide a reason and recommendation.
            
            {format_instructions}
            """,
            input_variables=["clause_id", "clause_text"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )
        
    def analyze_clause(self, clause_id: str, clause_text: str) -> RiskClause:
        """
        Analyze a single clause combining LLM and Rules.
        """
        # 1. Run LLM Analysis
        chain = self.prompt | self.llm | self.parser
        
        try:
            llm_result: RiskClause = chain.invoke({
                "clause_id": clause_id, 
                "clause_text": clause_text
            })
        except Exception as e:
            # Fallback in case of parsing error
            print(f"Error parsing LLM response for {clause_id}: {e}")
            return RiskClause(
                clause_id=clause_id,
                clause_type="Unknown",
                risk_level="Unknown",
                risk_score=5,
                reason=f"Analysis failed: {str(e)}",
                recommendation="Manual review required."
            )
            
        # 2. Run Rule Engine
        rule_score_modifier, rule_reasons = self.rule_engine.evaluate(clause_text)
        
        # 3. Combine Scores
        final_score = llm_result.risk_score + rule_score_modifier
        final_score = max(1, min(10, final_score)) # Clamp between 1-10
        
        # Update Risk Level based on new score
        final_risk_level = "High" if final_score >= 8 else ("Medium" if final_score >= 5 else "Low")
        
        # Update Result
        llm_result.risk_score = final_score
        llm_result.risk_level = final_risk_level
        if rule_reasons:
            llm_result.reason += " Target keywords detected: " + "; ".join(rule_reasons)
            
        return llm_result


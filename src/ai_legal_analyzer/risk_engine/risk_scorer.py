import logging
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from src.ai_legal_analyzer.utils.project_config import Config
from .risk_models import RiskClause
from .risk_rules import RiskRuleEngine

logger = logging.getLogger("scorer")

class RiskScorer:
    # ai based scoring plus manual rules
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model=Config.LLM_MODEL,
            google_api_key=Config.GOOGLE_API_KEY,
            temperature=0
        )
        self.rules = RiskRuleEngine()
        self.parser = PydanticOutputParser(pydantic_object=RiskClause)
        
        self.prompt = PromptTemplate(
            template="""analyze legal risk for this clause. 
            id: {clause_id}
            text: {clause_text}
            {format_instructions}""",
            input_variables=["clause_id", "clause_text"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )
        
    def analyze_clause(self, clause_id, clause_text):
        # run llm and rule engine
        try:
            chain = self.prompt | self.llm | self.parser
            res = chain.invoke({"clause_id": clause_id, "clause_text": clause_text})
        except Exception as e:
            # fallback for errors
            return RiskClause(
                clause_id=clause_id,
                clause_type="unknown",
                risk_level="unknown",
                risk_score=5,
                reason=f"error: {str(e)}",
                recommendation="check manually"
            )
            
        mod, reasons = self.rules.evaluate(clause_text)
        res.risk_score = max(1, min(10, res.risk_score + mod))
        res.risk_level = "High" if res.risk_score >= 8 else ("Medium" if res.risk_score >= 5 else "Low")
        if reasons: res.reason += " rules: " + ", ".join(reasons)
            
        return res

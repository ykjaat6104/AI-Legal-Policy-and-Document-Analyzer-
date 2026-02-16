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
        # use 2.0 flash for high-speed parallel scanning
        self.llm = ChatGoogleGenerativeAI(
            model=Config.LLM_SCAN_MODEL,
            google_api_key=Config.GOOGLE_API_KEY,
            temperature=0
        )
        self.rules = RiskRuleEngine()
        self.parser = PydanticOutputParser(pydantic_object=RiskClause)
        
        self.prompt = PromptTemplate(
            template="""Analyze the following legal document segment (could be a contract, offer letter, court order, or policy).
            segment_id: {clause_id}
            content: {clause_text}
            
            Task: 
            1. Identify the main purpose or topic of this section in simple terms.
            2. Detect potential risks, critical facts, or definitive statements.
            3. Provide a score from 1-10 on importance or impact.
            
            Format instructions:
            {format_instructions}""",
            input_variables=["clause_id", "clause_text"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )
        
    async def analyze_clause(self, clause_id, clause_text):
        # run llm and rule engine asynchronously
        try:
            chain = self.prompt | self.llm | self.parser
            res = await chain.ainvoke({"clause_id": clause_id, "clause_text": clause_text})
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

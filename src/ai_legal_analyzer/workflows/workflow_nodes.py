import asyncio
from typing import List, Dict, Any, TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI
from src.ai_legal_analyzer.utils.project_config import Config
from src.ai_legal_analyzer.retrieval.vector_storage import VectorStoreManager
from src.ai_legal_analyzer.risk_engine.risk_scorer import RiskScorer

class GraphState(TypedDict):
    query: str
    documents: list
    risk_analysis: list
    final_answer: str

class LegalNodes:
    # workflow steps for langgraph
    
    def __init__(self):
        self.vector_store = VectorStoreManager()
        self.risk_scorer = RiskScorer()
        # use 2.0 flash for the deep expert reasoning/summary (higher quota stability)
        self.reasoning_llm = ChatGoogleGenerativeAI(
            model=Config.LLM_REASONING_MODEL,
            google_api_key=Config.GOOGLE_API_KEY,
            temperature=0
        )

    async def retrieve(self, state):
        # get matching clauses from chroma
        query = state["query"]
        results = self.vector_store.search(query, k=5)
        return {"documents": [d for d, s in results]}

    async def analyze_risk(self, state):
        # scan each clause for risk in parallel
        docs = state["documents"]
        tasks = []
        for d in docs:
            rid = d.metadata.get("clause_id", "intro")
            tasks.append(self.risk_scorer.analyze_clause(rid, d.page_content))
        
        # zip through them all at once!
        reports = await asyncio.gather(*tasks)
        return {"risk_analysis": reports}

    async def generate_answer(self, state):
        # use reasoning llm for expert summary
        risks = state["risk_analysis"]
        query = state["query"]
        if not risks: return {"final_answer": "no results found"}
        
        # format prompt for synthesis
        segment_text = "\n".join([f"Segment {r.clause_id} ({r.risk_level}): {r.reason}" for r in risks])
        
        prompt = f"""You are a helpful and expert legal document assistant. 
        Your goal is to explain things in simple, plain English that a regular person can understand.
        
        Based on the following analysis of the document, answer the user's query: '{query}'
        
        --- Document Analysis & Content ---
        {segment_text}
        
        --- Instructions ---
        1. Start by identifying the type of document (e.g., "This appears to be an Offer Letter" or "This is a Court Order").
        2. Use **simple English** and avoid legal jargon where possible.
        3. Use `*` (single asterisk) to highlight notable facts or interesting statements.
        4. Use `**` (double asterisks) to highlight definitive requirements, high risks, or critical deadlines.
        5. Provide a clear, direct answer to the user's specific question based ONLY on the provided content.
        """
        
        res = await self.reasoning_llm.ainvoke(prompt)
        return {"final_answer": res.content}

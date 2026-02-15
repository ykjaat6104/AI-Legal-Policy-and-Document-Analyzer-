from typing import List, Dict, Any, TypedDict
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

    async def retrieve(self, state):
        # get matching clauses from chroma
        query = state["query"]
        results = self.vector_store.search(query, k=5)
        return {"documents": [d for d, s in results]}

    async def analyze_risk(self, state):
        # scan each clause for risk
        docs = state["documents"]
        reports = []
        for d in docs:
            rid = d.metadata.get("clause_id", "intro")
            res = self.risk_scorer.analyze_clause(rid, d.page_content)
            reports.append(res)
        return {"risk_analysis": reports}

    async def generate_answer(self, state):
        # format final risk summary
        risks = state["risk_analysis"]
        if not risks: return {"final_answer": "no results found"}
        
        parts = [f"analyzed {len(risks)} clauses\n"]
        high = [r for r in risks if r.risk_level == "High"]
        
        if high:
            parts.append("HIGH RISK ALERT:\n")
            for r in high:
                parts.append(f"- {r.clause_id}: {r.reason}")
                parts.append(f"  score: {r.risk_score} | rec: {r.recommendation}\n")
        else:
            parts.append("no high risk found")
            
        return {"final_answer": "\n".join(parts)}

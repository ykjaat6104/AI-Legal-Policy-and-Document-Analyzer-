from typing import List, Dict, Any
from langchain_core.documents import Document
from ai_legal_analyzer.retrieval.vector_store import VectorStoreManager
from ai_legal_analyzer.risk_engine.scorer import RiskScorer
from ai_legal_analyzer.risk_engine.models import RiskClause

# Define State
from typing import TypedDict

class GraphState(TypedDict):
    query: str
    documents: List[Document]
    risk_analysis: List[RiskClause]
    final_answer: str

class LegalNodes:
    def __init__(self):
        self.vector_store = VectorStoreManager()
        self.risk_scorer = RiskScorer()

    def retrieve(self, state: GraphState) -> Dict[str, Any]:
        """
        Retrieve relevant clauses from Vector Store.
        """
        query = state["query"]
        print(f"---RETRIEVING CLAUSES FOR: {query}---")
        
        # Determine number of documents to retrieve
        # Could be dynamic based on query complexity
        k = 5
        
        # Assume documents are already ingested and available
        # In a real flow, we'd check if we need to ingest first or if we are querying existing base.
        # Here we assume retrieval from existing store.
        
        results = self.vector_store.search(query, k=k)
        documents = [doc for doc, score in results]
        
        return {"documents": documents}

    def analyze_risk(self, state: GraphState) -> Dict[str, Any]:
        """
        Analyze risk for each retrieved clause.
        """
        documents = state["documents"]
        print(f"---ANALYZING RISK FOR {len(documents)} CLAUSES---")
        
        risk_reports = []
        
        for doc in documents:
            clause_id = doc.metadata.get("clause_id", "Unknown")
            clause_text = doc.page_content
            
            # Using the RiskScorer (LLM + Rules)
            risk_report = self.risk_scorer.analyze_clause(clause_id, clause_text)
            risk_reports.append(risk_report)
            
        return {"risk_analysis": risk_reports}

    def generate_answer(self, state: GraphState) -> Dict[str, Any]:
        """
        Generate final grounded answer.
        """
        # This would use an LLM to synthesize the answer
        # For now, let's create a placeholder utilizing the risk analysis
        
        query = state["query"]
        risks = state["risk_analysis"]
        
        print("---GENERATING FINAL ANSWER---")
        
        # Simple synthesis
        high_risks = [r for r in risks if r.risk_level == "High"]
        
        answer = f"Based on the analysis of {len(risks)} clauses:\n\n"
        
        if high_risks:
            answer += "⚠️ HIGH RISK ALERT:\n"
            for r in high_risks:
                answer += f"- Clause {r.clause_id} ({r.clause_type}): {r.reason} (Score: {r.risk_score}/10)\n"
                answer += f"  Recommendation: {r.recommendation}\n"
        else:
            answer += "No high-risk clauses detected in the retrieved context.\n"
            
        return {"final_answer": answer}

from typing import List, Dict, Any, TypedDict

from langchain_google_genai import ChatGoogleGenerativeAI

from src.utils.project_config import Config
from src.retrieval.vector_storage import VectorStoreManager
from src.risk_engine.risk_scorer import RiskScorer


class GraphState(TypedDict):
    query: str
    documents: list
    risk_analysis: List[Any]
    final_answer: str
    overall_report: Dict[str, Any]


class LegalNodes:
    """LangGraph workflow nodes."""

    def __init__(self):
        self.vector_store = VectorStoreManager()
        self.risk_scorer = RiskScorer()
        self.reasoning_llm = ChatGoogleGenerativeAI(
            model=Config.LLM_REASONING_MODEL,
            google_api_key=Config.GOOGLE_API_KEY,
            temperature=0
        )

    # ------------------------------------------------------------------ #
    # Node 1: Retrieve relevant clauses
    # ------------------------------------------------------------------ #
    async def retrieve(self, state: GraphState) -> dict:
        query = state["query"]
        results = self.vector_store.search(query, k=5)
        documents = [doc for doc, _score in results]
        return {"documents": documents}

    # ------------------------------------------------------------------ #
    # Node 2: Risk analysis on retrieved clauses
    # ------------------------------------------------------------------ #
    async def analyze_risk(self, state: GraphState) -> dict:
        docs = state.get("documents", [])
        if not docs:
            return {"risk_analysis": []}

        clauses = [
            {"id": d.metadata.get("clause_id", f"clause_{i}"), "text": d.page_content}
            for i, d in enumerate(docs)
        ]

        try:
            reports = await self.risk_scorer.analyze_batch(clauses)
            return {"risk_analysis": reports}
        except Exception as e:
            return {
                "risk_analysis": [],
                "final_answer": f"Risk analysis failed: {str(e)}"
            }

    # ------------------------------------------------------------------ #
    # Node 3: Generate plain-English answer
    # ------------------------------------------------------------------ #
    async def generate_answer(self, state: GraphState) -> dict:
        # If a previous node already set final_answer due to an error, pass through
        if state.get("final_answer") and not state.get("risk_analysis"):
            return state

        risks = state.get("risk_analysis", [])
        query = state.get("query", "")

        if not risks:
            return {"final_answer": "No relevant clauses found. Try a different query or ingest a document first."}

        # --- Build overall report stats ---
        def get_attr(obj, attr, default=None):
            return getattr(obj, attr, None) if hasattr(obj, attr) else obj.get(attr, default)

        high = [r for r in risks if get_attr(r, 'risk_level') == "High"]
        med  = [r for r in risks if get_attr(r, 'risk_level') == "Medium"]
        low  = [r for r in risks if get_attr(r, 'risk_level') == "Low"]
        scores = [get_attr(r, 'risk_score', 5) for r in risks]
        avg_score = round(sum(scores) / len(scores), 2) if scores else 0

        overall_report = {
            "overall_risk_score": avg_score,
            "high_risk_count": len(high),
            "medium_risk_count": len(med),
            "low_risk_count": len(low),
        }

        segment_lines = []
        for r in risks:
            cid   = get_attr(r, 'clause_id', 'N/A')
            level = get_attr(r, 'risk_level', 'N/A')
            score = get_attr(r, 'risk_score', 'N/A')
            reason = get_attr(r, 'reason', 'N/A')
            rec   = get_attr(r, 'recommendation', 'N/A')
            segment_lines.append(
                f"- Clause {cid} ({level}, Score: {score}/10): {reason}\n  Recommendation: {rec}"
            )

        segment_text = "\n".join(segment_lines)

        prompt = f"""You are a helpful and expert legal document assistant.
Explain things in simple, plain English that a non-lawyer can understand.

User question: '{query}'

--- Document Risk Statistics ---
Overall Risk Score: {overall_report['overall_risk_score']}/10
Critical (High) Risks: {overall_report['high_risk_count']}
Medium Risks: {overall_report['medium_risk_count']}
Low Risks: {overall_report['low_risk_count']}

--- Clause Analysis ---
{segment_text}

--- Instructions ---
1. Identify the document type (e.g., SaaS Agreement, NDA, Vendor Contract).
2. Use plain language — avoid unexplained legal jargon.
3. Use * to highlight notable facts.
4. Use ** to highlight HIGH risks, critical deadlines, or requirements.
5. Directly and clearly answer the user's specific question based ONLY on the provided analysis.
6. End with a concise summary of key action items.
"""

        try:
            response = await self.reasoning_llm.ainvoke(prompt)
            return {
                "final_answer": response.content,
                "overall_report": overall_report
            }
        except Exception as e:
            return {
                "final_answer": (
                    f"Answer generation failed: {str(e)}\n\n"
                    "This is often caused by API quota limits (free tier: ~20 requests/day). "
                    "Please wait and try again later."
                ),
                "overall_report": overall_report
            }

from pydantic import BaseModel, Field
from typing import List, Optional

class RiskClause(BaseModel):
    """
    Structured output for risk analysis of a single clause.
    """
    clause_id: str = Field(..., description="The clause number or ID (e.g., '1.1', 'Section 5')")
    clause_type: str = Field(..., description="The type of clause (e.g., 'Indemnity', 'Liability Cap', 'Termination')")
    risk_level: str = Field(..., description="Risk level: 'High', 'Medium', 'Low'")
    risk_score: int = Field(..., ge=1, le=10, description="Risk score from 1 (Low) to 10 (High)")
    reason: str = Field(..., description="Brief explanation of why this risk score was assigned.")
    recommendation: str = Field(..., description="Actionable recommendation to mitigate the risk.")

class RiskReport(BaseModel):
    """
    Overall risk report for the document.
    """
    document_id: str
    overall_risk_score: float
    high_risk_clauses: List[RiskClause]
    medium_risk_clauses: List[RiskClause]
    low_risk_clauses: List[RiskClause]

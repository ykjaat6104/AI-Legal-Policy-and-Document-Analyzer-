from typing import List, Dict, Tuple

class RiskRuleEngine:
    """
    Deterministic rule-based risk assessment.
    """
    
    def __init__(self):
        # Define rules: (keyword_pattern, score_modifier, reason)
        self.rules: List[Tuple[List[str], int, str]] = [
            (
                ["indemnify", "unlimited", "loss", "claim"], 
                7, 
                "Potential unlimited indemnity obligation found."
            ),
            (
                ["liability", "aggregate", "cap", "not exceed"], 
                -2, 
                "Liability cap detected (Reduces risk)."
            ),
            (
                ["termination for convenience", "terminate", "without cause"], 
                3, 
                "Termination for convenience clause detected."
            ),
            (
                ["jurisdiction", "exclusive", "governing law"], 
                1, 
                "Verify governing law and jurisdiction."
            ),
            (
                ["auto-renew", "automatic renewal"], 
                2, 
                "Auto-renewal clause present."
            ),
             (
                ["confidential information", "survival"], 
                1, 
                "Confidentiality obligations survive termination."
            )
        ]
        
    def evaluate(self, clause_text: str) -> Tuple[int, List[str]]:
        """
        Evaluate a clause against rules.
        Returns total risk modifier and list of reasons.
        """
        score = 0
        reasons = []
        text_lower = clause_text.lower()
        
        for patterns, modifier, reason in self.rules:
            # Check if all keywords in pattern exist (simple implementation)
            # Or check if any existing pattern matches depending on logic.
            # Let's use ANY pattern match for simplicity or define more complex logic.
            
            # Simple logic: If ANY of the significant keywords are present logic
            # OR logic: if ALL keywords in a tuple
            
            # Let's refine logic: Check if all keywords in the list are present
            if all(keyword in text_lower for keyword in patterns):
                score += modifier
                reasons.append(reason)
                
        return score, reasons


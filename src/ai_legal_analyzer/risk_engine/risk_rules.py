from typing import List, Tuple

class RiskRuleEngine:
    # keyword based risk detection for safety net
    
    def __init__(self):
        # (keywords, score_change, reason)
        self.rules = [
            (["indemnify", "unlimited"], 7, "unlimited indemnity"),
            (["liability", "cap"], -2, "liability cap"),
            (["termination", "convenience"], 3, "termination for convenience"),
            (["auto-renew"], 2, "auto-renewal"),
            (["confidential", "survival"], 1, "survival clause")
        ]
        
    def evaluate(self, text: str):
        # check all rules against text
        score = 0
        found = []
        text_lower = text.lower()
        for keywords, mod, res in self.rules:
            if all(kw in text_lower for kw in keywords):
                score += mod
                found.append(res)
        return score, found

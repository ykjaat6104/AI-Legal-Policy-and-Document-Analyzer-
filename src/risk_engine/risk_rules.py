from typing import List, Tuple


class RiskRuleEngine:
    """Keyword-based deterministic risk scoring as a safety net alongside LLM analysis."""

    def __init__(self):
        # Each rule: (required_keywords, score_modifier, label)
        self.rules: List[Tuple[List[str], int, str]] = [
            (["indemnify", "unlimited"], 7, "unlimited indemnity"),
            (["liability", "cap"], -2, "liability cap present"),
            (["termination", "convenience"], 3, "termination for convenience"),
            (["auto-renew"], 2, "auto-renewal clause"),
            (["confidential", "survival"], 1, "confidentiality survival"),
            (["no warranty", "as is"], 2, "warranty disclaimer"),
            (["governing law"], -1, "governing law defined"),
        ]

    def evaluate(self, text: str) -> Tuple[int, List[str]]:
        """Return (total_score_modifier, list_of_triggered_rule_labels)."""
        score = 0
        triggered: List[str] = []
        text_lower = text.lower()
        for keywords, modifier, label in self.rules:
            if all(kw in text_lower for kw in keywords):
                score += modifier
                triggered.append(label)
        return score, triggered

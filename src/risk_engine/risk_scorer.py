import json
import re
import logging
import asyncio
from typing import List

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

from src.utils.project_config import Config
from .risk_models import RiskClause
from .risk_rules import RiskRuleEngine

logger = logging.getLogger("scorer")


class RiskScorer:
    """Hybrid risk scorer: LLM analysis + deterministic rule engine."""

    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model=Config.LLM_SCAN_MODEL,
            google_api_key=Config.GOOGLE_API_KEY,
            temperature=0
        )
        self.rules = RiskRuleEngine()
        self.parser = PydanticOutputParser(pydantic_object=RiskClause)

        # Single-clause prompt (fallback)
        self.single_prompt = PromptTemplate(
            template="""Analyze the following legal document segment.
segment_id: {clause_id}
content: {clause_text}

Task:
1. Identify the main purpose or topic of this section in simple terms.
2. Detect potential risks, critical facts, or definitive statements.
3. Provide a risk score from 1-10 (10 = highest risk).

Format instructions:
{format_instructions}""",
            input_variables=["clause_id", "clause_text"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )

        # Batch prompt (preferred to save API quota)
        self.batch_prompt = PromptTemplate(
            template="""Analyze the following legal document segments and return a VALID JSON ARRAY.

Segments:
{segments_text}

For EACH segment provide:
1. Its purpose/topic in simple language.
2. Risks or critical facts.
3. A risk score from 1-10.

Return ONLY a valid JSON array (no markdown, no explanation) matching this schema:
[
  {{
    "clause_id": "<original_id>",
    "clause_type": "<type>",
    "risk_level": "<Low|Medium|High>",
    "risk_score": <1-10>,
    "reason": "<plain english explanation>",
    "recommendation": "<actionable advice>"
  }}
]""",
            input_variables=["segments_text"]
        )

    async def analyze_clause(self, clause_id: str, clause_text: str) -> RiskClause:
        """Analyze a single clause (used as fallback)."""
        try:
            chain = self.single_prompt | self.llm | self.parser
            result = await chain.ainvoke({"clause_id": clause_id, "clause_text": clause_text})
        except Exception as e:
            logger.warning(f"Single clause analysis failed for {clause_id}: {e}")
            result = RiskClause(
                clause_id=clause_id,
                clause_type="Unknown",
                risk_level="Medium",
                risk_score=5,
                reason=f"Analysis error: {str(e)}",
                recommendation="Manual review recommended."
            )

        # Apply rule engine on top
        modifier, triggered = self.rules.evaluate(clause_text)
        result.risk_score = max(1, min(10, result.risk_score + modifier))
        result.risk_level = "High" if result.risk_score >= 8 else ("Medium" if result.risk_score >= 5 else "Low")
        if triggered:
            result.reason += f" | Rules triggered: {', '.join(triggered)}"

        return result

    async def analyze_batch(self, clauses: List[dict]) -> List[RiskClause]:
        """
        Analyze multiple clauses in a single LLM call to conserve API quota.
        Falls back to individual calls if batch parsing fails.
        """
        if not clauses:
            return []

        segments_text = "\n\n".join(
            [f"ID: {c['id']}\nContent: {c['text']}" for c in clauses]
        )

        try:
            response = await self.llm.ainvoke(
                self.batch_prompt.format(segments_text=segments_text)
            )
            content = response.content

            # Strip markdown fences if present
            match = re.search(r'\[.*\]', content, re.DOTALL)
            if match:
                content = match.group(0)

            data = json.loads(content)
            results: List[RiskClause] = []

            for item in data:
                original_text = next(
                    (c['text'] for c in clauses if str(c['id']) == str(item.get('clause_id', ''))), ""
                )
                try:
                    rc = RiskClause(**item)
                except Exception:
                    # Try to build a minimal valid object
                    rc = RiskClause(
                        clause_id=item.get('clause_id', 'Unknown'),
                        clause_type=item.get('clause_type', 'Unknown'),
                        risk_level=item.get('risk_level', 'Medium'),
                        risk_score=max(1, min(10, int(item.get('risk_score', 5)))),
                        reason=item.get('reason', 'N/A'),
                        recommendation=item.get('recommendation', 'Review manually.')
                    )

                modifier, triggered = self.rules.evaluate(original_text)
                rc.risk_score = max(1, min(10, rc.risk_score + modifier))
                rc.risk_level = "High" if rc.risk_score >= 8 else ("Medium" if rc.risk_score >= 5 else "Low")
                if triggered:
                    rc.reason += f" | Rules triggered: {', '.join(triggered)}"

                results.append(rc)

            return results

        except Exception as e:
            logger.error(f"Batch analysis failed ({e}), falling back to individual calls…")
            tasks = [self.analyze_clause(c['id'], c['text']) for c in clauses]
            return await asyncio.gather(*tasks)

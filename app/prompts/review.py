from app.prompts.base import BasePrompt


class ReviewPrompt(BasePrompt):

    def build(self, symbol: str):

        return f"""
Review {symbol}

Return ONLY valid JSON.

Schema:

{{
  "summary": "",
  "strengths": [],
  "weaknesses": [],
  "bugs": [],
  "performance": [],
  "security": [],
  "refactor": []
}}

Return JSON only.
"""


review_prompt = ReviewPrompt()

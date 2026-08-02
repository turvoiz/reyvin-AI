import json

from app.prompts.insight_prompt import insight_prompt
from app.services.ai_service import ai_service


class InsightAIService:
    def run(
        self,
        knowledge,
        model,
        thinking,
    ):

        prompt = insight_prompt.build(
            knowledge,
        )

        result = ai_service.chat(
            model=model,
            message=prompt,
            thinking=thinking,
        )

        return json.loads(result["response"])


insight_ai_service = InsightAIService()

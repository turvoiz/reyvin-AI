import json

from app.workspace.cache import workspace_cache
from app.workspace.prompt_builder import prompt_builder
from app.services.ai_service import ai_service


class WorkspaceAIService:

    def run(
        self,
        symbol: str,
        instruction: str,
        model: str,
        thinking: bool,
    ):

        knowledge = workspace_cache.knowledge(symbol)

        prompt = prompt_builder.build(
            knowledge,
            instruction,
        )

        result = ai_service.chat(
            model=model,
            message=prompt,
            thinking=thinking,
        )

        response = result["response"]

        try:
            response = json.loads(response)
        except Exception:
            pass

        return response


workspace_ai_service = WorkspaceAIService()

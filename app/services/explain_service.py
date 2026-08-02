from app.prompts.explain import explain_prompt
from app.services.workspace_ai_service import workspace_ai_service


class ExplainService:

    def explain(
        self,
        symbol: str,
        model: str,
        thinking: bool,
    ):

        answer = workspace_ai_service.run(
            symbol,
            explain_prompt.build(symbol),
            model,
            thinking,
        )

        return {
            "symbol": symbol,
            "answer": answer,
        }


explain_service = ExplainService()

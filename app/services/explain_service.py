from app.services.workspace_ai_service import workspace_ai_service
from app.workspace.cache import workspace_cache
from app.workspace.planner.workspace_planner import workspace_planner


class ExplainService:

    def explain(
        self,
        symbol: str,
        model: str,
        thinking: bool,
        cache=workspace_cache,
    ):

        plan = workspace_planner.plan(
            cache,
            f"Explain {symbol}",
        )

        if not plan["symbols"]:
            return {
                "symbol": symbol,
                "error": "Symbol not found",
            }

        answer = workspace_ai_service.run(
            plan=plan,
            question=f"Explain {symbol}",
            model=model,
            thinking=thinking,
            cache=cache,
        )

        return {
            "symbol": symbol,
            "answer": answer,
        }


explain_service = ExplainService()

from app.services.insight_ai_service import insight_ai_service
from app.workspace.cache import workspace_cache


class InsightService:
    def insight(
        self,
        symbol: str,
        model: str = "auto",
        thinking: bool = False,
    ):

        knowledge = workspace_cache.knowledge(symbol)

        ai = insight_ai_service.run(
            knowledge,
            model,
            thinking,
        )

        return {
            "symbol": symbol,
            "knowledge": knowledge,
            "explanation": ai["explanation"],
            "review": ai["review"],
            "metrics": {
                "calls": len(knowledge["calls"]),
                "callers": len(knowledge["callers"]),
                "references": len(knowledge["references"]),
                "risk": knowledge["impact"]["risk"],
            },
        }


insight_service = InsightService()

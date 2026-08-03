from app.workspace.cache import workspace_cache


class ImpactService:
    def analyze(self, symbol: str):

        calls = workspace_cache.calls()
        refs = workspace_cache.references()

        return {
            "symbol": symbol,
            "calls": calls.get(symbol, []),
            "called_by": refs.get(symbol, []),
        }


impact_service = ImpactService()

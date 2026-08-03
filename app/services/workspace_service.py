from app.services.workspace_ai_service import workspace_ai_service
from app.workspace.cache import workspace_cache
from app.workspace.planner.workspace_planner import workspace_planner


class WorkspaceService:
    def search(self, query: str, cache=workspace_cache):
        return cache.get(query)

    def ask(
        self,
        question: str,
        model: str,
        thinking: bool,
        cache=workspace_cache,
    ):

        plan = workspace_planner.plan(
            cache,
            question,
        )

        if not plan["symbols"]:
            return "Saya tidak menemukan symbol yang dimaksud."

        return workspace_ai_service.run(
            plan=plan,
            question=question,
            model=model,
            thinking=thinking,
            cache=cache,
        )


workspace_service = WorkspaceService()

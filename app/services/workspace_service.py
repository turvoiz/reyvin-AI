from app.workspace.symbol_matcher import symbol_matcher
from app.workspace.cache import workspace_cache
from app.workspace.context_builder import context_builder
from app.services.ai_service import ai_service
from app.workspace.prompt_builder import prompt_builder


class WorkspaceService:

    def search(self, query: str):
        return workspace_cache.get(query)

    def ask(self, question: str, model: str, thinking: bool):

        match = symbol_matcher.match(
            workspace_cache.symbols(),
            question,
        )

        if not match:
            return "Saya tidak menemukan symbol yang dimaksud."

        name, _ = match

        knowledge = workspace_cache.knowledge(name)

        prompt = prompt_builder.build(
            knowledge,
            question,
        )

        result = ai_service.chat(
            model=model,
            message=prompt,
            thinking=thinking,
        )

        return result["response"]




workspace_service = WorkspaceService()
import json

from app.services.ai_service import ai_service
from app.workspace.cache import workspace_cache
from app.workspace.retriever.workspace_retriever import workspace_retriever
from app.workspace.context.context_compressor import context_compressor
from app.workspace.context.context_formatter import context_formatter
from app.workspace.prompt_builder import prompt_builder


class WorkspaceAIService:
    def run(
        self,
        plan,
        question,
        model,
        thinking,
    ):

        context = workspace_retriever.retrieve(
            workspace_cache,
            plan["symbols"][0],
        )

        compressed = context_compressor.compress(
            context,
            plan.get("intent", "explain"),
        )

        formatted = context_formatter.format(
            compressed,
        )

        print("\n========== FORMATTED CONTEXT ==========")
        print(formatted)
        print("======== END FORMATTED CONTEXT ========\n")

        prompt = prompt_builder.build(
            formatted,
            question,
        )

        print("\n================ PROMPT ================\n")
        print(prompt)
        print("\n============== END PROMPT ==============\n")

        result = ai_service.chat(
            model=model,
            message=prompt,
            thinking=thinking,
        )

        response = result["response"]

        try:
            response = json.loads(response)
        except json.JSONDecodeError:
            pass

        return response


workspace_ai_service = WorkspaceAIService()

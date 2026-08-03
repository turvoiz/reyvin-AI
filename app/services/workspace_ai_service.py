import json

from app.services.ai_service import ai_service
from app.workspace.cache import workspace_cache
from app.workspace.context.context_assembler import context_assembler
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
        cache=workspace_cache,
    ):

        symbols = plan.get("symbols", [])

        if not symbols:
            raise ValueError("A workspace symbol is required to run the AI pipeline")

        context = context_assembler.build(
            cache,
            symbols[0],
            plan.get("intent", "explain"),
        )

        if not context.get("symbol"):
            raise ValueError("Workspace context could not be assembled")

        compressed = context_compressor.compress(
            context,
            plan.get("intent", "explain"),
        )

        formatted = context_formatter.format(
            compressed,
        )

        prompt = prompt_builder.build(
            formatted,
            question,
        )

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

        if not response:
            response = "No explanation could be generated from the supplied context."

        return response


workspace_ai_service = WorkspaceAIService()

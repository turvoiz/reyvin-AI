from app.services.ai_service import ai_service
from app.services.workspace_ai_service import workspace_ai_service
from app.workspace.cache import workspace_cache
from app.workspace.context.context_assembler import context_assembler
from app.workspace.context.context_compressor import context_compressor
from app.workspace.context.context_formatter import context_formatter
from app.workspace.prompt_builder import prompt_builder


class CodeService:

    def explain(
        self,
        code,
        file="",
        start_line=0,
        end_line=0,
        model="qwen",
        thinking=False,
        cache=workspace_cache,
    ):

        related = self._related_symbols(
            cache,
            code,
            file,
            start_line,
            end_line,
        )

        context = self._build_context(
            cache,
            code,
            related,
        )

        compressed = context_compressor.compress(
            context,
            "explain",
        )

        formatted = context_formatter.format(
            compressed,
        )

        prompt = prompt_builder.build(
            formatted,
            "Explain the selected code. Describe its responsibility, inputs, outputs, and behavior using the supplied workspace context. If a symbol in the workspace relates to the selection, use it as evidence.",
        )

        result = ai_service.chat(
            model=model,
            message=prompt,
            thinking=thinking,
        )

        answer = result["response"]

        if not answer:
            answer = "No explanation could be generated from the supplied context."

        return {
            "code": code,
            "file": file,
            "related_symbols": [name for name, _ in related],
            "answer": answer,
        }

    def _related_symbols(
        self,
        cache,
        code,
        file,
        start_line,
        end_line,
    ):

        matches = []

        for name, info in cache.symbols().items():

            in_file = bool(file) and info.get("file") == file

            in_range = (
                start_line
                and end_line
                and info.get("start_line", 0) <= end_line
                and info.get("end_line", 0) >= start_line
            )

            named = name in code

            if (in_file and in_range) or named:
                matches.append(
                    (
                        name,
                        info,
                        (in_file and in_range),
                    )
                )

        matches.sort(
            key=lambda item: (
                item[2],
                item[0] in code,
                len(item[0]),
            ),
            reverse=True,
        )

        return [
            (name, info)
            for name, info, _ in matches[:5]
        ]

    def _build_context(
        self,
        cache,
        code,
        related,
    ):

        primary = related[0][0] if related else None

        if primary:

            context = context_assembler.build(
                cache,
                primary,
                "explain",
            )

            context["source"] = code

            return context

        return {
            "symbol": {
                "name": "SELECTED CODE",
                "type": "snippet",
            },
            "source": code,
            "calls": [],
            "callers": [],
            "dependencies": [],
            "impact": {},
            "trace": {},
            "related_sources": [],
            "top_symbols": [],
            "intent": "explain",
        }


code_service = CodeService()

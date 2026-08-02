from app.workspace.cache import workspace_cache
from app.workspace.context_builder import context_builder
from app.services.ai_service import ai_service


class WorkspaceService:

    def search(self, query: str):
        return workspace_cache.get(query)

    def ask(self, question: str, model: str, thinking: bool):

        symbols = workspace_cache.symbols()

        matches = [
            (name, symbol)
            for name, symbol in symbols.items()
            if name.lower() in question.lower()
        ]

        if not matches:
            return "Saya tidak menemukan symbol yang dimaksud."

        name, symbol = max(matches, key=lambda x: len(x[0]))

        context = context_builder.build(symbol)

        prompt = f"""
You are an expert software engineer.

IMPORTANT RULES

- Never guess.
- Never invent information.
- Use ONLY the workspace information below.
- If CALLED BY is not empty, the symbol IS called.
- If DIRECT CALLS is not empty, mention them.
- If the answer exists in the workspace context, you MUST use it.
- If information is missing, say "Not found in workspace".


==================================================
SYMBOL
==================================================
{name}

FILE
==================================================
{symbol['file']}

DIRECT CALLS
==================================================
{chr(10).join('- ' + c['call'] for c in workspace_cache.calls(name)) or '- None'}

CALLED BY
==================================================
{chr(10).join('- ' + c['caller'] for c in workspace_cache.callers(name)) or '- None'}

FILE DEPENDENCIES
==================================================
{chr(10).join('- ' + d for d in workspace_cache.graph()['imports'].get(symbol['file'], [])) or '- None'}

EXECUTION TRACE
==================================================
{workspace_cache.trace(name)}

IMPORTANT:
- DIRECT CALLS = functions called by this symbol.
- WHO USES THIS SYMBOL = callers/importers of this symbol.
- FILE DEPENDENCIES = imported modules.
- EXECUTION TRACE = recursive call chain.

SOURCE
==================================================
{context}

QUESTION
==================================================
{question}

Before answering:

1. Read CALLED BY.
2. Read DIRECT CALLS.
3. Read FILE DEPENDENCIES.
4. Read SOURCE.

Then answer.
"""

        print(prompt)

        result = ai_service.chat(
            model=model,
            message=prompt,
            thinking=thinking,
        )

        return result["response"]




workspace_service = WorkspaceService()

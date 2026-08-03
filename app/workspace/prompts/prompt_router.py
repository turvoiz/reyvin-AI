from app.prompts.explain import explain_prompt
from app.prompts.review import review_prompt


class PromptRouter:

    def build(
        self,
        intent,
        symbol,
    ):

        if intent == "review":
            return review_prompt.build(symbol)

        if intent == "explain":
            return explain_prompt.build(symbol)

        if intent == "impact":
            return f"Impact {symbol}"

        if intent == "trace":
            return f"Trace {symbol}"

        return f"Explain {symbol}"


prompt_router = PromptRouter()

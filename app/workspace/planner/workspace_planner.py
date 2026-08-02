from typing import ClassVar

from app.workspace.symbol_matcher import symbol_matcher


class WorkspacePlanner:
    INTENTS: ClassVar[dict] = {
        "explain": ["explain", "what is", "what does"],
        "review": ["review", "refactor", "improve"],
        "impact": ["impact", "affected", "change"],
        "trace": ["trace", "flow", "call path"],
    }

    def detect_intent(self, question):

        q = question.lower()

        for intent, keywords in self.INTENTS.items():
            if any(k in q for k in keywords):
                return intent

        return "general"

    def plan(
        self,
        cache,
        question,
    ):

        match = symbol_matcher.match(
            cache.symbols(),
            question,
        )

        symbols = []

        if match:
            symbol, _ = match
            symbols.append(symbol)

        return {
            "intent": self.detect_intent(question),
            "symbols": symbols,
        }


workspace_planner = WorkspacePlanner()

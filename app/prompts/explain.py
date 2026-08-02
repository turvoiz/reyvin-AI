from app.prompts.base import BasePrompt


class ExplainPrompt(BasePrompt):

    def build(self, symbol: str):

        return f"""
Explain {symbol}.

Explain:

- Purpose
- Responsibilities
- Parameters
- Return Value
- Dependencies
- Callers
- Risks

Use ONLY workspace knowledge.
"""
        

explain_prompt = ExplainPrompt()

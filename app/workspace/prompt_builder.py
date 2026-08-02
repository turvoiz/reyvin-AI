class PromptBuilder:
    def build(
        self,
        formatted_context,
        instruction,
    ):

        return f"""
You are a senior software architect.

Use ONLY the supplied workspace context.

Never invent information.

{instruction}

{formatted_context}
"""


prompt_builder = PromptBuilder()

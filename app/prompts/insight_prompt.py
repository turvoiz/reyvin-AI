import json


class InsightPrompt:
    def build(
        self,
        knowledge,
    ):

        return f"""
You are a senior software engineer.

Analyze the following code knowledge.

Return ONLY valid JSON.

{{
    "explanation":"",
    "review":{{
        "summary":"",
        "strengths":[],
        "weaknesses":[],
        "bugs":[],
        "performance":[],
        "security":[],
        "refactor":[]
    }}
}}

Knowledge

{json.dumps(knowledge, indent=2)}
"""


insight_prompt = InsightPrompt()

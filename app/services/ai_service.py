from app.llm.providers.ollama import ollama_provider


class AIService:

    def choose_model(self, model: str):

        if model == "auto":
            return "qwen"

        return model

    def chat(
        self,
        model: str,
        message: str,
        thinking: bool,
    ):

        selected = self.choose_model(model)

        result = ollama_provider.chat(
            model=selected,
            message=message,
            thinking=thinking,
        )

        return {
            "response": result["response"],
            "model": selected,
            "thinking": thinking,
            "elapsed_ms": result["elapsed_ms"],
        }


ai_service = AIService()

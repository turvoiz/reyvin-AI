from app.prompts.review import review_prompt
from app.services.workspace_ai_service import workspace_ai_service


class ReviewService:

    def review(
        self,
        symbol: str,
        model: str,
        thinking: bool,
    ):

        review = workspace_ai_service.run(
            symbol,
            review_prompt.build(symbol),
            model,
            thinking,
        )

        return {
            "symbol": symbol,
            "review": review,
        }


review_service = ReviewService()

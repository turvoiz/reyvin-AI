from app.prompts.review import review_prompt
from app.services.workspace_ai_service import workspace_ai_service
from app.workspace.cache import workspace_cache
from app.workspace.planner.workspace_planner import workspace_planner


class ReviewService:

    def review(
        self,
        symbol: str,
        model: str,
        thinking: bool,
    ):

        question = review_prompt.build(symbol)

        plan = workspace_planner.plan(
            workspace_cache,
            question,
        )

        review = workspace_ai_service.run(
            plan=plan,
            question=question,
            model=model,
            thinking=thinking,
        )

        return {
            "symbol": symbol,
            "review": review,
        }


review_service = ReviewService()

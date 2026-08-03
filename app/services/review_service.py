from app.prompts.review import review_prompt
from app.workspace.review.review_validator import review_validator
from app.workspace.review.evidence_validator import evidence_validator
from app.workspace.review.summary_validator import summary_validator
from app.services.workspace_ai_service import workspace_ai_service
from app.workspace.cache import workspace_cache
from app.workspace.planner.workspace_planner import workspace_planner


class ReviewService:

    def review(
        self,
        symbol: str,
        model: str,
        thinking: bool,
        cache=workspace_cache,
    ):

        question = review_prompt.build(symbol)

        plan = workspace_planner.plan(
            cache,
            question,
        )

        if not plan["symbols"]:
            return {
                "symbol": symbol,
                "review": {
                    "summary": "Symbol not found",
                    "strengths": [],
                    "findings": [],
                },
            }

        review = workspace_ai_service.run(
            plan=plan,
            question=question,
            model=model,
            thinking=thinking,
            cache=cache,
        )

        context = cache.knowledge(
            symbol
        )

        review = review_validator.validate(
            review
        )

        review = evidence_validator.validate(
            review,
            context,
        )

        review = summary_validator.validate(
            review
        )

        return {
            "symbol": symbol,
            "review": review,
        }


review_service = ReviewService()

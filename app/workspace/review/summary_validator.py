class SummaryValidator:

    def validate(
        self,
        review,
    ):

        findings = review.get(
            "findings",
            []
        )

        if not findings:

            review["summary"] = (
                "No significant issues were identified "
                "based on the supplied code evidence."
            )

            review["strengths"] = (
                review.get("strengths", [])
                or [
                    "The implementation follows "
                    "a straightforward structure."
                ]
            )

        return review


summary_validator = SummaryValidator()

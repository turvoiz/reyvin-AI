class ReviewValidator:

    def validate(
        self,
        review,
    ):

        findings = []

        for item in review.get("findings", []):

            issue = item.get(
                "issue",
                ""
            ).lower()

            evidence = item.get(
                "evidence",
                ""
            ).lower()

            combined = issue + " " + evidence


            # Design choices are not findings
            if any(
                word in combined
                for word in [
                    "hard-coded",
                    "hardcoded",
                    "fixed value",
                    "fixed value",
                ]
            ):
                if any(
                    word in combined
                    for word in [
                        "auto",
                        "qwen",
                        "default",
                        "fallback",
                        "configuration",
                    ]
                ):
                    continue


            # Missing validation alone is not a defect
            if (
                "lack validation" in combined
                or "lacks validation" in combined
                or "no validation" in combined
            ):
                if not any(
                    x in combined
                    for x in [
                        "crash",
                        "exception",
                        "security",
                        "incorrect",
                        "corrupt",
                        "broken",
                    ]
                ):
                    continue


            # Configuration fallback is not automatically a bug
            if (
                "environment variable" in combined
                or "configuration" in combined
            ):
                if not any(
                    x in combined
                    for x in [
                        "crash",
                        "exception",
                        "broken",
                        "security",
                    ]
                ):
                    continue


            # Missing parameter validation alone is not a finding
            if (
                "validate the input" in combined
                or "validates the input" in combined
                or "validation" in combined
            ):
                if not any(
                    x in combined
                    for x in [
                        "security",
                        "injection",
                        "crash",
                        "exception",
                        "invalid state",
                        "incorrect result",
                    ]
                ):
                    continue


            # Logging absence is not a defect
            if "logging" in combined:
                continue


            findings.append(item)


        review["findings"] = findings

        return review


review_validator = ReviewValidator()

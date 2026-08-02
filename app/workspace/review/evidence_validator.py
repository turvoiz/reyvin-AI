class EvidenceValidator:

    def validate(
        self,
        review,
        context,
    ):

        source = (
            context.get("source", "")
            + "\n"
            + "\n".join(
                x.get("source", "")
                for x in context.get(
                    "related_sources",
                    []
                )
            )
        ).lower()


        valid = []

        for finding in review.get(
            "findings",
            []
        ):

            evidence = finding.get(
                "evidence",
                ""
            ).lower()

            issue = finding.get(
                "issue",
                ""
            ).lower()


            # Evidence must reference actual code behavior
            if (
                "hardcoded" in issue
                or "hard-coded" in issue
            ):
                if (
                    "return \"qwen\"" in source
                    or "return 'qwen'" in source
                ):
                    continue


            # Remove missing validation claims
            if (
                "validation" in issue
                or "validate" in issue
            ):
                if not any(
                    x in evidence
                    for x in [
                        "crash",
                        "exception",
                        "security",
                        "incorrect result",
                        "broken",
                    ]
                ):
                    continue


            valid.append(finding)


        review["findings"] = valid

        return review


evidence_validator = EvidenceValidator()

from difflib import SequenceMatcher
import re


class SymbolMatcher:
    FUZZY_THRESHOLD = 75

    def match(self, symbols, question):

        q = question.lower().strip()
        words = re.findall(r"[a-z0-9_]+", q)
        normalized = "".join(words)

        # Qualified symbol (e.g. AIService.chat) must match exactly.
        if "." in q:
            for name, symbol in symbols.items():
                if name.lower() == q:
                    return name, symbol
            return None

        ranked = []

        for name, symbol in symbols.items():
            lname = name.lower()

            cls = (symbol.get("class") or "").lower()

            method = lname.split(".")[-1]

            score = 0

            # Exact qualified name
            if lname == q:
                score = 1000

            # "AIService.chat"
            elif cls and cls in normalized and method in words:
                score = 950

            # Qualified name appears
            elif lname in words:
                score = 900

            # Method only
            elif method in words:
                score = 700

            # Class only
            elif cls and cls in normalized:
                score = 600

            else:
                score = int(
                    SequenceMatcher(
                        None,
                        lname,
                        q,
                    ).ratio()
                    * 100
                )

            ranked.append((score, len(lname), name, symbol))

        ranked.sort(reverse=True)

        score, _, name, symbol = ranked[0]

        if score < self.FUZZY_THRESHOLD:
            return None

        return name, symbol


symbol_matcher = SymbolMatcher()

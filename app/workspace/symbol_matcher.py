from difflib import SequenceMatcher


class SymbolMatcher:
    def match(self, symbols, question):

        q = question.lower()

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
            elif cls and cls in q and method in q:
                score = 950

            # Qualified name appears
            elif lname in q:
                score = 900

            # Method only
            elif method in q:
                score = 700

            # Class only
            elif cls and cls in q:
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

        if score < 60:
            return None

        return name, symbol


symbol_matcher = SymbolMatcher()

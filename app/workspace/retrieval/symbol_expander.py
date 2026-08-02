from collections import deque


class SymbolExpander:

    def expand(
        self,
        cache,
        symbol,
        depth=2,
        limit=20,
    ):

        seen = {symbol}
        result = []
        queue = deque([(symbol, 0)])

        while queue and len(result) < limit:

            current, level = queue.popleft()

            result.append(current)

            if level >= depth:
                continue

            knowledge = cache.knowledge(current)

            if not knowledge:
                continue

            neighbors = []

            for call in knowledge.get("calls", []):
                neighbors.append(call["call"])

            for caller in knowledge.get("callers", []):
                neighbors.append(caller["caller"])

            for neighbor in neighbors:

                if neighbor in seen:
                    continue

                if not cache.get(neighbor):
                    continue

                seen.add(neighbor)
                queue.append((neighbor, level + 1))

        return result


symbol_expander = SymbolExpander()

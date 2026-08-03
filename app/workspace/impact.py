class ImpactAnalyzer:
    def _walk(self, reverse_graph, symbol, visited):

        if symbol in visited:
            return

        visited.add(symbol)

        for caller in reverse_graph.get(symbol, []):
            self._walk(
                reverse_graph,
                caller["caller"],
                visited,
            )

    def analyze(self, reverse_graph, symbol):

        visited = set()

        self._walk(
            reverse_graph,
            symbol,
            visited,
        )

        visited.discard(symbol)

        return sorted(visited)


impact_analyzer = ImpactAnalyzer()

class TraceEngine:
    def trace(self, graph, start, visited=None):

        if visited is None:
            visited = set()

        if start in visited:
            return {}

        visited.add(start)

        result = {}

        for call in graph.get(start, []):
            target = call["call"]

            result[target] = self.trace(
                graph,
                target,
                visited,
            )

        return result


trace_engine = TraceEngine()

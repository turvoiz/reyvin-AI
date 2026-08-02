from time import perf_counter

from app.workspace.cache import workspace_cache

workspace_cache.load(".")

start = perf_counter()

workspace_cache.rebuild()

elapsed = perf_counter() - start

print(f"Rebuild: {elapsed:.3f}s")

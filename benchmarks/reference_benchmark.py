import time

from app.workspace.cache import workspace_cache

workspace_cache.load(".")

start = time.perf_counter()

workspace_cache.rebuild()

elapsed = time.perf_counter() - start

print(f"Incremental rebuild : {elapsed:.4f}s")

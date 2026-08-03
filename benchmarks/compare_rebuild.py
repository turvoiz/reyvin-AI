import time

from app.workspace.cache import workspace_cache

print("Loading workspace...")
workspace_cache.load(".")

print()

start = time.perf_counter()
workspace_cache.reload()
reload_time = time.perf_counter() - start

start = time.perf_counter()
workspace_cache.rebuild()
rebuild_time = time.perf_counter() - start

print(f"Reload      : {reload_time:.4f}s")
print(f"Incremental : {rebuild_time:.4f}s")

if rebuild_time > 0:
    print(f"Speedup     : {reload_time/rebuild_time:.2f}x")

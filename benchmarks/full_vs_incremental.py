import time

from app.workspace.cache import workspace_cache
from app.workspace.storage.snapshot import workspace_snapshot

workspace_snapshot.FILE.unlink(missing_ok=True)

start = time.perf_counter()
workspace_cache.load(".")
full = time.perf_counter() - start

start = time.perf_counter()
workspace_cache.rebuild()
inc = time.perf_counter() - start

print(f"Full build  : {full:.4f}s")
print(f"Incremental : {inc:.4f}s")

if inc > 0:
    print(f"Speedup     : {full/inc:.2f}x")

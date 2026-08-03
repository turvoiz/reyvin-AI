from pathlib import Path

from app.services.ai_service import ai_service
from app.workspace.cache import workspace_cache
from app.workspace.prompt_builder import prompt_builder


class ArchitectureService:

    def explain(
        self,
        model,
        thinking,
        cache=workspace_cache,
    ):

        summary = self._summarize(cache)

        formatted = self._format(summary)

        prompt = prompt_builder.build(
            formatted,
            "Describe the overall architecture of this repository. Cover the main components, their responsibilities, how they relate through calls and imports, and any clear hotspots. Base every claim on the supplied workspace summary.",
        )

        result = ai_service.chat(
            model=model,
            message=prompt,
            thinking=thinking,
        )

        answer = result["response"]

        if not answer:
            answer = "No architecture summary could be generated from the supplied context."

        return {
            "summary": summary,
            "answer": answer,
        }

    def _summarize(self, cache):

        symbols = cache.symbols()

        files = {}
        languages = {}

        for info in symbols.values():
            files[info["file"]] = files.get(info["file"], 0) + 1

            suffix = Path(info["file"]).suffix or "unknown"

            languages[suffix] = languages.get(suffix, 0) + 1

        hotspots = []

        for name in symbols:
            callers = cache.callers(name)

            if callers:
                hotspots.append(
                    {
                        "symbol": name,
                        "callers": len(callers),
                    }
                )

        hotspots.sort(
            key=lambda item: item["callers"],
            reverse=True,
        )

        imports = cache.graph()["imports"]

        edges = []

        for source, targets in imports.items():
            for target in targets[:10]:
                edges.append(
                    {
                        "from": source,
                        "to": target,
                    }
                )

        edges.sort(
            key=lambda item: (item["from"], item["to"]),
        )

        return {
            "workspace": cache.workspace,
            "languages": dict(
                sorted(
                    languages.items(),
                    key=lambda item: item[1],
                    reverse=True,
                )
            ),
            "total_files": len(files),
            "total_symbols": len(symbols),
            "top_files": sorted(
                files.items(),
                key=lambda item: item[1],
                reverse=True,
            )[:10],
            "hotspots": hotspots[:15],
            "import_edges": edges[:20],
            "deadcode_count": len(cache.deadcode()),
        }

    def _format(self, summary):

        files = "\n".join(
            f"{name} ({count} symbols)"
            for name, count in summary["top_files"]
        )

        languages = "\n".join(
            f".{lang}: {count}"
            for lang, count in summary["languages"].items()
        )

        hotspots = "\n".join(
            f"{item['symbol']} ({item['callers']} callers)"
            for item in summary["hotspots"]
        )

        edges = "\n".join(
            f"{edge['from']} -> {edge['to']}"
            for edge in summary["import_edges"]
        )

        return f"""
==================================================
REPOSITORY SUMMARY
==================================================

WORKSPACE:
{summary["workspace"]}

LANGUAGES:
{languages}

TOTAL FILES:
{summary["total_files"]}

TOTAL SYMBOLS:
{summary["total_symbols"]}

DEADCODE COUNT:
{summary["deadcode_count"]}

==================================================
TOP FILES BY SYMBOL COUNT
==================================================

{files}

==================================================
SYMBOL HOTSPOTS (MOST CALLED)
==================================================

{hotspots}

==================================================
IMPORT EDGES (TOP)
==================================================

{edges}
"""


architecture_service = ArchitectureService()

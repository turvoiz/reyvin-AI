import re

WEB_KEYWORDS = (
    "version",
    "library",
    "deprecated",
    "deprecat",
    "policy",
    "must use",
    "requires",
    "require",
    "outdated",
    "minimum",
    "no longer",
    "compliance",
    "api key",
    "certificate",
    "signing",
    "sdk",
    "billing",
    "targetsdk",
    "compileSdk",
    "compile sdk",
)

QUERY_CLEANUP = re.compile(r"[^\w\s:.\-/@']+")


class WebSearchService:
    def __init__(self):
        self.enabled = True
        self._search_func = None

    def needs_search(self, error):
        if not self.enabled:
            return False
        if not error:
            return False
        low = error.lower()
        return any(keyword in low for keyword in WEB_KEYWORDS)

    def build_query(self, error, limit=200):
        cleaned = QUERY_CLEANUP.sub(" ", error).strip()
        cleaned = re.sub(r"\s+", " ", cleaned)
        return cleaned[:limit]

    def search(self, query, limit=5):
        if not query:
            return []

        try:
            results = self._run_search(query, limit)
        except Exception:  # noqa: BLE001 - network fallback for a local tool
            return []

        cleaned = []
        for item in results:
            if not isinstance(item, dict):
                continue
            title = str(item.get("title") or "").strip()
            url = str(item.get("href") or item.get("url") or "").strip()
            body = str(item.get("body") or item.get("snippet") or "").strip()
            if not url:
                continue
            if not title and not body:
                continue
            cleaned.append(
                {
                    "title": title,
                    "url": url,
                    "body": body,
                }
            )

        return cleaned

    def _run_search(self, query, limit):
        if self._search_func is not None:
            return self._search_func(query, limit)

        from ddgs import DDGS

        with DDGS() as ddgs:
            results = ddgs.text(query, max_results=limit)

        return list(results)


web_search_service = WebSearchService()

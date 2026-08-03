import re
from pathlib import Path

CAMEL_RE = re.compile(r"([a-z0-9])([A-Z])")
TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_.\-]*")
VERSION_RE = re.compile(r"\d+(?:\.\d+)+")

STOPWORDS = frozenset(
    [
        "about", "actively", "add", "added", "after", "against", "all", "also",
        "always", "and", "any", "app", "apps", "are", "as", "at", "available",
        "based", "because", "been", "before", "being", "between", "both",
        "but", "by", "can", "cannot", "change", "changes", "check", "could",
        "date", "day", "did", "does", "each", "ensure", "error", "even",
        "experience", "failed", "failure", "feature", "features", "file",
        "from", "get", "has", "have", "how", "if", "include", "included",
        "including", "into", "is", "later", "library", "line", "make", "many",
        "may", "meet", "more", "most", "must", "new", "now", "occurred",
        "old", "on", "only", "or", "other", "our", "out", "over", "per",
        "prevent", "provide", "provides", "providers", "publish", "published",
        "publishing", "recomend", "recommend", "recommended", "rejected",
        "rejection", "required", "requirements", "safe", "secure", "set",
        "should", "some", "still", "sure", "than", "that", "the", "their",
        "them", "then", "there", "these", "they", "this", "those", "through",
        "throw", "thrown", "tracks", "type", "update", "updates", "updated",
        "upgraded", "use", "used", "uses", "using", "version", "via", "want",
        "was", "way", "were", "what", "when", "where", "which", "while", "who",
        "will", "with", "within", "without", "would", "year", "years", "you",
        "your", "jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep",
        "oct", "nov", "dec",
    ]
)

MANIFEST_REL = (
    "package.json",
    "pyproject.toml",
    "requirements.txt",
    "app.json",
    "app.config.js",
    "app.config.ts",
    "expo.config.js",
    "android/app/build.gradle",
    "android/build.gradle",
    "android/settings.gradle",
    "android/gradle.properties",
    "go.mod",
    "Cargo.toml",
    "pom.xml",
    "Podfile",
)


class ErrorSearch:

    def keywords(self, error, limit=12):

        seen = set()

        keywords = []

        for token in TOKEN_RE.findall(error):

            lower = token.lower()

            if len(token) < 3 or lower in STOPWORDS:
                continue

            for part in CAMEL_RE.sub(r"\1 \2", lower).split():

                part = part.rstrip(".-")

                if len(part) < 3 or part in STOPWORDS:
                    continue

                if part not in seen:
                    seen.add(part)
                    keywords.append(part)

        for version in VERSION_RE.findall(error):

            if version not in seen:
                seen.add(version)
                keywords.append(version)

        return keywords[:limit]

    def search(
        self,
        cache,
        error,
        limit=6,
        max_files=150,
    ):

        keywords = self.keywords(error)

        root = Path(cache.workspace)

        manifest_priority = {
            rel: index
            for index, rel in enumerate(MANIFEST_REL)
        }

        files = {}

        for rel in cache.files():
            files[rel] = "source"

        for rel in MANIFEST_REL:
            if (root / rel).is_file():
                files.setdefault(rel, "manifest")

        manifest_hits = []

        source_hits = []

        budget = max_files

        for rel in sorted(
            files,
            key=self._sort_key(keywords, manifest_priority),
        ):

            kind = files[rel]

            if kind == "source":

                if budget <= 0:
                    continue

                budget -= 1

            path = root / rel

            if not path.is_file():
                continue

            try:
                text = path.read_text(
                    encoding="utf-8",
                    errors="ignore",
                )
            except OSError:
                continue

            score, hits = self._score(text, keywords)

            if kind == "source" and score == 0:
                continue

            target = (
                manifest_hits
                if kind == "manifest"
                else source_hits
            )

            target.append(
                {
                    "file": rel,
                    "kind": kind,
                    "score": score,
                    "hits": hits,
                    "snippet": self._snippet(
                        text,
                        keywords,
                        max_chars=4000,
                        full=(kind == "manifest"),
                    ),
                }
            )

        manifest_hits.sort(
            key=lambda item: (
                -item["score"],
                manifest_priority.get(item["file"], 999),
                item["file"],
            )
        )

        source_hits.sort(
            key=lambda item: (
                -item["score"],
                item["file"],
            )
        )

        results = manifest_hits[:2] + source_hits

        return results[:limit]

    def _sort_key(
        self,
        keywords,
        manifest_priority,
    ):

        def key(rel):

            lower = rel.lower()

            path_hit = any(
                keyword in lower
                for keyword in keywords
            )

            return (
                rel not in manifest_priority,
                not path_hit,
                lower,
            )

        return key

    def _score(
        self,
        text,
        keywords,
    ):

        lowered = text.lower()

        hits = {}

        for keyword in keywords:

            count = lowered.count(keyword)

            if count:
                hits[keyword] = count

        return sum(hits.values()), hits

    def _snippet(
        self,
        text,
        keywords,
        max_chars=1600,
        full=False,
    ):

        lines = text.splitlines()

        if full or not keywords:

            selected = list(
                range(1, len(lines) + 1)
            )

            return self._render(lines, selected, max_chars)

        lowered_lines = [
            line.lower()
            for line in lines
        ]

        hit_lines = [
            index + 1
            for index, line in enumerate(lowered_lines)
            if any(
                keyword in line
                for keyword in keywords
            )
        ]

        if not hit_lines:

            selected = list(
                range(1, min(40, len(lines)) + 1)
            )

        else:

            selected = set()

            for line in hit_lines:

                selected.update(
                    range(line - 1, line + 2)
                )

            selected = sorted(
                line
                for line in selected
                if 1 <= line <= len(lines)
            )

        return self._render(lines, selected, max_chars)

    def _render(
        self,
        lines,
        selected,
        max_chars,
    ):

        out = []

        chars = 0

        for line in selected:

            entry = f"{line}: {lines[line - 1]}"

            out.append(entry)

            chars += len(entry) + 1

            if chars > max_chars:

                out.append("... (truncated)")

                break

        return "\n".join(out)


error_search = ErrorSearch()

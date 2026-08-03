import json
import re
from pathlib import Path

from app.services.ai_service import ai_service
from app.services.web_search_service import web_search_service
from app.workspace.cache import workspace_cache
from app.workspace.context.context_assembler import context_assembler
from app.workspace.context.context_compressor import context_compressor
from app.workspace.context.context_formatter import context_formatter
from app.workspace.prompt_builder import prompt_builder
from app.workspace.search.error_search import error_search
from app.workspace.symbol_matcher import symbol_matcher


class DiagnoseService:

    JS_PAREN = re.compile(
        r"at\s+(?:async\s+)?([\w$.<>]+)\s*\(([^):]+):(\d+):\d+\)"
    )
    JS_BARE = re.compile(
        r"at\s+([^:()\s\\/]+):(\d+):\d+"
    )
    PY_FRAME = re.compile(
        r'File\s+"([^"]+)",\s+line\s+(\d+)(?:,\s+in\s+([\w<>]+))?'
    )
    PATH_LINE = re.compile(
        r"([\w./\\-]+\.(?:py|ts|tsx|js|jsx)):(\d+)"
    )
    MOBILE_ERROR_PATTERN = re.compile(
        r"(play billing|billing library|google play|play console|compilesdk|"
        r"targetsdk|react[- ]native|expo|flutter|xcode|app store|"
        r"bundle identifier|\bandroid\b|\bgradle\b|\bios\b|\badb\b)",
        re.IGNORECASE,
    )
    MOBILE_WORKSPACE_HINTS = (
        "react-native",
        "react_native",
        "expo",
        "purchases",
        "flutter",
    )

    def diagnose(
        self,
        error,
        file="",
        model="qwen",
        thinking=False,
        cache=workspace_cache,
    ):

        frames = self._extract_frames(
            error,
            file,
        )

        matched = self._match_frames(
            cache,
            frames,
        )

        context = self._build_context(
            cache,
            matched,
            error,
        )

        compressed = context_compressor.compress(
            context,
            "diagnose",
        )

        formatted = context_formatter.format(
            compressed,
        )

        frame_text = self._format_frames(
            matched,
            frames,
        )

        question = (
            "A failure was reported. Diagnose the root cause using only the "
            "supplied workspace context as evidence.\n\n"
            "REPORTED ERROR:\n"
            f"{error}\n\n"
            "MATCHED STACK FRAMES:\n"
            f"{frame_text}\n\n"
            "If no stack frames matched, trace the root cause using the "
            "WORKSPACE CONTEXT (dependency manifest files and matched source "
            "evidence). For library, version, or policy errors:\n"
            "- Locate the exact dependency entry or configuration in the "
            "manifests (package.json, pyproject.toml, build.gradle, ...) that "
            "the error refers to.\n"
            "- Store-library errors (Google Play Billing Library, StoreKit, "
            "App Store IAP, ...) are usually caused by a subscription/IAP SDK "
            "that BUNDLES the store library transitively. When the error says "
            "to update a third-party SDK, search the workspace for that SDK "
            "(for example react-native-purchases / RevenueCat in "
            "package.json) and fix by UPGRADING THE SDK version, never by "
            "hand-adding the bundled library to a gradle file.\n"
            "- The fix MUST name a file that exists in this workspace AND that "
            "declares the dependency or configuration the error mentions. "
            "Never invent files, dependencies, or versions.\n"
            "- NEVER suggest adding a dependency or library that is not "
            "already present in the workspace.\n"
            "- A version bump is only valid if the error names that library, "
            "the workspace actually declares it, and the WEB EVIDENCE (if "
            "supplied) supports the target version and upgrade path.\n"
            "- If the workspace does not contain the technology the error "
            "refers to, return fixes: [] and state the mismatch in root_cause.\n\n"
            "Respond with ONLY valid JSON, no surrounding text:\n"
            "{\n"
            '  "root_cause": "one sentence root cause",\n'
            '  "location": "file:line:symbol (or the closest matched symbol)",\n'
            '  "explanation": "detailed explanation tied to the code evidence",\n'
            '  "fixes": [{"description": "what to fix", "file": "", '
            '"symbol": "", "suggestion": "concrete code-level fix"}]\n'
            "}"
        )

        web_evidence = self._web_evidence(error)

        if web_evidence:
            lines = [
                f"- {item['title']} ({item['url']}): {item['body']}"
                for item in web_evidence
            ]
            question += "\n\nWEB EVIDENCE (from internet search):\n" + "\n".join(lines)

        mismatch = self._stack_mismatch(cache, error)

        if mismatch:
            question += (
                "\n\nSTACK MISMATCH WARNING:\n"
                "The reported error refers to an Android/iOS/mobile "
                "technology (for example Google Play Billing), but this "
                "workspace does not appear to contain a mobile project (no "
                "android/, ios/, or react-native/expo dependency). The error "
                "probably belongs to a different repository.\n"
                "Do not invent a fix here. Set file and symbol to \"\" and "
                "return fixes: [] unless you can point to an existing file in "
                "this workspace that is genuinely responsible for the "
                "reported error."
            )

        prompt = prompt_builder.build(
            formatted,
            question,
            external=bool(web_evidence),
        )

        result = ai_service.chat(
            model=model,
            message=prompt,
            thinking=thinking,
        )

        response = result["response"]

        diagnosis = self._parse_response(
            response,
            error,
            matched,
        )

        if isinstance(diagnosis, dict):
            diagnosis["fixes"] = self._prune_fixes(
                cache,
                diagnosis.get("fixes") or [],
            )

            if mismatch and not diagnosis.get("fixes"):
                diagnosis["explanation"] = (
                    "The reported error appears to belong to a different "
                    "project than this workspace. No valid fix location was "
                    "found, so no fix was suggested."
                )

        return {
            "frames": matched,
            "diagnosis": diagnosis,
            "model": result["model"],
            "elapsed_ms": result["elapsed_ms"],
        }

    def _web_evidence(self, error):
        if not web_search_service.needs_search(error):
            return []

        query = web_search_service.build_query(error)

        return web_search_service.search(query)

    def _stack_mismatch(self, cache, error):
        if not self._error_hints_mobile(error):
            return False

        return not self._workspace_has_mobile_stack(cache)

    def _error_hints_mobile(self, error):
        return bool(self.MOBILE_ERROR_PATTERN.search(error or ""))

    def _workspace_has_mobile_stack(self, cache):
        root = Path(cache.workspace)

        if (root / "android").is_dir():
            return True

        if (root / "ios").is_dir():
            return True

        if (root / "pubspec.yaml").is_file():
            return True

        package = root / "package.json"

        if package.is_file():
            try:
                text = package.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                return False

            lowered = text.lower()

            if any(hint in lowered for hint in self.MOBILE_WORKSPACE_HINTS):
                return True

        return False

    def _prune_fixes(self, cache, fixes):
        root = Path(cache.workspace).resolve()

        kept = []

        for fix in fixes:
            if not isinstance(fix, dict):
                continue

            file_name = str(fix.get("file") or "").strip()

            if not file_name:
                kept.append(fix)
                continue

            raw = Path(file_name.replace("\\", "/"))

            if raw.is_absolute():
                continue

            try:
                candidate = (root / raw).resolve()
                candidate.relative_to(root)
            except (OSError, ValueError):
                continue

            if candidate.is_file():
                kept.append(fix)

        return kept

    def _extract_frames(
        self,
        error,
        file,
    ):

        frames = []

        seen = set()

        for match in self.JS_PAREN.finditer(error):
            self._add_frame(
                frames,
                seen,
                match.group(2),
                match.group(3),
                match.group(1),
            )

        for match in self.PY_FRAME.finditer(error):
            self._add_frame(
                frames,
                seen,
                match.group(1),
                match.group(2),
                match.group(3),
            )

        for match in self.JS_BARE.finditer(error):
            self._add_frame(
                frames,
                seen,
                match.group(1),
                match.group(2),
                "",
            )

        for match in self.PATH_LINE.finditer(error):
            self._add_frame(
                frames,
                seen,
                match.group(1),
                match.group(2),
                "",
            )

        if file and not frames:
            frames.append(
                {
                    "file": file,
                    "line": 0,
                    "function": "",
                }
            )

        return frames

    def _add_frame(
        self,
        frames,
        seen,
        file,
        line,
        function,
    ):

        key = (
            file,
            line,
        )

        if key in seen:
            return

        seen.add(key)

        frames.append(
            {
                "file": file,
                "line": int(line),
                "function": function,
            }
        )

    def _match_frames(
        self,
        cache,
        frames,
    ):

        symbols = cache.symbols()

        matched = []

        seen = set()

        for frame in frames:

            name = frame["function"]

            symbol = None

            if name:
                symbol = self._match_name(
                    symbols,
                    name,
                )

            if not symbol:
                symbol = self._match_file(
                    symbols,
                    frame["file"],
                )

            symbol_key = symbol or ""

            if symbol_key in seen:
                continue

            seen.add(symbol_key)

            matched.append(
                {
                    "file": frame["file"],
                    "line": frame["line"],
                    "function": frame["function"],
                    "symbol": symbol,
                }
            )

        return matched

    def _match_name(
        self,
        symbols,
        name,
    ):

        if name in symbols:
            return name

        if name.endswith(">") and "<" in name:
            name = name[name.index("<") + 1:name.index(">")]

        result = symbol_matcher.match(
            symbols,
            name,
        )

        if result:
            return result[0]

        return None

    def _match_file(
        self,
        symbols,
        file,
    ):

        normalized = self._relative(file)

        candidates = [
            symbol
            for symbol, info in symbols.items()
            if info.get("file") == file
            or info.get("file") == normalized
            or info.get("file", "").endswith("/" + normalized)
            or normalized.endswith("/" + info.get("file", ""))
        ]

        if not candidates:
            return None

        candidates.sort(
            key=lambda symbol: (
                symbols[symbol].get("start_line", 0),
                symbol,
            ),
        )

        return candidates[0]

    def _relative(
        self,
        path,
    ):

        normalized = path.replace("\\", "/")

        parts = normalized.split("/")

        for index in range(len(parts) - 1):
            candidate = "/".join(parts[index + 1:])
            if candidate.endswith(
                ("ts", "tsx", "js", "jsx", "py")
            ):
                return candidate

        return normalized

    def _build_context(
        self,
        cache,
        matched,
        error,
    ):

        primary = matched[0]["symbol"] if matched else None

        if primary:

            context = context_assembler.build(
                cache,
                primary,
                "review",
            )

            return context

        evidence = error_search.search(
            cache,
            error,
        )

        related_sources = [
            {
                "symbol": item["file"],
                "type": item["kind"],
                "source": item["snippet"],
            }
            for item in evidence
        ]

        return {
            "symbol": {
                "name": "REPORTED ERROR",
                "type": "error",
            },
            "source": error[:1200],
            "calls": [],
            "callers": [],
            "dependencies": [
                item["file"]
                for item in evidence
            ],
            "impact": {},
            "trace": {
                "keywords": error_search.keywords(error),
                "evidence": [
                    item["file"]
                    for item in evidence
                ],
            },
            "related_sources": related_sources,
            "top_symbols": [],
            "intent": "diagnose",
        }

    def _format_frames(
        self,
        matched,
        frames,
    ):

        if matched:
            lines = [
                f"{item['file']}:{item['line']}"
                + (f" in {item['function']}" if item["function"] else "")
                + (f" -> matched symbol: {item['symbol']}" if item["symbol"] else " -> no symbol match")
                for item in matched
            ]
            return "\n".join(lines)

        if frames:
            lines = [
                f"{item['file']}:{item['line']}"
                + (f" in {item['function']}" if item["function"] else "")
                for item in frames
            ]
            return "\n".join(lines)

        return "No stack frame could be parsed from the reported error."

    def _parse_response(
        self,
        response,
        error,
        matched,
    ):

        text = re.sub(
            r"```(?:json)?\s*",
            "",
            response.strip(),
        )

        diagnosis = None

        try:
            parsed = json.loads(text)

            if isinstance(parsed, dict):
                diagnosis = parsed
        except json.JSONDecodeError:
            pass

        if not isinstance(diagnosis, dict):

            decoder = json.JSONDecoder()

            for start in range(len(text)):

                if text[start] != "{":
                    continue

                try:
                    obj, _ = decoder.raw_decode(text[start:])
                except json.JSONDecodeError:
                    continue

                if not isinstance(obj, dict):
                    continue

                root_cause = obj.get("root_cause")

                if (
                    isinstance(root_cause, str)
                    and not root_cause.lstrip().startswith("{")
                ):
                    diagnosis = obj

        if not isinstance(diagnosis, dict):

            if text:
                diagnosis = {
                    "root_cause": text[:4000],
                    "location": matched[0]["symbol"] if matched else "",
                    "explanation": "",
                    "fixes": [],
                }
            else:
                diagnosis = {}

        if not diagnosis.get("root_cause"):
            diagnosis["root_cause"] = (
                "Could not determine the root cause from the supplied "
                "workspace context."
            )

        if not isinstance(diagnosis.get("fixes"), list):
            diagnosis["fixes"] = []

        return diagnosis


diagnose_service = DiagnoseService()

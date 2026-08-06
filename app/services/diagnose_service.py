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
from app.workspace.tech_mismatch import stack_mismatch


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

    MAX_CLARIFYING_TURNS = 3

    def diagnose(
        self,
        error,
        file="",
        model="qwen",
        thinking=False,
        cache=workspace_cache,
        history=None,
    ):

        history = history or []

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
            "refers to, return fixes: [] and state the mismatch in root_cause.\n"
            "- If the same buggy pattern is repeated at more than one call "
            "site (for example the same function called without a required "
            "argument in several places), do not silently fix only one. "
            "List every affected file:line you can see in the supplied "
            "context inside that fix's \"suggestion\" text, so the fix can "
            "be applied to all of them in a single pass. A fix that only "
            "covers some of the known call sites is incomplete — never "
            "present it as a full fix.\n\n"
        )

        questions_asked = sum(
            1 for turn in history if turn.get("role") == "assistant"
        )

        remaining_questions = max(0, self.MAX_CLARIFYING_TURNS - questions_asked)

        if remaining_questions > 0:
            question += (
                "You may respond in one of two ways:\n"
                "1. If the supplied context is genuinely insufficient to "
                "pinpoint the root cause, ask ONE clarifying question "
                'instead of guessing: {"status": "question", "question": '
                '"..."}\n'
                "2. Otherwise, respond with the full diagnosis: "
                '{"status": "diagnosed", "root_cause": "one sentence root '
                'cause", "location": "file:line:symbol (or the closest '
                'matched symbol)", "explanation": "detailed explanation '
                'tied to the code evidence", "fixes": [{"description": '
                '"what to fix", "file": "", "symbol": "", "suggestion": '
                '"concrete code-level fix"}]}\n'
                f"You have {remaining_questions} clarifying question(s) "
                "left in this conversation. Prefer diagnosing directly "
                "whenever the evidence is enough — do not ask a question "
                "you can already answer from the supplied context, and "
                "never repeat a question already asked in the conversation "
                "below.\n\n"
                "Respond with ONLY valid JSON, no surrounding text."
            )
        else:
            question += (
                "You have used all your clarifying questions for this "
                "conversation. Give your best-effort full diagnosis now "
                'using everything gathered so far: {"status": "diagnosed", '
                '"root_cause": "...", "location": "...", "explanation": '
                '"...", "fixes": [...]}\n\n'
                "Respond with ONLY valid JSON, no surrounding text."
            )

        if history:
            question += "\n\nCONVERSATION SO FAR:\n" + self._format_history(history)

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
            history,
        )

        if isinstance(diagnosis, dict):
            if mismatch:
                # Enforced in code, not just requested in the prompt: a small
                # local model will sometimes ignore the "return fixes: []"
                # instruction (or the "ask a question" option) and invent a
                # fix anyway (e.g. editing a file that happens to exist in
                # the workspace by coincidence). This always wins, even
                # mid-conversation.
                diagnosis["status"] = "diagnosed"
                diagnosis["question"] = ""
                diagnosis["fixes"] = []
                diagnosis["explanation"] = (
                    "The reported error appears to belong to a different "
                    "project than this workspace. No valid fix location was "
                    "found, so no fix was suggested."
                )
            elif diagnosis.get("status") == "diagnosed":
                diagnosis["fixes"] = self._prune_fixes(
                    cache,
                    diagnosis.get("fixes") or [],
                )

        return {
            "frames": matched,
            "diagnosis": diagnosis,
            "history": self._append_turn(history, diagnosis),
            "model": result["model"],
            "elapsed_ms": result["elapsed_ms"],
        }

    def _format_history(self, history):
        lines = []

        for turn in history:
            role = turn.get("role", "user")
            content = turn.get("content", "")
            speaker = "AI" if role == "assistant" else "USER"
            lines.append(f"{speaker}: {content}")

        return "\n".join(lines)

    def _append_turn(self, history, diagnosis):
        updated = list(history)

        if diagnosis.get("status") == "question":
            updated.append(
                {"role": "assistant", "content": diagnosis.get("question", "")}
            )
        else:
            updated.append(
                {
                    "role": "assistant",
                    "content": f"Diagnosed: {diagnosis.get('root_cause', '')}",
                }
            )

        return updated

    def _web_evidence(self, error):
        if not web_search_service.needs_search(error):
            return []

        query = web_search_service.build_query(error)

        return web_search_service.search(query)

    def _stack_mismatch(self, cache, error):
        return stack_mismatch(cache.workspace, error)

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

    def _looks_like_diagnosis(self, obj):
        if not isinstance(obj, dict):
            return False

        question = obj.get("question")

        if (
            obj.get("status") == "question"
            and isinstance(question, str)
            and question.strip()
        ):
            return True

        root_cause = obj.get("root_cause")

        return isinstance(root_cause, str) and not root_cause.lstrip().startswith("{")

    def _parse_response(
        self,
        response,
        error,
        matched,
        history=None,
    ):

        history = history or []

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

                if self._looks_like_diagnosis(obj):
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

        questions_asked = sum(
            1 for turn in history if turn.get("role") == "assistant"
        )

        can_still_ask = questions_asked < self.MAX_CLARIFYING_TURNS

        is_question = (
            can_still_ask
            and diagnosis.get("status") == "question"
            and isinstance(diagnosis.get("question"), str)
            and diagnosis["question"].strip()
        )

        if is_question:
            diagnosis["status"] = "question"
            diagnosis.setdefault("root_cause", "")
            diagnosis.setdefault(
                "location", matched[0]["symbol"] if matched else ""
            )
            diagnosis.setdefault("explanation", "")
            diagnosis["fixes"] = []

            return diagnosis

        diagnosis["status"] = "diagnosed"
        diagnosis["question"] = ""

        if not diagnosis.get("root_cause"):
            diagnosis["root_cause"] = (
                "Could not determine the root cause from the supplied "
                "workspace context."
                if can_still_ask
                else "Reached the clarifying-question limit without enough "
                "evidence to pinpoint a root cause."
            )

        if not isinstance(diagnosis.get("fixes"), list):
            diagnosis["fixes"] = []

        return diagnosis


diagnose_service = DiagnoseService()

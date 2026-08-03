import re
import subprocess
from pathlib import Path

from app.services.ai_service import ai_service
from app.services.web_search_service import web_search_service
from app.workspace.project_registry import workspace_registry
from app.workspace.prompt_builder import prompt_builder

DIFF_BLOCK = re.compile(r"```(?:diff)?\s*(.*?)```", re.DOTALL)
CODE_BLOCK = re.compile(r"```(?:[a-zA-Z]*)\s*(.*?)```", re.DOTALL)


class FixService:
    def __init__(self):
        self._checkpoints = {}

    def apply(self, fix, project="default", model="qwen", thinking=False):
        cache = workspace_registry.get(project)
        workspace = Path(cache.workspace)

        if not self._is_git(workspace):
            raise ValueError(
                "Auto-fix requires a git repository. "
                f"'{workspace}' is not inside a git work tree."
            )

        relative, source = self._resolve_target(cache, workspace, fix)

        if relative is None:
            raise ValueError(
                "The fix does not name a target file. Add 'file' to the fix "
                "before applying."
            )

        checkpoint = self._checkpoint(workspace)

        self._ignore_snapshot(workspace)

        evidence = self._web_evidence(fix)

        diff = self._generate_diff(relative, source, fix, evidence, model, thinking)

        applied_diff, method = self._apply_diff(workspace, diff)

        if not applied_diff:
            new_content = self._generate_content(
                relative, source, fix, evidence, model, thinking
            )
            if not new_content:
                return {
                    "applied": False,
                    "file": relative,
                    "message": (
                        "Could not produce an applicable patch. "
                        "Manual review required."
                    ),
                    "raw_diff": diff,
                    "checkpoint_commit": checkpoint,
                    "revert": f"git reset --hard {checkpoint}",
                }
            self._write_file(workspace, relative, new_content)
            method = "rewrite"

        cache.reload()

        actual_diff = self._git(workspace, "diff")[1]

        fix_commit = self._commit_fix(workspace, fix)

        self._checkpoints[project] = checkpoint

        return {
            "applied": True,
            "file": relative,
            "method": method,
            "diff": actual_diff or applied_diff or diff,
            "checkpoint_commit": checkpoint,
            "fix_commit": fix_commit,
            "revert": f"git reset --hard {checkpoint}",
            "message": "Fix applied and committed.",
        }

    def revert(self, project="default"):
        checkpoint = self._checkpoints.get(project)

        if not checkpoint:
            raise ValueError(
                f"No auto-fix has been applied for project '{project}'."
            )

        cache = workspace_registry.get(project)
        workspace = Path(cache.workspace)

        self._git(workspace, "reset", "--hard", checkpoint)

        cache.reload()

        return {
            "reverted": True,
            "checkpoint": checkpoint,
            "message": f"Workspace reset to {checkpoint}.",
        }

    def _resolve_target(self, cache, workspace, fix):
        file_name = fix.get("file") or ""

        if file_name:
            relative = self._safe_relative(workspace, file_name)
            if relative is not None:
                return relative, self._read_file(workspace, relative)

        symbol = fix.get("symbol") or ""

        if symbol:
            info = cache.symbols().get(symbol)
            if info and info.get("file"):
                relative = self._safe_relative(workspace, info["file"])
                if relative is not None:
                    return relative, self._read_file(workspace, relative)

        return None, ""

    def _safe_relative(self, workspace, file_name):
        raw = Path(file_name.replace("\\", "/"))
        candidate = workspace / raw

        if raw.is_absolute():
            candidate = Path(file_name)

        try:
            candidate = candidate.resolve()
            candidate.relative_to(workspace.resolve())
        except ValueError:
            return None

        if not candidate.is_file():
            return None

        return candidate.relative_to(workspace.resolve()).as_posix()

    def _read_file(self, workspace, relative):
        path = workspace / relative
        if not path.is_file():
            return ""
        try:
            return path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return ""

    def _web_evidence(self, fix):
        text = " ".join(
            str(fix.get(key) or "")
            for key in ("description", "suggestion", "error")
        )

        if not web_search_service.needs_search(text):
            return []

        query = web_search_service.build_query(text)

        return web_search_service.search(query)

    def _generate_diff(self, relative, source, fix, evidence, model, thinking):
        context = self._context_block(relative, source, fix, evidence)

        question = (
            "Produce a unified diff that implements the suggested fix.\n\n"
            "Rules:\n"
            "- Output ONLY the unified diff between ```diff and ``` markers.\n"
            "- The diff must apply with `git apply`.\n"
            "- Use a/ and b/ paths relative to the repository root, matching "
            "the FILE path exactly.\n"
            "- Make the smallest possible change. Do not reformat unrelated code.\n"
            "- No surrounding commentary."
        )

        prompt = prompt_builder.build(context, question, external=bool(evidence))

        result = ai_service.chat(model=model, message=prompt, thinking=thinking)

        return self._extract_block(result["response"], "diff")

    def _generate_content(self, relative, source, fix, evidence, model, thinking):
        context = self._context_block(relative, source, fix, evidence)

        question = (
            "Output ONLY the complete new content of this file that implements "
            "the suggested fix, between ``` and ``` markers.\n\n"
            "Rules:\n"
            "- Preserve every line that is not part of the fix, byte for byte.\n"
            "- No commentary outside the code block."
        )

        prompt = prompt_builder.build(context, question, external=bool(evidence))

        result = ai_service.chat(model=model, message=prompt, thinking=thinking)

        return self._extract_block(result["response"], "code")

    def _context_block(self, relative, source, fix, evidence):
        lines = [
            "You are applying a fix to a source file.",
            "",
            "TARGET FILE:",
            relative,
            "",
            "CURRENT FILE CONTENT:",
            source[:20000],
            "",
            "FIX:",
            f"description: {fix.get('description') or ''}",
            f"suggestion: {fix.get('suggestion') or ''}",
        ]

        if evidence:
            lines.append("")
            lines.append("WEB EVIDENCE:")
            for item in evidence[:5]:
                lines.append(
                    f"- {item['title']} ({item['url']}): {item['body']}"
                )

        return "\n".join(lines)

    def _extract_block(self, response, kind):
        pattern = DIFF_BLOCK if kind == "diff" else CODE_BLOCK

        match = pattern.search(response or "")

        if not match:
            return ""

        return match.group(1).strip()

    def _apply_diff(self, workspace, diff):
        if not diff:
            return "", ""

        patch = diff.rstrip() + "\n"

        returncode, _, _ = self._git(
            workspace,
            "apply",
            "--3way",
            "--whitespace=nowarn",
            "-",
            input_data=patch,
        )

        if returncode == 0:
            return diff, "diff"

        return "", ""

    def _write_file(self, workspace, relative, content):
        path = workspace / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content + "\n", encoding="utf-8")

    def _commit_fix(self, workspace, fix):
        returncode, output, _ = self._git(
            workspace,
            "status",
            "--porcelain",
        )

        if returncode != 0 or not output:
            return ""

        message = f"reyvin: apply fix - {fix.get('description') or 'auto-fix'}"

        self._git(workspace, "add", "-A")

        returncode, _, _ = self._git(
            workspace,
            "commit",
            "-m",
            message,
        )

        if returncode != 0:
            return ""

        return self._git(workspace, "rev-parse", "HEAD")[1]

    def _checkpoint(self, workspace):
        returncode, head, _ = self._git(workspace, "rev-parse", "HEAD")

        if returncode != 0:
            raise ValueError("Workspace has no git HEAD to checkpoint.")

        returncode, dirty, _ = self._git(
            workspace,
            "status",
            "--porcelain",
        )

        if dirty:
            self._git(workspace, "add", "-A")
            self._git(workspace, "commit", "-m", "reyvin: checkpoint before auto-fix")
            returncode, head, _ = self._git(workspace, "rev-parse", "HEAD")

        return head

    def _is_git(self, workspace):
        returncode, stdout, _ = self._git(
            workspace,
            "rev-parse",
            "--is-inside-work-tree",
        )

        return returncode == 0 and stdout == "true"

    def _ignore_snapshot(self, workspace):
        exclude = workspace / ".git" / "info" / "exclude"
        marker = ".workspace_snapshot.json"

        if not exclude.is_file():
            return

        content = exclude.read_text(encoding="utf-8")

        if marker not in content:
            exclude.write_text(
                content.rstrip() + "\n" + marker + "\n",
                encoding="utf-8",
            )

    def _git(self, workspace, *args, input_data=None):
        proc = subprocess.run(
            ["git", "-C", str(workspace), *args],
            input=input_data,
            capture_output=True,
            text=True,
            check=False,
        )

        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


fix_service = FixService()

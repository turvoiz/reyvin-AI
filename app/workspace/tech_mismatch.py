import re
from pathlib import Path

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


def error_hints_mobile(error):
    return bool(MOBILE_ERROR_PATTERN.search(error or ""))


def workspace_has_mobile_stack(workspace):
    root = Path(workspace)

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

        if any(hint in lowered for hint in MOBILE_WORKSPACE_HINTS):
            return True

    return False


def stack_mismatch(workspace, error):
    """True when the error clearly names mobile tooling the workspace doesn't have."""
    if not error_hints_mobile(error):
        return False

    return not workspace_has_mobile_stack(workspace)

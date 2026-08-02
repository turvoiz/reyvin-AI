from pathlib import Path


def read_file(filepath: str):

    path = Path(filepath)

    if not path.exists():
        raise FileNotFoundError(filepath)

    content = path.read_text(
        encoding="utf-8",
        errors="ignore",
    )

    return {
        "path": str(path),
        "content": content,
        "size": len(content),
        "lines": len(content.splitlines()),
    }

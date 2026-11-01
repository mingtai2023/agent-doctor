"""Read-only heuristic diagnostics; findings are signals, not proof of hallucination."""
import argparse
import hashlib
import json
import re
from pathlib import Path
from .sandbox import WorkspaceJail, PathBoundaryError

ERRORS = re.compile(r"traceback|\berror\b|\bexception\b|\bfailed\b|maximum context length", re.I)


def diagnose(workspace: str | Path, target: str | Path, *, expected_sha256: str | None = None,
             max_bytes: int = 1_048_576) -> dict:
    """Inspect one UTF-8 file without modifying it or returning its content."""
    if max_bytes < 1:
        raise ValueError("max_bytes must be positive")
    path = WorkspaceJail(workspace).resolve(target)
    with path.open("rb") as handle:
        data = handle.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise ValueError("File exceeds diagnostic size limit")
    digest = hashlib.sha256(data).hexdigest()
    findings = []
    if expected_sha256 is not None:
        if not re.fullmatch(r"[a-fA-F0-9]{64}", expected_sha256):
            raise ValueError("Expected SHA-256 must contain 64 hexadecimal characters")
        if digest != expected_sha256.lower():
            findings.append({"code": "context_changed", "count": 1})
    try:
        content = data.decode("utf-8")
    except UnicodeDecodeError:
        findings.append({"code": "invalid_utf8", "count": 1})
        content = data.decode("utf-8", errors="replace")
    count = len(ERRORS.findall(content))
    if count:
        findings.append({"code": "error_markers", "count": count})
    if path.suffix.lower() == ".json":
        try:
            json.loads(content)
        except (ValueError, RecursionError):
            findings.append({"code": "invalid_json", "count": 1})
    if re.search(r"(?<![A-Za-z0-9_])/home(?:/|\b)", content):
        findings.append({"code": "home_path_reference", "count": 1})
    return {"file": str(path.relative_to(Path(workspace).resolve())), "sha256": digest,
            "bytes": len(data), "findings": findings, "read_only": True}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Read-only agent memory diagnostics")
    parser.add_argument("target", help="Memory file, relative to the workspace or absolute")
    parser.add_argument("--workspace", required=True, help="Existing approved directory")
    parser.add_argument("--expected-sha256", help="Trusted baseline digest for change detection")
    args = parser.parse_args(argv)
    try:
        report = diagnose(args.workspace, args.target, expected_sha256=args.expected_sha256)
    except (OSError, ValueError) as exc:
        parser.exit(2, f"agent-doctor: {exc}\n")
    print(json.dumps(report, indent=2))
    return 1 if report["findings"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

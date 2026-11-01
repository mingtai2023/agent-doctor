"""Run after installing the package: python examples/quickstart.py."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from agent_doctor import WorkspaceJail, PathBoundaryError, diagnose

with TemporaryDirectory(prefix="agent-doctor-") as directory:
    jail = WorkspaceJail(directory)
    target = jail.resolve("memory.json")
    target.write_text(json.dumps({"status": "failed", "path": "/home/agent"}), encoding="utf-8")
    print(json.dumps(diagnose(directory, "memory.json"), indent=2))
    try:
        jail.resolve("../outside.txt")
    except PathBoundaryError as exc:
        print(f"Blocked: {exc}")

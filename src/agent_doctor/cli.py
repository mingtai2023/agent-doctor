"""One-shot static inspection and reversible file quarantine. No background tasks."""
import argparse
from contextlib import closing
import hashlib
import json
import os
import re
import sqlite3
import tempfile
import uuid
from pathlib import Path

from .sandbox import WorkspaceJail

VAULT = ".agent_doctor_quarantine"
PATTERNS = re.compile(
    r"ignore\s+(?:all\s+)?(?:previous|prior|above)\s+instructions|"
    r"(?:reveal|print|exfiltrate)\s+(?:the\s+)?(?:system\s+prompt|secrets?|api\s+keys?)|"
    r"<\|(?:im_start|system)\|>|\[INST\]", re.I)


def digest(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest() if hasattr(hashlib, "file_digest") else hashlib.sha256(handle.read()).hexdigest()


def inspect(path):
    findings = set()
    if path.suffix.lower() in {".sqlite", ".sqlite3", ".db"}:
        # Never move a database with live journal state; stop its writer first.
        if any(Path(str(path) + suffix).exists() for suffix in ("-wal", "-shm", "-journal")):
            return ["database_sidecars_present"]
        try:
            with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as connection:
                connection.execute("PRAGMA trusted_schema=OFF")
                if connection.execute("PRAGMA quick_check").fetchall() != [("ok",)]:
                    findings.add("invalid_sqlite")
                tables = connection.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
                for (name,) in tables:
                    quoted = '"' + name.replace('"', '""') + '"'
                    for row in connection.execute("SELECT * FROM " + quoted):
                        if any(PATTERNS.search(value) for value in row if isinstance(value, str)):
                            findings.add("prompt_injection")
        except sqlite3.DatabaseError:
            findings.add("invalid_sqlite")
    else:
        try:
            content = path.read_text(encoding="utf-8-sig")
        except UnicodeError:
            return ["invalid_utf8"]
        if PATTERNS.search(content):
            findings.add("prompt_injection")
        if path.suffix.lower() == ".json":
            try:
                json.loads(content)
            except (ValueError, RecursionError):
                findings.add("invalid_json")
    return sorted(findings)


def scan(workspace):
    jail = WorkspaceJail(workspace)
    reports = []
    for folder, directories, files in os.walk(jail.workspace, followlinks=False):
        directories[:] = sorted(
            d for d in directories
            if d not in {VAULT, ".git", ".venv", "__pycache__"}
            and not (Path(folder) / d).is_symlink()
            and not getattr(Path(folder) / d, "is_junction", lambda: False)()
        )
        for name in sorted(files):
            path = Path(folder) / name
            if path.is_symlink() or path.suffix.lower() not in {".json", ".txt", ".sqlite", ".sqlite3", ".db"}:
                continue
            path = jail.resolve(path)
            reports.append({"file": path.relative_to(jail.workspace).as_posix(), "sha256": digest(path), "findings": inspect(path)})
    return reports


def ledger(jail):
    vault = jail.resolve(VAULT)
    if (jail.workspace / VAULT).is_symlink() or getattr(jail.workspace / VAULT, "is_junction", lambda: False)():
        raise ValueError("Quarantine must not be a symbolic link")
    vault.mkdir(mode=0o700, exist_ok=True)
    index = jail.resolve(vault / "index.json")
    entries = json.loads(index.read_text(encoding="utf-8")) if index.exists() else []
    if not isinstance(entries, list) or any(not isinstance(e, dict) for e in entries):
        raise ValueError("Invalid quarantine index")
    return vault, index, entries


def save(index, entries):
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=index.parent, delete=False) as handle:
        temporary = Path(handle.name)
        json.dump(entries, handle, indent=2)
        handle.flush()
        os.fsync(handle.fileno())
    temporary.replace(index)


def quarantine(workspace):
    jail = WorkspaceJail(workspace)
    reports = scan(workspace)
    vault, index, entries = ledger(jail)
    moved = []
    for report in reports:
        if not report["findings"] or "database_sidecars_present" in report["findings"]:
            continue
        source = jail.resolve(report["file"])
        if digest(source) != report["sha256"]:
            raise ValueError("File changed after scan")
        entry = {**report, "id": uuid.uuid4().hex}
        # Persist recovery information before moving; incomplete entries remain recoverable.
        entries.append(entry)
        save(index, entries)
        try:
            source.rename(vault / entry["id"])
        except OSError:
            entries.remove(entry)
            save(index, entries)
            raise
        moved.append(report["file"])
    return moved


def restore(workspace, name=None, all_files=False):
    jail = WorkspaceJail(workspace)
    vault, index, entries = ledger(jail)
    selected = entries if all_files else [e for e in entries if e["file"] == name or Path(e["file"]).name == name]
    if not selected:
        raise ValueError("No matching quarantined file")
    if not all_files and len(selected) != 1:
        raise ValueError("Ambiguous filename; use its original relative path")
    operations = []
    destinations = set()
    for entry in selected:
        if not re.fullmatch(r"[a-f0-9]{32}", entry["id"]):
            raise ValueError("Invalid quarantine identifier")
        source = jail.resolve(vault / entry["id"])
        target = jail.resolve(entry["file"])
        if target in destinations:
            raise ValueError("Duplicate restore destination")
        destinations.add(target)
        if target.is_relative_to(vault) or target.exists() or target.is_symlink():
            raise ValueError("Restore target exists or is unsafe")
        if digest(source) != entry["sha256"]:
            raise ValueError("Quarantined file integrity check failed")
        operations.append((entry, source, target))
    restored = []
    for entry, source, target in operations:
        target.parent.mkdir(parents=True, exist_ok=True)
        # Exclusive creation prevents accidental overwrite, including concurrent creation.
        with target.open("xb") as output, source.open("rb") as input_file:
            import shutil
            shutil.copyfileobj(input_file, output)
        source.unlink()
        entries.remove(entry)
        save(index, entries)
        restored.append(entry["file"])
    return restored


def main(argv=None):
    parser = argparse.ArgumentParser(description="One-shot static agent workspace inspection and recovery")
    parser.add_argument("--version", action="version", version="agent-doctor 0.2.0")
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ("scan", "quarantine", "restore"):
        sub = commands.add_parser(command)
        sub.add_argument("--dir", default=".", help="Approved workspace (default: current directory)")
        if command == "restore":
            group = sub.add_mutually_exclusive_group(required=True)
            group.add_argument("--file")
            group.add_argument("--all", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.command == "scan":
            result = scan(args.dir)
        elif args.command == "quarantine":
            result = quarantine(args.dir)
        else:
            result = restore(args.dir, args.file, args.all)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(2, f"agent-doctor: {exc}\n")
    print(json.dumps(result, indent=2))
    return int(args.command == "scan" and any(item["findings"] for item in result))

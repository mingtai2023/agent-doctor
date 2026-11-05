# 🩺 Agent Doctor (Community Edition)

> **On-Demand Diagnostic, Quarantine & Recovery Toolkit for Autonomous AI Agent Workspaces.**
> Inspect agent session files, quarantine suspicious or corrupted context, and restore quarantined files with zero background daemons.

[![Version: 0.2.0](https://img.shields.io/badge/version-0.2.0-blue.svg)](https://github.com/mingtai2023/agent-doctor)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![GitHub Install](https://img.shields.io/badge/Install-Direct%20from%20GitHub-orange.svg)](#installation)
[![Official Store](https://img.shields.io/badge/Official-nova--mint.store-00C49F)](https://nova-mint.store)

---

## ⚠️ IMPORTANT LEGAL DISCLAIMER

> **PLEASE READ CAREFULLY BEFORE USE:**
>
> **Agent Doctor Community Edition is an experimental, open-source diagnostic and file management utility provided "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED.**
>
> In no event shall the authors, contributors, or NovaMint Studio Limited be liable for any claim, damages, data loss, corrupted workspaces, interrupted agent workflows, or other liability arising from the use of, or inability to use, this software. Users are solely responsible for maintaining independent backups of their codebases, databases, and agent memory snapshots before running quarantine or restore commands.

---

## Why Was Agent Doctor Built?

Autonomous agents such as Hermes Agent, CrewAI, LangChain-based workers, and AutoGPT can produce large collections of session logs, tool outputs, and persistent memory files. When those files contain malformed JSON or suspicious instructions, developers need a practical way to inspect and isolate them without rebuilding their agent infrastructure.

Common pain points include:

1. **Context poisoning and prompt injection:** Untrusted text can persist in session files and influence later agent runs.
2. **Corrupted snapshots:** Broken JSON, invalid text encoding, or damaged SQLite databases can interrupt workflows.
3. **Difficult recovery:** Manually moving suspicious files makes it easy to lose their original paths or overwrite newer work during recovery.
4. **Workspace boundaries:** Agent tools can be given excessive filesystem access. This CLI confines its own operations to an approved workspace; it does not constrain another agent's tools or prevent their writes.

**Agent Doctor Community Edition provides a small, on-demand inspection and recovery workflow without running a resident service.** Scan files, move flagged files into an indexed quarantine directory, and restore their original bytes and paths after review.

## What the Free Community Edition Does For You

- **One-shot inspection (`scan`):** Recursively checks JSON, UTF-8 TXT, and SQLite files for common prompt injection markers and format corruption.
- **Indexed isolation (`quarantine`):** Rescans the workspace and moves flagged files into `.agent_doctor_quarantine/`, recording their original paths and SHA-256 hashes.
- **Verified recovery (`restore`):** Restores a selected file or all quarantined files, verifies hashes, and refuses to overwrite existing destinations.
- **Framework-independent operation:** Works with supported session file formats produced by Hermes Agent, CrewAI, LangChain, and similar agents. No framework plugin or running agent is required.
- **No resident processes:** Every command runs once and exits. There is no daemon, background hook, real-time file interception, filesystem guard, or active runtime containment.

Detection is heuristic. Findings can be false positives, and a clean scan does not prove that a file is safe. This tool does not repair corrupted files, roll back arbitrary code changes, or inspect live memory, remote vector databases, or unsupported file formats.

## Installation

Requires **Python 3.10 or newer** and **Git** for installation from GitHub. A virtual environment is recommended.

Install directly from the official GitHub repository:

```bash
python -m pip install "git+https://github.com/mingtai2023/agent-doctor.git"
```

To update an existing installation from GitHub:

```bash
python -m pip install --upgrade "git+https://github.com/mingtai2023/agent-doctor.git"
```

Or clone the repository and install locally for development:

```bash
git clone https://github.com/mingtai2023/agent-doctor.git
cd agent-doctor
python -m pip install -e .
```

Verify the installed version:

```bash
agent-doctor --version
```

Expected output: `agent-doctor 0.2.0`. If the console command is unavailable on your PATH, use `python -m agent_doctor` with the same arguments.

## 3-Step Quickstart

Stop the agent and back up the workspace independently before moving or restoring files. Replace `./my_agent_workspace` with an existing, approved workspace directory. Use the same `--dir` for every step; otherwise, the default is the current directory.

### Step 1. Scan Your Agent Workspace

```bash
agent-doctor scan --dir ./my_agent_workspace
```

Scan is read-only. Its JSON report contains relative paths, SHA-256 hashes, and findings without printing file contents. Recognized extensions are `.json`, `.txt`, `.sqlite`, `.sqlite3`, and `.db`. JSON syntax, UTF-8 decoding, and SQLite integrity are checked; TXT has no schema to validate. SQLite text columns are inspected for injection markers. Other extensions, including `.log` and `.jsonl`, are not scanned.

### Step 2. Quarantine Flagged Files

```bash
agent-doctor quarantine --dir ./my_agent_workspace
```

Flagged files move into the workspace's `.agent_doctor_quarantine/` directory. Its `index.json` records original paths, hashes, findings, and unique storage identifiers. Quarantine moves files; it does not sanitize their contents.

SQLite databases with `-wal`, `-shm`, or `-journal` sidecars are reported and skipped during quarantine. Stop the writer and checkpoint or cleanly close the database before trying again. Do not manually delete database sidecars to force quarantine.

### Step 3. Restore Quarantined Files

Restore a specific file:

```bash
agent-doctor restore --dir ./my_agent_workspace --file session_memory.json
```

Restore all quarantined files:

```bash
agent-doctor restore --dir ./my_agent_workspace --all
```

For duplicate basenames, select the original relative path, for example `--file hermes/session_memory.json`. `--file` and `--all` are mutually exclusive. Restore refuses ambiguous selections, modified quarantine contents, existing destinations, and paths outside the workspace. A restore request with no matching entries returns an error.

## Command Results and Safety Boundaries

| Exit code | Meaning |
| --- | --- |
| `0` | Successful command, or scan with no findings |
| `1` | Scan completed with findings |
| `2` | Operational error or invalid command arguments |

- Keep the quarantine directory and `index.json` together. Maintain independent backups; quarantine is not a backup service.
- Run commands only against a stopped workspace. Concurrent commands or external file changes are unsupported. Multi-file operations are not an all-or-nothing transaction; an error can leave earlier files already moved or restored.
- The vault is excluded from scanning. POSIX vault creation requests owner-only permissions. On Windows, permissions follow inherited ACLs; configure access restrictions for sensitive workspaces.
- The vault is not encrypted and does not protect against processes running as the same user. Hash verification detects changes relative to the index; it does not authenticate an index that an attacker can also modify.
- Recovery preserves file bytes and original paths, not every filesystem metadata field. It restores quarantined content, including any suspicious instructions still present in that content.
- Filesystem roots and paths containing a `home` component are rejected by the workspace boundary helper. Use a dedicated workspace outside those paths.

## The NovaMint Ecosystem & Advanced Services

Visit the [NovaMint Studio official store](https://nova-mint.store) for publications, architecture resources, and [advanced services and enterprise inquiries](https://nova-mint.store).

Community Edition remains focused on one-shot static inspection, quarantine, and recovery. Continuous runtime defense, graphical monitoring, and enterprise containment are not included in this release.

## Development and Verification

From the cloned repository:

```bash
python -m pip install -e . pytest
python -m pytest -q
```

Tests cover read-only scans, JSON/TXT/SQLite findings, quarantine moves, byte-for-byte recovery, overwrite refusal, hash mismatch, ambiguous filenames, and workspace boundary checks. Symbolic-link tests may be skipped on systems without permission to create links.

Licensed under [MIT](LICENSE).

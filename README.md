# 🩺 Agent Doctor (Community Edition)

> **Static Inspection, Quarantine & Recovery Toolkit for Autonomous AI Agent Workspaces.**
> A lightweight, on-demand CLI utility to diagnose corrupted context, safely quarantine infected agent session files, and restore workspace snapshots without running background daemons.

[![Version: 0.2.0](https://img.shields.io/badge/version-0.2.0-blue.svg)](https://github.com/mingtai2023/agent-doctor)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Official Store](https://img.shields.io/badge/Official-nova--mint.store-00C49F)](https://nova-mint.store)

---

### ⚠️ IMPORTANT LEGAL DISCLAIMER / 法律免責聲明

> **PLEASE READ CAREFULLY BEFORE USE:**
> **Agent Doctor Community Edition is an experimental, open-source diagnostic and file management utility provided "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED.**
> In no event shall the authors, contributors, or NovaMint Studio Limited be liable for any claim, damages, data loss, corrupted workspaces, interrupted agent processes, or other liability arising from the use of, or inability to use, this software. Users are solely responsible for creating independent backups of their codebase, databases, and agent memory snapshots prior to running quarantine or restore commands.

---

### 🎯 What Agent Doctor Community Edition Does (And Doesn't Do)

Agent Doctor Community Edition is intentionally designed as an **on-demand, zero-daemon, one-shot CLI tool**.

- **✅ What It Does:**
  - **On-Demand Inspection**: Scans workspace logs, session files, and memory snapshots from autonomous agents (such as **Hermes Agent**, **CrewAI**, **LangChain**, and **AutoGen**) for corrupted context tokens and injection patterns.
  - **Safe Quarantine**: Moves suspicious or broken agent output files into an isolated `.agent_doctor_quarantine/` vault with an automated index ledger.
  - **Reversible Recovery**: Allows immediate, one-command restoration of quarantined files back to their original paths.
- **❌ What It Does NOT Do:**
  - **No Background Monitoring**: Does not run daemon processes or monitor active memory vectors in real-time.
  - **No Kernel/System Interception**: Does not block ongoing OS processes or system calls on the fly. Real-time active memory defense and sandbox containment matrices are reserved for enterprise environments.

---

### ⚡ Quickstart

```bash
pip install agent-doctor
```
1. One-Shot Workspace Scan
Scan your agent's current working directory for abnormal tokens and prompt injection payloads:

```bash
agent-doctor scan --dir ./my_agent_workspace
```
2. Quarantine Suspicious Files
Move detected or corrupted files out of the active runtime into the isolated quarantine vault:
```bash
agent-doctor quarantine --dir ./my_agent_workspace
```
3. Restore Files
Safely restore files back to the active directory whenever needed:
```bash
agent-doctor restore --dir ./my_agent_workspace --file session_memory_20261105.json
# Or restore all quarantined files:
agent-doctor restore --dir ./my_agent_workspace --all
```

### Workspace and recovery safety

Run commands only against an approved, stopped agent workspace. The file format adapters inspect JSON, UTF-8 TXT, and SQLite (`.sqlite`, `.sqlite3`, `.db`) files produced by Hermes Agent, CrewAI, LangChain, and similar agents. No framework integration or running agent is required.

Use the same workspace for all commands:

```bash
agent-doctor scan --dir ./my_agent_workspace
agent-doctor quarantine --dir ./my_agent_workspace
agent-doctor restore --dir ./my_agent_workspace --file session_memory_20261105.json
agent-doctor restore --dir ./my_agent_workspace --all
agent-doctor --version
```

Scan reports relative paths, SHA-256 hashes, and heuristic findings without printing file contents. Exit codes: `0` success/clean scan, `1` scan findings, `2` operational error. Findings are review signals, not proof of compromise; injection detection can miss attacks or flag legitimate quotations. JSON syntax, UTF-8 decoding, and SQLite integrity are checked. TXT has no schema to validate.

Quarantine rescans and moves flagged files into `.agent_doctor_quarantine/` with an index recording original paths and hashes. SQLite files with WAL, SHM, or journal sidecars are reported but never moved; stop the writer and checkpoint the database first. Back up independently before moving files. Do not run concurrent commands or modify the workspace during inspection/recovery.

Restore verifies hashes and refuses existing destinations, workspace escapes, and ambiguous basenames. Use the original relative path to select duplicate names. Keep the vault and `index.json` together. The vault is excluded from scans; creation requests owner-only permissions on POSIX. On Windows, access follows inherited ACLs: configure directory permissions for sensitive workspaces. The vault is not encrypted and is not a security sandbox against processes running as the same user. Recovery preserves file bytes and original paths, not every filesystem metadata field.

### Official store and advanced services

Visit the [NovaMint official store](https://nova-mint.store) for [advanced services and enterprise inquiries](https://nova-mint.store). Community Edition remains a one-shot static CLI: no daemon, background hook, real-time file interception, or filesystem guard.

### Development

```bash
python -m pip install -e . pytest
python -m pytest -q
```

Licensed under [MIT](LICENSE).

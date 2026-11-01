# Agent Doctor

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Created by NovaMint Studio](https://img.shields.io/badge/created_by-NovaMint_Studio-black.svg)](https://nova-mint.store)

**Keep agent memory inspectable. Keep file tools inside their workspace.**

Agent Doctor Community Edition provides read-only context diagnostics and an explicit workspace jail for Python agent integrations. Zero third-party runtime dependencies. Created by **NovaMint Studio Limited**.

## The problem

Autonomous agents such as AutoGPT and Hermes can lose track of their working directory, attempt writes under `/home/` or filesystem roots, and accumulate error traces in persistent memory. These failures make context harder to trust and tool behavior harder to predict.

Agent Doctor surfaces memory pollution signals, detects changes against a trusted context digest, and rejects paths outside a designated workspace before your file tool uses them.

## Quickstart

Install directly from GitHub (no PyPI release required):

```sh
python -m pip install "git+https://github.com/mingtai2023/agent-doctor.git"
```

Or clone and install locally:

```sh
git clone https://github.com/mingtai2023/agent-doctor.git
cd agent-doctor
python -m pip install -e .
python examples/quickstart.py
```

Three lines to guard a file-tool path; run from your existing, approved project directory:

```python
from agent_doctor import WorkspaceJail
jail = WorkspaceJail(".")
safe_path = jail.resolve("memory.json")
```

Pass `safe_path` to your file operation. Route **every** agent file-tool path through `jail.resolve()` immediately before use. Relative paths resolve from the workspace, independent of the process working directory. Parent traversal, outside absolute paths, resolved symlink escapes, and paths containing a `home` component are rejected. Filesystem roots and workspaces under `/home/` are intentionally unsupported; choose a dedicated workspace such as `/srv/agent-workspace` on Linux.

Inspect a memory file:

```sh
agent-doctor memory.json --workspace .
agent-doctor memory.json --workspace . --expected-sha256 YOUR_TRUSTED_64_CHARACTER_SHA256
```

The CLI prints JSON with a digest and findings, never memory content. Exit codes: `0` for no findings, `1` for findings, `2` for invalid input or read failure. The default file size limit is 1 MiB. Python callers can set `max_bytes` in `diagnose()`.

## What the diagnostics mean

- `error_markers`: error or traceback keywords may indicate memory pollution.
- `invalid_json` / `invalid_utf8`: the input has a structural or encoding issue.
- `home_path_reference`: context mentions a potentially unwanted home-directory path.
- `context_changed`: bytes differ from a caller-supplied trusted SHA-256 baseline.

Findings require review. Error examples in healthy memory can trigger markers; a digest change can be intentional. This tool does not establish factual truth, prove hallucinations, or measure semantic drift. It never prunes, repairs, or quarantines memory.

## Boundary model

The jail is a cooperative application-level path validator. It does not intercept arbitrary Python I/O, shell commands, subprocesses, or network tools. It cannot prevent a concurrent process from replacing symlinks or directories between validation and I/O, or stop writes through existing hard links. Use OS permissions and container isolation for hostile agents; do not let untrusted processes mutate the workspace directory topology. The example illustrates integration, not an OS security boundary.

## Go further with Agent Doctor Pro

Start with the community core. Move to the flagship architecture package when you need an operational defense strategy across agents.

| Capability | Community (MIT) | Pro ($69 USD) |
| --- | --- | --- |
| Read-only CLI memory checks | Included | Included in the broader architecture |
| Static workspace path boundary | Included | Included in the broader architecture |
| 24/7 automatic repair and defense | Not included | Pro offering |
| Long-term multi-agent memory sandbox blueprints | Not included | Pro offering |
| Complete 200+ page defense and architecture manual | Not included | Pro offering |

**Get the full enterprise architecture & sandbox blueprints at https://nova-mint.store ($69 USD)**

[Explore the official Agent Doctor Pro flagship showroom](https://nova-mint.store) for 24/7 automatic repair defense, multi-agent sandbox blueprints, and the complete 200+ page defense manual. Pro materials and automation code are distributed separately and are not part of this MIT repository.

## Development

```sh
python -m pip install -e .
python -m unittest discover -s tests -v
```

Contributions to diagnostics, integration examples, and boundary tests are welcome. Keep reports synthetic and never submit private agent memory, credentials, or environment files.

## Author & citation

Agent Doctor originated at **NovaMint Studio Limited**.

Suggested citation: NovaMint Studio Limited (2026). *Agent Doctor: Community Edition*, version 0.1.0. https://github.com/mingtai2023/agent-doctor

## License

[MIT](LICENSE). Copyright (c) 2026 NovaMint Studio Limited. The license covers this repository; separately distributed Pro materials are excluded.

# pywho

**One command to explain your Python environment.**

Ever asked *"Which Python am I running? Why is it using that venv? Where are my packages?"* — pywho answers all of it instantly.

```bash
$ pywho
```

```
  pywho - Python Environment Inspector
  ==============================================

  Interpreter
    Executable: /Users/dev/.venv/bin/python3
    Version:    3.12.3 (CPython)
    Compiler:   Clang 15.0.0
    Architecture: 64-bit

  Virtual Environment
    Active: Yes
    Type:   uv
    Path:   /Users/dev/myproject/.venv

  Package Manager
    Detected: uv
```

## Why pywho?

- **"Works on my machine"** is the #1 debugging friction in Python. pywho kills it with one command.
- **Paste the output** into a GitHub issue, Slack message, or Stack Overflow question.
- **Zero dependencies.** Pure stdlib. Works everywhere Python runs.
- **Cross-platform.** Linux, macOS, Windows. Python 3.9+.

## Quick start

```bash
pip install pywho
pywho
```

## Features

- Interpreter details (version, compiler, architecture)
- Virtual environment detection (venv, virtualenv, uv, conda, poetry, pipenv)
- Package manager identification
- Full sys.path listing
- Site-packages locations
- JSON output for CI/scripting
- Installed package listing
- Import tracing (`pywho trace <module>`)
- Project-wide shadow scanning (`pywho scan .`)

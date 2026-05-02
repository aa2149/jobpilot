"""Apply copyright headers to every Python and JS/JSX source file.

Idempotent — won't double-apply if the header is already present.
Run from the repo root.
"""
from __future__ import annotations

import sys
from pathlib import Path

PY_HEADER = '''# ============================================================================
# Copyright (c) 2026 [Areej Ahmed]. All rights reserved.
# Part of JobPilot — Submitted to the 1000Jobs Final Stage assessment.
# Licensed under the JobPilot Evaluation & Personal-Use License.
# See LICENSE and NOTICE.md in the repository root.
# ============================================================================
'''

JS_HEADER = '''/* ============================================================================
 * Copyright (c) 2026 [Areej Ahmed]. All rights reserved.
 * Part of JobPilot — Submitted to the 1000Jobs Final Stage assessment.
 * Licensed under the JobPilot Evaluation & Personal-Use License.
 * See LICENSE and NOTICE.md in the repository root.
 * ========================================================================== */
'''

MARKER = "Part of JobPilot"


def apply_to_python(path: Path) -> bool:
    """Returns True if the file was modified."""
    text = path.read_text(encoding="utf-8")
    if MARKER in text:
        return False
    # Preserve any leading shebang or `from __future__ import ...`
    lines = text.splitlines(keepends=True)
    insert_at = 0
    if lines and lines[0].startswith("#!"):
        insert_at = 1
    # Find first non-blank, non-future-import line — header goes ABOVE it
    # but we want to keep the header at the top so just insert at 0 (after shebang)
    new_text = "".join(lines[:insert_at]) + PY_HEADER + "".join(lines[insert_at:])
    path.write_text(new_text, encoding="utf-8")
    return True


def apply_to_js(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    if MARKER in text:
        return False
    new_text = JS_HEADER + text
    path.write_text(new_text, encoding="utf-8")
    return True


def main() -> int:
    root = Path.cwd()
    if not (root / "pyproject.toml").exists():
        print("Run from repo root.")
        return 1

    py_count = 0
    js_count = 0

    for path in (root / "src").rglob("*.py"):
        if apply_to_python(path):
            py_count += 1

    for path in (root / "tests").rglob("*.py"):
        if apply_to_python(path):
            py_count += 1

    for path in (root / "scripts").rglob("*.py"):
        if apply_to_python(path):
            py_count += 1

    fe = root / "frontend" / "src"
    if fe.exists():
        for ext in ("*.js", "*.jsx", "*.ts", "*.tsx"):
            for path in fe.rglob(ext):
                if apply_to_js(path):
                    js_count += 1

    print(f"Headers applied: {py_count} Python files, {js_count} JS/JSX files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

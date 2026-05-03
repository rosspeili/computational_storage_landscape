#!/usr/bin/env python3
"""Used by git filter-branch --msg-filter. Drops Cursor co-author trailer."""
import sys

MARKER = "Co-authored-by: Cursor <cursoragent@cursor.com>"


def main() -> None:
    data = sys.stdin.read()
    lines = data.splitlines()
    out = [ln for ln in lines if ln.strip() != MARKER]
    text = "\n".join(out)
    if data.endswith("\n"):
        if text and not text.endswith("\n"):
            text += "\n"
    sys.stdout.write(text)


if __name__ == "__main__":
    main()

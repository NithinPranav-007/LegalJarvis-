#!/usr/bin/env python3
"""Local secrets detection script for pre-commit and CI verification."""

import re
import subprocess
import sys
from pathlib import Path

SUSPICIOUS_PATTERNS = [
    (r"(?i)api[_-]?key\s*[:=]\s*['\"][a-zA-Z0-9_\-]{20,}['\"]", "Hardcoded API key"),
    (r"(?i)secret[_-]?key\s*[:=]\s*['\"][a-zA-Z0-9_\-]{20,}['\"]", "Hardcoded Secret key"),
    (r"-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----", "Private key block"),
    (r"(?i)password\s*[:=]\s*['\"][^'\"]{8,}['\"]", "Possible hardcoded password"),
    (r"ghp_[a-zA-Z0-9]{36}", "GitHub Personal Access Token"),
    (r"sk-[a-zA-Z0-9]{48}", "OpenAI Secret Key"),
]

EXCLUDE_PATTERNS = [
    re.compile(r"replace_with_a_secure_random_hex_string_in_production"),
    re.compile(r"dev_secret_change_in_production"),
    re.compile(r"legaljarvis_dev_pass"),
    re.compile(r"your_llm_api_key_here"),
    re.compile(r"test_ci_secret_key"),
]


def check_git_files() -> int:
    try:
        files = (
            subprocess.check_output(["git", "ls-files"], text=True)
            .strip()
            .split("\n")
        )
    except Exception as e:
        print(f"Error listing git files: {e}")
        return 1

    findings = []
    repo_root = Path(__file__).resolve().parent.parent.parent

    for file_path in files:
        if not file_path:
            continue
        p = repo_root / file_path
        if not p.is_file():
            continue

        try:
            content = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        for pattern, desc in SUSPICIOUS_PATTERNS:
            for match in re.finditer(pattern, content):
                matched_text = match.group(0)
                if any(ex.search(matched_text) for ex in EXCLUDE_PATTERNS):
                    continue
                findings.append((file_path, desc, matched_text[:30]))

    if findings:
        print("SECRET SCAN FAILED: Potential secrets found:")
        for f, desc, snippet in findings:
            print(f"  {f}: {desc} (snippet: {snippet}...)")
        return 1

    print("Secret scan passed: zero unapproved secrets detected in Git-tracked files.")
    return 0


if __name__ == "__main__":
    sys.exit(check_git_files())

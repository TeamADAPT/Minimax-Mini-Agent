#!/usr/bin/env python3
"""Scan tracked repository files for high-risk secret material.

The scanner reports only file names, line numbers, and secret classes. It never
prints matched values. It is intended as a cheap pre-commit or pre-push gate
after a scrubbed branch has been cleaned.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SecretPattern:
    """A compiled high-risk secret detector."""

    name: str
    pattern: re.Pattern[bytes]


@dataclass(frozen=True)
class Finding:
    """A redacted finding emitted by the scanner."""

    path: str
    line: int
    kind: str


PATTERNS: tuple[SecretPattern, ...] = (
    SecretPattern("nvidia_api_key", re.compile(rb"\bnvapi-[A-Za-z0-9_-]{20,}\b")),
    SecretPattern("openai_or_openrouter_key", re.compile(rb"\bsk-(?:or-v1-)?[A-Za-z0-9_-]{20,}\b")),
    SecretPattern("github_token", re.compile(rb"\b(?:github_pat|ghp)_[A-Za-z0-9_]{20,}\b")),
    SecretPattern("nats_or_redis_auth_url", re.compile(rb"\b(?:nats|redis)://[^/\s:@]+:[^@\s]+@")),
    SecretPattern(
        "bearer_token",
        re.compile(rb"(?i)\bauthorization\s*[:=]\s*bearer\s+[A-Za-z0-9._~+/=-]{30,}"),
    ),
    SecretPattern(
        "known_infra_password_literal",
        re.compile(b"".join((b"Echo", b"vaeris", b"1966"))),
    ),
)


def run_git(repo: Path, args: list[str]) -> bytes:
    """Run a git command and return stdout.

    Parameters:
        repo: Repository root to execute inside.
        args: Git arguments excluding the `git` executable.

    Returns:
        Raw stdout bytes.

    Raises:
        SystemExit: If git exits with a non-zero status.
    """

    process = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if process.returncode != 0:
        sys.stderr.write(process.stderr.decode("utf-8", errors="replace"))
        raise SystemExit(process.returncode)
    return process.stdout


def repo_root(start: Path) -> Path:
    """Resolve the git repository root for `start`."""

    output = run_git(start, ["rev-parse", "--show-toplevel"])
    return Path(output.decode("utf-8").strip()).resolve()


def tracked_paths(repo: Path) -> list[Path]:
    """Return tracked paths relative to `repo`."""

    output = run_git(repo, ["ls-files", "-z"])
    return [Path(item.decode("utf-8")) for item in output.split(b"\0") if item]


def scan_file(repo: Path, rel_path: Path) -> list[Finding]:
    """Scan one tracked file without printing matched secret values."""

    full_path = repo / rel_path
    rel_text = rel_path.as_posix()
    if full_path.is_symlink():
        target = os.readlink(full_path)
        if target.startswith("/adapt/secrets/") or "/adapt/secrets/" in target:
            return [Finding(rel_text, 1, "secret_symlink")]
        return []
    try:
        data = full_path.read_bytes()
    except OSError as error:
        return [Finding(rel_text, 1, f"read_error:{error.__class__.__name__}")]

    findings: list[Finding] = []
    for secret_pattern in PATTERNS:
        for match in secret_pattern.pattern.finditer(data):
            line = data.count(b"\n", 0, match.start()) + 1
            findings.append(Finding(rel_text, line, secret_pattern.name))
    return findings


def scan_repo(repo: Path) -> list[Finding]:
    """Scan all tracked files in the repository."""

    findings: list[Finding] = []
    for rel_path in tracked_paths(repo):
        findings.extend(scan_file(repo, rel_path))
    return sorted(findings, key=lambda item: (item.path, item.line, item.kind))


def main() -> int:
    """Run the tracked-secret scan CLI."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path.cwd(),
        help="repository or subdirectory to scan; defaults to cwd",
    )
    args = parser.parse_args()
    root = repo_root(args.repo.resolve())
    findings = scan_repo(root)
    if not findings:
        print(f"tracked secret scan clean: {root}")
        return 0

    print(f"tracked secret scan found {len(findings)} redacted finding(s):")
    for finding in findings:
        print(f"{finding.path}:{finding.line}: {finding.kind}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

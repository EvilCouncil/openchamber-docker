#!/usr/bin/env python3
"""Check the build status of openchamber-docker (GHCR tag + GitHub Actions run)."""

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request

REPO = "EvilCouncil/openchamber-docker"
ORG = "evilcouncil"
IMAGE = f"ghcr.io/{ORG}/openchamber-docker"
WORKFLOW = "Build and Push Docker Image"

GITHUB_TOKEN = os.environ.get("GH_TOKEN", os.environ.get("GITHUB_TOKEN", ""))


def run_git(*args: str) -> str:
    result = subprocess.run(
        ["git", "-C", os.path.dirname(__file__) or "."] + list(args),
        capture_output=True, text=True,
    )
    return result.stdout.strip()


def gh_api(url: str) -> dict | list | None:
    req = urllib.request.Request(url)
    if GITHUB_TOKEN:
        req.add_header("Authorization", f"Bearer {GITHUB_TOKEN}")
    req.add_header("Accept", "application/vnd.github.v3+json")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except (urllib.error.HTTPError, urllib.error.URLError) as e:
        print(f"  GitHub API error: {e}", file=sys.stderr)
        return None


def ghcr_auth_token() -> str | None:
    url = f"https://ghcr.io/token?scope=repository:{ORG}/{REPO.split('/')[-1]}:pull"
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            return json.loads(resp.read().decode())["token"]
    except Exception:
        return None


def ghcr_has_tag(tag: str, token: str | None = None) -> bool:
    token = token or ghcr_auth_token()
    if not token:
        return False
    url = f"https://ghcr.io/v2/{ORG}/{REPO.split('/')[-1]}/tags/list?n=100"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return tag in json.loads(resp.read().decode()).get("tags", [])
    except Exception:
        return False


def get_latest_tag() -> str:
    return run_git("tag", "--sort=-v:refname").split("\n")[0]


def check_run(tag: str) -> dict | None:
    sha = run_git("rev-list", "-n", "1", tag)
    if not sha:
        return None
    runs = gh_api(f"https://api.github.com/repos/{REPO}/actions/runs?head_sha={sha}&per_page=5")
    if not runs or "workflow_runs" not in runs:
        return None
    for run in runs["workflow_runs"]:
        if run.get("name") == WORKFLOW:
            return gh_api(f"https://api.github.com/repos/{REPO}/actions/runs/{run['id']}") or run
    return None


def check_tag(tag: str) -> None:
    print(f"Tag: {tag}")
    has_image = ghcr_has_tag(tag)
    print(f"  Image: {IMAGE}:{tag}  {'✅ present on GHCR' if has_image else '❌ not found on GHCR'}")
    run = check_run(tag)
    if run is None:
        print("  CI:   ❓ no build found")
        return
    print(f"  CI:   {run['status']} ({run.get('conclusion', '')})")
    if run.get("html_url"):
        print(f"  Link: {run['html_url']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Check openchamber-docker build status")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("tag", nargs="?", default=None)
    group.add_argument("--version", dest="version")
    group.add_argument("--all", action="store_true")
    args = parser.parse_args()

    if args.all:
        for tag in run_git("tag", "--sort=-v:refname").split("\n")[:5]:
            if tag:
                check_tag(tag)
                print()
        return

    tag = f"v{args.version}" if args.version else (args.tag or get_latest_tag())
    if not tag or not re.match(r"^v?\d+\.\d+\.\d+\.?\d*$", tag):
        print(f"Error: invalid or missing tag: {tag!r}", file=sys.stderr)
        sys.exit(1)
    check_tag(tag if tag.startswith("v") else f"v{tag}")


if __name__ == "__main__":
    main()

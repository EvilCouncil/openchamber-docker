#!/usr/bin/env python3
"""Check npm for latest OpenChamber and OpenCode versions and update Dockerfile and VERSION."""

import json
import re
import sys
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).parent
DOCKERFILE = REPO_ROOT / "Dockerfile"
VERSION_FILE = REPO_ROOT / "VERSION"

PINNED_PACKAGES = ["@openchamber/web", "@opencode/cli"]


def get_latest_version(package: str) -> str:
    encoded = package.replace("/", "%2F")
    url = f"https://registry.npmjs.org/{encoded}/latest"
    with urllib.request.urlopen(url, timeout=10) as resp:
        return json.loads(resp.read())["version"]


def main() -> int:
    content = DOCKERFILE.read_text()

    openchamber_arg = re.search(r"ARG OPENCHAMBER_VERSION=(\S+)", content)
    opencode_arg = re.search(r"ARG OPENCODE_VERSION=(\S+)", content)

    current = {
        "@openchamber/web": openchamber_arg.group(1) if openchamber_arg else None,
        "@opencode/cli": opencode_arg.group(1) if opencode_arg else None,
    }

    print("Checking npm for latest versions...")
    latest = {pkg: get_latest_version(pkg) for pkg in PINNED_PACKAGES}

    changed = False

    for pkg, new_ver in latest.items():
        old_ver = current[pkg]
        if new_ver != old_ver:
            print(f"  {pkg}: {old_ver} → {new_ver}")
            changed = True
        else:
            print(f"  {pkg}: {old_ver} (up to date)")

    if not changed:
        print("\nAll packages up to date.")
        return 0

    if latest["@openchamber/web"] != current["@openchamber/web"]:
        VERSION_FILE.write_text(latest["@openchamber/web"] + "\n")

    content = re.sub(
        r"ARG OPENCHAMBER_VERSION=\S+",
        f"ARG OPENCHAMBER_VERSION={latest['@openchamber/web']}",
        content,
    )
    content = re.sub(
        r"ARG OPENCODE_VERSION=\S+",
        f"ARG OPENCODE_VERSION={latest['@opencode/cli']}",
        content,
    )
    DOCKERFILE.write_text(content)

    print("\nUpdated VERSION and Dockerfile.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

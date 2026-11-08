"""Validate effective APT policy on Ubuntu using only Python's standard library."""

import os
import re
import subprocess
import sys


def validate(release, arch, repositories, packages):
    pocket = f"{release}-proposed"
    # A loaded binary index, not merely an enabled sources.list entry.
    index = rf"(?m)^\s*-1\s+https?://\S+\s+{re.escape(pocket)}/main\s+{re.escape(arch)}\s+Packages\s*$"
    if not re.search(index, repositories):
        raise ValueError(f"Missing loaded {pocket}/main {arch} index with priority -1")

    package = None
    priority = None
    checked = set()
    for line in packages.splitlines():
        if line and not line[0].isspace() and line.endswith(":"):
            package = line[:-1]
            priority = None
        version = re.match(r"^\s+(?:\*\*\*\s+)?\S+\s+(-?\d+)\s*$", line)
        if version:
            priority = int(version[1])
        if re.search(rf"\s{re.escape(pocket)}/\S+\s+\S+\s+Packages\s*$", line):
            if priority != 990:
                raise ValueError(f"{package}: proposed version priority is {priority}, expected 990")
            checked.add(package)
    if not checked:
        raise ValueError(
            f"{pocket} is loaded but no linux-* versions at priority 990 were found; "
            "inspect apt-cache policy 'linux-*' before upgrading"
        )
    return f"Validated {pocket}/main {arch}: default -1; {len(checked)} linux-* packages at 990"


def main():
    environment = dict(os.environ, LC_ALL="C")

    def policy(*args):
        return subprocess.run(
            ["apt-cache", "policy", *args],
            check=True, capture_output=True, text=True, env=environment,
        ).stdout

    try:
        print(validate(sys.argv[1], sys.argv[2], policy(), policy("linux-*")))
    except (ValueError, subprocess.CalledProcessError) as error:
        print(f"Proposed validation failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

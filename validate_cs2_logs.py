#!/usr/bin/env python3
"""Check CS2 console and GDB logs after a manual player test."""

import argparse
import re
from pathlib import Path


ACTIVE_MAP_MARKER = (
    "CNetworkGameServerBase::SetServerState (ss_loading -> ss_active)"
)
PATTERNS = {
    "segmentation_faults": r"segmentation fault|SIGSEGV",
    "fatal_errors": r"\bFATAL\b",
    "missing_human_class": r"Missing default human class",
    "obsolete_scale_toggle": r"Unknown command.*zr_class_scale_enable",
}


def validate_logs(console, gdb):
    """Return matching-line counts and whether GDB captured a native crash.

    Only console entries after the latest active-map marker are checked.
    The complete supplied GDB log is checked; it must belong to the test.
    """
    if ACTIVE_MAP_MARKER not in console:
        raise ValueError("No active-map marker found in console log.")
    if not gdb.strip():
        raise ValueError("GDB log is empty; no capture is available to check.")

    recent = console.rsplit(ACTIVE_MAP_MARKER, 1)[1]
    results = {
        label: sum(bool(re.search(pattern, line, re.IGNORECASE))
                   for line in recent.splitlines())
        for label, pattern in PATTERNS.items()
    }
    results["native_crash_capture"] = bool(re.search(
        r"received signal SIG(?:SEGV|ABRT|BUS|ILL|FPE)\b"
        r"|NATIVE CRASH BACKTRACE",
        gdb,
        re.IGNORECASE,
    ))
    return results


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--console-log", required=True, type=Path,
                        help="Path to the CS2 console log")
    parser.add_argument("--gdb-log", required=True, type=Path,
                        help="GDB capture from the same test session")
    args = parser.parse_args(argv)

    try:
        console = args.console_log.read_text(errors="replace")
        gdb = args.gdb_log.read_text(errors="replace")
        results = validate_logs(console, gdb)
    except (OSError, ValueError) as error:
        parser.exit(2, f"Unable to validate logs: {error}\n")

    for label, value in results.items():
        print(f"{label}: {value}")
    return 1 if any(results.values()) else 0


if __name__ == "__main__":
    raise SystemExit(main())

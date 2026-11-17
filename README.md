# CS2 log validator

A small Python utility for checking CS2 console and GDB logs after a manual
join, infection and reconnect test. Developed while investigating a CS2Fixes
network-event ABI crash and Zombie:Reborn class-model clipping.

Python 3.9 or newer is required. There are no third-party dependencies.
The script reads existing logs; it does not connect to a server, start GDB,
restart the game, or change its configuration.

## Run

```bash
python3 validate_cs2_logs.py \
  --console-log /path/to/cs2server-console.log \
  --gdb-log /path/to/join-test-gdb.log
```

Use `sudo` only if the supplied log files require elevated read access.
On Windows, use `python` and the appropriate Windows file paths.

Example output when no matching problems are found:

```text
segmentation_faults: 0
fatal_errors: 0
missing_human_class: 0
obsolete_scale_toggle: 0
native_crash_capture: False
```

Exit codes:

| Code | Meaning |
| --- | --- |
| 0 | No matching problems found in the supplied evidence |
| 1 | At least one console error or native-crash indicator found |
| 2 | Arguments/logs could not be used, the GDB log is empty, or no active-map marker exists |

## Checks and limits

Console checks count matching **lines** after the last
`CNetworkGameServerBase::SetServerState (ss_loading -> ss_active)` marker.
They look for segmentation faults, `FATAL`, missing human-class configuration,
and the obsolete experimental `zr_class_scale_enable` command. The last two
checks are specific to the CS2Fixes investigation, not general CS2 requirements.

The entire supplied GDB log is checked for fatal signals or the custom
`NATIVE CRASH BACKTRACE` marker used by the diagnostic capture. Use a GDB log
from the same test session. The utility does not verify that GDB attached
successfully or remained attached throughout the test.

A map change/restart advances the console window and can exclude earlier
errors; review rotated logs when investigating those incidents. An empty
GDB log is rejected rather than treated as successful evidence.

Zero matching errors does not prove that a server is alive, reachable, stable,
or behaving correctly. Test gameplay manually and check the process/listening
port separately. These errors are game-process failures, not evidence of a
Linux kernel panic. The script prints counts only, not raw logs or credentials.

This reusable version counts lines rather than regex occurrences (so a single
`SIGSEGV, Segmentation fault` line is not double-counted), handles GDB thread
signal messages without a custom marker, and rejects empty GDB evidence.
Earlier CS2Fixes PR validation output came from the original ad hoc checks;
this repository does not claim those historical results were produced by this
later version.

## Tests

```bash
python -m unittest discover -s tests -v
```

CI runs on Linux and Windows with Python 3.9 and 3.14. The Python 3.9 Linux
job is pinned to Ubuntu 24.04 because Python 3.9 binaries are unavailable
for Ubuntu 26.04. Other jobs use the latest runner images. Matrix jobs run
independently so a setup failure does not cancel the remaining checks.

## Publish under PtxDK

Create an empty GitHub repository named `cs2-log-validator` under `PtxDK`.
Do not initialize it with a README, license or gitignore; these are included.
From this checkout, run:

```bash
git push -u origin main
```

The configured origin is `https://github.com/PtxDK/cs2-log-validator.git`.
No GitHub repository is created by preparing this local checkout.

## Development and license

Substantially developed with OpenAI Codex assistance; human review is encouraged.
MIT licensed. No server logs, credentials or machine-specific paths are shipped.

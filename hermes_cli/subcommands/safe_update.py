"""Safe-update subcommand: wrapper around hermes-update-with-extras.sh.

Preserves optional [messaging] extras that standard `hermes update` strips,
verifies platform adapters, and restarts the gateway if healthy.
"""
import os
import sys
from pathlib import Path


def cmd_safe_update(args):
    """Run the safe-update wrapper script that preserves extras and verifies adapters."""
    script = Path.home() / ".hermes" / "scripts" / "hermes-update-with-extras.sh"
    if not script.exists():
        print(f"✗ Safe-update script not found: {script}")
        print("  Expected: ~/.hermes/scripts/hermes-update-with-extras.sh")
        sys.exit(1)
    os.execvp("bash", ["bash", str(script)])


def build_safe_update_parser(subparsers, cmd_safe_update):
    """Register the safe-update subcommand parser."""
    parser = subparsers.add_parser(
        "safe-update",
        help="Update Hermes Agent preserving messaging extras and verifying adapters",
        description=(
            "Pull the latest changes from git, reinstall dependencies, "
            "preserve optional [messaging] extras, verify adapters, "
            "and restart the gateway if healthy."
        ),
    )
    parser.set_defaults(func=cmd_safe_update)
    return parser
#!/bin/bash
# One-command re-check for the permission gate
cd "$(dirname "$0")/../.." && python3 hardening_audit/permission-gate-2026-06-15/verify.py

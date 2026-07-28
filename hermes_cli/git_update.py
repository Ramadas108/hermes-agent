"""Safe Git update primitives for Hermes deployments.

This module only operates on Git worktrees and source files. It never opens
Hermes databases and never controls systemd services.
"""
from __future__ import annotations
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class GitStatus:
    remote: str
    target: str
    branch: str | None
    behind: int
    ahead: int
    detached: bool

class GitError(RuntimeError):
    pass

def run(repo: Path, *args: str, check: bool = True) -> str:
    p = subprocess.run(["git", "-C", str(repo), *args], text=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check and p.returncode:
        raise GitError(f"git {' '.join(args)} failed: {p.stderr.strip()}")
    return p.stdout.strip()

def select_remote(repo: Path, preferred: str | None = None) -> str:
    names = run(repo, "remote").splitlines()
    for name in ([preferred] if preferred else []) + ["origin", "upstream"]:
        if name and name in names:
            return name
    raise GitError("No upstream Git remote configured")

def fetch_main(repo: Path, remote: str) -> str:
    run(repo, "fetch", "--no-tags", remote, "main")
    target = f"{remote}/main"
    run(repo, "rev-parse", "--verify", target)
    return target

def status(repo: Path, *, fetch: bool = True, remote: str | None = None) -> GitStatus:
    repo = Path(repo).resolve()
    remote = select_remote(repo, remote)
    target = fetch_main(repo, remote) if fetch else f"{remote}/main"
    run(repo, "rev-parse", "--verify", target)
    head = run(repo, "rev-parse", "HEAD")
    detached = run(repo, "symbolic-ref", "--quiet", "--short", "HEAD", check=False) == ""
    branch = None if detached else run(repo, "symbolic-ref", "--quiet", "--short", "HEAD")
    # These are the authoritative Git counts required by the operator workflow.
    behind = int(run(repo, "rev-list", "--count", f"HEAD..{target}"))
    ahead = int(run(repo, "rev-list", "--count", f"{target}..HEAD"))
    return GitStatus(remote, target, branch, behind, ahead, detached)

def status_text(s: GitStatus) -> str:
    local = "local deployment commit" if s.ahead == 1 else "local deployment commits"
    if s.ahead:
        return f"{s.behind} upstream commits available; {s.ahead} {local} must be reconciled"
    if s.behind:
        return f"{s.behind} upstream commits available; no local deployment commits"
    return "Hermes is up to date"

def safe_update(repo: Path, *, remote: str | None = None,
                worktree: Path | None = None, run_tests: bool = True) -> int:
    repo = Path(repo).resolve()
    s = status(repo, fetch=True, remote=remote)
    print(f"Status: {status_text(s)}")
    if s.detached:
        print("Refusing safe-update: detached HEAD; name the deployment branch first.")
        return 2
    if s.ahead == 0:
        print("No local deployment commit to reapply; use the normal fast-forward path.")
        return 0
    if s.ahead != 1:
        print("Refusing safe-update: expected exactly one local deployment commit.")
        return 2
    deployment = run(repo, "rev-parse", "HEAD")
    root = worktree or Path(tempfile.mkdtemp(prefix="hermes-safe-update-", dir="/tmp"))
    created = worktree is None
    try:
        if root.exists() and any(root.iterdir()):
            raise GitError(f"worktree is not empty: {root}")
        root.parent.mkdir(parents=True, exist_ok=True)
        run(repo, "worktree", "add", "--detach", str(root), s.target)
        print(f"Disposable worktree: {root}")
        p = subprocess.run(["git", "-C", str(root), "cherry-pick", "--no-commit", deployment],
                           text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if p.returncode:
            print("CONFLICT: deployment commit cannot be reapplied cleanly.")
            print(p.stdout.strip())
            subprocess.run(["git", "-C", str(root), "cherry-pick", "--abort"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return 3
        if run_tests:
            env = dict(os.environ, PYTHONPATH=str(root))
            test = subprocess.run([sys.executable, "-m", "pytest", "tests/hermes_cli/test_update_check.py",
                                   "-q", "-o", "addopts="], cwd=root, env=env,
                                  text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            print(test.stdout[-12000:])
            if test.returncode:
                print("Refusing proposed integration: targeted tests failed.")
                return 4
        check = subprocess.run(["/home/openclaw/.local/bin/hermes-python-safe", "--check-runtime"],
                               text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        print(check.stdout.strip())
        if check.returncode:
            return 5
        unit = subprocess.run(["systemctl", "--user", "show", "hermes-gateway.service",
                              "-p", "ExecStart", "-p", "Restart"],
                             text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        print(unit.stdout.strip())
        if unit.returncode or "hermes-python-safe" not in unit.stdout or "--external-supervisor" not in unit.stdout:
            print("Refusing proposed integration: unsafe effective service command.")
            return 6
        run(root, "add", "-A")
        if subprocess.run(["git", "-C", str(root), "diff", "--cached", "--quiet"]).returncode == 0:
            # The cherry-pick --no-commit may be empty if upstream already contains it.
            print("No proposed integration diff.")
            return 0
        run(root, "commit", "-m", "integrate upstream with deployment changes")
        print(f"PROPOSED_COMMIT={run(root, 'rev-parse', 'HEAD')}")
        print("Preparation complete. No production checkout or service was changed.")
        print("Explicit promotion is required; do not run plain hermes update.")
        return 0
    except GitError as exc:
        print(f"ERROR: {exc}")
        return 1
    finally:
        if created:
            subprocess.run(["git", "-C", str(repo), "worktree", "remove", "--force", str(root)], check=False)
            shutil.rmtree(root, ignore_errors=True)

def self_test() -> int:
    with tempfile.TemporaryDirectory(prefix="hermes-git-test-") as td:
        base=Path(td); bare=base/"remote.git"; work=base/"work"
        run(base, "init", "--bare", str(bare))
        run(base, "clone", str(bare), str(work))
        run(work, "config", "user.email", "test@example.invalid"); run(work, "config", "user.name", "Test")
        (work/"f").write_text("base\n"); run(work,"add","f"); run(work,"commit","-m","base"); run(work,"branch","-M","main"); run(work,"push","origin","main")
        # clean, behind-only, local-ahead, diverged, detached
        assert status(work, fetch=True).behind == 0 and status(work, fetch=False).ahead == 0
        (work/"f").write_text("upstream\n"); run(work,"commit","-am","upstream"); run(work,"push","origin","main")
        assert status(work, fetch=True).behind == 0 and status(work, fetch=False).behind == 0
        run(work,"reset","--hard","HEAD~1"); (work/"f").write_text("local\n"); run(work,"commit","-am","deployment")
        s=status(work,fetch=True); assert (s.behind,s.ahead)==(1,1)
        assert safe_update(work, run_tests=False) == 3; run(work,"checkout","--detach","HEAD"); assert status(work,fetch=False).detached
        print("SELF_TEST_PASS clean behind-only local-ahead diverged detached stale-fetch")
    return 0

def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("--repo",default=os.getcwd()); ap.add_argument("--remote"); ap.add_argument("--self-test",action="store_true")
    ns=ap.parse_args()
    if ns.self_test: return self_test()
    return safe_update(Path(ns.repo), remote=ns.remote)

if __name__ == "__main__": raise SystemExit(main())

#!/usr/bin/env python3
"""Submit a verified countertest archive, wait for the verdict, and record it."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import getpass
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
import zipfile


ROOT = Path(__file__).resolve().parent
ARCHIVE = ROOT / "baseline" / "submission.zip"
TOKEN_FILE = ROOT / ".secrets" / "participant.token"
STATE_FILE = ROOT / ".secrets" / "last-submission.json"
RESULTS = ROOT / "baseline" / "results"
SERVER = os.environ.get("HACK_SERVER", "https://hack-contest.hse-hack-club.ru").rstrip("/")
ACTIVE_STATUSES = {"queued", "pending", "processing", "checking", "running"}
TERMINAL_STATUSES = {
    "completed",
    "complete",
    "done",
    "finished",
    "failed",
    "error",
    "rejected",
    "cancelled",
    "canceled",
}


class ContestError(RuntimeError):
    pass


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def archive_sha256(path: Path = ARCHIVE) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_archive(path: Path = ARCHIVE) -> list[str]:
    if not path.is_file():
        raise ContestError(f"Archive not found: {path}")
    if path.stat().st_size > 15 * 1024 * 1024:
        raise ContestError("Archive exceeds the platform limit of 15 MiB")

    with zipfile.ZipFile(path) as archive:
        bad = archive.testzip()
        if bad:
            raise ContestError(f"Corrupt ZIP entry: {bad}")
        names = archive.namelist()
        if not names:
            raise ContestError("Archive is empty")
        if any("/" in name or "\\" in name for name in names):
            raise ContestError("All .in files must be stored at the ZIP root")
        invalid = [name for name in names if not re.fullmatch(r"\d+-\d+\.in", name)]
        if invalid:
            raise ContestError(f"Invalid countertest names: {', '.join(invalid)}")
        empty = [name for name in names if not archive.read(name)]
        if empty:
            raise ContestError(f"Empty countertests: {', '.join(empty)}")
    return sorted(names)


def run_verifier() -> None:
    subprocess.run([sys.executable, str(ROOT / "baseline" / "verify.py")], cwd=ROOT, check=True)


def require_token() -> None:
    if not os.environ.get("HACK_TOKEN") and not TOKEN_FILE.is_file():
        raise ContestError("Contest token is missing. Run: python contest.py configure")


def run_client(*args: str, allow_error: bool = False) -> dict:
    require_token()
    token = os.environ.get("HACK_TOKEN") or TOKEN_FILE.read_text(encoding="utf-8").strip()
    command = args[0]
    headers = {"Authorization": f"Bearer {token}"}
    payload = None
    if command == "progress":
        path = "/progress"
    elif command == "status":
        path = f"/submissions/{args[1]}"
    elif command == "submit":
        source = Path(args[1])
        idempotency_key = args[3] if len(args) == 4 and args[2] == "--key" else str(uuid.uuid4())
        payload = source.read_bytes()
        headers.update(
            {
                "Content-Type": "application/octet-stream",
                "X-Filename": source.name,
                "Idempotency-Key": idempotency_key,
            }
        )
        path = "/submissions"
    else:
        raise ContestError(f"Unsupported API command: {command}")

    request = urllib.request.Request(f"{SERVER}/api/v1{path}", data=payload, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        try:
            response = json.loads(error.read())
        except ValueError:
            response = {"error": {"code": "HTTP_ERROR", "http_status": error.code}}
        if allow_error:
            return response
        raise ContestError(json.dumps(response, ensure_ascii=False)) from error
    except urllib.error.URLError as error:
        raise ContestError("Could not connect securely to the contest API") from error


def nested_value(data: object, keys: set[str]) -> object | None:
    if isinstance(data, dict):
        for key, value in data.items():
            if key.lower() in keys:
                return value
        for value in data.values():
            found = nested_value(value, keys)
            if found is not None:
                return found
    elif isinstance(data, list):
        for value in data:
            found = nested_value(value, keys)
            if found is not None:
                return found
    return None


def submission_id(data: dict) -> str:
    value = nested_value(data, {"submission_id", "id"})
    if not isinstance(value, str) or not value:
        raise ContestError(f"Submission response has no ID: {json.dumps(data, ensure_ascii=False)}")
    return value


def status_name(data: dict) -> str | None:
    value = nested_value(data, {"status", "state"})
    return value.lower() if isinstance(value, str) else None


def is_terminal(data: dict) -> bool:
    status = status_name(data)
    if status in TERMINAL_STATUSES:
        return True
    if status in ACTIVE_STATUSES:
        return False
    return nested_value(data, {"completed_at", "finished_at", "checked_at"}) is not None


def score_summary(data: dict) -> dict[str, int]:
    aliases = {
        "new_hacks": {"new_hacks", "newly_hacked", "new_solutions_hacked", "score_delta"},
        "total_hacks": {"total_hacks", "total_solutions_hacked", "hacked_total", "score"},
    }
    summary = {}
    for label, keys in aliases.items():
        value = nested_value(data, keys)
        if isinstance(value, int):
            summary[label] = value
    results = data.get("results")
    if isinstance(results, dict):
        summary["total_hacks"] = sum(value == "HACKED" for value in results.values())
    return summary


def configure() -> None:
    token = getpass.getpass("Team access key: ").strip()
    if not token:
        raise ContestError("Token is empty")
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(token + "\n", encoding="utf-8")
    try:
        TOKEN_FILE.chmod(0o600)
    except OSError:
        pass
    print(f"Token saved outside Git: {TOKEN_FILE.relative_to(ROOT)}")


def preflight() -> dict:
    names = validate_archive()
    run_verifier()
    info = {
        "archive": str(ARCHIVE.relative_to(ROOT)).replace("\\", "/"),
        "sha256": archive_sha256(),
        "countertests": names,
    }
    print(json.dumps(info, ensure_ascii=False, indent=2))
    return info


def save_result(sid: str, archive: dict, response: dict) -> Path:
    record = {
        "schema_version": 1,
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "archive": archive,
        "submission_id": sid,
        "summary": score_summary(response),
        "response": response,
    }
    path = RESULTS / f"{sid}.json"
    write_json(path, record)
    return path


def save_progress(response: dict) -> Path:
    path = RESULTS / "progress.json"
    existing = load_json(path)
    if existing.get("response") == response:
        return path
    record = {
        "schema_version": 1,
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "summary": score_summary(response),
        "response": response,
    }
    write_json(path, record)
    return path


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, check=check
    )


def commit_result(path: Path, sid: str, push: bool) -> str | None:
    if git("rev-parse", "--is-inside-work-tree", check=False).returncode:
        git("init", "-b", "main")
    # Result commits stay scoped so concurrent project documentation is never swept in.
    git("add", "baseline")
    if not git("diff", "--cached", "--quiet", check=False).returncode:
        return None
    summary = json.loads(path.read_text(encoding="utf-8")).get("summary", {})
    score = summary.get("total_hacks", summary.get("new_hacks", "unknown"))
    git("commit", "-m", f"Record contest result {sid}: {score} hacks")
    commit = git("rev-parse", "HEAD").stdout.strip()
    if push:
        remote = git("remote", "get-url", "origin", check=False)
        if remote.returncode:
            raise ContestError(f"Commit {commit} created, but Git remote 'origin' is not configured")
        git("push", "-u", "origin", "HEAD")
    return commit


def submit(timeout: int, poll_interval: int, force: bool, push: bool) -> None:
    archive = preflight()
    require_token()
    progress = run_client("progress")
    target_ids = [Path(name).stem for name in archive["countertests"]]
    results = progress.get("results", {})
    if not force and isinstance(results, dict) and all(
        results.get(target) == "HACKED" for target in target_ids
    ):
        path = save_progress(progress)
        commit = commit_result(path, "progress", push)
        print(
            json.dumps(
                {
                    "result": str(path.relative_to(ROOT)),
                    "commit": commit,
                    "already_hacked": target_ids,
                    **score_summary(progress),
                },
                ensure_ascii=False,
            )
        )
        return
    state = load_json(STATE_FILE)
    sid = None

    if not force and state.get("archive_sha256") == archive["sha256"]:
        candidate = state.get("submission_id")
        if isinstance(candidate, str):
            current = run_client("status", candidate, allow_error=True)
            if not nested_value(current, {"error"}):
                sid = candidate
                print(f"Resuming submission {sid}; identical archive will not be uploaded again.")

    if sid is None:
        idem_key = str(uuid.uuid4())
        response = run_client("submit", str(ARCHIVE), "--key", idem_key)
        sid = submission_id(response)
        state = {
            "archive_sha256": archive["sha256"],
            "submission_id": sid,
            "idempotency_key": idem_key,
            "submitted_at": datetime.now(timezone.utc).isoformat(),
        }
        write_json(STATE_FILE, state)
        print(f"Submitted {sid}")

    deadline = time.monotonic() + timeout
    while True:
        response = run_client("status", sid)
        status = status_name(response) or "unknown"
        summary = score_summary(response)
        print(f"{datetime.now().astimezone().isoformat(timespec='seconds')} status={status} {summary}")
        if is_terminal(response):
            break
        if time.monotonic() >= deadline:
            raise ContestError(
                f"Submission {sid} is still {status}; rerun the same command to resume polling"
            )
        time.sleep(poll_interval)

    path = save_result(sid, archive, response)
    commit = commit_result(path, sid, push)
    print(json.dumps({"result": str(path.relative_to(ROOT)), "commit": commit, **score_summary(response)}, ensure_ascii=False))


def snapshot(push: bool) -> None:
    response = run_client("progress")
    path = save_progress(response)
    commit = commit_result(path, "progress", push)
    print(
        json.dumps(
            {
                "result": str(path.relative_to(ROOT)),
                "commit": commit,
                **score_summary(response),
            },
            ensure_ascii=False,
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("configure")
    sub.add_parser("preflight")
    sub.add_parser("progress")
    snapshot_parser = sub.add_parser("snapshot")
    snapshot_parser.add_argument("--no-push", action="store_true")
    submit_parser = sub.add_parser("submit")
    submit_parser.add_argument("--timeout", type=int, default=300)
    submit_parser.add_argument("--poll-interval", type=int, default=5)
    submit_parser.add_argument("--force", action="store_true")
    submit_parser.add_argument("--no-push", action="store_true")
    args = parser.parse_args()

    try:
        if args.command == "configure":
            configure()
        elif args.command == "preflight":
            preflight()
        elif args.command == "progress":
            print(json.dumps(run_client("progress"), ensure_ascii=False, indent=2))
        elif args.command == "snapshot":
            snapshot(not args.no_push)
        else:
            submit(args.timeout, args.poll_interval, args.force, not args.no_push)
    except (ContestError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


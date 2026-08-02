from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

import requests


DEFAULT_API_BASE = "http://8.149.247.100:8088"
EXPECTED_BUCKET = "guuanggao001"
REQUIRED_SCOPE = "manju"
NAME_RE = re.compile(
    r"^\d+_(?P<drama>.+?)（第(?P<start>\d+)集到第(?P<end>\d+)集）_"
    r"(?P<title>.+?)_约2分钟_.*\.mp4$",
    re.IGNORECASE,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inventory or upload finished drama videos and create material submissions."
    )
    parser.add_argument("--root", action="append", required=True, help="Delivery tree; repeatable")
    parser.add_argument("--team-name", required=True)
    parser.add_argument("--delivery-time", default=datetime.now().strftime("%Y-%m-%d %H:%M"))
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--api-base", default=os.getenv("MATERIAL_API_BASE_URL", DEFAULT_API_BASE))
    parser.add_argument("--scope", default=REQUIRED_SCOPE)
    parser.add_argument("--expected-bucket", default=EXPECTED_BUCKET)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--skip-drama", action="append", default=[])
    parser.add_argument("--only-drama", action="append", default=[])
    parser.add_argument("--transport-ascii-names", action="store_true")
    parser.add_argument("--retry-unknown", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--upload-only", action="store_true")
    return parser.parse_args()


def atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def load_manifest(path: Path, args: argparse.Namespace) -> dict[str, Any]:
    if path.exists():
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        if "entries" not in payload and payload.get("local_file") and payload.get("oss_key"):
            payload = {
                "version": 1,
                "api_base": args.api_base.rstrip("/"),
                "expected_bucket": payload.get("bucket_expected", args.expected_bucket),
                "bucket_verified": bool(payload.get("bucket_verified", False)),
                "scope": payload.get("scope", args.scope),
                "team_name": args.team_name,
                "delivery_time": args.delivery_time,
                "entries": [
                    {
                        "local_file": payload["local_file"],
                        "status": "upload_success",
                        "oss_key": payload["oss_key"],
                        "submission_id": payload.get("submission_id"),
                        "last_error": None,
                    }
                ],
            }
        return payload
    return {
        "version": 1,
        "api_base": args.api_base.rstrip("/"),
        "expected_bucket": args.expected_bucket,
        "bucket_verified": False,
        "scope": args.scope,
        "team_name": args.team_name,
        "delivery_time": args.delivery_time,
        "entries": [],
    }


def discover(roots: list[str]) -> list[dict[str, Any]]:
    files: list[Path] = []
    for raw_root in roots:
        root = Path(raw_root).resolve()
        if not root.is_dir():
            raise RuntimeError(f"Root does not exist: {root}")
        files.extend(path for path in root.rglob("*.mp4") if path.parent.name.lower() == "delivery")
    rows = []
    for path in sorted(set(files), key=lambda item: str(item).casefold()):
        match = NAME_RE.match(path.name)
        if not match:
            raise RuntimeError(f"Filename does not match delivery contract: {path.name}")
        rows.append(
            {
                "local_file": str(path),
                "file_size_bytes": path.stat().st_size,
                "drama_name": match.group("drama"),
                "episode_range": f"{match.group('start')}-{match.group('end')}",
                "title_name": match.group("title"),
                "video_file_name": path.name,
                "status": "planned",
                "oss_key": None,
                "submission_id": None,
                "last_error": None,
            }
        )
    if not rows:
        raise RuntimeError("No MP4 files were found below delivery directories")
    return rows


def merge_inventory(manifest: dict[str, Any], inventory: list[dict[str, Any]]) -> None:
    existing = {item["local_file"]: item for item in manifest.get("entries", [])}
    merged = []
    for row in inventory:
        prior = existing.get(row["local_file"])
        if prior:
            for key in ("status", "oss_key", "submission_id", "last_error", "upload_response"):
                if key in prior:
                    row[key] = prior[key]
        merged.append(row)
    manifest["entries"] = merged


def require_credentials() -> tuple[str, str]:
    user = os.getenv("MATERIAL_API_USER", "")
    password = os.getenv("MATERIAL_API_PASSWORD", "")
    if not user or not password:
        raise RuntimeError("Set MATERIAL_API_USER and MATERIAL_API_PASSWORD before --execute")
    return user, password


def login(session: requests.Session, api_base: str, user: str, password: str) -> str:
    response = session.post(
        f"{api_base}/users/login",
        json={"name": user, "password": password},
        timeout=(15, 30),
    )
    response.raise_for_status()
    token = response.json().get("token")
    if not token:
        raise RuntimeError("Login response did not include token")
    return token


def run() -> int:
    args = parse_args()
    if args.scope.strip("/") != REQUIRED_SCOPE:
        raise RuntimeError(f"Refusing nonstandard scope; expected {REQUIRED_SCOPE}")
    api_base = args.api_base.rstrip("/")
    manifest = load_manifest(args.manifest, args)
    merge_inventory(manifest, discover(args.root))
    manifest.update(
        api_base=api_base,
        expected_bucket=args.expected_bucket,
        scope=REQUIRED_SCOPE,
        team_name=args.team_name,
        delivery_time=args.delivery_time,
    )
    atomic_write(args.manifest, manifest)

    targets = [entry for entry in manifest["entries"] if entry["drama_name"] not in set(args.skip_drama)]
    if args.only_drama:
        targets = [entry for entry in targets if entry["drama_name"] in set(args.only_drama)]
    targets = targets[: args.limit] if args.limit else targets
    if not args.execute:
        print(json.dumps({"mode": "dry-run", "count": len(targets), "manifest": str(args.manifest)}, ensure_ascii=False))
        return 0

    user, password = require_credentials()
    session = requests.Session()
    token = login(session, api_base, user, password)
    headers = {"Authorization": f"Bearer {token}"}

    for index, entry in enumerate(targets, start=1):
        if str(entry.get("status", "")).endswith("_outcome_unknown") and not args.retry_unknown:
            print(f"HOLD {index}/{len(targets)} unknown remote outcome: {entry['video_file_name']}", flush=True)
            continue
        if entry.get("submission_id") and not args.upload_only:
            entry["status"] = "submission_success"
            print(f"SKIP {index}/{len(targets)} already submitted: {entry['video_file_name']}", flush=True)
            continue
        path = Path(entry["local_file"])
        if not entry.get("oss_key"):
            try:
                with path.open("rb") as stream:
                    transport_name = path.name
                    if args.transport_ascii_names:
                        digest = hashlib.sha256(str(path).encode("utf-8")).hexdigest()[:20]
                        transport_name = f"video-{digest}.mp4"
                    response = session.post(
                        f"{api_base}/admin/uploads/file",
                        headers=headers,
                        files={"file": (transport_name, stream, "video/mp4")},
                        data={"scope": REQUIRED_SCOPE},
                        timeout=(30, 900),
                    )
                response.raise_for_status()
                result = response.json()
                oss_key = result.get("oss_key", "")
                if not oss_key.startswith(f"{REQUIRED_SCOPE}/"):
                    raise RuntimeError(f"Unexpected oss_key prefix: {oss_key}")
                entry.update(status="upload_success", oss_key=oss_key, upload_response=result, transport_file_name=transport_name, last_error=None)
                atomic_write(args.manifest, manifest)
                print(f"UPLOADED {index}/{len(targets)}: {path.name}", flush=True)
            except requests.RequestException as exc:
                entry.update(status="upload_outcome_unknown", last_error=str(exc))
                atomic_write(args.manifest, manifest)
                raise RuntimeError(f"Upload outcome unknown for {path.name}; investigate before retrying") from exc

        elif args.upload_only:
            print(f"SKIP {index}/{len(targets)} existing upload: {path.name}", flush=True)

        if args.upload_only:
            continue

        payload = {
            "team_name": args.team_name,
            "delivery_time": args.delivery_time,
            "drama_name": entry["drama_name"],
            "oss_key": entry["oss_key"],
            "video_file_name": entry["video_file_name"],
            "title_name": entry["title_name"],
            "episode_range": entry["episode_range"],
        }
        try:
            response = session.post(
                f"{api_base}/admin/material-submissions",
                headers={**headers, "Content-Type": "application/json"},
                json=payload,
                timeout=(15, 60),
            )
            response.raise_for_status()
            result = response.json()
            submission_id = result.get("id")
            if not submission_id:
                raise RuntimeError("Submission response did not include id")
            entry.update(status="submission_success", submission_id=str(submission_id), last_error=None)
            atomic_write(args.manifest, manifest)
            print(f"SUBMITTED {index}/{len(targets)} id={submission_id}: {path.name}", flush=True)
        except requests.RequestException as exc:
            entry.update(status="submission_outcome_unknown", last_error=str(exc))
            atomic_write(args.manifest, manifest)
            raise RuntimeError(f"Submission outcome unknown for {path.name}; investigate before retrying") from exc

    counts: dict[str, int] = {}
    for entry in manifest["entries"]:
        counts[entry["status"]] = counts.get(entry["status"], 0) + 1
    print(json.dumps({"mode": "execute", "counts": counts, "manifest": str(args.manifest)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(run())
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import zipfile
from pathlib import Path


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def refs(payload: dict) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    materials = payload.get("materials", {})
    for kind in ("videos", "audios"):
        for item in materials.get(kind, []):
            if item.get("path"):
                found.append((kind, item["path"]))
    for item in materials.get("texts", []):
        try:
            content = json.loads(item.get("content", "{}"))
        except json.JSONDecodeError:
            continue
        for style in content.get("styles", []):
            path = style.get("font", {}).get("path")
            if path:
                found.append(("fonts", path))
    return found


def replace_text_files(root: Path, replacements: dict[str, str]) -> None:
    variants: list[tuple[str, str]] = []
    for old, new in replacements.items():
        variants.extend([
            (old.replace("\\", "\\\\"), new.replace("\\", "\\\\")),
            (old.replace("\\", "\\"), new.replace("\\", "\\")),
            (old, new),
        ])
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".json", ".bak"}:
            continue
        text = path.read_text(encoding="utf-8")
        updated = text
        for old, new in variants:
            updated = updated.replace(old, new)
        if updated != text:
            path.write_text(updated, encoding="utf-8")


def bind_draft_content(path: Path, replacements: dict[str, str]) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    materials = payload.get("materials", {})
    for kind in ("videos", "audios"):
        for item in materials.get(kind, []):
            if item.get("path") in replacements:
                item["path"] = replacements[item["path"]]
    for item in materials.get("texts", []):
        try:
            content = json.loads(item.get("content", "{}"))
        except json.JSONDecodeError:
            continue
        changed = False
        for style in content.get("styles", []):
            font = style.get("font", {})
            if font.get("path") in replacements:
                font["path"] = replacements[font["path"]]
                changed = True
        if changed:
            item["content"] = json.dumps(content, ensure_ascii=False, separators=(",", ":"))
    path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def probe(path: Path) -> dict:
    if path.suffix.lower() not in {".mp4", ".mov", ".mkv", ".avi", ".m4a", ".wav", ".mp3", ".aac"}:
        return {"checked": False}
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height", "-of", "json", str(path)],
        check=True, capture_output=True, text=True, encoding="utf-8",
    )
    data = json.loads(result.stdout)
    duration = float(data.get("format", {}).get("duration") or 0)
    if duration <= 0 or not data.get("streams"):
        raise RuntimeError(f"Media probe failed: {path}")
    return {"checked": True, "duration": duration, "streams": data["streams"]}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--draft", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--zip", action="store_true")
    args = parser.parse_args()
    source = args.draft.resolve()
    if not (source / "draft_content.json").is_file():
        raise SystemExit("draft_content.json not found")
    bundle = args.output.resolve()
    project = bundle / "project" / source.name
    if bundle.exists():
        raise SystemExit(f"Output already exists: {bundle}")
    project.parent.mkdir(parents=True)
    shutil.copytree(source, project)

    payload = json.loads((source / "draft_content.json").read_text(encoding="utf-8"))
    replacements = {str(source): str(project)}
    imported = project / "Resources" / "portable_imports"
    for kind, raw in refs(payload):
        original = Path(raw)
        if not original.is_file():
            raise FileNotFoundError(f"Missing dependency: {original}")
        try:
            relative = original.resolve().relative_to(source)
            target = project / relative
        except ValueError:
            digest = sha256(original)
            target = imported / kind / f"{digest[:12]}_{original.name}"
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                shutil.copy2(original, target)
        replacements[str(original)] = str(target)
    replace_text_files(project, replacements)
    bind_draft_content(project / "draft_content.json", replacements)

    packaged_payload = json.loads((project / "draft_content.json").read_text(encoding="utf-8"))
    records = []
    for kind, raw in refs(packaged_payload):
        path = Path(raw)
        if not path.is_file():
            raise FileNotFoundError(f"Packaged dependency missing: {path}")
        if project not in path.resolve().parents:
            raise RuntimeError(f"External packaged dependency: {path}")
        records.append({
            "kind": kind,
            "path": path.relative_to(project).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
            "probe": probe(path),
        })
    manifest = {
        "schema_version": 1,
        "project_name": source.name,
        "draft_content_sha256": sha256(project / "draft_content.json"),
        "dependency_count": len(records),
        "dependencies": records,
    }
    (bundle / "portable-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    template = Path(__file__).with_name("install_to_jianying.ps1")
    shutil.copy2(template, bundle / "安装到剪映.ps1")
    if args.zip:
        zip_path = bundle.with_suffix(".zip")
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
            for file in bundle.rglob("*"):
                if file.is_file():
                    zf.write(file, file.relative_to(bundle.parent))
        print(zip_path)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

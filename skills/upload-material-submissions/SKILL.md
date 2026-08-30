---
name: upload-material-submissions
description: Inventory, upload, resume, and register finished Chinese short-drama MP4 files with the material-submission API. Use when the user asks to upload finished videos, submit materials, send recaps to OSS, batch-create material submissions, verify the guuanggao001/manju destination, or resume a partially completed submission batch.
---

# Upload Material Submissions

Upload finished MP4 files through the material-submission API and preserve a local manifest after every successful remote step.

## Fixed destination

- Expected OSS bucket: `guuanggao001`
- Object-key prefix: `manju/`
- API base: `http://8.149.247.100:8088`
- Upload endpoint: `POST /admin/uploads/file`
- Submission endpoint: `POST /admin/material-submissions`

Pass `scope=manju` to the upload endpoint. The API response exposes only `oss_key`, not the bucket. Treat a returned `manju/...` key as prefix verification only; confirm the bucket through server configuration or the OSS console before a full batch.

## Credential rules

Never store credentials, bearer tokens, access keys, or passwords in this skill or its manifests. For execution, require:

```text
MATERIAL_API_USER
MATERIAL_API_PASSWORD
```

Allow `MATERIAL_API_BASE_URL` to override the default endpoint. Warn that the current endpoint uses plaintext HTTP; use it only on a trusted network unless the service is upgraded to HTTPS.

## Workflow

1. Inventory all intended delivery MP4 files before making network calls.
2. Run `scripts/upload_material_submissions.py` without `--execute` to generate and inspect a dry-run manifest.
3. Confirm the count, title parsing, episode ranges, team name, destination prefix, and whether the user wants upload-only testing or full submission creation.
4. When the user explicitly asks to upload, run with `--execute`. Their upload request authorizes the scoped remote writes; do not ask again merely because the call creates remote objects.
5. For a canary, add `--limit 1 --upload-only`. Do not create a submission during an upload-only test.
6. For a full batch, omit `--upload-only`. Save `oss_key` immediately after each upload, then save the returned submission `id` immediately after registration.
7. On rerun, reuse the same manifest. Skip entries with `submission_success`; reuse an existing `oss_key` rather than uploading that file again.
8. Stop on an unknown timeout outcome. Do not blindly retry a POST because the server may have completed it.

## File and field mapping

Discover MP4 files below `delivery` directories. Parse names shaped like:

```text
01_剧名（第1集到第4集）_标题_约2分钟_其余生产标记.mp4
```

Map fields as follows:

- `drama_name`: parsed drama name
- `episode_range`: `1-4`
- `title_name`: text between the episode marker and `_约2分钟_`
- `video_file_name`: exact local basename including `.mp4`
- `oss_key`: exact value returned by the upload endpoint
- `team_name`: explicit user value; do not invent one
- `delivery_time`: one consistent local timestamp for the whole batch

If a filename does not parse, fail dry-run validation instead of submitting incomplete metadata.

## Commands

Dry-run four roots:

```powershell
python scripts/upload_material_submissions.py `
  --root "D:\path\drama-a\edit\recap-videos-qc-repaired" `
  --root "D:\path\drama-b\edit\recap-videos-qc-repaired" `
  --team-name "团队名称" `
  --manifest "D:\path\material-submission-manifest.json"
```

Upload one canary without creating a submission:

```powershell
python scripts/upload_material_submissions.py ... --execute --upload-only --limit 1
```

Upload and create all submissions:

```powershell
python scripts/upload_material_submissions.py ... --execute
```

On Windows, if Python `requests` is repeatedly reset during a large multipart
upload while a small `curl.exe` upload succeeds, switch only the file-transfer
layer and retain the same manifest/submission workflow:

```powershell
python scripts/upload_material_submissions.py ... --execute `
  --curl-upload --transport-ascii-names --curl-limit-rate 1M
```

The curl path keeps the bearer token in a temporary header file rather than the
process command line. Diagnose with one requested file first; do not use this
flag to blindly replay an unknown upload outcome. If a long batch still sees
intermittent connection resets, query the failed filename first and retry that
entry with a lower rate such as `--curl-limit-rate 768K`.

Read [references/api-contract.md](references/api-contract.md) when diagnosing API responses, changing destination configuration, or implementing another client.

## Delivery report

Report:

- discovered, uploaded, submitted, skipped, and failed counts;
- manifest path;
- each successful `oss_key` and submission ID;
- whether `manju/` was verified;
- that `guuanggao001` still requires console/server-side verification unless independently confirmed.

Never claim the bucket is verified solely from `oss_key`.

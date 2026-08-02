# Material submission API contract

## Destination

```text
Expected bucket: guuanggao001
Required prefix: manju/
Base URL: http://8.149.247.100:8088
```

The client controls only the prefix through `scope=manju`. Bucket selection is server-side. The uploader must be configured to use `guuanggao001`; the upload response does not prove this.

## Authentication

```http
POST /users/login
Content-Type: application/json

{"name":"...","password":"..."}
```

Read the token from `token` and send `Authorization: Bearer <token>` on later calls.

## Upload

```http
POST /admin/uploads/file
Authorization: Bearer <token>
Content-Type: multipart/form-data

file=<MP4>
scope=manju
```

Require HTTP 200 and a nonempty `oss_key` beginning with `manju/`.

```json
{
  "oss_key": "manju/uuid-video.mp4",
  "file_name": "video.mp4"
}
```

## Create submission

```http
POST /admin/material-submissions
Authorization: Bearer <token>
Content-Type: application/json
```

```json
{
  "team_name": "团队名称",
  "delivery_time": "2026-08-02 12:00",
  "drama_name": "短剧名称",
  "oss_key": "manju/uuid-video.mp4",
  "video_file_name": "原始视频文件名.mp4",
  "title_name": "标题",
  "episode_range": "1-4"
}
```

Require HTTP 200 and a nonempty `id`.

## Failure handling

- `400`: record response body and stop that entry.
- `401`: token expired; log in again only when the previous POST outcome is known.
- `403`: account lacks admin permission; stop the batch.
- `500`: record the body. Do not automatically replay a submission POST.
- Timeout or connection loss after sending a POST: mark outcome unknown and stop. Investigate server state before retrying.
- Upload succeeded but submission failed: retain and reuse the returned `oss_key`.

The API documents no lookup, checksum, delete, rollback, chunked upload, or idempotency endpoint. The local manifest is therefore mandatory for batch work.

# 短剧剪辑 Skills 迁移指南

本包迁移的是可复用的短剧解说、字幕、配音、质检、视频分析、剪映工程打包和素材提交能力。包内不包含 API Key、账号密码、Bearer Token、原始剧集、成片、缓存、模型或客户素材。

## 1. 包内内容

- `skills/`：10 个自建 Skill 及其脚本、参考文档和配置模板。
- `install.ps1`：安装到 Codex 全局 Skills 目录。
- `validate.ps1`：检查 Skill 结构、Python 语法和常见凭证泄漏。
- `.env.example`：运行时环境变量模板，不含真实值。
- `requirements.txt`：Python 最小依赖。
- `examples/upload-manifest.example.json`：素材上传断点清单示例。
- `MIGRATION_GUIDE.md`：本指南。

## 2. 目标机器要求

推荐 Windows 10/11、PowerShell 7、Python 3.11 或更高版本、Node.js 20 或更高版本，并确保以下命令可用：

```powershell
python --version
node --version
ffmpeg -version
ffprobe -version
curl.exe --version
```

视频制作还需要 Codex、Video Use、HyperFrames 和 Remotion 等公共能力；这些公共依赖未复制进本包。

## 3. 解压与完整性校验

将 ZIP 解压到不含临时缓存的固定目录，例如：

```text
D:\tools\duanjuxiaoshuo-skills
```

在 ZIP 同目录核对 SHA-256：

```powershell
Get-FileHash .\duanjuxiaoshuo-skills_20260803.zip -Algorithm SHA256
```

与随包提供的 `.sha256` 文件比较。解压后运行：

```powershell
Set-Location D:\tools\duanjuxiaoshuo-skills
.\validate.ps1
```

## 4. 安装 Skills

默认安装到 `%USERPROFILE%\.codex\skills`：

```powershell
.\install.ps1
```

目标目录已有同名 Skill 时，先备份旧目录，再明确覆盖：

```powershell
Copy-Item "$env:USERPROFILE\.codex\skills" `
  "$env:USERPROFILE\.codex\skills-backup-$(Get-Date -Format yyyyMMdd-HHmmss)" `
  -Recurse
.\install.ps1 -Force
```

也可以安装到独立测试目录：

```powershell
.\install.ps1 -Destination D:\codex-test\skills
```

安装后重启 Codex 或新建任务，使 Skill 清单重新加载。

## 5. 安装运行依赖

```powershell
python -m pip install -r .\requirements.txt
```

FFmpeg 建议加入系统 `PATH`。需要 Remotion 或 HyperFrames 的任务，应在对应视频项目中安装其 Node.js 依赖，不要把 `node_modules` 放入全局 Skill 目录。

## 6. 配置凭证

复制 `.env.example` 到项目外的私有目录，填入目标机器自己的凭证：

```powershell
Copy-Item .\.env.example D:\private\duanju.env
```

在运行任务的 PowerShell 中加载变量：

```powershell
Get-Content D:\private\duanju.env | ForEach-Object {
  $line = $_.Trim()
  if ($line -and -not $line.StartsWith('#') -and $line.Contains('=')) {
    $parts = $line.Split('=', 2)
    [Environment]::SetEnvironmentVariable(
      $parts[0].Trim(),
      $parts[1].Trim().Trim('"').Trim("'"),
      'Process'
    )
  }
}
```

不要把填写后的文件放进 Git、Skill 目录、ZIP 或共享盘。本包不会自动迁移旧机器上的任何真实 Key。

## 7. 短剧生产链路

典型调用顺序：

```text
produce-two-minute-drama-recap
→ minimax-emotional-narration
→ script-aligned-subtitles
→ build-ck-highlight-captions
→ qc-repair-talking-head-video
→ upload-material-submissions
```

主要约束：

- 成片剧情镜头保持原速；旁白可按项目要求加速。
- 对白必须从完整句首进入，在完整句尾后留出必要空间再切回旁白。
- 字幕不得断词，双行字幕必须设置足够行距。
- 单条成片内避免重复镜头和重复旁白。
- 成片文件名保留“第几集到第几集”，便于上传接口解析。

## 8. 素材上传迁移

固定业务配置：

```text
API：http://8.149.247.100:8088
期望 bucket：guuanggao001
对象前缀：manju/
```

客户端只能从返回值验证 `manju/` 前缀；`guuanggao001` 必须通过服务端配置或 OSS 控制台确认。当前 API 为明文 HTTP，只应在可信网络使用。

先生成清单，不执行远端写入：

```powershell
python "$env:USERPROFILE\.codex\skills\upload-material-submissions\scripts\upload_material_submissions.py" `
  --root "D:\delivery\drama-a\edit\recap-videos-qc-repaired" `
  --team-name "短剧剪辑" `
  --manifest "D:\delivery\manifests\drama-a.json"
```

检查文件数量、剧名、集数范围和标题后再执行：

```powershell
python "$env:USERPROFILE\.codex\skills\upload-material-submissions\scripts\upload_material_submissions.py" `
  --root "D:\delivery\drama-a\edit\recap-videos-qc-repaired" `
  --team-name "短剧剪辑" `
  --manifest "D:\delivery\manifests\drama-a.json" `
  --execute --transport-ascii-names --curl-upload --curl-limit-rate 1M
```

Windows 大文件上传如果出现 `curl exit=56` 或连接重置：

1. 不要立即盲目重放 POST。
2. 按精确 `video_file_name` 查询素材系统，确认是否已生成记录。
3. 确认不存在后，复用同一清单并增加 `--retry-unknown`。
4. 将速率降为 `--curl-limit-rate 768K` 或更低。
5. 清单会跳过 `submission_success`，复用已有 `oss_key`，避免重复上传。

## 9. 数据目录迁移建议

代码和素材分离：

```text
D:\tools\duanjuxiaoshuo-skills\   # 本包代码
D:\drama-source\                   # 原剧集，只读保存
D:\drama-jobs\                     # 脚本、EDL、字幕、清单
D:\drama-output\                   # 成片和 QC 交付
D:\private\duanju.env              # 凭证，不进入 Git
```

从旧机器迁移项目数据时，优先复制脚本、EDL、字幕块、旁白计划、QC 报告和上传清单。缓存、临时帧、`node_modules`、渲染缓存和 ASR 中间文件可以在新机器重建。

## 10. 验收清单

- `validate.ps1` 通过。
- Codex 能识别 10 个自建 Skill。
- `python -m pip check` 无依赖冲突。
- `ffmpeg`、`ffprobe`、`curl.exe` 均可调用。
- 使用一个非生产样例完成字幕或 QC 冒烟测试。
- 素材上传先 dry-run，再上传一个明确授权的 canary。
- 上传后逐条核对 `video_file_name`、`oss_key`、submission ID 和重复项。

## 11. 回滚

安装前若已备份全局 Skills，可删除本次安装的 10 个同名目录，再从备份恢复。不要使用递归删除指向 `%USERPROFILE%` 或磁盘根目录；只处理已经核对过的具体 Skill 目录。


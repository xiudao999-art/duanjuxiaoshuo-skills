# duanjuxiaoshuo-skills

自建的中文短剧解说、字幕、配音、质检与素材提报 Skills 集合。

## Skills

| Skill | 用途 |
|---|---|
| `produce-two-minute-drama-recap` | 制作约两分钟、横跨 4–8 集的短剧解说成片 |
| `produce-short-drama-highlight` | 根据批准文案制作旁白与完整原剧对白混剪 |
| `build-ck-highlight-captions` | 生成普通字幕、CK 强调字、弹出动画与同步音效 |
| `script-aligned-subtitles` | 使用 ASR 时间戳对齐批准脚本，避免错字和断词 |
| `minimax-emotional-narration` | 规划并生成 MiniMax 中文情绪旁白 |
| `qc-repair-talking-head-video` | 检查并修复字幕、断句、响度、黑帧和尾句问题 |
| `video-reverse-engineer` | 反向分析参考视频的镜头、声音和剪辑结构 |
| `continuous-story-video` | 管理 AI 剧情视频的人物、场景和镜头连续性 |
| `package-portable-jianying-project` | 打包、迁移并验证可编辑剪映工程 |
| `upload-material-submissions` | 上传成片至 OSS 并创建素材提报记录 |

## 安装

在 PowerShell 中执行：

```powershell
.\install.ps1
```

默认安装到：

```text
%USERPROFILE%\.codex\skills
```

如果目标 Skill 已存在，安装会停止。确认需要覆盖时使用：

```powershell
.\install.ps1 -Force
```

也可以手动复制单个目录：

```powershell
Copy-Item .\skills\produce-two-minute-drama-recap `
  "$env:USERPROFILE\.codex\skills" -Recurse
```

## 典型短剧生产链

```text
produce-two-minute-drama-recap
→ minimax-emotional-narration
→ script-aligned-subtitles
→ build-ck-highlight-captions
→ qc-repair-talking-head-video
→ upload-material-submissions
```

## 外部依赖

本仓库不复制公共 Skill。根据任务按需安装：

- Video Use
- HyperFrames
- Remotion Skills
- FFmpeg / FFprobe
- Python 3.11+
- Node.js（需要 HyperFrames 或 Remotion 时）

各 Skill 的具体依赖、环境变量和验证命令以其 `SKILL.md` 为准。

## 安全

- 仓库不包含 API Key、密码、Bearer Token、成片或客户素材。
- 凭据必须通过环境变量在运行时提供。
- `upload-material-submissions` 的接口地址和 OSS 目标属于业务配置；公开仓库前应再次确认是否允许披露。
- 上传与素材提报是远端写操作，执行前必须核对本地清单和目标环境。

## 验证

```powershell
.\validate.ps1
```

验证脚本会检查 Skill 目录、YAML 基础结构、Python 语法以及常见凭据模式。

## 迁移

完整的依赖安装、凭证配置、目录规划、素材上传断点续传和验收步骤见 [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)。

生成不含凭证和媒体文件的可迁移压缩包：

```powershell
.\build-portable-package.ps1
```

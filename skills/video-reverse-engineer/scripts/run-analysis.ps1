$ErrorActionPreference = 'Stop'

$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..\..'))
$python = Join-Path $projectRoot '.codex\skills\video-use\.venv\Scripts\python.exe'
$analyzer = Join-Path $PSScriptRoot 'analyze_video.py'

if (-not (Test-Path -LiteralPath $python)) {
  throw "Project-local video-use Python environment is missing: $python"
}

$ffmpeg = @(
  (Join-Path $projectRoot 'harness\video-reverse-engineer\node_modules\ffmpeg-static\ffmpeg.exe'),
  (Join-Path $projectRoot 'harness\qishui-ad-production\node_modules\ffmpeg-static\ffmpeg.exe')
) | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
$ffprobe = @(
  (Join-Path $projectRoot 'harness\video-reverse-engineer\node_modules\ffprobe-static\bin\win32\x64\ffprobe.exe'),
  (Join-Path $projectRoot 'harness\qishui-ad-production\node_modules\ffprobe-static\bin\win32\x64\ffprobe.exe')
) | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if ($ffmpeg) { $env:FFMPEG = $ffmpeg }
if ($ffprobe) { $env:FFPROBE = $ffprobe }
if ($ffmpeg) {
  $env:PATH = (Split-Path -Parent $ffmpeg) + [IO.Path]::PathSeparator + $env:PATH
}

$analyzerArgs = @($args)
$modeIndex = [Array]::IndexOf($analyzerArgs, '--mode')
$isDeep = $modeIndex -ge 0 -and $modeIndex + 1 -lt $analyzerArgs.Count -and $analyzerArgs[$modeIndex + 1] -eq 'deep'
$hasTransNet = [Array]::IndexOf($analyzerArgs, '--transnet-json') -ge 0

if ($isDeep -and -not $hasTransNet) {
  $input = $analyzerArgs | Where-Object { $_ -and -not $_.StartsWith('-') } | Select-Object -First 1
  if (-not $input) { throw 'The input video path is required.' }
  $inputPath = [IO.Path]::GetFullPath((Join-Path (Get-Location) $input))
  if (-not (Test-Path -LiteralPath $inputPath)) { throw "Input video not found: $inputPath" }

  $cacheRoot = Join-Path $projectRoot '.vre-cache\transnet'
  New-Item -ItemType Directory -Force -Path $cacheRoot | Out-Null
  $sourceHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $inputPath).Hash.ToLowerInvariant()
  $transNetJson = Join-Path $cacheRoot ($sourceHash + '.json')

  if (-not (Test-Path -LiteralPath $transNetJson)) {
    $transNet = Join-Path $projectRoot '.codex\skills\video-use\.venv\Scripts\transnetv2_pytorch.exe'
    if (-not (Test-Path -LiteralPath $transNet)) { throw "TransNetV2 CLI is missing: $transNet" }
    & $transNet $inputPath --device cpu --format json --output $transNetJson --no-progress-bar --quiet
    if ($LASTEXITCODE -ne 0) { throw "TransNetV2 failed with exit code $LASTEXITCODE" }
  }

  $analyzerArgs += @('--transnet-json', $transNetJson)
}

& $python $analyzer @analyzerArgs
exit $LASTEXITCODE

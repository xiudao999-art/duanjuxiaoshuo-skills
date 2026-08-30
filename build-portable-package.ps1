param(
    [string]$OutputDirectory = (Join-Path (Split-Path $PSScriptRoot -Parent) "skill_packages"),
    [string]$Version = (Get-Date -Format "yyyyMMdd"),
    [string]$UploadManifest
)

$ErrorActionPreference = "Stop"
$packageName = "duanjuxiaoshuo-skills_$Version"
$stage = Join-Path $OutputDirectory $packageName
$zip = "$stage.zip"
$checksumFile = "$zip.sha256"

foreach ($target in @($stage, $zip, $checksumFile)) {
    if (Test-Path -LiteralPath $target) {
        throw "Refusing to overwrite existing package target: $target"
    }
}

New-Item -ItemType Directory -Path $stage -Force | Out-Null

$excludedDirectoryNames = @('.git', 'node_modules', '__pycache__', 'dist', 'outputs', 'upload-manifests')
$excludedExtensions = @('.pyc', '.pyo', '.log', '.tmp', '.wav', '.mp3', '.mp4', '.mov')
$sourceFiles = Get-ChildItem -LiteralPath $PSScriptRoot -Recurse -File | Where-Object {
    $relative = $_.FullName.Substring($PSScriptRoot.Length).TrimStart('\', '/')
    $segments = $relative -split '[\\/]'
    -not ($segments | Where-Object { $_ -in $excludedDirectoryNames }) -and
    $_.Extension.ToLowerInvariant() -notin $excludedExtensions -and
    $_.Name -notin @('.env', 'Thumbs.db', '.DS_Store')
}

foreach ($file in $sourceFiles) {
    $relative = $file.FullName.Substring($PSScriptRoot.Length).TrimStart('\', '/')
    $destination = Join-Path $stage $relative
    $parent = Split-Path $destination -Parent
    New-Item -ItemType Directory -Path $parent -Force | Out-Null
    Copy-Item -LiteralPath $file.FullName -Destination $destination
}

if ($UploadManifest) {
    $resolvedManifest = (Resolve-Path -LiteralPath $UploadManifest).Path
    $payload = Get-Content -LiteralPath $resolvedManifest -Raw -Encoding UTF8 | ConvertFrom-Json
    foreach ($entry in $payload.entries) {
        $entry.local_file = "<RELINK_ROOT>\$($entry.video_file_name)"
    }
    $recordDirectory = Join-Path $stage 'operation-records'
    New-Item -ItemType Directory -Path $recordDirectory -Force | Out-Null
    $recordBaseName = [IO.Path]::GetFileNameWithoutExtension($resolvedManifest)
    $recordPath = Join-Path $recordDirectory ($recordBaseName + '.sanitized.json')
    $payload | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $recordPath -Encoding UTF8
}

$manifestEntries = Get-ChildItem -LiteralPath $stage -Recurse -File | Sort-Object FullName | ForEach-Object {
    [ordered]@{
        path = $_.FullName.Substring($stage.Length).TrimStart('\', '/').Replace('\', '/')
        bytes = $_.Length
        sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    }
}

$packageManifest = [ordered]@{
    package = $packageName
    created_at = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss zzz')
    source = $PSScriptRoot
    credentials_included = $false
    media_included = $false
    files = @($manifestEntries)
}
$packageManifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $stage 'package-manifest.json') -Encoding UTF8

Compress-Archive -Path (Join-Path $stage '*') -DestinationPath $zip -CompressionLevel Optimal
$zipHash = (Get-FileHash -LiteralPath $zip -Algorithm SHA256).Hash.ToLowerInvariant()
"$zipHash  $(Split-Path $zip -Leaf)" | Set-Content -LiteralPath $checksumFile -Encoding ASCII

Write-Host "PACKAGE=$stage"
Write-Host "ZIP=$zip"
Write-Host "SHA256=$zipHash"

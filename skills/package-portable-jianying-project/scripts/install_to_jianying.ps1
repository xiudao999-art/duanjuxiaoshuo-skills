$ErrorActionPreference = "Stop"
$bundle = Split-Path -Parent $MyInvocation.MyCommand.Path
$container = Join-Path $bundle "project"
$projects = @(Get-ChildItem -LiteralPath $container -Directory)
if ($projects.Count -ne 1) { throw "The package must contain exactly one project directory." }
$source = $projects[0].FullName
$name = $projects[0].Name
$draftRoot = Join-Path $env:LOCALAPPDATA "JianyingPro\User Data\Projects\com.lveditor.draft"
if (-not (Test-Path -LiteralPath $draftRoot)) { throw "Start Jianying Pro once, close it, and retry." }
$destination = Join-Path $draftRoot $name
if (Test-Path -LiteralPath $destination) {
    $destination = Join-Path $draftRoot ($name + "_import_" + (Get-Date -Format "yyyyMMdd_HHmmss"))
}
Copy-Item -LiteralPath $source -Destination $destination -Recurse
$old = (Resolve-Path -LiteralPath $source).Path
$new = (Resolve-Path -LiteralPath $destination).Path
$oldEscaped = $old.Replace("\", "\\")
$newEscaped = $new.Replace("\", "\\")
$oldDoubleEscaped = $old.Replace("\", "\\\\")
$newDoubleEscaped = $new.Replace("\", "\\\\")
foreach ($file in Get-ChildItem -LiteralPath $destination -Recurse -File | Where-Object { $_.Extension -in ".json", ".bak" }) {
    $text = [IO.File]::ReadAllText($file.FullName, [Text.Encoding]::UTF8)
    $updated = $text.Replace($oldDoubleEscaped, $newDoubleEscaped)
    $updated = $updated.Replace($oldEscaped, $newEscaped).Replace($old, $new)
    if ($updated -ne $text) { [IO.File]::WriteAllText($file.FullName, $updated, [Text.UTF8Encoding]::new($false)) }
}
$candidateFiles = @(Get-ChildItem -LiteralPath $destination -Recurse -File | Where-Object { $_.Extension -in ".json", ".bak" })
$resourceRoot = Join-Path $destination "Resources"
$resourceFiles = @(Get-ChildItem -LiteralPath $resourceRoot -Recurse -File)
$draftFile = Join-Path $destination "draft_content.json"
$data = Get-Content -LiteralPath $draftFile -Raw -Encoding UTF8 | ConvertFrom-Json
$paths = @($data.materials.videos.path) + @($data.materials.audios.path)
foreach ($textItem in @($data.materials.texts)) {
    if (-not $textItem.content) { continue }
    $content = $textItem.content | ConvertFrom-Json
    foreach ($style in @($content.styles)) { if ($style.font.path) { $paths += $style.font.path } }
}
$paths = @($paths | Where-Object { $_ } | Select-Object -Unique)

# The packaged JSON may contain the absolute path from the build machine.
# Rebind every dependency from its Resources-relative suffix; use a unique
# basename only as a fallback. This makes drive letter, username, extraction
# directory, and package-folder renaming irrelevant.
$rebound = 0
foreach ($oldReference in $paths) {
    if ((Test-Path -LiteralPath $oldReference) -and $oldReference.StartsWith($destination, [StringComparison]::OrdinalIgnoreCase)) {
        continue
    }
    $normalized = $oldReference.Replace("/", "\")
    $target = $null
    $marker = "\Resources\"
    $markerIndex = $normalized.IndexOf($marker, [StringComparison]::OrdinalIgnoreCase)
    if ($markerIndex -ge 0) {
        $relative = $normalized.Substring($markerIndex + 1)
        $candidate = Join-Path $destination $relative
        if (Test-Path -LiteralPath $candidate) { $target = (Resolve-Path -LiteralPath $candidate).Path }
    }
    if (-not $target) {
        $leaf = [IO.Path]::GetFileName($normalized)
        $matches = @($resourceFiles | Where-Object { $_.Name.Equals($leaf, [StringComparison]::OrdinalIgnoreCase) })
        if ($matches.Count -eq 1) { $target = $matches[0].FullName }
    }
    if (-not $target) {
        throw "Dependency rebind failed: $oldReference"
    }
    $refEscaped = $oldReference.Replace("\", "\\")
    $targetEscaped = $target.Replace("\", "\\")
    $refDoubleEscaped = $oldReference.Replace("\", "\\\\")
    $targetDoubleEscaped = $target.Replace("\", "\\\\")
    foreach ($file in $candidateFiles) {
        $text = [IO.File]::ReadAllText($file.FullName, [Text.Encoding]::UTF8)
        $updated = $text.Replace($refDoubleEscaped, $targetDoubleEscaped)
        $updated = $updated.Replace($refEscaped, $targetEscaped).Replace($oldReference, $target)
        if ($updated -ne $text) {
            [IO.File]::WriteAllText($file.FullName, $updated, [Text.UTF8Encoding]::new($false))
        }
    }
    $rebound++
}

$data = Get-Content -LiteralPath $draftFile -Raw -Encoding UTF8 | ConvertFrom-Json
$paths = @($data.materials.videos.path) + @($data.materials.audios.path)
foreach ($textItem in @($data.materials.texts)) {
    if (-not $textItem.content) { continue }
    $content = $textItem.content | ConvertFrom-Json
    foreach ($style in @($content.styles)) { if ($style.font.path) { $paths += $style.font.path } }
}
$paths = @($paths | Where-Object { $_ } | Select-Object -Unique)
$missing = @($paths | Where-Object { -not (Test-Path -LiteralPath $_) })
$external = @($paths | Where-Object { -not $_.StartsWith($destination, [StringComparison]::OrdinalIgnoreCase) })
if ($missing.Count -or $external.Count) { throw "Migration validation failed: missing=$($missing.Count), external=$($external.Count)." }
$fontDir = Join-Path $env:LOCALAPPDATA "Microsoft\Windows\Fonts"
New-Item -ItemType Directory -Force -Path $fontDir | Out-Null
foreach ($font in Get-ChildItem -LiteralPath (Join-Path $destination "Resources") -Recurse -File | Where-Object { $_.Extension -in ".otf", ".ttf" }) {
    Copy-Item -LiteralPath $font.FullName -Destination (Join-Path $fontDir $font.Name) -Force
}
$report = Join-Path $destination "PORTABLE_IMPORT_OK.txt"
@("PASS", "Project=$destination", "ValidatedPaths=$($paths.Count)", "ReboundPaths=$rebound", "Missing=0", "External=0") | Set-Content -LiteralPath $report -Encoding UTF8
Write-Host "Install and relink completed: $destination" -ForegroundColor Green
if ($env:PORTABLE_TEST_NO_PAUSE -ne "1") { Read-Host "Press Enter to exit" }

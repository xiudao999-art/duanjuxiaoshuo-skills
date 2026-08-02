param(
    [string]$Destination = (Join-Path $env:USERPROFILE ".codex\skills"),
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$sourceRoot = Join-Path $PSScriptRoot "skills"
$skillDirs = @(Get-ChildItem -LiteralPath $sourceRoot -Directory | Sort-Object Name)

if ($skillDirs.Count -eq 0) {
    throw "No skills found in $sourceRoot"
}

New-Item -ItemType Directory -Path $Destination -Force | Out-Null

if (-not $Force) {
    $conflicts = @($skillDirs | Where-Object {
        Test-Path -LiteralPath (Join-Path $Destination $_.Name)
    })
    if ($conflicts.Count -gt 0) {
        $names = ($conflicts.Name -join ", ")
        throw "Destination already contains: $names. Re-run with -Force to replace them."
    }
}

foreach ($skill in $skillDirs) {
    $target = Join-Path $Destination $skill.Name
    if (Test-Path -LiteralPath $target) {
        Remove-Item -LiteralPath $target -Recurse -Force
    }
    Copy-Item -LiteralPath $skill.FullName -Destination $Destination -Recurse
    Write-Host "Installed $($skill.Name)"
}

Write-Host "Installed $($skillDirs.Count) skills to $Destination"

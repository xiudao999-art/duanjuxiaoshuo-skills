$ErrorActionPreference = "Stop"
$skillRoot = Join-Path $PSScriptRoot "skills"
$skills = @(Get-ChildItem -LiteralPath $skillRoot -Directory | Sort-Object Name)
$errors = @()

foreach ($skill in $skills) {
    $skillFile = Join-Path $skill.FullName "SKILL.md"
    if (-not (Test-Path -LiteralPath $skillFile)) {
        $errors += "Missing SKILL.md: $($skill.Name)"
        continue
    }
    $content = Get-Content -LiteralPath $skillFile -Raw -Encoding UTF8
    $frontmatter = [regex]::Match($content, '(?ms)^---\s*(.*?)^---').Groups[1].Value
    if (-not $frontmatter -or
        $frontmatter -notmatch '(?m)^name:\s*[^\r\n]+' -or
        $frontmatter -notmatch '(?m)^description:\s*[^\r\n]+') {
        $errors += "Invalid frontmatter: $($skill.Name)"
    }
}

$pythonFiles = @(Get-ChildItem -LiteralPath $skillRoot -Recurse -File -Filter "*.py")
foreach ($file in $pythonFiles) {
    python -m py_compile $file.FullName
    if ($LASTEXITCODE -ne 0) {
        $errors += "Python compile failed: $($file.FullName)"
    }
}

$secretPattern = '(sk-[A-Za-z0-9_-]{16,}|Bearer\s+[A-Za-z0-9._-]{16,}|api[_-]?key\s*[=:]\s*[A-Za-z0-9_-]{16,})'
foreach ($file in Get-ChildItem -LiteralPath $PSScriptRoot -Recurse -File) {
    if ($file.Extension -in @('.wav', '.mp3', '.mp4', '.mov', '.png', '.jpg', '.jpeg', '.pyc')) {
        continue
    }
    $content = Get-Content -LiteralPath $file.FullName -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
    if ($content -match $secretPattern) {
        $errors += "Possible credential in: $($file.FullName)"
    }
}

if ($errors.Count -gt 0) {
    $errors | ForEach-Object { Write-Error $_ }
    exit 1
}

Write-Host "PASS: $($skills.Count) skills and $($pythonFiles.Count) Python files validated."

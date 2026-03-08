$ErrorActionPreference = "Stop"

$rootDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $rootDir

$submodules = @(
    @{ Url = "https://github.com/gitroomhq/postiz-app"; Path = "vendor/postiz-app" },
    @{ Url = "https://github.com/ClimenteA/social-media-posts-scheduler"; Path = "vendor/django-social-scheduler" },
    @{ Url = "https://github.com/Masterjx9/socialmediascheduler"; Path = "vendor/socialmediascheduler" },
    @{ Url = "https://github.com/ayrshare/social-media-api"; Path = "vendor/ayrshare-js" },
    @{ Url = "https://github.com/ayrshare/social-post-api-python"; Path = "vendor/ayrshare-python" }
)

function Show-ExpectedCommands {
    foreach ($module in $submodules) {
        Write-Host "git submodule add $($module.Url) $($module.Path)"
    }
}

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Error "git is not installed or not available in PATH."
    exit 1
}

$insideRepo = (& git rev-parse --is-inside-work-tree 2>$null)
if ($LASTEXITCODE -ne 0 -or $insideRepo.Trim() -ne "true") {
    Write-Host "This folder is not inside a git repository."
    Write-Host "Expected commands:"
    Show-ExpectedCommands
    Write-Host "git submodule update --init --recursive"
    Write-Host "git submodule foreach --recursive git pull origin main"
    exit 0
}

$topLevel = (& git rev-parse --show-toplevel).Trim()
$rootFull = [System.IO.Path]::GetFullPath($rootDir)
$topFull = [System.IO.Path]::GetFullPath($topLevel)
if ($topFull -ne $rootFull) {
    Write-Host "Safety stop: $rootDir is not the active git top-level."
    Write-Host "Detected git top-level: $topLevel"
    Write-Host "Skipping automatic submodule add to avoid writing outside this project folder."
    Write-Host "Expected commands:"
    Show-ExpectedCommands
    Write-Host "git submodule update --init --recursive"
    Write-Host "git submodule foreach --recursive git pull origin main"
    exit 0
}

New-Item -ItemType Directory -Force -Path (Join-Path $rootDir "vendor") | Out-Null

foreach ($module in $submodules) {
    $targetPath = Join-Path $rootDir $module.Path
    if (Test-Path $targetPath) {
        Write-Host "Skipping existing path: $($module.Path)"
        Write-Host "Expected command: git submodule add $($module.Url) $($module.Path)"
        continue
    }

    & git submodule add $module.Url $module.Path
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to add submodule: $($module.Path)"
    }
}

& git submodule update --init --recursive
if ($LASTEXITCODE -ne 0) {
    throw "Failed to initialize submodules."
}

$submoduleLines = & git config --file .gitmodules --get-regexp path 2>$null
if ($LASTEXITCODE -eq 0 -and $submoduleLines) {
    foreach ($line in $submoduleLines) {
        $parts = $line -split "\s+"
        if ($parts.Count -lt 2) {
            continue
        }

        $subPath = $parts[1]
        $subAbsPath = Join-Path $rootDir $subPath
        $branch = (& git -C $subAbsPath symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>$null)
        if (-not $branch) {
            $branch = "origin/main"
        }
        $branch = $branch.Trim() -replace "^origin/", ""

        Write-Host "Updating $subPath using $branch"
        & git -C $subAbsPath pull origin $branch
    }
}

Write-Host "Current submodules:"
& git submodule status --recursive

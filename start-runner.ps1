<#
.SYNOPSIS
    Starts the GitHub Actions self-hosted runner for local Docker Desktop CI/CD.
.DESCRIPTION
    Runs C:\Users\ADMIN\actions-runner\run.cmd to listen for GitHub Actions workflow jobs.
#>

$runnerDir = "C:\Users\ADMIN\actions-runner"
if (-not (Test-Path $runnerDir)) {
    Write-Error "Runner directory not found at $runnerDir"
    exit 1
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Starting GitHub Actions Runner (Docker Desktop Agent)    " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Listening for CI/CD jobs from https://github.com/akarshrajap/dataframe..." -ForegroundColor Yellow

Set-Location $runnerDir
.\run.cmd

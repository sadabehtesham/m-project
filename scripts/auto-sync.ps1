param(
    [int]$QuietSeconds = 8,
    [int]$PollSeconds = 3
)

$ErrorActionPreference = 'Stop'
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..')
Set-Location $repoRoot

Write-Host "GitHub auto-sync is watching $repoRoot"
Write-Host "Changes are pushed after $QuietSeconds quiet seconds. Press Ctrl+C to stop."

$lastChange = Get-Date
$hadChanges = $false

while ($true) {
    $status = @(git status --porcelain)

    if ($status.Count -gt 0 -and -not $hadChanges) {
        Write-Host "Change detected; waiting for edits to settle..."
        $lastChange = Get-Date
        $hadChanges = $true
    } elseif ($hadChanges -and ((Get-Date) - $lastChange).TotalSeconds -ge $QuietSeconds) {
        git add --all
        $staged = @(git diff --cached --name-only)

        if ($staged.Count -gt 0) {
            $message = "Auto-sync $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
            git commit -m $message
            git push
            Write-Host "Pushed $($staged.Count) changed path(s) to GitHub."
        }

        $hadChanges = $false
    }

    Wait-Event -Timeout $PollSeconds | Out-Null
}
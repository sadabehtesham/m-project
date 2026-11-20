param(
    [string]$Output = "m-project-submission.zip"
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$outputPath = Join-Path $repoRoot $Output

if (Test-Path $outputPath) {
    Remove-Item $outputPath -Force
}

$rawDatasetFiles = @(
    "ckd.csv",
    "diabetes.csv",
    "heart_disease.csv",
    "hypertension.csv",
    "liver_disease.csv"
)

foreach ($fileName in $rawDatasetFiles) {
    $datasetPath = Join-Path $repoRoot "data\raw\$fileName"
    if (-not (Test-Path $datasetPath)) {
        throw "Missing required raw dataset: data/raw/$fileName"
    }
}

$tempDir = Join-Path ([System.IO.Path]::GetTempPath()) ("m-project-submission-" + [guid]::NewGuid())
New-Item -ItemType Directory -Path $tempDir | Out-Null

try {
    Copy-Item (Join-Path $repoRoot "README.md") $tempDir
    Copy-Item (Join-Path $repoRoot "requirements.txt") $tempDir

    foreach ($directoryName in @("data", "models", "notebooks", "presentation", "reports", "src", "webapp")) {
        Copy-Item (Join-Path $repoRoot $directoryName) (Join-Path $tempDir $directoryName) -Recurse
    }

    Remove-Item (Join-Path $tempDir "webapp\.env") -Force -ErrorAction SilentlyContinue
    Remove-Item (Join-Path $tempDir "webapp\*.db") -Force -ErrorAction SilentlyContinue

    Compress-Archive -Path (Join-Path $tempDir "*") -DestinationPath $outputPath
    Write-Host "Created submission archive: $outputPath"
}
finally {
    Remove-Item $tempDir -Recurse -Force
}

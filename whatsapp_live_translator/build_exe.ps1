$ErrorActionPreference = 'Stop'

$projectRoot = [System.IO.Path]::GetFullPath($PSScriptRoot)
$buildPath = [System.IO.Path]::GetFullPath((Join-Path $projectRoot 'build'))
$distPath = [System.IO.Path]::GetFullPath((Join-Path $projectRoot 'dist'))
$specPath = [System.IO.Path]::GetFullPath((Join-Path $projectRoot 'WhatsAppTranslator.spec'))

# dist/data contains persistent settings when the EXE is used locally.
# Only intermediate build files may be removed; never clean the whole dist.
foreach ($path in @($buildPath)) {
    if (-not $path.StartsWith($projectRoot + [System.IO.Path]::DirectorySeparatorChar)) {
        throw "Refusing to clean a path outside the project: $path"
    }
    if (Test-Path -LiteralPath $path) {
        Remove-Item -LiteralPath $path -Recurse -Force
    }
}
if (Test-Path -LiteralPath $specPath) {
    Remove-Item -LiteralPath $specPath -Force
}

python -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --name 'WhatsAppTranslator' `
    --distpath $distPath `
    --workpath $buildPath `
    --specpath $projectRoot `
    --collect-all rapidocr_onnxruntime `
    --hidden-import PIL._tkinter_finder `
    (Join-Path $projectRoot 'app.py')

if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller failed with exit code $LASTEXITCODE"
}

$exePath = Join-Path $distPath 'WhatsAppTranslator.exe'
if (-not (Test-Path -LiteralPath $exePath)) {
    throw "Build completed but the EXE was not found: $exePath"
}

Write-Host ""
Write-Host "Build succeeded: $exePath" -ForegroundColor Green
Write-Host "The EXE includes Python, RapidOCR, ONNX Runtime, OpenCV, and OCR models."

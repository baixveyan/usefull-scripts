$ErrorActionPreference = 'Stop'
$workspaceRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$sampleRoot = Join-Path $PSScriptRoot ('build-sample-' + [guid]::NewGuid().ToString())
$sampleRoot = [IO.Path]::GetFullPath($sampleRoot)
if (-not $sampleRoot.StartsWith($workspaceRoot + [IO.Path]::DirectorySeparatorChar)) {
    throw 'Sample must be inside workspace'
}
New-Item -ItemType Directory -Path (Join-Path $sampleRoot 'dist/data') -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $sampleRoot 'build') -Force | Out-Null
$sentinelPath = Join-Path $sampleRoot 'dist/data/contacts-sample.txt'
Set-Content -LiteralPath $sentinelPath -Value 'synthetic-data-only'
Set-Content -LiteralPath (Join-Path $sampleRoot 'build/stale.txt') -Value 'stale'
Set-Content -LiteralPath (Join-Path $sampleRoot 'app.py') -Value '# synthetic entrypoint'
Copy-Item -LiteralPath (Join-Path $workspaceRoot 'whatsapp_live_translator/build_exe.ps1') -Destination (Join-Path $sampleRoot 'build_exe.ps1')
$buildCapture = [pscustomobject]@{ Arguments = @() }
function python {
    $buildCapture.Arguments = @($args)
    $distIndex = [Array]::IndexOf($buildCapture.Arguments, '--distpath')
    if ($distIndex -lt 0) { throw 'Missing explicit distpath' }
    $mockOutput = Join-Path $buildCapture.Arguments[$distIndex + 1] 'WhatsAppTranslator.exe'
    Set-Content -LiteralPath $mockOutput -Value 'mock-executable-not-runnable'
    $global:LASTEXITCODE = 0
}
try {
    # Run from a different working directory to exercise absolute output paths.
    Push-Location $workspaceRoot
    try { & (Join-Path $sampleRoot 'build_exe.ps1') } finally { Pop-Location }
    if ((Get-Content -Raw -LiteralPath $sentinelPath).Trim() -ne 'synthetic-data-only') {
        throw 'Persistent data was modified or removed'
    }
    if (Test-Path -LiteralPath (Join-Path $sampleRoot 'build/stale.txt')) {
        throw 'Stale intermediate build file was not removed'
    }
    foreach ($flag in @('--distpath', '--workpath', '--specpath')) {
        $index = [Array]::IndexOf($buildCapture.Arguments, $flag)
        if ($index -lt 0 -or -not [IO.Path]::IsPathRooted($buildCapture.Arguments[$index + 1])) {
            throw "Missing absolute path: $flag"
        }
    }
    Write-Output 'Build fixture: PASS (persistent data retained; absolute paths; no real Python or EXE run)'
} finally {
    Remove-Item Function:\python
    $resolvedSample = [IO.Path]::GetFullPath($sampleRoot)
    if ($resolvedSample.StartsWith($workspaceRoot + [IO.Path]::DirectorySeparatorChar) -and
        (Split-Path $resolvedSample -Leaf).StartsWith('build-sample-')) {
        Remove-Item -LiteralPath $resolvedSample -Recurse -Force
    } else {
        throw 'Refusing cleanup outside known sample root'
    }
}

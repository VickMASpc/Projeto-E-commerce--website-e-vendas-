param(
    [string]$PluginRoot = "$env:USERPROFILE\.understand-anything\repo\understand-anything-plugin",
    [string]$OutputDir = "docs\demo",
    [string]$BasePath = "./"
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$graphDir = Join-Path $repoRoot ".understand-anything"
$graphFile = Join-Path $graphDir "knowledge-graph.json"
$metaFile = Join-Path $graphDir "meta.json"
$configFile = Join-Path $graphDir "config.json"
$dashboardDir = Join-Path $PluginRoot "packages\dashboard"
$coreDistFile = Join-Path $PluginRoot "packages\core\dist\index.js"
$dashboardTsc = Join-Path $dashboardDir "node_modules\typescript\bin\tsc"
$dashboardVite = Join-Path $dashboardDir "node_modules\vite\bin\vite.js"
$resolvedOutputDir = Join-Path $repoRoot $OutputDir

if (-not (Test-Path $graphFile)) {
    throw "Knowledge graph not found at '$graphFile'. Generate it first with Understand Anything."
}

if (-not (Test-Path $dashboardDir)) {
    throw "Dashboard package not found at '$dashboardDir'. Check the -PluginRoot argument."
}

if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    throw "Node.js was not found in PATH. Install Node.js before building the static dashboard."
}

if (-not (Test-Path $coreDistFile)) {
    throw "Understand Anything core is not built at '$coreDistFile'. Build/install the plugin once before using this script."
}

if (-not (Test-Path $dashboardTsc) -or -not (Test-Path $dashboardVite)) {
    throw "Dashboard dependencies are missing in '$dashboardDir\\node_modules'. Install the plugin dependencies once before using this script."
}

Write-Host "[1/3] Validating Understand Anything build prerequisites..."
Write-Host "Core bundle found at '$coreDistFile'."

Write-Host "[2/3] Building static dashboard bundle..."
$env:VITE_GRAPH_URL = "./knowledge-graph.json"
$env:VITE_META_URL = "./meta.json"
$env:VITE_CONFIG_URL = "./config.json"
Push-Location $dashboardDir
try {
    & node $dashboardTsc -b
    if ($LASTEXITCODE -ne 0) {
        throw "TypeScript build failed for the dashboard."
    }

    & node $dashboardVite build --config vite.config.demo.ts --base $BasePath
    if ($LASTEXITCODE -ne 0) {
        throw "Vite demo build failed for the dashboard."
    }
}
finally {
    Pop-Location
}

Write-Host "[3/3] Copying bundle and graph data to '$resolvedOutputDir'..."
if (Test-Path $resolvedOutputDir) {
    Remove-Item -LiteralPath $resolvedOutputDir -Recurse -Force
}
New-Item -ItemType Directory -Path $resolvedOutputDir | Out-Null
Copy-Item -Path (Join-Path $dashboardDir "dist\*") -Destination $resolvedOutputDir -Recurse -Force

Copy-Item -LiteralPath $graphFile -Destination (Join-Path $resolvedOutputDir "knowledge-graph.json") -Force
if (Test-Path $metaFile) {
    Copy-Item -LiteralPath $metaFile -Destination (Join-Path $resolvedOutputDir "meta.json") -Force
}
if (Test-Path $configFile) {
    Copy-Item -LiteralPath $configFile -Destination (Join-Path $resolvedOutputDir "config.json") -Force
}

Write-Host ""
Write-Host "Static dashboard ready:"
Write-Host "  $resolvedOutputDir"
Write-Host ""
Write-Host "Build base path:"
Write-Host "  $BasePath"
Write-Host ""
Write-Host "GitHub Pages examples:"
Write-Host "  User/Org site publishing from docs root:    -BasePath ./"
Write-Host "  Project site publishing from docs root:     -BasePath /<repo-name>/"

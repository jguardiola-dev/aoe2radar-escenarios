# Construye escenarios.exe con PyInstaller (sin consola: aoe2radar lo lanza sin que aparezca ninguna ventana).
#
#   .\empaquetado\construir-exe.ps1                # onedir (el que se distribuye): dist\escenarios\escenarios.exe
#   .\empaquetado\construir-exe.ps1 -Modo onefile  # un solo .exe, solo para comparar
#
# Por qué onedir (medido en octubre de 2026, Python 3.11, PyInstaller 6.22): arranca en 0,8 s frente a 1,5 s del onefile
# (que se descomprime en %TEMP% cada vez, y eso además suele despertar al antivirus); comprimido pesan casi igual
# (9,9 MB frente a 9,4 MB), que es lo que crece la descarga del instalador. Instalado ocupa 25,6 MB frente a 9,7 MB.
#
# Necesita el venv del proyecto con requirements-dev.txt instalado. No incluye xs-check (el linter de XS que trae la
# librería): la herramienta lo desactiva y solo lo usan los tests.
param(
    [ValidateSet('onefile', 'onedir')] [string] $Modo = 'onedir'
)
$ErrorActionPreference = 'Stop'
$raiz = Split-Path -Parent $PSScriptRoot
$py = Join-Path $raiz 'venv\Scripts\python.exe'
if (-not (Test-Path $py)) { throw "No encuentro el venv ($py). Créalo: python -m venv venv; venv\Scripts\pip install -r requirements-dev.txt -e ." }
$lib = & $py -c "import AoE2ScenarioParser, os; print(os.path.dirname(AoE2ScenarioParser.__file__))"
$dist = Join-Path $raiz 'dist'
$work = Join-Path $raiz "build\work-$Modo"

& $py -m PyInstaller --noconfirm --clean --log-level WARN "--$Modo" --noconsole --name escenarios `
    --distpath $dist --workpath $work --specpath (Join-Path $raiz 'build') `
    --collect-submodules AoE2ScenarioParser `
    --add-data "$lib\versions;AoE2ScenarioParser\versions" `
    --add-data "$lib\datasets\sources;AoE2ScenarioParser\datasets\sources" `
    (Join-Path $PSScriptRoot 'escenarios.py')
if ($LASTEXITCODE -ne 0) { throw "PyInstaller falló ($LASTEXITCODE)" }

$exe = if ($Modo -eq 'onefile') { Join-Path $dist 'escenarios.exe' } else { Join-Path $dist 'escenarios\escenarios.exe' }

# La licencia GPL y dónde está el código fuente, junto al exe (así viajan dentro del instalador de aoe2radar)
if ($Modo -eq 'onedir') {
    $version = & $py -c "import aoe2radar_escenarios as a; print(a.__version__)"
    Copy-Item (Join-Path $raiz 'LICENSE') (Join-Path $dist 'escenarios\LICENSE') -Force
    $fuentes = (Get-Content (Join-Path $PSScriptRoot 'FUENTES.txt') -Raw -Encoding UTF8).Replace('{VERSION}', $version)
    [IO.File]::WriteAllText((Join-Path $dist 'escenarios\FUENTES.txt'), $fuentes, [Text.UTF8Encoding]::new($false))
}
$mb = if ($Modo -eq 'onefile') { (Get-Item $exe).Length / 1MB } else { ((Get-ChildItem (Join-Path $dist 'escenarios') -Recurse -File | Measure-Object Length -Sum).Sum) / 1MB }
Write-Host ("{0}: {1:N1} MB" -f $exe, $mb)

# Prueba de humo: genera el escenario de ejemplo con el exe recién hecho
$sal = Join-Path $env:TEMP 'aoe2radar-escenarios-humo.aoe2scenario'
$res = "$sal.json"
Remove-Item $sal, $res -ErrorAction SilentlyContinue
$p = Start-Process -FilePath $exe -ArgumentList @("`"$raiz\tests\batalla_ejemplo.json`"", "`"$sal`"", '--resultado', "`"$res`"") -Wait -PassThru -NoNewWindow
if ($p.ExitCode -ne 0 -or -not (Test-Path $sal)) { throw "La prueba de humo falló (código $($p.ExitCode)): $(Get-Content $res -Raw -ErrorAction SilentlyContinue)" }
Write-Host "Prueba de humo: bien ($sal)"

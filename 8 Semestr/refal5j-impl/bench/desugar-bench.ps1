# bench/desugar-bench.ps1
#
# Бенчмарк «Рассахаренный рассахариватель» — производительность на реальной
# программе: наш интерпретатор (refal5q) против компиляторов (Refal-5 PZ, Refal-5J).
#
# Программа: рассахариватель (5 файлов, ~4200 строк суммарно).
# Вход: refal-5-framework-master/lib/R5FW-Parser.ref (1038 строк) — реальная
#       содержательная программа (сам парсер рассахаривателя).
#
# Один и тот же рассахариватель прогоняется тремя способами:
#   refal5q   — интерпретирует 5 рассахаренных .ref файлов;
#   Refal-5 PZ — компилирует .ref → .rsl (refc) и исполняет (refgo);
#   Refal-5J   — компилирует .ref → .java → .class (r5jc + javac) и исполняет.
#
# Ожидаемый результат: компиляторы быстрее интерпретатора. Это принципиальная
# разница (интерпретация vs компиляция + накладные расходы), а не алгоритмическая
# проблема нашей реализации.
#
# Использование:
#   powershell -File bench\desugar-bench.ps1
#   powershell -File bench\desugar-bench.ps1 -WithPZ -WithR5J
#   powershell -File bench\desugar-bench.ps1 -WithPZ -WithR5J -MeasuredRuns 5

param(
    [switch]$WithPZ,
    [switch]$WithR5J,
    [int]$WarmupRuns    = 1,
    [int]$MeasuredRuns  = 3,
    [int]$TimeoutSec    = 300
)

$ErrorActionPreference = "Continue"
# $PSScriptRoot = ...\Diploma\refal5j-impl\bench
# $ImplRoot     = ...\Diploma\refal5j-impl   (где target\, tests\)
# $ProjRoot     = ...\Diploma                (где refal-5-framework-master\)
$Bench    = $PSScriptRoot
$ImplRoot = Split-Path $PSScriptRoot -Parent
$ProjRoot = Split-Path $ImplRoot -Parent

$Jar = Join-Path $ImplRoot "target\refal5q.jar"

$Refal5 = "D:\Iterpretators\refal5"
$R5JBin = "D:\Programming\Projects\8 Semestr\Diploma\refal-5j\bin"
$R5JLib = "D:\Programming\Projects\8 Semestr\Diploma\refal-5j\lib"

$Desugar5 = Join-Path $ImplRoot "tests\desugar"             # 5 *_desugared.ref для refal5q
$FwLib    = Join-Path $ProjRoot "refal-5-framework-master\lib"  # *.ref исходники для PZ/R5J
$FwSrc    = Join-Path $ProjRoot "refal-5-framework-master\src"  # desugar.ref

# Реальная программа на вход рассахаривателю: парсер рассахаривателя (1038 строк).
$InputRef = Join-Path $FwLib "R5FW-Parser.ref"

# Work-папки. Путь к проекту содержит пробел ('8 Semestr'), а Refal-5 PZ
# (REF5RSL/refgo) на путях с пробелами падает (heap corruption). Поэтому
# рабочие каталоги PZ и R5J размещаем в %TEMP% — там пробелов в пути нет.
$TmpDir   = Join-Path $env:TEMP "refal5q-desugar"
$PzWork   = Join-Path $env:TEMP "refal5q-desugar-pz"
$R5JWork  = Join-Path $env:TEMP "refal5q-desugar-r5j"

# Имена 5 модулей рассахаривателя (порядок как в штатной обёртке r5fw-desugar).
$Modules  = @("desugar", "LibraryEx", "R5FW-Parser", "R5FW-Transformer", "R5FW-Plainer")

# --- утилиты -----------------------------------------------------------------

function New-CleanDir {
    param([string]$Path)
    if (Test-Path $Path) { Remove-Item $Path -Recurse -Force }
    New-Item -ItemType Directory -Path $Path | Out-Null
}

if (-not (Test-Path $TmpDir)) { New-Item -ItemType Directory -Path $TmpDir | Out-Null }

function Invoke-WithTimeout {
    param([string]$Exe, [string]$CmdArgs, [string]$WorkDir, [int]$ToutSec = 60)
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $Exe
    $psi.Arguments = $CmdArgs
    if ($WorkDir) { $psi.WorkingDirectory = $WorkDir }
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow  = $true
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError  = $true
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $p  = [System.Diagnostics.Process]::Start($psi)
    $finished = $p.WaitForExit($ToutSec * 1000)
    $sw.Stop()
    if (-not $finished) {
        try { $p.Kill() } catch {}
        return @{ Ok = $false; Time = $null; Reason = "TIMEOUT" }
    }
    $p.StandardOutput.ReadToEnd() | Out-Null
    $p.StandardError.ReadToEnd()  | Out-Null
    return @{ Ok = ($p.ExitCode -eq 0); Time = $sw.ElapsedMilliseconds; Exit = $p.ExitCode }
}

function Measure-Median {
    param([scriptblock]$Block, [int]$Warmup = 1, [int]$Runs = 3)
    for ($i = 0; $i -lt $Warmup; $i++) {
        $r = & $Block
        if (-not $r.Ok) { return $null }
    }
    $times = @()
    for ($i = 0; $i -lt $Runs; $i++) {
        $r = & $Block
        if (-not $r.Ok) { return $null }
        $times += $r.Time
    }
    $sorted = $times | Sort-Object
    return $sorted[[Math]::Floor($sorted.Count / 2)]
}

# --- сборка jar -------------------------------------------------------------

if (-not (Test-Path $Jar)) {
    Write-Host "Сборка refal5q.jar..." -ForegroundColor DarkGray
    $buildDir = if (Test-Path (Join-Path $Root "refal5j-impl\pom.xml")) {
        Join-Path $Root "refal5j-impl"
    } else { $Root }
    Push-Location $buildDir
    mvn -q -DskipTests package | Out-Null
    Pop-Location
}

$hasPZ  = $WithPZ  -and (Test-Path "$Refal5\refgo.exe") -and (Test-Path "$Refal5\refc.exe")
$hasR5J = $WithR5J -and (Test-Path "$R5JBin\r5jc.jar") -and (Test-Path "$R5JLib\r5jrt.jar")

# --- заголовок ---------------------------------------------------------------

$inputLines = (Get-Content $InputRef | Measure-Object -Line).Lines
Write-Host "=== Бенчмарк: Рассахаренный рассахариватель ===" -ForegroundColor Cyan
Write-Host "  Программа: рассахариватель (5 файлов, ~4200 строк суммарно)"
Write-Host "  Вход: R5FW-Parser.ref ($inputLines строк) — реальная программа"
Write-Host ""
Write-Host "  refal5q       : наш интерпретатор (ВКР, bootstrapped deque, Java)"
if ($WithPZ)  { Write-Host ("  Refal-5 PZ    : PZ (C, компилятор){0}"   -f $(if ($hasPZ)  { "" } else { " — НЕ НАЙДЕН ($Refal5)" })) }
if ($WithR5J) { Write-Host ("  Refal-5J      : R5J (Java, компилятор){0}" -f $(if ($hasR5J) { "" } else { " — НЕ НАЙДЕН ($R5JBin)" })) }
Write-Host ("  Warmup × $WarmupRuns + Measure × $MeasuredRuns, отчёт по медиане.") -ForegroundColor DarkGray
Write-Host ""

# --- refal5q ----------------------------------------------------------------
# Вход копируем в work-папку, чтобы рассахариватель писал выход (input-out.ref)
# рядом — в work-папку, а не в исходный framework/lib.

$ourInput = Join-Path $TmpDir "input.ref"
Copy-Item $InputRef $ourInput -Force
$ourOut   = Join-Path $TmpDir "input-out.ref"

$ourFiles = ($Modules | ForEach-Object {
    $name = if ($_ -eq "desugar") { "desugar_desugared.ref" } else { "$($_)_desugared.ref" }
    Join-Path $Desugar5 $name
}) -join "+"

Write-Host "  Прогон refal5q..." -ForegroundColor DarkGray
$tOur = Measure-Median {
    if (Test-Path $ourOut) { Remove-Item $ourOut -Force }
    Invoke-WithTimeout "java" "-jar `"$Jar`" `"$ourFiles`" --step-limit 200000000 --entry Go `"$ourInput`"" $null $TimeoutSec
} $WarmupRuns $MeasuredRuns

# --- Refal-5 PZ -------------------------------------------------------------
# Разовая подготовка: копируем 5 .ref в work-папку без пробелов, компилируем refc.

$tPZ = $null
if ($hasPZ) {
    Write-Host "  Подготовка PZ (refc → .rsl)..." -ForegroundColor DarkGray
    New-CleanDir $PzWork
    Copy-Item (Join-Path $FwSrc "desugar.ref") $PzWork -Force
    foreach ($m in @("LibraryEx", "R5FW-Parser", "R5FW-Plainer", "R5FW-Transformer")) {
        Copy-Item (Join-Path $FwLib "$m.ref") $PzWork -Force
    }
    $pzOk = $true
    foreach ($m in $Modules) {
        $r = Invoke-WithTimeout "$Refal5\refc.exe" "$m.ref" $PzWork 120
        if (-not $r.Ok) { $pzOk = $false; Write-Host "    [WARN] refc $m не удался" -ForegroundColor Yellow; break }
    }
    if ($pzOk) {
        Copy-Item $InputRef (Join-Path $PzWork "input.ref") -Force
        $pzOut = Join-Path $PzWork "input-out.ref"
        $env:REF5RSL = $PzWork
        $pzModules = $Modules -join "+"
        Write-Host "  Прогон Refal-5 PZ..." -ForegroundColor DarkGray
        $tPZ = Measure-Median {
            if (Test-Path $pzOut) { Remove-Item $pzOut -Force }
            Invoke-WithTimeout "$Refal5\refgo.exe" "$pzModules input.ref" $PzWork $TimeoutSec
        } $WarmupRuns $MeasuredRuns
    }
}

# --- Refal-5J ---------------------------------------------------------------
# Разовая компиляция: r5jc генерит .java, javac компилирует.

$tR5J = $null
if ($hasR5J) {
    Write-Host "  Подготовка R5J (r5jc + javac)..." -ForegroundColor DarkGray
    New-CleanDir $R5JWork
    New-Item -ItemType Directory -Path "$R5JWork\gen.@@@\r5j" -Force | Out-Null
    Copy-Item (Join-Path $FwSrc "desugar.ref") $R5JWork -Force
    foreach ($m in @("LibraryEx", "R5FW-Parser", "R5FW-Plainer", "R5FW-Transformer")) {
        Copy-Item (Join-Path $FwLib "$m.ref") $R5JWork -Force
    }
    $env:R5JPATH = $R5JLib
    $r5jSrcArg = ($Modules | ForEach-Object { "$_.ref" }) -join " "

    $r5jOk = $false
    $rc = Invoke-WithTimeout "java" "-ea -cp `"$R5JLib\r5jrt.jar;$R5JBin\r5jc.jar`" r5j.GO_ $r5jSrcArg" $R5JWork 300
    if ($rc.Ok) {
        $jc = Invoke-WithTimeout "javac" "-cp `"$R5JLib\r5jrt.jar;gen.@@@`" gen.@@@\r5j\*.java" $R5JWork 300
        $r5jOk = $jc.Ok
        if (-not $jc.Ok) { Write-Host "    [WARN] javac не удался (exit $($jc.Exit))" -ForegroundColor Yellow }
    } else {
        Write-Host "    [WARN] r5jc не удался (exit $($rc.Exit))" -ForegroundColor Yellow
    }

    if ($r5jOk) {
        Copy-Item $InputRef (Join-Path $R5JWork "input.ref") -Force
        $r5jOut = Join-Path $R5JWork "input-out.ref"
        Write-Host "  Прогон Refal-5J..." -ForegroundColor DarkGray
        $tR5J = Measure-Median {
            if (Test-Path $r5jOut) { Remove-Item $r5jOut -Force }
            Invoke-WithTimeout "java" "-ea -cp `"$R5JLib\r5jrt.jar;gen.@@@`" r5j.Go_ input.ref" $R5JWork $TimeoutSec
        } $WarmupRuns $MeasuredRuns
    }
}

# --- итоговый вывод ----------------------------------------------------------

Write-Host ""
Write-Host "=== Результаты ===" -ForegroundColor Cyan

function Format-Time { param($ms) if ($null -ne $ms) { "$ms ms" } else { "FAIL/TIMEOUT" } }
function Format-Ratio {
    param($base, $other)
    if ($null -ne $base -and $null -ne $other -and $other -gt 0) {
        "(×{0} быстрее)" -f [Math]::Round($base / $other, 1)
    } else { "" }
}

$oStr = Format-Time $tOur
$pStr = if ($null -ne $tPZ)  { "{0,-9} {1}" -f (Format-Time $tPZ),  (Format-Ratio $tOur $tPZ) }  elseif ($hasPZ)  { "FAIL" } else { "—" }
$rStr = if ($null -ne $tR5J) { "{0,-9} {1}" -f (Format-Time $tR5J), (Format-Ratio $tOur $tR5J) } elseif ($hasR5J) { "FAIL" } else { "—" }

Write-Host ("  refal5q    : {0}" -f $oStr)
Write-Host ("  Refal-5 PZ : {0}" -f $pStr)
Write-Host ("  Refal-5J   : {0}" -f $rStr)
Write-Host ""
Write-Host "  (Компилятор vs интерпретатор + накладные расходы — разница ожидаема)" -ForegroundColor DarkGray

# --- CSV ---------------------------------------------------------------------

$row = [pscustomobject]@{
    program  = "desugar (5 модулей)"
    input    = "R5FW-Parser.ref"
    ours_ms  = $tOur
    pz_ms    = $tPZ
    r5j_ms   = $tR5J
}
$csv = Join-Path $Bench "desugar-results.csv"
$row | Export-Csv $csv -NoTypeInformation -Encoding UTF8
Write-Host "Сохранено: $csv" -ForegroundColor DarkGray

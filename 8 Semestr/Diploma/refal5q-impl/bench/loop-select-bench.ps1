# bench/loop-select-bench.ps1
#
# Бенчмарк Loop/Select — демонстрирует O(N) для раскрученной двусторонней
# очереди (наша реализация) против O(N²) для связносписочных реализаций (PZ).
#
# Алгоритм: N итераций, каждая строит (e.Acc A) или (e.Acc B) из растущего
# аккумулятора e.Acc. Для связного списка — O(N) копирование на каждой итерации
# → O(N²) суммарно. Для bootstrapped deque — Expr.concat O(1) амортизировано
# → O(N) суммарно.
#
# Использование:
#   powershell -File bench\loop-select-bench.ps1
#   powershell -File bench\loop-select-bench.ps1 -WithPZ -WithR5J
#   python bench\plot-benchmark.py
#   powershell -File bench\loop-select-bench.ps1 -Sizes @(100,500,1000,5000,10000)

param(
    [switch]$WithPZ,
    [switch]$WithR5J,
    [int[]]$Sizes = @(100, 300, 600, 1000, 2000, 3000, 5000, 7000, 10000, 15000, 20000),
    [int]$TimeoutSec = 120,
    [int]$WarmupRuns = 1,
    [int]$MeasuredRuns = 3
)

$ErrorActionPreference = "Continue"
$Root   = Split-Path $PSScriptRoot -Parent
$Bench  = Join-Path $Root "bench"
$Jar    = Join-Path $Root "target\refal5q.jar"
$Refal5 = "D:\Iterpretators\refal5"
$R5JBin = "D:\Programming\Projects\8 Semestr\Diploma\refal-5j\bin"
$R5JLib = "D:\Programming\Projects\8 Semestr\Diploma\refal-5j\lib"
$TmpDir = Join-Path $Bench "tmp-loop-select"

# --- шаблоны -----------------------------------------------------------------

# Наш интерпретатор: Go без $ENTRY (используем Go как точку входа через --entry)
$TplOurs = @'
$ENTRY Go {
  = <Loop Left () {N}>;
}
Loop {
  s.Side (e.Acc) 0 = ;
  s.Side (e.Acc) s.Rest
    = <Loop <Select s.Side (e.Acc A) (e.Acc B)> <Sub s.Rest 1>>;
}
Select {
  Left  t.Left t.Right = Right t.Left;
  Right t.Left t.Right = Left  t.Right;
}
'@

# PZ/R5J вариант: то же самое (Sub и числа совместимы)
$TplPZ = $TplOurs

# --- утилиты -----------------------------------------------------------------

if (-not (Test-Path $TmpDir)) { New-Item -ItemType Directory -Path $TmpDir | Out-Null }

$Utf8NoBom = New-Object System.Text.UTF8Encoding $false

function Expand-Template {
    param([string]$Tpl, [int]$N)
    $Tpl -replace '\{N\}', $N
}

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
    $buildDir = $Root
    Push-Location $buildDir
    mvn -q -DskipTests package | Out-Null
    Pop-Location
}

$hasPZ  = $WithPZ  -and (Test-Path "$Refal5\refgo.exe")
$hasR5J = $WithR5J -and (Test-Path "$R5JBin\r5jc.cmd")

Write-Host "=== Бенчмарк Loop/Select ===" -ForegroundColor Cyan
Write-Host "  Алгоритм: N итераций, каждая строит (e.Acc A/B)."
Write-Host "  Ожидается: bootstrapped deque → O(N), связный список → O(N²)."
Write-Host ""
Write-Host "  refal5q-impl  : ВКР (bootstrapped deque, Java)"
if ($WithPZ)  { Write-Host ("  Refal-5 PZ    : PZ (C, байт-код){0}" -f $(if ($hasPZ) { "" } else { " — НЕ НАЙДЕН ($Refal5\refgo.exe)" })) }
if ($WithR5J) { Write-Host ("  Refal-5J      : R5J (Java){0}"        -f $(if ($hasR5J) { "" } else { " — НЕ НАЙДЕН ($R5JBin)" })) }
Write-Host ("  Warmup × $WarmupRuns + Measure × $MeasuredRuns, отчёт по медиане.") -ForegroundColor DarkGray
Write-Host ""

$rows = @()

foreach ($n in $Sizes) {
    # Наш интерпретатор
    $srcOur = Join-Path $TmpDir "loop-select-our-$n.ref"
    [System.IO.File]::WriteAllText($srcOur, (Expand-Template $TplOurs $n), $Utf8NoBom)
    $tOur = Measure-Median { Invoke-WithTimeout "java" "-jar `"$Jar`" --step-limit 200000000 `"$srcOur`"" $null $TimeoutSec } $WarmupRuns $MeasuredRuns

    # PZ
    $tPZ = $null
    if ($hasPZ) {
        $srcPZ = Join-Path $TmpDir "loop-select-pz-$n.ref"
        [System.IO.File]::WriteAllText($srcPZ, (Expand-Template $TplPZ $n), [System.Text.Encoding]::ASCII)
        Push-Location $TmpDir
        & "$Refal5\refc.exe" "loop-select-pz-$n.ref" 2>&1 | Out-Null
        Pop-Location
        $tPZ = Measure-Median { Invoke-WithTimeout "$Refal5\refgo.exe" "loop-select-pz-$n" $TmpDir $TimeoutSec } $WarmupRuns $MeasuredRuns
    }

    # Refal-5J
    $tR5J = $null
    if ($hasR5J) {
        $srcPZ = Join-Path $TmpDir "loop-select-pz-$n.ref"
        if (-not (Test-Path $srcPZ)) {
            [System.IO.File]::WriteAllText($srcPZ, (Expand-Template $TplPZ $n), [System.Text.Encoding]::ASCII)
        }
        $workDir = Join-Path $TmpDir "r5j-loop-select-$n"
        if (Test-Path $workDir) { Remove-Item $workDir -Recurse -Force }
        New-Item -ItemType Directory -Path "$workDir\gen.@@@\r5j" -Force | Out-Null
        Copy-Item $srcPZ (Join-Path $workDir "loop-select-pz-$n.ref") -Force
        $env:R5JPATH = $R5JLib
        cmd /c "cd /d `"$workDir`" && java -ea -cp `"$R5JLib\r5jrt.jar;$R5JBin\r5jc.jar`" r5j.GO_ loop-select-pz-$n.ref > nul 2>&1"
        if ($LASTEXITCODE -eq 0) {
            cmd /c "cd /d `"$workDir`" && javac -cp `"$R5JLib\r5jrt.jar;gen.@@@`" gen.@@@\r5j\*.java > nul 2>&1"
            if ($LASTEXITCODE -eq 0) {
                $tR5J = Measure-Median { Invoke-WithTimeout "java" "-ea -cp `"$R5JLib\r5jrt.jar;gen.@@@`" r5j.Go_" $workDir $TimeoutSec } $WarmupRuns $MeasuredRuns
            }
        }
    }

    $oStr = if ($null -ne $tOur) { "$tOur ms" } else { "FAIL/TIMEOUT" }
    $pStr = if ($null -ne $tPZ)  { "$tPZ ms" }  elseif ($hasPZ)  { "FAIL" } else { "—" }
    $rStr = if ($null -ne $tR5J) { "$tR5J ms" } elseif ($hasR5J) { "FAIL" } else { "—" }
    Write-Host ("  N={0,5}: ours={1,15}  PZ={2,15}  R5J={3,15}" -f $n, $oStr, $pStr, $rStr) -ForegroundColor Gray

    $rows += [pscustomobject]@{
        N        = $n
        ours_ms  = $tOur
        pz_ms    = $tPZ
        r5j_ms   = $tR5J
    }
}

Write-Host ""
Write-Host "=== Итого ===" -ForegroundColor Cyan
$rows | Format-Table -AutoSize

$csv = Join-Path $Bench "loop-select-results.csv"
$rows | Export-Csv $csv -NoTypeInformation -Encoding UTF8
Write-Host "Сохранено: $csv" -ForegroundColor DarkGray
Write-Host "Для графика запустите: python bench\plot-benchmark.py" -ForegroundColor DarkGray

# Чистка tmp
Get-ChildItem $TmpDir -File -ErrorAction SilentlyContinue | Remove-Item -Force

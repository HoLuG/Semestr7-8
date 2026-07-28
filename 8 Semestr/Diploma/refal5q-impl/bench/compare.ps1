# Сравнение реализаций Рефала на параметризованных бенчмарках.
# Сравниваются:
#   refal5q-impl
#   Refal-5 PZ
#   Refal-5J
#
# Запуск: powershell -File bench\compare.ps1            # без R5J (по умолчанию)
#         powershell -File bench\compare.ps1 -WithR5J   # включить Refal-5J

param(
    [switch]$WithR5J,
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
$TmpDir = Join-Path $Bench "tmp"

# --- шаблоны бенчмарков -----------------------------------------------------
# {N}, {NP1}, {N2} - подстановочные плейсхолдеры.
# Compare возвращает '+' когда первый > второго во всех реализациях Рефала-5.
# Один шаблон используется для всех трёх реализаций (PZ компилирует его через refc).

$TplReverse = @"
`$ENTRY Go {
  = <Reverse <RangeUp 1 {N}>>;
}
Reverse {
  = ;
  s.X e.Rest = <Reverse e.Rest> s.X;
}
RangeUp {
  s.From s.To = <ConsBy <Compare s.From s.To> s.From s.To>;
}
ConsBy {
  '+' s.From s.To = ;
  s.Op  s.From s.To = s.From <RangeUp <Add s.From 1> s.To>;
}
"@

$TplConcat = @"
`$ENTRY Go {
  = <Append (<RangeUp 1 {N}>) (<RangeUp {NP1} {N2}>)>;
}
Append {
  (e.X) (e.Y) = e.X e.Y;
}
RangeUp {
  s.From s.To = <ConsBy <Compare s.From s.To> s.From s.To>;
}
ConsBy {
  '+' s.From s.To = ;
  s.Op  s.From s.To = s.From <RangeUp <Add s.From 1> s.To>;
}
"@

$TplSum = @"
`$ENTRY Go {
  = <Sum <RangeUp 1 {N}>>;
}
Sum {
  = 0;
  s.X e.Rest = <Add s.X <Sum e.Rest>>;
}
RangeUp {
  s.From s.To = <ConsBy <Compare s.From s.To> s.From s.To>;
}
ConsBy {
  '+' s.From s.To = ;
  s.Op  s.From s.To = s.From <RangeUp <Add s.From 1> s.To>;
}
"@

$benchmarks = @(
    [pscustomobject]@{
        Name = "reverse"
        Desc = "Reverse [1..N]"
        Template = $TplReverse
        Sizes = @(100, 300, 600, 1000, 2000, 4000)
        R5JSizes = @(100, 300, 600, 1000)
    }
    [pscustomobject]@{
        Name = "concat"
        Desc = "Append ([1..N]) ([N+1..2N])"
        Template = $TplConcat
        Sizes = @(500, 1000, 2000, 5000, 10000)
        R5JSizes = @(500, 1000, 2000)
    }
    [pscustomobject]@{
        Name = "sumlist"
        Desc = "Sum of [1..N]"
        Template = $TplSum
        Sizes = @(500, 1000, 2000, 5000, 10000)
        R5JSizes = @(500, 1000, 2000)
    }
)

# --- утилиты ----------------------------------------------------------------

if (-not (Test-Path $TmpDir)) { New-Item -ItemType Directory -Path $TmpDir | Out-Null }
Get-ChildItem $TmpDir -Filter "*.ref" -ErrorAction SilentlyContinue | Remove-Item -Force
Get-ChildItem $TmpDir -Filter "*.rsl" -ErrorAction SilentlyContinue | Remove-Item -Force
Get-ChildItem $TmpDir -Filter "*.txt" -ErrorAction SilentlyContinue | Remove-Item -Force

$Utf8NoBom = New-Object System.Text.UTF8Encoding $false

function Expand-Template {
    param([string]$Template, [int]$N)
    ($Template `
        -replace '\{NP1\}', ($N + 1) `
        -replace '\{N2\}',  ($N * 2) `
        -replace '\{N\}',   $N)
}

# Запуск процесса с таймаутом. Возвращает [hashtable] @{ Ok = $bool; Time = $ms }.
# Параметр называется CmdArgs, потому что $Args — зарезервированная
# автоматическая переменная PowerShell (массив всех нераспределённых аргументов функции).
# ВАЖНО: stdout/stderr читаются асинхронно ДО WaitForExit, иначе при большом выводе
# буфер трубы заполняется → процесс блокируется → deadlock.
function Invoke-WithTimeout {
    param([string]$File, [string]$CmdArgs, [string]$WorkDir, [int]$TimeoutSec = 60)
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $File
    $psi.Arguments = $CmdArgs
    if ($WorkDir) { $psi.WorkingDirectory = $WorkDir }
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow  = $true
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError  = $true
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $p = [System.Diagnostics.Process]::Start($psi)
    # Асинхронное чтение предотвращает deadlock при большом выводе
    $outTask = $p.StandardOutput.ReadToEndAsync()
    $errTask = $p.StandardError.ReadToEndAsync()
    $finished = $p.WaitForExit($TimeoutSec * 1000)
    $sw.Stop()
    if (-not $finished) {
        try { $p.Kill() } catch {}
        [void]$outTask.Wait(1000)
        [void]$errTask.Wait(1000)
        return @{ Ok = $false; Time = $null; Exit = -1; Reason = "TIMEOUT" }
    }
    [void]$outTask.Wait()
    [void]$errTask.Wait()
    return @{ Ok = ($p.ExitCode -eq 0); Time = $sw.ElapsedMilliseconds; Exit = $p.ExitCode }
}

# Измерение: warmup + N измеренных запусков, возвращает медиану.
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

# --- запускалки реализаций --------------------------------------------------

function Run-Refal5j {
    param([string]$Source)
    Invoke-WithTimeout "java" "-jar `"$Jar`" `"$Source`"" $null 30
}

function Run-PZ {
    param([string]$BaseName)
    Invoke-WithTimeout "$Refal5\refgo.exe" $BaseName $TmpDir 30
}

function Run-R5J {
    param([string]$WorkDir)
    Invoke-WithTimeout "java" "-ea -cp `"$R5JLib\r5jrt.jar;gen.@@@`" r5j.Go_" $WorkDir 30
}

# Компиляция R5J (Refal -> Java -> bytecode) — один раз на (бенчмарк, N).
function Compile-R5J {
    param([string]$Source, [string]$WorkDir)
    if (Test-Path $WorkDir) { Remove-Item $WorkDir -Recurse -Force }
    New-Item -ItemType Directory -Path "$WorkDir\gen.@@@\r5j" -Force | Out-Null
    Copy-Item $Source (Join-Path $WorkDir (Split-Path $Source -Leaf)) -Force
    $env:R5JPATH = $R5JLib
    $name = Split-Path $Source -Leaf
    cmd /c "cd /d `"$WorkDir`" && java -ea -cp `"$R5JLib\r5jrt.jar;$R5JBin\r5jc.jar`" r5j.GO_ $name > nul 2>&1"
    if ($LASTEXITCODE -ne 0) { return $false }
    cmd /c "cd /d `"$WorkDir`" && javac -cp `"$R5JLib\r5jrt.jar;gen.@@@`" gen.@@@\r5j\*.java > nul 2>&1"
    return ($LASTEXITCODE -eq 0)
}

# --- сборка jar -------------------------------------------------------------

if (-not (Test-Path $Jar)) {
    Write-Host "Сборка refal5q.jar..." -ForegroundColor DarkGray
    Push-Location $Root
    mvn -q -DskipTests package | Out-Null
    Pop-Location
}

# --- проверка наличия -------------------------------------------------------

$hasPZ  = Test-Path "$Refal5\refgo.exe"
$hasR5J = $WithR5J -and (Test-Path "$R5JBin\r5jc.cmd")

Write-Host "=== Сравнение реализаций Refal ===" -ForegroundColor Cyan
Write-Host "  refal5q-impl  : ВКР (deque-представление, Java)"
$pzMark = if ($hasPZ) { "" } else { " — НЕТ" }
Write-Host "  Refal-5 PZ    : Переславль-Залесский (C, байт-код)$pzMark"
if ($WithR5J) {
    $r5jMark = if ($hasR5J) { "" } else { " — НЕТ ($R5JBin)" }
    Write-Host "  Refal-5J      : реализация  (Java)$r5jMark"
} else {
    Write-Host "  Refal-5J      : отключён (включить: -WithR5J)" -ForegroundColor DarkGray
}
Write-Host ("Warmup × $WarmupRuns + Measure × $MeasuredRuns на точку, отчёт по медиане.") -ForegroundColor DarkGray
Write-Host ""

$env:REF5RSL = $Refal5
$rows = @()

foreach ($b in $benchmarks) {
    Write-Host ("--- {0,-10}  {1}" -f $b.Name, $b.Desc) -ForegroundColor Yellow
    foreach ($n in $b.Sizes) {
        # Единый источник: '+' используется во всех реализациях (Compare стандартный)
        # ASCII-кодировка безопасна — шаблон содержит только ASCII символы.
        $src = Join-Path $TmpDir "$($b.Name)-$n.ref"
        [System.IO.File]::WriteAllText($src, (Expand-Template $b.Template $n), [System.Text.Encoding]::ASCII)

        $tOur = Measure-Median { Run-Refal5j $src } $WarmupRuns $MeasuredRuns

        $tPz = $null
        if ($hasPZ) {
            Push-Location $TmpDir
            & "$Refal5\refc.exe" "$($b.Name)-$n.ref" 2>&1 | Out-Null
            Pop-Location
            $tPz = Measure-Median { Run-PZ "$($b.Name)-$n" } $WarmupRuns $MeasuredRuns
        }

        $tR5J = $null
        if ($hasR5J -and ($b.R5JSizes -contains $n)) {
            $workDir = Join-Path $TmpDir "r5j-$($b.Name)-$n"
            if (Compile-R5J $src $workDir) {
                $tR5J = Measure-Median { Run-R5J $workDir } $WarmupRuns $MeasuredRuns
            }
        }

        $ratioPz  = if ($tOur -and $tPz)  { [math]::Round($tOur / $tPz, 2) } else { "-" }
        $ratioR5J = if ($tOur -and $tR5J) { [math]::Round($tR5J / $tOur, 2) } else { "-" }

        $oStr = if ($tOur) { "$tOur" } else { "FAIL" }
        $pStr = if ($tPz)  { "$tPz" }  else { if ($hasPZ)  { "FAIL" } else { "—"} }
        $rStr = if ($tR5J) { "$tR5J" } else { if ($hasR5J -and ($b.R5JSizes -contains $n)) { "FAIL" } else { "—" } }
        Write-Host ("    n={0,4}:  refal5q-impl={1,5}ms  PZ={2,5}ms  R5J={3,5}ms  (our/PZ={4}× , R5J/our={5}×)" `
            -f $n, $oStr, $pStr, $rStr, $ratioPz, $ratioR5J) -ForegroundColor Gray
        $rows += [pscustomobject]@{
            Benchmark = $b.Name
            N         = $n
            refal5j   = $tOur
            pz        = $tPz
            r5j       = $tR5J
            our_div_pz  = $ratioPz
            r5j_div_our = $ratioR5J
        }
    }
    Write-Host ""
}

Write-Host "=== Итоговая таблица (медиана $MeasuredRuns запусков, мс) ===" -ForegroundColor Cyan
$rows | Format-Table -AutoSize

$csv = Join-Path $Bench "compare-results.csv"
$rows | Export-Csv $csv -NoTypeInformation -Encoding UTF8
Write-Host "Сохранено: $csv" -ForegroundColor DarkGray

# Чистим временные файлы (gen.@@@ для R5J ниже не трогаем — пригодятся для повторных запусков)
Get-ChildItem $TmpDir -File -ErrorAction SilentlyContinue | Remove-Item -Force

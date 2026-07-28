# Autotest Results

Generated automatically by AutotestsRunnerTest.


## desugared tests (50 tests) — 2026-06-17 22:42

| Test | Status | Time |
|------|--------|------|
| 1-Prout.OK_d.ref | ✅ PASS | 33ms |
| Add-Numb-Symb.OK_d.ref | ✅ PASS | 13ms |
| Arg.OK_d.ref | ❌ FAIL(exit=2) | 3ms |
| Br-Cp-Dg-Dgall-Rp-bug.OK_d.ref | ❌ FAIL(exit=1) | 3ms |
| Br-Cp-Dg-Dgall-Rp.OK_d.ref | ❌ FAIL(exit=1) | 1ms |
| Card.OK_d.ref | ⚠️ SKIP | 0ms |
| Chr-Lower-Ord-Upper.OK_d.ref | ✅ PASS | 8ms |
| classic-extended.OK_d.ref | ✅ PASS | 1ms |
| Close.OK_d.ref | ✅ PASS | 4ms |
| Compare.OK_d.ref | ✅ PASS | 2ms |
| conditions.OK_d.ref | ✅ PASS | 4ms |
| Div-Numb-Symb.OK_d.ref | ✅ PASS | 1ms |
| Divmod-Numb-Symb.OK_d.ref | ✅ PASS | 3ms |
| escapes.OK_d.ref | ✅ PASS | 2ms |
| ExistFile.OK_d.ref | ❌ FAIL(exit=1) | 1ms |
| Explode.OK_d.ref | ✅ PASS | 1ms |
| fact.OK_d.ref | ✅ PASS | 6ms |
| First-Last-Lenw.OK_d.ref | ✅ PASS | 2ms |
| Get-0-stdin.OK_d.ref | ⚠️ SKIP | 0ms |
| Get-autoopen.OK_d.ref | ⚠️ SKIP | 0ms |
| Get-Open.OK_d.ref | ❌ FAIL(exit=2) | 2ms |
| GetCurrentDirectory.OK_d.ref | ❌ FAIL(exit=1) | 0ms |
| GetEnv.OK_d.ref | ❌ FAIL(exit=1) | 1ms |
| GetPID-GetPPID.OK_d.ref | ❌ FAIL(exit=1) | 1ms |
| Go-GO.OK_d.ref | ✅ PASS | 0ms |
| GO.OK_d.ref | ✅ PASS | 0ms |
| Implode-Implode_Ext.OK_d.ref | ✅ PASS | 1ms |
| ListOfBuiltin.OK_d.ref | ✅ PASS | 9ms |
| math-sign.OK_d.ref | ✅ PASS | 3ms |
| Mod-Numb-Symb.OK_d.ref | ✅ PASS | 2ms |
| Mu-Residue.OK_d.ref | ❌ FAIL(exit=2) | 3ms |
| Mul-Numb-Symb.OK_d.ref | ✅ PASS | 2ms |
| Numb-Symb.OK_d.ref | ✅ PASS | 1ms |
| Print.OK_d.ref | ✅ PASS | 1ms |
| Put-Putout-files.OK_d.ref | ✅ PASS | 1ms |
| Put-Putout-stderr.OK_d.ref | ✅ PASS | 1ms |
| Random.OK_d.ref | ❌ FAIL(exit=1) | 1ms |
| RandomDigit.OK_d.ref | ❌ FAIL(exit=1) | 1ms |
| RemoveFile.OK_d.ref | ⚠️ SKIP | 0ms |
| SizeOf.OK_d.ref | ❌ FAIL(exit=1) | 1ms |
| Step.OK_d.ref | ✅ PASS | 0ms |
| Sub.OK_d.ref | ✅ PASS | 2ms |
| Sysfun.OK_d.ref | ❌ FAIL(exit=1) | 1ms |
| System-1-echo.OK_d.ref | ⚠️ SKIP | 0ms |
| System-2-Exit-retcode.OK_d.ref | ⚠️ SKIP | 0ms |
| tab.OK_d.ref | ✅ PASS | 1ms |
| Time.OK_d.ref | ❌ FAIL(exit=1) | 1ms |
| TimeElapsed.OK_d.ref | ❌ FAIL(exit=2) | 2ms |
| Type.OK_d.ref | ✅ PASS | 1ms |
| Write.OK_d.ref | ✅ PASS | 24ms |

**Summary**: 29 passed, 15 failed, 6 skipped / 50 total

### Failed tests
- **Arg.OK_d.ref**: [ERROR] runtime: No matching rule for Eq on args=[Br[items=Shallow[Str[value=H], Str[value=e], Str[value=l], Str[value=l], Str[value=o]]]]
- **Br-Cp-Dg-Dgall-Rp-bug.OK_d.ref**: [ERROR] D:\Programming\Projects\8 Semestr\Diploma\refal5j-impl\tests\desugared\Br-Cp-Dg-Dgall-Rp-bug.OK_d.ref: function 'Go', rule #1: call to undefined function 'Br'
- **Br-Cp-Dg-Dgall-Rp.OK_d.ref**: [ERROR] D:\Programming\Projects\8 Semestr\Diploma\refal5j-impl\tests\desugared\Br-Cp-Dg-Dgall-Rp.OK_d.ref: function 'Test1', rule #1: call to undefined function 'Dg'
- **ExistFile.OK_d.ref**: [ERROR] D:\Programming\Projects\8 Semestr\Diploma\refal5j-impl\tests\desugared\ExistFile.OK_d.ref: function 'Go', rule #1: call to undefined function 'ExistFile'
- **Get-Open.OK_d.ref**: [ERROR] runtime: Open: I/O error: 2lines.txt
- **GetCurrentDirectory.OK_d.ref**: [ERROR] D:\Programming\Projects\8 Semestr\Diploma\refal5j-impl\tests\desugared\GetCurrentDirectory.OK_d.ref: function 'Go', rule #1: call to undefined function 'GetCurrentDirectory'
- **GetEnv.OK_d.ref**: [ERROR] D:\Programming\Projects\8 Semestr\Diploma\refal5j-impl\tests\desugared\GetEnv.OK_d.ref: function 'Go', rule #1: call to undefined function 'GetEnv'
- **GetPID-GetPPID.OK_d.ref**: [ERROR] D:\Programming\Projects\8 Semestr\Diploma\refal5j-impl\tests\desugared\GetPID-GetPPID.OK_d.ref: function 'Go', rule #1: call to undefined function 'GetPID'
- **Mu-Residue.OK_d.ref**: [ERROR] runtime: Unknown function: External-1
- **Random.OK_d.ref**: [ERROR] D:\Programming\Projects\8 Semestr\Diploma\refal5j-impl\tests\desugared\Random.OK_d.ref: function 'Loop5', rule #2: call to undefined function 'Random'
- **RandomDigit.OK_d.ref**: [ERROR] D:\Programming\Projects\8 Semestr\Diploma\refal5j-impl\tests\desugared\RandomDigit.OK_d.ref: function 'Loop5', rule #2: call to undefined function 'RandomDigit'
- **SizeOf.OK_d.ref**: [ERROR] D:\Programming\Projects\8 Semestr\Diploma\refal5j-impl\tests\desugared\SizeOf.OK_d.ref: function 'CheckSizeOf', rule #1: call to undefined function 'SizeOf'
- **Sysfun.OK_d.ref**: [ERROR] D:\Programming\Projects\8 Semestr\Diploma\refal5j-impl\tests\desugared\Sysfun.OK_d.ref: function 'Go', rule #1: call to undefined function 'DeSysfun'
- **Time.OK_d.ref**: [ERROR] D:\Programming\Projects\8 Semestr\Diploma\refal5j-impl\tests\desugared\Time.OK_d.ref: function 'Go', rule #1: call to undefined function 'Time'
- **TimeElapsed.OK_d.ref**: [ERROR] runtime: No matching rule for Check on args=[Str[value=0.00]]

## refal-5j autotests (29 tests) — 2026-06-17 22:42

| Test | Status | Time |
|------|--------|------|
| 01-go-out.ref | ✅ PASS | 2ms |
| 01-go.ref | ✅ PASS | 0ms |
| 02-matches-out.ref | ✅ PASS | 3ms |
| 02-matches.ref | ✅ PASS | 3ms |
| 03-concat.ref | ✅ PASS | 10350ms |
| 04-br-dg-cp-rp.ref | ❌ FAIL(exit=1) | 2ms |
| 05-refal5-conditions.ref | ❌ FAIL(exit=1) | 2ms |
| 06-arithm.ref | ❌ FAIL(exit=1) | 2ms |
| 07-arg.ref | ❌ FAIL(exit=2) | 2ms |
| 08-implode-explode.ref | ❌ FAIL(exit=2) | 2ms |
| 09-1-mu-uses-all.ref | ✅ PASS | 2ms |
| 09-2-mu.ref | ✅ PASS | 2ms |
| 10-getenv.ref | ❌ FAIL(exit=1) | 1ms |
| 11-exist-file.ref | ❌ FAIL(exit=1) | 1ms |
| 12-file-functions.ref | ❌ FAIL(exit=1) | 1ms |
| 13-type.ref | ❌ FAIL(exit=2) | 1ms |
| 14-list-of-builtin.ref | ❌ FAIL(exit=1) | 1ms |
| 15-system-exit-retcode.ref | ❌ FAIL(exit=1) | 0ms |
| 16-chr-lower-ord-upper.ref | ❌ FAIL(exit=1) | 0ms |
| 17-first-last-lenw.ref | ❌ FAIL(exit=1) | 1ms |
| 18-beautiful-test.ref | ❌ FAIL(exit=2) | 2ms |
| 19-utf-8-bom.ref | ❌ FAIL(exit=1) | 1ms |
| 20-time-timeelapsed.ref | ⚠️ SKIP | 0ms |
| 21-step.ref | ❌ FAIL(exit=1) | 1ms |
| 22-blocks.ref | ❌ FAIL(exit=1) | 1ms |
| 23-random-randomdigit.ref | ❌ FAIL(exit=1) | 1ms |
| 24-sizeof.ref | ❌ FAIL(exit=1) | 1ms |
| 25-sysfuns.ref | ❌ FAIL(exit=1) | 1ms |
| 26-getsystemproperty.ref | ❌ FAIL(exit=1) | 1ms |

**Summary**: 7 passed, 21 failed, 1 skipped / 29 total

### Failed tests
- **04-br-dg-cp-rp.ref**: [ERROR] D:\Programming\Projects\8 Semestr\Diploma\refal5j-impl\tests\autotests\04-br-dg-cp-rp.ref: function 'Go', rule #1: call to undefined function 'Dg'
- **05-refal5-conditions.ref**: [ERROR] D:\Programming\Projects\8 Semestr\Diploma\refal5j-impl\tests\autotests\05-refal5-conditions.ref:39:41: Unexpected character ':' (U+3a)
- **06-arithm.ref**: [ERROR] D:\Programming\Projects\8 Semestr\Diploma\refal5j-impl\tests\autotests\06-arithm.ref:195:27: Unexpected character ':' (U+3a)
- **07-arg.ref**: [ERROR] runtime: No matching rule for Eq on args=[Br[items=Shallow[Str[value=r], Str[value=5], Str[value=j], Str[value=.], Str[value=G], Str[value=o], Str[value=_]]], Str[value=r], Str[value=e], St...
- **08-implode-explode.ref**: [ERROR] runtime: No matching rule for Eq on args=[Br[items=Shallow[Num[value=0], Num[value=1], Num[value=2], Num[value=3]]], Num[value=1], Num[value=2], Num[value=3]]
- **10-getenv.ref**: [ERROR] D:\Programming\Projects\8 Semestr\Diploma\refal5j-impl\tests\autotests\10-getenv.ref: function 'Go', rule #1: call to undefined function 'GetEnv'
- **11-exist-file.ref**: [ERROR] D:\Programming\Projects\8 Semestr\Diploma\refal5j-impl\tests\autotests\11-exist-file.ref: function 'Go', rule #1: call to undefined function 'ExistFile'
- **12-file-functions.ref**: [ERROR] D:\Programming\Projects\8 Semestr\Diploma\refal5j-impl\tests\autotests\12-file-functions.ref:101:4: Unexpected character '\' (U+5c)
- **13-type.ref**: [ERROR] runtime: Open: I/O error: preved.txt
- **14-list-of-builtin.ref**: [ERROR] D:\Programming\Projects\8 Semestr\Diploma\refal5j-impl\tests\autotests\14-list-of-builtin.ref:28:19: Unexpected character ':' (U+3a)
- **15-system-exit-retcode.ref**: [ERROR] D:\Programming\Projects\8 Semestr\Diploma\refal5j-impl\tests\autotests\15-system-exit-retcode.ref:5:23: Unexpected character ':' (U+3a)
- **16-chr-lower-ord-upper.ref**: [ERROR] D:\Programming\Projects\8 Semestr\Diploma\refal5j-impl\tests\autotests\16-chr-lower-ord-upper.ref:5:23: Unexpected character ':' (U+3a)
- **17-first-last-lenw.ref**: [ERROR] D:\Programming\Projects\8 Semestr\Diploma\refal5j-impl\tests\autotests\17-first-last-lenw.ref:6:23: Unexpected character ':' (U+3a)
- **18-beautiful-test.ref**: [ERROR] runtime: No matching rule for Равно on args=[Br[items=Shallow[Num[value=333333333333333333333333333333333333333333333333333333333333333]]], Num[value=53103], Num[value=273608379], Num[value...
- **19-utf-8-bom.ref**: [ERROR] D:\Programming\Projects\8 Semestr\Diploma\refal5j-impl\tests\autotests\19-utf-8-bom.ref:1:1: Unexpected character '﻿' (U+feff)
- **21-step.ref**: [ERROR] D:\Programming\Projects\8 Semestr\Diploma\refal5j-impl\tests\autotests\21-step.ref:46:41: Unexpected character ':' (U+3a)
- **22-blocks.ref**: [ERROR] D:\Programming\Projects\8 Semestr\Diploma\refal5j-impl\tests\autotests\22-blocks.ref:14:5: Unexpected character ':' (U+3a)
- **23-random-randomdigit.ref**: [ERROR] D:\Programming\Projects\8 Semestr\Diploma\refal5j-impl\tests\autotests\23-random-randomdigit.ref:27:48: Unexpected character ':' (U+3a)
- **24-sizeof.ref**: [ERROR] D:\Programming\Projects\8 Semestr\Diploma\refal5j-impl\tests\autotests\24-sizeof.ref:5:20: Unexpected character ':' (U+3a)
- **25-sysfuns.ref**: [ERROR] D:\Programming\Projects\8 Semestr\Diploma\refal5j-impl\tests\autotests\25-sysfuns.ref:60:5: Unexpected character ':' (U+3a)
- **26-getsystemproperty.ref**: [ERROR] D:\Programming\Projects\8 Semestr\Diploma\refal5j-impl\tests\autotests\26-getsystemproperty.ref:5:49: Unexpected character ':' (U+3a)

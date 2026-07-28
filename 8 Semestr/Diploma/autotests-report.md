# Отчёт по автотестам

> Актуально на 2026-05-28. Тесты из `autotests/compatibility/`.
> Запуск: `mvn test -Dtest=CompatibilityTest` из `refal5j-impl/`.

## 1. Десахаренный рассахариватель на .OK.ref (pipeline)

**Прошли (36):**
- 1-Prout.OK.ref
- Add-Numb-Symb.OK.ref
- Arg.OK.ref
- Card.OK.ref
- Chr-Lower-Ord-Upper.OK.ref
- Close.OK.ref
- Compare.OK.ref
- Div-Numb-Symb.OK.ref
- Divmod-Numb-Symb.OK.ref
- Explode.OK.ref
- First-Last-Lenw.OK.ref
- GO.OK.ref
- Get-0-stdin.OK.ref
- Get-Open.OK.ref
- Get-autoopen.OK.ref
- Go-GO.OK.ref
- Implode-Implode_Ext.OK.ref
- ListOfBuiltin.OK.ref
- Mod-Numb-Symb.OK.ref
- Mu-Residue.OK.ref
- Mul-Numb-Symb.OK.ref
- Numb-Symb.OK.ref
- Print.OK.ref
- Put-Putout-files.OK.ref
- Put-Putout-stderr.OK.ref
- Step.OK.ref
- Sub.OK.ref
- TimeElapsed.OK.ref
- Type.OK.ref
- Write.OK.ref
- classic-extended.OK.ref
- conditions.OK.ref
- escapes.OK.ref
- fact.OK.ref
- math-sign.OK.ref
- tab.OK.ref

**Не прошли (14):**
- Br-Cp-Dg-Dgall-Rp-bug.OK.ref
- Br-Cp-Dg-Dgall-Rp.OK.ref
- ExistFile.OK.ref
- GetCurrentDirectory.OK.ref
- GetEnv.OK.ref
- GetPID-GetPPID.OK.ref
- Random.OK.ref
- RandomDigit.OK.ref
- RemoveFile.OK.ref
- SizeOf.OK.ref
- Sysfun.OK.ref
- System-1-echo.OK.ref
- System-2-Exit-retcode.OK.ref
- Time.OK.ref

## 2. .FAIL.ref (ожидаемый exit 2 — runtime error)

**Корректно завершились с exit 2 (10):**
- Div-zero-divide.FAIL.ref
- Sysfun-fail-EOF-escape-x.FAIL.ref
- Sysfun-fail-EOF-escape.FAIL.ref
- Sysfun-fail-bad-escape-x.FAIL.ref
- Sysfun-fail-bad-escape.FAIL.ref
- Sysfun-fail-number-EOF.FAIL.ref
- Sysfun-fail-number-nospace.FAIL.ref
- Sysfun-fail-unbalanced-double-quote.FAIL.ref
- Sysfun-fail-very-long-number.FAIL.ref
- Sysfun-fail-word-nospace.FAIL.ref

## 3. .SYNTAX-ERROR.ref (ожидаемый exit 1 — parse/semantic error)

**Корректно завершились с exit 1 (30):**
- adt.SYNTAX-ERROR.ref
- assigns-conditions.SYNTAX-ERROR.ref
- bad-comment.SYNTAX-ERROR.ref
- blocks-conditions.SYNTAX-ERROR.ref
- empty-block-1.SYNTAX-ERROR.ref
- empty-block-2.SYNTAX-ERROR.ref
- enum.SYNTAX-ERROR.ref
- equal-block.SYNTAX-ERROR.ref
- escapes1.SYNTAX-ERROR.ref
- escapes2.SYNTAX-ERROR.ref
- eswap.SYNTAX-ERROR.ref
- function-ptr-call.SYNTAX-ERROR.ref
- function-ptr.SYNTAX-ERROR.ref
- include-not-found.SYNTAX-ERROR.ref
- include.SYNTAX-ERROR.ref
- keyword-label.SYNTAX-ERROR.ref
- native-insertion.SYNTAX-ERROR.ref
- nested-function.SYNTAX-ERROR.ref
- no-colon-block.SYNTAX-ERROR.ref
- scopeid.SYNTAX-ERROR.ref
- swap.SYNTAX-ERROR.ref
- two-blocks-missed-colon.SYNTAX-ERROR.ref
- two-blocks.SYNTAX-ERROR.ref
- underscore-var.SYNTAX-ERROR.ref
- unnamed-adt.SYNTAX-ERROR.ref
- variable-in-call.SYNTAX-ERROR.ref
- variable-redef-in-result.SYNTAX-ERROR.ref
- variable-redef-no-variable.SYNTAX-ERROR.ref
- variable-redef.SYNTAX-ERROR.ref
- where-with-ampersand.SYNTAX-ERROR.ref
- start-index-from-dash.SYNTAX-ERROR.ref rc=0
- underscore-call.SYNTAX-ERROR.ref rc=0

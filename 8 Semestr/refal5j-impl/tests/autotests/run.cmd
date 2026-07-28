@echo off
call :MAIN %*
exit /b

:MAIN
setlocal
  if {%1}=={} (
    for %%r in (*.ref) do call :RUN_TEST "%%~r" || exit /b 1
  ) else (
    for %%r in (%*) do call :RUN_TEST "%%~r" || exit /b 1
  )
  echo All tests passed!
endlocal
goto :EOF

:RUN_TEST
setlocal
  echo Passing %1...
  if exist gen.@@@\nul rd /s /q gen.@@@
  md gen.@@@\r5j

  if exist "%~n1".args (
    set /P ARGS=<"%~n1".args
  ) else (
    set ARGS=
  )

  if exist "%~n1".sysargs (
    set /P SYSARGS=<"%~n1".sysargs
  ) else (
    set SYSARGS=
  )

  if exist "satellite\%~1" (
    set SAT=satellite\%~1
  ) else (
    set SAT=
  )

  set PATH_SEP=;
  set FOO=BAR
  set UNDEF=

  java -ea -cp "..\lib;..\bin\r5jc.jar" r5j.GO_ %1 %SAT% 2> _compiler.error
  if not exist gen.@@@\r5j\Go_.java goto :RUN_TEST_FAIL
  if exist _java_compiler.error erase _java_compiler.error
  for %%j in (gen.@@@\r5j\*.java) do (
    javac -Xlint -Xdiags:verbose -encoding utf-8 -classpath ..\lib;gen.@@@ %%j ^
      2>_java_compiler.error ^
      || goto :RUN_TEST_FAIL
  )
  java -enableassertions -classpath ..\lib;gen.@@@ %SYSARGS% r5j.Go_ %ARGS% ^
    2>_run.error ^
    || goto :RUN_TEST_FAIL

  for /L %%i in (10, 1, 20) do (
    if exist "%~n1.REFAL%%i.txt" (
      fc "%~n1.REFAL%%i.txt" REFAL%%i.DAT || goto :RUN_TEST_FAIL
      erase REFAL%%i.DAT
    ) else if exist "%~n1.REFAL%%i.bin" (
      fc /b "%~n1.REFAL%%i.bin" REFAL%%i.DAT || goto :RUN_TEST_FAIL
      erase REFAL%%i.DAT
    )
  )

  rd /s /q gen.@@@
  erase *.error
endlocal
goto :EOF

:RUN_TEST_FAIL
  echo TEST %1 FAILED! See *.error files!
  exit /b 1

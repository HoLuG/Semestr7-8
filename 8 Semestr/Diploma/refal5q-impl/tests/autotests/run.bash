#!/bin/bash

main() {
  if [[ -z "$1" ]]; then
    for r in *.ref; do
      run_test "$r" || exit 1
    done
  else
    for r in "$@"; do
      run_test "$@" || exit 1
    done
  fi
}

run_test() {
  echo Passing $1...
  rm -rf gen.@@@
  mkdir -p gen.@@@/r5j

  REF="$1"
  BASE="${REF%%.ref}"

  if [[ -e "$BASE.args" ]]; then
    ARGS="$(cat "$BASE.args")"
  else
    ARGS=
  fi

  if [[ -e "$BASE.sysargs" ]]; then
    SYSARGS="$(cat "$BASE.sysargs")"
  else
    SYSARGS=
  fi

  if [[ -e "satellite/$REF" ]]; then
    SAT="satellite/$REF"
  else
    SAT=
  fi

  export PATH_SEP=:
  export FOO=BAR
  export UNDEF=

  java -ea -cp ../lib:../bin/r5jc.jar r5j.GO_ "$REF" $SAT 2> _compiler.error
  [[ -e gen.@@@/r5j/Go_.java ]] || run_test_fail "$1"
  rm -f _java_compiler.error
  javac -Xlint -Xdiags:verbose -encoding utf-8 -classpath ../lib:gen.@@@ \
    gen.@@@/r5j/*.java 2> _java_compiler.error || run_test_fail "$1"

  PATH=".:$PATH" java -ea -cp ../lib:gen.@@@ $SYSARGS r5j.Go_ $ARGS \
    2> _run.error || run_test_fail "$1"

  for ((i = 10; i <= 20; ++i)); do
    if [[ -e "$BASE.REFAL$i.txt" ]]; then
      diff -u "$BASE.REFAL$i.txt" REFAL$i.DAT || run_test_fail "$1"
      rm REFAL$i.DAT
    elif [[ -e "$BASE.REFAL$i.bin" ]]; then
      cmp "$BASE.REFAL$i.bin" REFAL$i.DAT || run_test_fail "$1"
      rm REFAL$i.DAT
    fi
  done

  rm -rf gen.@@@ *.error
}

run_test_fail() {
  echo TEST $1 FAILED! See *.error files!
  exit 1
}

main "$@"

#! /usr/bin/env bash

declare -a SPECIAL_VERSIONS=('2.6' '3.2' '3.3')

function find_get_pip_version() {
  local version="$1"

  for v in "${SPECIAL_VERSIONS[@]}"
  do
    [[ "$version" == "$v" ]] && echo "$version" && return 0
  done

  return 1
}

function cat_get_pip() {
  local version=$(find_get_pip_version "$1")

  local path="get-pip.py"
  [[ -n "$version" ]] && path="$version/$path"
  local src="$2"
  local cmd=cat
  if [[  "$src" == "remote" ]]
  then
    path="https://bootstrap.pypa.io/$path"
    cmd='wget -O - '
  elif [[ "$src" != "local" ]]
  then
    >&2 echo Wrong source argument: $src
    exit 1
  fi

  $cmd $path
}

function main() {
  local python_version="$1"
  local get_pip_src="$2"
  cat_get_pip "$python_version" "$get_pip_src" | python -
}

# Reset settings
set +eu

main $*

function cat_get_pip() {
  local version="$1"
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

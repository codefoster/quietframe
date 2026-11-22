#!/usr/bin/env bash
set -euo pipefail

if (( $# != 1 )); then
  printf 'Usage: %s <Tizen security profile>\n' "$0" >&2
  exit 2
fi

root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cli=${TIZEN_CLI:-tizen}
stage=$(mktemp -d "$root/.buildResult.XXXXXXXX")
trap 'rm -r -- "$stage"' EXIT

cp -a -- "$root/app/." "$stage/"
mkdir -p -- "$root/dist"
"$cli" package -t wgt -s "$1" -o "$root/dist" -- "$stage"

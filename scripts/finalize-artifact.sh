#!/usr/bin/env bash
# Run on the Linux builder only after Catalyst has returned successfully.
set -euo pipefail
[[ $# == 2 ]] || { echo 'Usage: finalize-artifact.sh INPUT.tar.xz OUTPUT.tar.xz' >&2; exit 2; }
input=$(realpath -- "$1")
output=$(realpath -m -- "$2")
[[ -f $input && $input != "$output" && ! -e $output ]] || {
  echo 'Input must exist; output must be a different, new file.' >&2; exit 2;
}
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
root=$(mktemp -d "${RUNNER_TEMP:-/var/tmp}/skeleton-root.XXXXXX")
partial="${output}.partial"
trap 'rm -rf -- "$root"; rm -f -- "$partial"' EXIT
# Input is the archive produced by this build, not an arbitrary uploaded tar.
tar --numeric-owner --xattrs --acls -xpf "$input" -C "$root"
python3 "$script_dir/finalize-rootfs.py" "$root" --report "${output}.manifest.json"
# ldconfig runs only inside the extracted root; never against host libraries.
chroot "$root" /sbin/ldconfig
bash "$script_dir/check-rootfs.sh" "$root"
tar --numeric-owner --xattrs --acls -cJpf "$partial" -C "$root" .
mv -- "$partial" "$output"

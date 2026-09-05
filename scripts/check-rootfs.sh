#!/usr/bin/env bash
# Host-side entry point, after finalization and before packing.
set -euo pipefail
[[ $# == 1 && $1 != / ]] || { echo 'Usage: check-rootfs.sh ROOTFS (not /)' >&2; exit 2; }
root=$(realpath -- "$1")
[[ $root != / && -f $root/etc/passwd ]] || exit 2
[[ $(uname -s) == Linux && $(uname -m) == x86_64 ]] || {
  echo 'Runtime validation requires an x86_64 Linux host.' >&2; exit 1;
}
chroot "$root" /usr/bin/env -i HOME=/root LC_ALL=C \
  PATH=/usr/sbin:/usr/bin:/sbin:/bin /bin/bash -s <<'CHECK'
# Login profiles are not required to support nounset/errexit.
source /etc/profile
set -euo pipefail
for tool in emerge portageq ebuild eselect q env-update; do
  if command -v "$tool" >/dev/null 2>&1; then
    echo "Unexpected build tool: $tool" >&2; exit 1
  fi
done
for path in /etc/os-release /usr/lib/os-release /etc/gentoo-release /etc/env.d \
    /etc/portage /etc/profile.env /var/db/pkg /var/db/repos; do
  if [[ -e $path || -L $path ]]; then
    echo "Unexpected identity/build state: $path" >&2; exit 1
  fi
done
if grep -q '^portage:' /etc/passwd /etc/group /etc/shadow; then
  echo 'Portage account remains' >&2; exit 1
fi
# Include stderr: gcc prints its verbose version there.
for tool in gcc ld ldd; do
  banner=$("$tool" --version 2>&1)
  printf '%s\n' "$banner"
  if [[ ${banner,,} == *gentoo* ]]; then
    echo "Remaining Gentoo banner in $tool; rebuild that package first." >&2; exit 1
  fi
done
[[ $(getconf GNU_LIBC_VERSION) == glibc\ * ]]
systemctl --version
[[ -x /usr/lib/systemd/systemd || -x /lib/systemd/systemd ]]
[[ -x /sbin/init && $(readlink -f /sbin/init) == */systemd ]]
[[ ! -s /etc/machine-id ]]
[[ $(getent passwd root) == root:* ]]
getent hosts localhost
work=$(mktemp -d /tmp/skeleton-check.XXXXXX)
trap 'rm -rf "$work"' EXIT
cat > "$work/hello.c" <<'C'
#include <stdio.h>
int main(void) { puts("skeleton-ok"); return 0; }
C
gcc "$work/hello.c" -o "$work/hello"
[[ $("$work/hello") == skeleton-ok ]]
ldd "$work/hello"
# This is a userspace/chroot check. PID 1 boot requires a separate VM test.
echo 'PASS: shell, glibc, compiler/linker, NSS and systemd executable checks.'
CHECK

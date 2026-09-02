#!/usr/bin/env bash
#
# strip-identity.sh - runs inside the Catalyst stage4 chroot (stage4/fsscript),
# after the toolchain is compiled and Portage/eselect are unmerged.
#
# Delete only. No replacement os-release, issue file or tooling is written.
# rm -f / rm -rf so a missing target (or an unmatched glob) never aborts.

set -euo pipefail

echo "==> strip-identity: OS identity files"
rm -f \
	/etc/os-release \
	/usr/lib/os-release \
	/etc/gentoo-release \
	/etc/issue* \
	/usr/share/factory/etc/issue

echo "==> strip-identity: Portage logs, python wrappers, sysusers/tmpfiles"
rm -rf \
	/var/lib/portage \
	/var/log/portage \
	/var/log/emerge*.log \
	/etc/portage \
	/usr/share/portage \
	/usr/lib/python*/site-packages/portage* \
	/usr/lib/python*/site-packages/_emerge \
	/usr/lib/python-exec/python*/emerge \
	/usr/lib/python-exec/python*/portageq \
	/usr/lib/sysusers.d/acct-*-portage.conf \
	/usr/lib/tmpfiles.d/portage-*.conf

echo "==> strip-identity: eselect traces"
rm -rf \
	/usr/share/eselect \
	/etc/env.d \
	/usr/share/bash-completion/completions/eselect \
	/usr/share/doc/eselect-*

echo "==> strip-identity: Gentoo systemd generators, hooks and state dirs"
rm -f \
	/usr/lib/systemd/system-generators/gentoo-local-generator \
	/usr/lib/systemd/system-environment-generators/10-gentoo-path \
	/etc/bash/bashrc.d/10-gentoo-*.bash \
	/etc/environment.d/10-gentoo-env.conf \
	/usr/lib/sysctl.d/60-gentoo.conf \
	/usr/lib/udev/rules.d/40-gentoo.rules \
	/usr/share/misc/magic/gentoo \
	/usr/share/nano/gentoo.nanorc
rm -rf \
	/usr/lib/gentoo \
	/var/lib/gentoo

echo "==> strip-identity: done"

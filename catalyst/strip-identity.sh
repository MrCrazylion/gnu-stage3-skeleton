#!/usr/bin/env bash
#
# strip-identity.sh - runs inside the Catalyst stage4 chroot (stage4/fsscript).
#
# This script ONLY deletes. It never writes a replacement os-release, issue
# file, package manager or distro tooling. After it runs the rootfs is a bare
# GNU/Linux systemd system with no Gentoo or Portage identity left behind.
#
# rm -f / rm -rf are used throughout so a missing target (or an unmatched glob,
# which is passed through literally) never aborts the build.

set -euo pipefail

echo "==> strip-identity: removing distro branding / identity files"
rm -f \
	/etc/os-release \
	/usr/lib/os-release \
	/etc/gentoo-release \
	/etc/issue* \
	/usr/share/factory/etc/issue

echo "==> strip-identity: removing Portage leftovers and python wrappers"
rm -rf \
	/var/lib/portage \
	/var/log/portage \
	/etc/portage \
	/usr/share/portage \
	/usr/lib/python*/site-packages/portage* \
	/usr/lib/python*/site-packages/_emerge \
	/usr/lib/python-exec/python*/emerge \
	/usr/lib/python-exec/python*/portageq \
	/usr/lib/sysusers.d/acct-*-portage.conf \
	/usr/lib/tmpfiles.d/portage-*.conf

echo "==> strip-identity: removing eselect leftovers"
rm -rf \
	/usr/share/eselect \
	/etc/env.d

echo "==> strip-identity: removing Gentoo hooks and config drop-ins"
rm -f \
	/etc/bash/bashrc.d/10-gentoo-*.bash \
	/etc/environment.d/10-gentoo-env.conf \
	/usr/lib/sysctl.d/60-gentoo.conf \
	/usr/lib/udev/rules.d/40-gentoo.rules \
	/usr/lib/systemd/system-generators/gentoo-local-generator \
	/usr/lib/systemd/system-environment-generators/10-gentoo-path \
	/usr/share/misc/magic/gentoo \
	/usr/share/nano/gentoo.nanorc

echo "==> strip-identity: removing Gentoo state directories"
rm -rf \
	/usr/lib/gentoo \
	/var/lib/gentoo

echo "==> strip-identity: done"

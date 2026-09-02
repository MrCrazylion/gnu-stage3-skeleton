#!/usr/bin/env bash
#
# strip-identity.sh - runs inside the Catalyst stage4 chroot (stage4/fsscript),
# after the toolchain is compiled.
#
# The spec no longer uses stage4/unmerge: portage inside the de-branded chroot
# is not reliably usable (a python default-version bump during the toolchain
# rebuild strands sys-apps/portage), so `emerge -C` cannot run. Instead this
# script removes Portage / eselect / portage-utils by file, along with every
# other Gentoo identity trace.
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

echo "==> strip-identity: Portage (binaries, libs, data, wrappers)"
rm -rf \
	/usr/bin/emerge /usr/bin/emerge-webrsync /usr/bin/emirrordist \
	/usr/bin/ebuild /usr/bin/egencache /usr/bin/portageq /usr/bin/quickpkg \
	/usr/bin/repoman /usr/bin/dispatch-conf /usr/bin/etc-update \
	/usr/bin/fixpackages /usr/bin/regenworld /usr/sbin/env-update \
	/usr/lib/portage /usr/share/portage \
	/usr/lib/python*/site-packages/portage* \
	/usr/lib/python*/site-packages/_emerge \
	/usr/lib/python-exec/python*/emerge \
	/usr/lib/python-exec/python*/emerge-webrsync \
	/usr/lib/python-exec/python*/portageq \
	/usr/lib/python-exec/python*/ebuild \
	/usr/lib/python-exec/python*/egencache \
	/usr/lib/python-exec/python*/repoman \
	/var/lib/portage /var/log/portage /var/log/emerge*.log \
	/var/cache/edb /etc/portage \
	/usr/lib/sysusers.d/acct-*-portage.conf \
	/usr/lib/tmpfiles.d/portage-*.conf \
	/usr/share/man/man?/{emerge,ebuild,portage,make.conf,color.map,dispatch-conf,etc-update,fixpackages,quickpkg,egencache,portageq}.* \
	/usr/share/bash-completion/completions/{emerge,ebuild,portageq}

echo "==> strip-identity: eselect"
rm -rf \
	/usr/bin/eselect \
	/usr/share/eselect \
	/etc/env.d \
	/usr/share/bash-completion/completions/eselect \
	/usr/share/doc/eselect-* \
	/usr/share/man/man?/*eselect*

echo "==> strip-identity: portage-utils (q applets)"
rm -rf \
	/usr/bin/q \
	/usr/bin/qatom /usr/bin/qcheck /usr/bin/qdepends /usr/bin/qfile \
	/usr/bin/qgrep /usr/bin/qkeyword /usr/bin/qlist /usr/bin/qlop \
	/usr/bin/qmanifest /usr/bin/qmerge /usr/bin/qpkg /usr/bin/qsize \
	/usr/bin/quse /usr/bin/qtbz2 /usr/bin/qwhich /usr/bin/qxpak \
	/usr/share/man/man1/q.1* /usr/share/man/man1/q[a-z]*.1*

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

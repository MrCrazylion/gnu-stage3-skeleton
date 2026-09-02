# Catalyst stage4 spec: identity-less, vanilla GNU/Linux systemd skeleton.
#
# Catalyst rebuilds the core toolchain and system set with the "vanilla" and
# "-branding" USE flags so the resulting binaries carry no Gentoo patches or
# distro branding, then unmerges the package manager and runs an in-chroot
# cleanup script (stage4/fsscript) that deletes every remaining Gentoo/Portage
# identity file.
#
# NOTE: this is a heavy source build - it recompiles gcc, glibc, binutils and
# systemd. Expect multiple hours and tens of GB of scratch space.

subarch: amd64
target: stage4
rel_type: default
profile: default/linux/amd64/23.0/systemd
version_stamp: skeleton

# Portage tree snapshot to build against. The workflow runs `catalyst -s stable`
# to materialise this. Some Catalyst versions want a git commit hash here
# instead of a branch name - adjust if the build complains.
snapshot_treeish: stable

# Seed: the plain upstream stage3 the workflow drops into
#   <builds>/default/stage3-amd64-systemd-latest.tar.xz
source_subpath: default/stage3-amd64-systemd-latest

# Force vanilla, unbranded builds for everything compiled in this stage.
stage4/use: vanilla -branding

# Core toolchain + system packages to (re)build with the USE flags above.
stage4/packages:
	sys-devel/gcc
	sys-devel/binutils
	sys-libs/glibc
	sys-apps/coreutils
	sys-apps/systemd
	sys-apps/baselayout

# Rip out the Gentoo package manager and its helpers.
stage4/unmerge:
	sys-apps/portage
	app-admin/eselect
	app-portage/portage-utils

# Wipe package DB, repos and caches so the image has no memory of Portage.
stage4/empty:
	/var/db/pkg
	/var/db/repos
	/var/cache/binpkgs
	/var/cache/distfiles
	/tmp
	/var/log
	/usr/src

# Final surgical identity strip, executed inside the chroot.
stage4/fsscript: /root/catalyst/strip-identity.sh

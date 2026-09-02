# Catalyst stage4 spec: 100% vanilla, identity-less GNU/Linux systemd skeleton.
#
# The core toolchain (binutils, gcc, glibc) is rebuilt against the local
# /tmp/gnu-overlay produced by scripts/prepare-overlay.sh, which strips Gentoo
# branding patches and the --with-pkgversion / --with-bugurl /
# --enable-gentoo-library-naming configure switches so the binaries carry pure
# upstream GNU identity strings. Portage/eselect are then unmerged, caches and
# the package DB are emptied, and strip-identity.sh removes the last traces.

subarch: amd64
target: stage4
rel_type: default
profile: default/linux/amd64/23.0/systemd
version_stamp: skeleton

# Portage tree snapshot to build against (materialised by `catalyst -s stable`).
# Some Catalyst versions want a git commit hash here instead of a branch name.
snapshot_treeish: stable

# Seed dropped by the workflow at builds/default/stage3-amd64-systemd-latest.tar.xz
source_subpath: default/stage3-amd64-systemd-latest

# Local toolchain overlay from scripts/prepare-overlay.sh.
# NOTE: this key is `portdir_overlay` on Catalyst <=3; on Catalyst 4 rename it
# to `repos`. The overlay uses thin manifests so no manifest signing is needed.
portdir_overlay: /tmp/gnu-overlay

# Force vanilla, unbranded builds for everything compiled in this stage.
stage4/use: vanilla -branding

# Only the core toolchain is rebuilt from the overlay.
stage4/packages: sys-devel/binutils sys-devel/gcc sys-libs/glibc

# Remove the Gentoo package manager and its helpers.
stage4/unmerge: sys-apps/portage app-admin/eselect app-portage/portage-utils

# Wipe package DB, repos, caches and volatile trees.
stage4/empty: /var/db/pkg /var/db/repos /var/cache/binpkgs /var/cache/distfiles /tmp /var/log /usr/src

# In-chroot identity strip, run after compilation + unmerge.
stage4/fsscript: /root/catalyst/strip-identity.sh

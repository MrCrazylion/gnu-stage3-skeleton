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

# Catalyst 4 builds the snapshot from the git repo at repo_basedir/repo_name
# (/var/db/repos/gentoo). The workflow clones it and runs `catalyst -s master`,
# so this treeish must match that ref.
snapshot_treeish: master

# Seed dropped by the workflow at builds/default/stage3-amd64-systemd-latest.tar.xz
source_subpath: default/stage3-amd64-systemd-latest

# Local toolchain overlay from scripts/prepare-overlay.sh. Catalyst 4 key for
# extra ebuild repositories (replaces the old portdir_overlay/portage_overlay).
# The overlay uses thin manifests so no manifest signing is needed.
repos: /tmp/gnu-overlay

# Force vanilla, unbranded builds for everything compiled in this stage.
stage4/use: vanilla -branding

# Only the core toolchain is rebuilt from the overlay.
stage4/packages: sys-devel/binutils sys-devel/gcc sys-libs/glibc

# NOTE: no stage4/unmerge. Portage is not reliably usable in the de-branded
# chroot (python default-version bump during the toolchain rebuild strands
# sys-apps/portage), so `emerge -C` fails. strip-identity.sh removes
# portage / eselect / portage-utils by file instead.

# Wipe package DB, repos, caches and volatile trees.
stage4/empty: /var/db/pkg /var/db/repos /var/cache/binpkgs /var/cache/distfiles /tmp /var/log /usr/src

# In-chroot identity strip, run after compilation.
stage4/fsscript: /root/catalyst/strip-identity.sh

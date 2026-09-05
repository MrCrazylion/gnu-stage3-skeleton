# Catalyst builds the intermediate amd64/glibc/systemd rootfs.
# Keep the build tools and package database until Catalyst has finished.
# The workflow finalizes and validates an extracted copy afterwards.

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

# Request these USE flags where supported; this is not an upstream-purity check.
stage4/use: vanilla -branding

# The workflow disables pkgcache to avoid --newuse skipping these rebuilds.
stage4/packages: sys-devel/binutils::gnu-overlay sys-devel/gcc::gnu-overlay sys-libs/glibc::gnu-overlay

# No identity-removal fsscript: preclean/clean still require Portage afterwards.
# Preserve /var/db/pkg so the finalizer can remove files by package ownership.
stage4/empty: /var/cache/binpkgs /var/cache/distfiles /tmp /var/log /usr/src

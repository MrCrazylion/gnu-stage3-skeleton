#!/usr/bin/env bash
#
# prepare-overlay.sh
#
# Build a local Portage overlay that removes Gentoo's fingerprints from the
# core toolchain (binutils, gcc, glibc) so the compiled binaries fall back to
# pure upstream GNU defaults. NOTHING is re-branded - we only DELETE:
#
#   1. Gentoo branding/identity patches carried in the toolchain patch tarballs
#      (dropped from ${WORKDIR}/patch/ before the ebuild eapply's them).
#   2. The Gentoo-specific configure switches
#         --with-pkgversion=...            -> gcc -v / ld -v version string
#         --with-bugurl=...                -> bug URL baked into the binaries
#         --enable-gentoo-library-naming   -> Gentoo-only library layout
#      removed from the ebuilds AND from the toolchain eclasses, because for
#      gcc/binutils those flags are actually set in toolchain.eclass /
#      toolchain-binutils.eclass, not in the ebuild.
#
set -euo pipefail

OVERLAY="${OVERLAY:-/tmp/gnu-overlay}"
GENTOO_GIT="${GENTOO_GIT:-https://github.com/gentoo/gentoo.git}"
GENTOO_GIT_FALLBACK="https://anongit.gentoo.org/git/repo/gentoo.git"

PKGS=(sys-devel/binutils sys-devel/gcc sys-libs/glibc)
ECLASSES=(toolchain.eclass toolchain-binutils.eclass)

WORK="$(mktemp -d)"
trap 'rm -rf "${WORK}"' EXIT

# ---------------------------------------------------------------------------
# 1. Overlay skeleton
# ---------------------------------------------------------------------------
echo "==> Creating overlay skeleton at ${OVERLAY}"
rm -rf "${OVERLAY}"
mkdir -p "${OVERLAY}/metadata" "${OVERLAY}/profiles" "${OVERLAY}/eclass"

# masters = gentoo   -> pull eclasses/profiles/licenses from the main repo.
# thin-manifests     -> Manifests hash only upstream DIST tarballs, never the
#                       ebuild text, so the sed edits below never invalidate a
#                       Manifest and the copied Manifest files stay valid.
cat > "${OVERLAY}/metadata/layout.conf" <<'EOF'
masters = gentoo
thin-manifests = true
sign-manifests = false
cache-formats = md5-dict
EOF
echo "gnu-overlay" > "${OVERLAY}/profiles/repo_name"

# ---------------------------------------------------------------------------
# 2. Shallow clone of the Gentoo ebuild repository
# ---------------------------------------------------------------------------
echo "==> Shallow-cloning the Gentoo ebuild repository"
git clone --depth=1 --single-branch --filter=blob:limit=1m \
  "${GENTOO_GIT}" "${WORK}/gentoo" \
  || git clone --depth=1 --single-branch "${GENTOO_GIT_FALLBACK}" "${WORK}/gentoo"

# ---------------------------------------------------------------------------
# 3. Import the toolchain packages and their eclasses into the overlay
# ---------------------------------------------------------------------------
echo "==> Importing toolchain packages"
for pkg in "${PKGS[@]}"; do
  mkdir -p "${OVERLAY}/${pkg%/*}"
  cp -a "${WORK}/gentoo/${pkg}" "${OVERLAY}/${pkg}"
  echo "    + ${pkg}"
done

echo "==> Importing toolchain eclasses"
for ec in "${ECLASSES[@]}"; do
  if [[ -f "${WORK}/gentoo/eclass/${ec}" ]]; then
    cp -a "${WORK}/gentoo/eclass/${ec}" "${OVERLAY}/eclass/${ec}"
    echo "    + eclass/${ec}"
  fi
done

# ---------------------------------------------------------------------------
# 4. sed surgery
# ---------------------------------------------------------------------------
# 4a. src_prepare() injection: delete Gentoo branding/identity patches before
#     they are applied. The snippet is spliced in right after the opening brace
#     of an existing src_prepare() (binutils, glibc); gcc has no ebuild-level
#     src_prepare() - it is exported by toolchain.eclass - so we append an
#     override that runs the rm's and then calls toolchain_src_prepare.
SNIP="${WORK}/src_prepare_snippet.txt"
cat > "${SNIP}" <<'EOF'
	# >>> gnu-overlay: revert to upstream GNU identity (prepare-overlay.sh)
	rm -f "${WORKDIR}/patch/"*branding*.patch || true
	rm -f "${WORKDIR}/patch/"*gentoo*.patch   || true
	rm -f "${WORKDIR}/patch/"*Gentoo*.patch   || true
	# <<< gnu-overlay
EOF

inject_src_prepare() {
  local f="$1"
  if grep -qE '^[[:space:]]*src_prepare[[:space:]]*\(\)[[:space:]]*\{[[:space:]]*$' "${f}"; then
    sed -i -e '/^[[:space:]]*src_prepare[[:space:]]*()[[:space:]]*{[[:space:]]*$/r '"${SNIP}" "${f}"
  else
    cat >> "${f}" <<'EOF'

# >>> gnu-overlay: revert to upstream GNU identity (prepare-overlay.sh)
src_prepare() {
	rm -f "${WORKDIR}/patch/"*branding*.patch || true
	rm -f "${WORKDIR}/patch/"*gentoo*.patch   || true
	rm -f "${WORKDIR}/patch/"*Gentoo*.patch   || true
	toolchain_src_prepare
}
# <<< gnu-overlay
EOF
  fi
}

# 4b. Flag stripping: delete the whole physical line carrying a Gentoo-only
#     configure switch. In the eclasses each switch lives on its own
#     `confgcc+=( --with-... )` line; in the binutils ebuild each is its own
#     backslash-continued `econf` argument line - so a line delete drops just
#     that one switch and nothing else.
strip_gentoo_flags() {
  sed -i -E \
    -e '/--with-pkgversion([=[:space:]"]|$)/d' \
    -e '/--with-bugurl([=[:space:]"]|$)/d' \
    -e '/--enable-gentoo-library-naming/d' \
    "$1"
}

echo "==> Rewriting ebuilds"
while IFS= read -r -d '' ebuild; do
  inject_src_prepare "${ebuild}"
  strip_gentoo_flags "${ebuild}"
  echo "    patched ${ebuild#"${OVERLAY}"/}"
done < <(find "${OVERLAY}" -name '*.ebuild' -print0)

echo "==> Rewriting eclasses"
for ec in "${ECLASSES[@]}"; do
  [[ -f "${OVERLAY}/eclass/${ec}" ]] || continue
  strip_gentoo_flags "${OVERLAY}/eclass/${ec}"
  echo "    stripped Gentoo flags from eclass/${ec}"
done

# ---------------------------------------------------------------------------
# 5. Manifests
# ---------------------------------------------------------------------------
# thin-manifests means the copied Manifest files are still valid after our text
# edits (they only checksum the upstream tarballs, which we never touched).
# Regenerate anyway when a usable Portage config is present; never fail on it.
echo "==> Refreshing manifests (best effort - thin manifests stay valid regardless)"
if command -v ebuild >/dev/null 2>&1; then
  export PORTAGE_REPOSITORIES="
[DEFAULT]
main-repo = gentoo

[gentoo]
location = ${WORK}/gentoo

[gnu-overlay]
location = ${OVERLAY}
masters = gentoo
"
  for pkg in "${PKGS[@]}"; do
    for e in "${OVERLAY}/${pkg}"/*.ebuild; do
      [[ -e "${e}" ]] || continue
      FEATURES="-strict digest assume-digests" ebuild "${e}" manifest 2>/dev/null || true
    done
  done
fi

echo "==> Overlay ready:"
find "${OVERLAY}" -maxdepth 2 -mindepth 1 | sort

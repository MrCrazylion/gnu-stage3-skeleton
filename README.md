# GNU/Linux systemd skeleton

Current target: **amd64, glibc, systemd**. Gentoo is the build/seed environment.
The output is an unbranded rootfs intended as a starting point for an independent
distribution, not a ready-to-install universal distribution or proof of 100%
unmodified upstream software.

## Build and finalization

Run `build-skeleton` with GitHub Actions `workflow_dispatch`.

1. Prepare the Gentoo seed and a toolchain overlay. The overlay and Catalyst
   snapshot now use the same repository revision within a run.
2. Catalyst builds its intermediate stage4. Its package cache is disabled so
   explicit requests for the three overlay toolchain packages aren't skipped by
   `--newuse`. Gentoo's remaining build configuration still applies.
3. Preserve the intermediate Catalyst archive as a separate 3-day artifact,
   then extract it into a temporary rootfs. Inputs may use xz, bzip2, gzip or
   uncompressed tar; the final output is always xz.
4. Remove Portage, eselect and portage-utils files using the installed package
   CONTENTS lists plus explicit cleanup paths. Remove account entries, generated
   environment files, login branding and OS identity files. Preserve the selected
   compiler PATH as static configuration and retain library search configuration.
5. Run ldconfig and userspace checks inside that rootfs. Only successful checks
   allow the final archive to be created and uploaded.

The final archive keeps the existing `gnu-stage3-skeleton-amd64.tar.xz` name.
A separate JSON manifest records the seed package inventory and removed paths;
it is not placed in the rootfs. Source attribution and license documentation are
preserved. No replacement OS brand is invented. A downstream distribution should
provide its own os-release before treating the rootfs as a finished OS.

The previous `stage4/fsscript` deleted `/etc/portage` too early. Catalyst's later
`clean` action attempted to write `/etc/portage/make.conf`, causing the observed
failure in run 33658039905. The old destructive hook now fails with migration
instructions rather than deleting files inside an unfinished Catalyst build.

## Checks

Portable cleanup regression tests and shell syntax checks:

```sh
python3 -m unittest discover -s tests -v
for script in scripts/*.sh catalyst/*.sh; do bash -n "$script"; done
```

The build additionally checks, on an x86_64 Linux host:

- absence of the explicitly removed tools, OS identity files and package state;
- removal of the Portage account;
- GCC, ld and ldd banners without Gentoo branding;
- glibc, root account and localhost NSS resolution;
- a working systemd executable and init link;
- compilation, dynamic linking and execution of a small C program.

For an already-built **trusted Catalyst archive**, as root on a Linux builder:

```sh
bash scripts/finalize-artifact.sh /path/to/stage4.tar.xz /path/to/new-output.tar.xz
```

The finalizer requires the package database; do not empty `/var/db/pkg` in the
Catalyst spec. Use a fresh extracted copy for each run. Do not run the old
baselayout-only patch as an additional required step: this pipeline finalizer
handles the installed files, including artifacts already present in the seed.

## Limits and next acceptance checks

- This change fixes the observed phase-order failure and adds validation. A full
  Catalyst run and a systemd PID 1 boot have not been executed while preparing it.
- Chroot checks do **not** demonstrate boot, service startup, login, network
  provisioning, or compatibility with another architecture/libc/init system.
  A VM boot test with an explicit test kernel and disk setup is still needed.
- `prepare-overlay.sh` still selects patches by filename and edits ebuild/eclass
  lines. This does not establish that every downstream patch was removed; other
  seed packages retain Gentoo build choices. Banner checks intentionally fail if
  the overlay did not achieve its claimed debranding for the tested commands.
- The finalizer removes known integrations, not every possible Gentoo reference
  in every installed file. Compiler selector utilities and other seed-specific
  files still need an ownership/dependency audit before claiming full independence.
- Sources still use moving `latest`/`master` inputs across runs. Pin the seed,
  repository revision, container digest and source checksums for reproducibility.

Upstream evidence: [failed build](https://github.com/MrCrazylion/gnu-stage3-skeleton/actions/runs/33658039905)
and [Catalyst merge options](https://github.com/gentoo/catalyst/blob/8c30e365218b204c41319aff321f4c2c9ddf1b24/targets/support/chroot-functions.sh).

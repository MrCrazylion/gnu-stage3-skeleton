#!/usr/bin/env bash
# Kept to fail clearly for old specs that still reference this unsafe hook.
printf '%s\n' 'Identity removal must run AFTER Catalyst finishes.' \
  'Use scripts/finalize-rootfs.py on an extracted copy of its output.' >&2
exit 1

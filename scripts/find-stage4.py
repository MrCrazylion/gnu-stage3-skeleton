#!/usr/bin/env python3
"""Locate one Catalyst stage4 tar archive, regardless of compression format."""
import argparse
from pathlib import Path

SUFFIXES = ('.tar.xz', '.tar.bz2', '.tar.gz', '.tar')


def find_stage4(directory):
    root = Path(directory)
    if not root.is_dir():
        raise ValueError(f'build directory does not exist: {root}')
    candidates = sorted(p for p in root.rglob('stage4-*')
                        if p.is_file() and p.name.endswith(SUFFIXES))
    if len(candidates) != 1:
        listing = ', '.join(str(p) for p in candidates) or '(none)'
        raise ValueError(f'expected exactly one stage4 tar archive; found {len(candidates)}: {listing}')
    return candidates[0]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory')
    args = parser.parse_args()
    try:
        print(find_stage4(args.directory))
    except ValueError as error:
        parser.exit(1, f'{error}\n')

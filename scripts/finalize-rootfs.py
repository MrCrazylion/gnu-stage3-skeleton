#!/usr/bin/env python3
"""Finalize an offline rootfs after Catalyst exits. Never operates on host /."""
import argparse
import glob
import json
from pathlib import Path
import re
import shlex
import shutil

PACKAGES = ('sys-apps/portage', 'app-admin/eselect', 'app-portage/portage-utils')
PATTERNS = '''
etc/os-release usr/lib/os-release etc/gentoo-release etc/issue*
usr/share/factory/etc/issue* usr/share/baselayout/issue*
etc/portage etc/env.d etc/profile.env etc/csh.env
var/lib/portage var/log/portage var/log/emerge*.log var/cache/edb
var/db/pkg var/db/repos var/cache/binpkgs var/cache/distfiles var/tmp/portage
usr/lib/portage usr/lib64/portage usr/share/portage usr/share/eselect
usr/lib/python*/site-packages/portage* usr/lib64/python*/site-packages/portage*
usr/lib/python*/site-packages/_emerge usr/lib64/python*/site-packages/_emerge
usr/lib/sysusers.d/*portage* usr/lib/tmpfiles.d/portage-*.conf
usr/lib/systemd/system-generators/gentoo-local-generator
usr/lib/systemd/system-environment-generators/10-gentoo-path
etc/bash/bashrc.d/10-gentoo-*.bash etc/environment.d/10-gentoo-env.conf
usr/lib/sysctl.d/60-gentoo.conf usr/lib/udev/rules.d/40-gentoo.rules
usr/share/misc/magic/gentoo usr/share/nano/gentoo.nanorc
usr/lib/gentoo var/lib/gentoo
'''.split()
TOOLS = '''emerge emerge-webrsync emirrordist ebuild egencache portageq quickpkg
repoman dispatch-conf etc-update fixpackages regenworld env-update eselect
q qatom qcheck qdepends qfile qgrep qkeyword qlist qlop qmanifest qmerge qpkg
qsize quse qtbz2 qwhich qxpak'''.split()


class Root:
    def __init__(self, path):
        supplied = Path(path).absolute()
        if supplied.is_symlink():
            raise ValueError('rootfs argument must not be a symlink')
        self.root = supplied.resolve(strict=True)
        if self.root == Path('/') or not (self.root / 'etc/passwd').is_file():
            raise ValueError('expected an extracted rootfs, never host /')
        self.removed = []

    def checked(self, path):
        p = Path(path)
        # Check the parent, not the leaf: removing an absolute symlink is safe.
        p.parent.resolve().relative_to(self.root)
        if p == self.root:
            raise ValueError('refusing to remove rootfs itself')
        return p

    def remove(self, p):
        p = self.checked(p)
        if p.is_symlink() or p.is_file():
            p.unlink()
        elif p.is_dir():
            shutil.rmtree(p)
        else:
            return
        self.removed.append('/' + str(p.relative_to(self.root)))

    def write(self, relative, content, mode=0o644):
        p = self.checked(self.root / relative)
        if p.is_symlink():
            raise ValueError(f'refusing to overwrite symlink: {relative}')
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        p.chmod(mode)


def package_files(root):
    """Use CONTENTS without needing a working Portage/Python inside the image."""
    inventory, files = [], []
    db = root.root / 'var/db/pkg'
    if not db.is_dir():
        raise ValueError('package database missing; finalize before discarding it')
    for contents in sorted(db.glob('*/*/CONTENTS')):
        root.checked(contents)
        if contents.is_symlink():
            raise ValueError('CONTENTS must not be a symlink')
        cpv = str(contents.parent.relative_to(db))
        inventory.append(cpv)
        selected = any(re.fullmatch(re.escape(cp) + r'-\d.*', cpv) for cp in PACKAGES)
        if not selected:
            continue
        for line in contents.read_text().splitlines():
            if line.startswith('obj '):
                path = line[4:].rsplit(' ', 2)[0]
            elif line.startswith('sym '):
                path = line[4:].split(' -> ', 1)[0]
            else:
                continue  # Shared directories are not package-owned leaves.
            if not path.startswith('/') or '..' in Path(path).parts:
                raise ValueError(f'invalid CONTENTS path: {path}')
            # Preserve source attribution and license documentation.
            if path.startswith(('/usr/share/doc/', '/usr/share/licenses/')):
                continue
            files.append(root.root / path.lstrip('/'))
    return inventory, files


def login_path(root):
    """Retain selected compiler paths without executing generated shell code."""
    result = []
    p = root.checked(root.root / 'etc/profile.env')
    if p.is_symlink():
        raise ValueError('profile.env must not be a symlink')
    if p.is_file():
        for line in p.read_text().splitlines():
            match = re.fullmatch(r'(?:export\s+)?PATH=(.*)', line.strip())
            if not match:
                continue
            words = shlex.split(match[1])
            if len(words) != 1:
                raise ValueError('unsupported generated PATH')
            for item in words[0].split(':'):
                if not item.startswith('/') or not re.fullmatch(r'/[A-Za-z0-9_./+:-]+', item):
                    raise ValueError('unsafe or dynamic generated PATH')
                if re.search(r'gentoo|portage|eselect', item, re.I):
                    continue
                if item not in result:
                    result.append(item)
    for item in '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'.split(':'):
        if item not in result:
            result.append(item)
    return ':'.join(result)


def clean_accounts(root, relative):
    p = root.checked(root.root / relative)
    if not p.exists():
        return
    if p.is_symlink():
        raise ValueError(f'account file is a symlink: {relative}')
    mode = p.stat().st_mode & 0o777
    lines = []
    for line in p.read_text().splitlines():
        fields = line.split(':')
        if fields[0] == 'portage':
            continue
        if p.name in ('group', 'gshadow') and len(fields) == 4:
            columns = (2, 3) if p.name == 'gshadow' else (3,)
            for col in columns:
                fields[col] = ','.join(x for x in fields[col].split(',') if x != 'portage')
        lines.append(':'.join(fields))
    root.write(relative, '\n'.join(lines) + '\n', mode)


def finalize(path, report):
    root = Root(path)
    report = Path(report).absolute()
    if report.resolve().is_relative_to(root.root):
        raise ValueError('report must be outside the distributable rootfs')
    inventory, owned = package_files(root)
    path_value = login_path(root)
    targets = set(owned)
    patterns = list(PATTERNS)
    for tool in TOOLS:
        patterns += [f'usr/bin/{tool}', f'usr/sbin/{tool}',
                     f'usr/lib/python-exec/python*/{tool}',
                     f'usr/share/man/man?/{tool}.*',
                     f'usr/share/bash-completion/completions/{tool}']
    for pattern in patterns:
        targets.update(Path(p) for p in glob.glob(str(root.root / pattern)))
    # Preflight all deletion parents before making any changes.
    for p in targets:
        root.checked(p)
    for p in sorted(targets, key=lambda x: (-len(x.parts), str(x))):
        root.remove(p)
    for directory in ('etc', 'usr/share/baselayout'):
        for name in ('passwd', 'shadow', 'group', 'gshadow'):
            clean_accounts(root, f'{directory}/{name}')
    # Remove old account backups too: they can restore the removed account.
    for name in ('passwd-', 'shadow-', 'group-', 'gshadow-'):
        root.remove(root.root / 'etc' / name)
    root.write('etc/profile', f'''# Base login environment; local extensions go in /etc/profile.d.
export PATH='{path_value}'
for profile_script in /etc/profile.d/*.sh; do
    [ ! -r "$profile_script" ] || . "$profile_script"
done
unset profile_script
''')
    # Do not inherit a build-machine identity.
    root.remove(root.root / 'etc/machine-id')
    root.write('etc/machine-id', '')
    root.remove(root.root / 'var/lib/dbus/machine-id')
    root.remove(root.root / 'var/lib/systemd/random-seed')
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps({'target': 'amd64-glibc-systemd',
        'seed_packages': inventory, 'removed': sorted(root.removed),
        'scope': 'Debranding and build-tool removal, not proof of upstream purity.'}, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rootfs')
    parser.add_argument('--report', required=True)
    args = parser.parse_args()
    finalize(args.rootfs, args.report)

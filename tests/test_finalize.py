import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('finalize', Path(__file__).resolve().parents[1] / 'scripts/finalize-rootfs.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class FinalizeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name).resolve()
        self.root = self.base / 'root'
        self.root.mkdir()
        self.report = self.base / 'report.json'
        self.put('etc/passwd', 'root:x:0:0:root:/root:/bin/bash\nportage:x:250:250:portage:/var/empty:/bin/false\n')
        self.put('etc/group', 'root:x:0:root\nwheel:x:10:root,portage\nportage:x:250:portage\n')
        self.put('etc/shadow', 'root:*:::::::\nportage:*:::::::\n').chmod(0o600)
        self.put('etc/gshadow', 'wheel:!:portage:root,portage\n')
        self.put('var/db/pkg/sys-apps/portage-3.0/CONTENTS',
                 'obj /usr/bin/new-portage-helper hash 0\n'
                 'sym /usr/bin/helper-link -> /usr/bin/new-portage-helper 0\n'
                 'obj /usr/share/doc/portage/COPYING hash 0\n')
        self.put('usr/bin/new-portage-helper', 'owned')
        (self.root / 'usr/bin/helper-link').symlink_to('/usr/bin/new-portage-helper')
        self.put('usr/share/doc/portage/COPYING', 'original attribution')
        self.put('usr/lib/os-release', 'ID=gentoo\n')
        (self.root / 'etc/os-release').symlink_to('../usr/lib/os-release')
        self.put('etc/profile.env', 'export PATH="/usr/bin:/usr/x86_64-pc-linux-gnu/gcc-bin/15"\n')
        self.put('etc/ld.so.conf', 'include /etc/ld.so.conf.d/*.conf\n')
        self.put('usr/lib/systemd/systemd', 'systemd fixture')
        self.put('etc/machine-id', 'seed identity')

    def put(self, path, content):
        p = self.root / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        return p

    def run_finalize(self):
        mod.finalize(self.root, self.report)

    def test_full_fixture(self):
        self.run_finalize()
        for path in ('etc/os-release', 'usr/lib/os-release', 'etc/profile.env',
                     'var/db/pkg', 'usr/bin/new-portage-helper', 'usr/bin/helper-link'):
            self.assertFalse((self.root / path).exists())
            self.assertFalse((self.root / path).is_symlink())
        for name in ('passwd', 'group', 'shadow', 'gshadow'):
            self.assertNotIn('portage', (self.root / 'etc' / name).read_text())
        self.assertEqual((self.root / 'etc/shadow').stat().st_mode & 0o777, 0o600)
        self.assertIn('/usr/x86_64-pc-linux-gnu/gcc-bin/15', (self.root / 'etc/profile').read_text())
        self.assertEqual((self.root / 'etc/machine-id').read_text(), '')
        self.assertEqual((self.root / 'usr/share/doc/portage/COPYING').read_text(), 'original attribution')
        self.assertTrue((self.root / 'usr/lib/systemd/systemd').exists())
        self.assertIn('include', (self.root / 'etc/ld.so.conf').read_text())
        self.assertIn('sys-apps/portage-3.0', json.loads(self.report.read_text())['seed_packages'])

    def test_absolute_identity_symlink_unlinked_not_followed(self):
        (self.root / 'etc/os-release').unlink()
        external = self.base / 'outside'
        external.write_text('keep')
        (self.root / 'etc/os-release').symlink_to(external)
        self.run_finalize()
        self.assertEqual(external.read_text(), 'keep')

    def test_symlinked_parent_escape_rejected(self):
        external = self.base / 'outside'
        external.mkdir()
        (external / 'keep').write_text('keep')
        (self.root / 'var').rename(self.root / 'saved-var')
        (self.root / 'var').symlink_to(external)
        with self.assertRaises(ValueError):
            self.run_finalize()
        self.assertEqual((external / 'keep').read_text(), 'keep')

    def test_generated_path_is_never_executed(self):
        sentinel = self.base / 'executed'
        self.put('etc/profile.env', f'export PATH="/usr/bin:$(touch {sentinel})"\n')
        with self.assertRaises(ValueError):
            self.run_finalize()
        self.assertFalse(sentinel.exists())
        self.assertTrue((self.root / 'usr/lib/os-release').exists())

    def test_host_root_rejected(self):
        with self.assertRaises(ValueError):
            mod.Root('/')

    def test_report_cannot_reintroduce_metadata_inside_image(self):
        with self.assertRaises(ValueError):
            mod.finalize(self.root, self.root / 'report.json')

    def test_package_names_do_not_match_unrelated_prefixes(self):
        self.put('var/db/pkg/sys-apps/portage-extra-1/CONTENTS', 'obj /usr/bin/unrelated hash 0\n')
        self.put('usr/bin/unrelated', 'keep')
        self.run_finalize()
        self.assertTrue((self.root / 'usr/bin/unrelated').exists())

    def test_missing_database_rejected(self):
        import shutil
        shutil.rmtree(self.root / 'var/db/pkg')
        with self.assertRaises(ValueError):
            self.run_finalize()


if __name__ == '__main__':
    unittest.main()

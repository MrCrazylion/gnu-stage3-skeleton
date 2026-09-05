import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('find_stage4', Path(__file__).resolve().parents[1] / 'scripts/find-stage4.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class FindStage4Tests(unittest.TestCase):
    def test_formats_and_sidecars(self):
        for suffix in ('.tar.bz2', '.tar.xz', '.tar.gz', '.tar'):
            with self.subTest(suffix=suffix), tempfile.TemporaryDirectory() as d:
                root = Path(d)
                archive = root / 'default' / ('stage4-amd64-skeleton' + suffix)
                archive.parent.mkdir()
                archive.touch()
                Path(str(archive) + '.DIGESTS').touch()
                (root / 'stage3-amd64-seed.tar.xz').touch()
                self.assertEqual(mod.find_stage4(root), archive)

    def test_ambiguous_archives_fail(self):
        with tempfile.TemporaryDirectory() as d:
            for suffix in ('.tar.xz', '.tar.bz2'):
                (Path(d) / ('stage4-amd64-skeleton' + suffix)).touch()
            with self.assertRaisesRegex(ValueError, 'found 2'):
                mod.find_stage4(d)

    def test_missing_archive_fails(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError, 'found 0'):
                mod.find_stage4(d)


if __name__ == '__main__':
    unittest.main()

import hashlib
import tempfile
import unittest
from pathlib import Path
from agent_doctor import WorkspaceJail, PathBoundaryError, diagnose
from agent_doctor.diagnostic import main


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.jail = WorkspaceJail(self.root)

    def test_paths(self):
        self.assertEqual(self.jail.resolve("nested/new.txt"), self.root / "nested/new.txt")
        for path in ("../escape", str(self.root.parent / "outside"), "/home/agent/x", "home/x", "C:relative", "memory.json:stream"):
            with self.subTest(path=path), self.assertRaises(PathBoundaryError):
                self.jail.resolve(path)
        with self.assertRaises(PathBoundaryError):
            WorkspaceJail(Path(self.root.anchor))

    def test_symlink_escape(self):
        with tempfile.TemporaryDirectory() as outside:
            link = self.root / "link"
            try:
                link.symlink_to(outside, target_is_directory=True)
            except OSError:
                self.skipTest("Symlink creation requires OS permission")
            with self.assertRaises(PathBoundaryError):
                self.jail.resolve("link/escape.txt")

    def test_read_only_diagnostics(self):
        target = self.root / "memory.json"
        data = b'{"error": "failed", "path": "/home/agent"}'
        target.write_bytes(data)
        report = diagnose(self.root, "memory.json", expected_sha256="0" * 64)
        self.assertEqual({f["code"] for f in report["findings"]}, {"error_markers", "home_path_reference", "context_changed"})
        self.assertEqual(target.read_bytes(), data)
        self.assertEqual(report["sha256"], hashlib.sha256(data).hexdigest())
        self.assertNotIn("failed", str(report))
        with self.assertRaises(ValueError):
            diagnose(self.root, "memory.json", max_bytes=2)

    def test_integrity_and_cli(self):
        target = self.root / "clean.json"
        target.write_bytes(b"{}")
        self.assertEqual(diagnose(self.root, target, expected_sha256=hashlib.sha256(b"{}").hexdigest())["findings"], [])
        self.assertEqual(main(["clean.json", "--workspace", str(self.root)]), 0)
        target.write_bytes(b"{invalid")
        self.assertEqual(main(["clean.json", "--workspace", str(self.root)]), 1)
        target.write_bytes(b"\xff")
        self.assertIn("invalid_utf8", {f["code"] for f in diagnose(self.root, target)["findings"]})
        with self.assertRaises(SystemExit) as caught:
            main(["../escape", "--workspace", str(self.root)])
        self.assertEqual(caught.exception.code, 2)


if __name__ == "__main__":
    unittest.main()

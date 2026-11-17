"""Run offline regression tests without opening project credentials or the network."""

import argparse
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT.parent
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]
_is_file = Path.is_file
_mkdir = os.mkdir
TEMP_ROOT = ROOT / "data" / "phase2_test_tmp"


def protected(path):
    try:
        candidate = Path(path).resolve()
    except (TypeError, ValueError, OSError):
        return False
    return (TEMP_ROOT not in candidate.parents
            and candidate.name in {".env", "connections.private.json"}
            and PROJECT_ROOT in candidate.parents)


def offline_audit(event, args):
    if event == "open" and protected(args[0]):
        raise PermissionError("Project credential access is forbidden in offline checks.")
    if event in {"socket.connect", "socket.getaddrinfo"}:
        raise RuntimeError("Network access is forbidden in offline checks.")


def test_mkdir(path, mode=0o777, *, dir_fd=None):
    # Windows' special 0o700 ACL excludes the sandbox token. Keep temporary
    # synthetic fixtures in this authorized scratch directory with normal ACLs.
    if TEMP_ROOT in Path(path).resolve().parents and mode == 0o700:
        mode = 0o777
    return _mkdir(path, mode, dir_fd=dir_fd)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pattern", default="test_*.py")
    options = parser.parse_args()
    TEMP_ROOT.mkdir(parents=True, exist_ok=True)
    tempfile.tempdir = str(TEMP_ROOT)
    sys.addaudithook(offline_audit)
    # Temporary synthetic credentials in existing tests remain usable. Only real
    # project credential files are hidden; no configuration is changed on disk.
    with patch.object(Path, "is_file", lambda path: False if protected(path) else _is_file(path)), \
         patch.object(os, "mkdir", test_mkdir):
        suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern=options.pattern)
        result = unittest.TextTestRunner(verbosity=1).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())

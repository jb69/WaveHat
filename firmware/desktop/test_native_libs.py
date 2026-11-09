"""Builds the firmware's small platform-free libraries natively and runs their tests.

    python3 -m unittest -v test_native_libs

  lib/n2k       NMEA 2000 decoding: hand-built frames (native/n2k_test.cpp)
  lib/underway  the underway flag: SOG patterns at anchor and motoring (native/underway_test.cpp)
"""
import os
import shutil
import subprocess
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(HERE, "..", "lib")


def build_and_run(test, lib, sources=()):
    with tempfile.TemporaryDirectory() as tmp:
        exe = os.path.join(tmp, "test")
        libdir = os.path.join(LIB, lib, "src")
        subprocess.run(["c++", "-std=c++17", "-O2", "-Wall", "-Wextra", "-Werror", "-I", libdir, "-o", exe,
                        os.path.join(HERE, "native", test)] + [os.path.join(libdir, s) for s in sources],
                       check=True)
        return subprocess.run([exe], capture_output=True, text=True)


@unittest.skipUnless(shutil.which("c++"), "no host C++ compiler")
class NativeLibs(unittest.TestCase):
    def test_n2k(self):
        run = build_and_run("n2k_test.cpp", "n2k", ["n2k.cpp"])
        self.assertEqual(run.returncode, 0, run.stdout)

    def test_underway(self):
        run = build_and_run("underway_test.cpp", "underway")
        self.assertEqual(run.returncode, 0, run.stdout)


if __name__ == "__main__":
    unittest.main()

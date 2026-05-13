"""Smoke tests: package importable, CLI wired, config sane."""

import subprocess
import sys


def test_import():
    import luthea
    assert luthea.__version__


def test_cli_help():
    res = subprocess.run([sys.executable, "-m", "luthea.cli", "--help"],
                         capture_output=True, text=True)
    assert res.returncode == 0


def test_config_constants():
    from luthea import config
    assert config.YEAR_START == 2016
    assert config.YEAR_END == 2025
    assert config.SUBPIXELS_PER_LST == 9

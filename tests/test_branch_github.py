#!/usr/bin/env python3
import unittest.mock
from pathlib import Path
from typing import BinaryIO

import conftest

from nix_update.version import fetch_latest_version
from nix_update.version.version import VersionPreference

TEST_ROOT = Path(__file__).parent.resolve()


def fake_urlopen(url: str) -> BinaryIO:
    return open(TEST_ROOT.joinpath("test_branch_github.atom"), "rb")


def test_branch_github(helpers: conftest.Helpers) -> None:
    with unittest.mock.patch("urllib.request.urlopen", fake_urlopen):
        assert (
            fetch_latest_version(
                "https://github.com/Mic92/nix-update",
                VersionPreference.BRANCH,
                "(.*)",
                "master",
            ).number
            == "unstable-2021-12-13"
        )

#!/usr/bin/env python3
import os
import subprocess
import unittest.mock
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, BinaryIO

import conftest
from test_branch_git import create_dummy_commit, dummy_git_repo

from nix_update.version import fetch_latest_version
from nix_update.version.version import VersionPreference

TEST_ROOT = Path(__file__).parent.resolve()


atom_feed_log_format = """\
  <entry>
    <link href="/%H"/>
    <updated>%cd</updated>
  </entry>"""


def create_dummy_commit_feed(tmp: str, branch: str) -> None:
    with open(Path(tmp) / f"{branch}.atom", "wb") as feed:
        feed.write(
            b"""\
<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
"""
        )
        feed.flush()
        env = os.environ.copy()
        env["TZ"] = "UTC"
        subprocess.run(
            [
                "git",
                "-C",
                tmp,
                "log",
                "--date=format-local:%FT%TZ",
                f"--format=format:{atom_feed_log_format}",
                "--max-count=20",
                branch,
            ],
            env=env,
            stdout=feed,
            check=True,
        )
        feed.write(
            b"""
</feed>
"""
        )


def fake_urlopen(url: str) -> BinaryIO:
    feed = url.rsplit("/", 1)[-1]
    return open(Path(os.environ["GIT_FAKE_REPO"]) / feed, "rb")


def fail_get_latest_snapshots_from_git(*args: Any, **kwargs: Any) -> None:
    raise AssertionError(
        "all the necessary commits are in the atom feed, so we must not fetch the git"
    )


def test_branch_github(helpers: conftest.Helpers) -> None:
    with dummy_git_repo() as tmp:
        create_dummy_commit_feed(tmp, "master")
        create_dummy_commit_feed(tmp, "short")

        os.environ["GIT_FAKE_REPO"] = tmp

        with unittest.mock.patch("urllib.request.urlopen", fake_urlopen):
            # add git script that overwrites `git remote add` to PATH
            os.environ["ORIG_PATH"] = os.environ["PATH"]
            os.environ["PATH"] = (
                str(helpers.root().joinpath("bin")) + ":" + os.environ["PATH"]
            )

            assert (
                fetch_latest_version(
                    "https://github.com/_/_", VersionPreference.BRANCH, "(.*)", "master"
                ).number
                == "unstable-2038-01-19"
            )

            # get_latest_snapshot_from_git is unnecessary
            with unittest.mock.patch(
                "nix_update.version.git.get_latest_snapshots_from_git",
                fail_get_latest_snapshots_from_git,
            ):
                assert (
                    fetch_latest_version(
                        "https://github.com/_/_",
                        VersionPreference.BRANCH,
                        "(.*)",
                        "short",
                    ).number
                    == "unstable-1970-01-02"
                )

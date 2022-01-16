#!/usr/bin/env python3
import os
import subprocess
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, BinaryIO, Iterator
from urllib.parse import quote

import conftest

from nix_update.version import fetch_latest_version
from nix_update.version.version import VersionPreference

TEST_ROOT = Path(__file__).parent.resolve()


def create_dummy_commit(tmp: str, date: datetime) -> None:
    datestr = date.strftime("%FT%TZ")
    with open(Path(tmp) / "date.txt", "w", encoding="utf-8") as fp:
        fp.write(datestr)
        fp.write("\n")
    subprocess.run(["git", "-C", tmp, "add", "date.txt"], check=True)
    env = os.environ.copy()
    env["GIT_AUTHOR_DATE"] = datestr
    env["GIT_COMMITTER_DATE"] = datestr
    subprocess.run(
        [
            "git",
            "-C",
            tmp,
            "-c",
            "user.name=dummy",
            "-c",
            "user.email=dummy@localhost",
            "commit",
            "--quiet",
            "--message=some message",
        ],
        env=env,
        check=True,
    )


@contextmanager
def dummy_git_repo() -> Iterator[str]:
    """Create a temporary git repository with a couple of commits and their
    atom feeds.
    """

    with TemporaryDirectory(suffix=".git") as tmp:
        subprocess.run(
            ["git", "-C", tmp, "init", "--quiet", "--initial-branch", "master"],
            check=True,
        )

        create_dummy_commit(tmp, datetime(1970, 1, 1))
        date = datetime(1970, 1, 2)
        for _ in range(10):
            create_dummy_commit(tmp, date)
            date += timedelta(minutes=10)
        subprocess.run(["git", "-C", tmp, "branch", "short"], check=True)
        date = datetime(1970, 1, 3)
        for _ in range(10):
            create_dummy_commit(tmp, date)
            date += timedelta(minutes=10)
        date = datetime(2038, 1, 19)
        for _ in range(90):
            create_dummy_commit(tmp, date)
            date += timedelta(minutes=10)

        yield tmp


def test_branch_git(helpers: conftest.Helpers) -> None:
    with dummy_git_repo() as git_dir:
        git_url = "file://" + quote(git_dir)

        assert (
            fetch_latest_version(
                git_url, VersionPreference.BRANCH, "(.*)", "master"
            ).number
            == "unstable-2038-01-19"
        )

        assert (
            fetch_latest_version(
                git_url, VersionPreference.BRANCH, "(.*)", "short"
            ).number
            == "unstable-1970-01-02"
        )

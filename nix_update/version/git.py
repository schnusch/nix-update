from tempfile import TemporaryDirectory
from typing import List
from urllib.parse import ParseResult, urlunparse

from ..utils import run
from .version import Version


def init_git(git_dir: str, url: str) -> None:
    run(["git", "init", "-q", git_dir], stdout=None)
    run(
        [
            "git",
            "-C",
            git_dir,
            "remote",
            "add",
            "origin",
            url,
        ],
        stdout=None,
    )


def get_latest_snapshots_from_git(
    git_dir: str,
    branch: str,
    increment: int = 20,
    initial: int = 20,
) -> List[Version]:
    """Even though it's called get_latest_snapshots_from_git with snapshots
    with an S it will actually only return zero or one Versions, so the git
    repo is only fetched as shallow as possible.
    """
    run(
        [
            "git",
            "-C",
            git_dir,
            "fetch",
            f"--depth={initial + increment}",
            "origin",
            branch,
        ],
        stdout=None,
    )
    # TODO use non-shallow fetch for dumb HTTP
    while True:
        log = run(
            [
                "git",
                "-C",
                git_dir,
                "log",
                "--format=%cd %H",
                "--date=format-local:%F",
                "--max-count=1",
                "FETCH_HEAD",
            ],
            extra_env={"TZ": "UTC"},
        ).stdout.strip()
        if log:
            date, commit = log.split(maxsplit=1)
            return [Version(f"unstable-{date}", rev=commit)]
        if (
            run(
                ["git", "-C", git_dir, "rev-parse", "--is-shallow-repository"]
            ).stdout.strip()
            == "false"
        ):
            return []
        run(
            [
                "git",
                "-C",
                git_dir,
                "fetch",
                f"--deepen={increment}",
                "origin",
                branch,
            ],
            stdout=None,
        )


def fetch_git_snapshots(url: ParseResult, branch: str) -> List[Version]:
    with TemporaryDirectory(suffix=".git") as tmp:
        init_git(tmp, urlunparse(url))
        return get_latest_snapshots_from_git(tmp, branch)

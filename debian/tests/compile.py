#!/usr/bin/python3
"""Build a trivial program using the drpm library."""

import argparse
import dataclasses
import os
import pathlib
import shlex
import subprocess
import sys
import tempfile

from typing import Dict


EXPECTED = [
    "make standard",
    "read standard",
    "standard",
    "make options",
    "make rpm-only",
    "read rpm-only",
    "rpm-only",
    "fine",
]


@dataclasses.dataclass(frozen=True)
class Config:
    """Runtime configuration."""

    source: pathlib.Path
    testdir: pathlib.Path

    env: Dict[str, str]

    tempd: pathlib.Path
    obj: pathlib.Path
    program: pathlib.Path


def do_compile(cfg: Config) -> None:
    """Compile the test program."""
    print("Fetching the C compiler flags for drpm")
    cflags = (
        subprocess.check_output(
            ["pkg-config", "--cflags", "drpm"], shell=False, env=cfg.env
        )
        .decode("UTF-8")
        .rstrip("\r\n")
    )
    if "\r" in cflags or "\n" in cflags:
        sys.exit(f"`pkg-config --cflags drpm` returned {cflags!r}")

    if cfg.obj.exists():
        sys.exit(f"Did not expect {cfg.obj} to exist")
    cmd = (
        ["cc", "-c", "-o", str(cfg.obj), "-Wall", "-W", "-Wextra", "-Werror"]
        + shlex.split(cflags)
        + [str(cfg.source)]
    )
    print(f"Running {cmd!r}")
    subprocess.check_call(cmd, shell=False, env=cfg.env)
    if not cfg.obj.is_file():
        sys.exit(f"{cmd!r} did not create the {cfg.obj} file")

    print("Fetching the C linker flags and libraries for drpm")
    libs = (
        subprocess.check_output(
            ["pkg-config", "--libs", "drpm"], shell=False, env=cfg.env
        )
        .decode("UTF-8")
        .rstrip("\r\n")
    )
    if "\r" in libs or "\n" in libs:
        sys.exit(f"`pkg-config --libs drpm` returned {libs!r}")

    if cfg.program.exists():
        sys.exit(f"Did not expect {cfg.program} to exist")
    cmd = ["cc", "-o", str(cfg.program), str(cfg.obj)] + shlex.split(libs)
    print(f"Running {cmd!r}")
    subprocess.check_call(cmd, shell=False, env=cfg.env)
    if not cfg.program.is_file():
        sys.exit(f"{cmd!r} did not create the {cfg.program} file")
    if not os.access(cfg.program, os.X_OK):
        sys.exit(f"Not an executable file: {cfg.program}")
    print(f"Looks like we got {cfg.program}")


def parse_args(dirname: str) -> Config:
    """Parse the command-line options."""
    parser = argparse.ArgumentParser(prog="compile")
    parser.add_argument(
        "-s",
        "--source",
        type=str,
        required=True,
        help="path to the source file to compile",
    )
    parser.add_argument(
        "-t",
        "--testdir",
        type=str,
        required=True,
        help="path to the directory containing the test RPM packages",
    )

    args = parser.parse_args()

    env = dict(os.environ)
    env["LC_ALL"] = "C.UTF-8"
    env["LANGUAGES"] = ""

    source = pathlib.Path(args.source).absolute()
    if source.suffixes != [".c"]:
        sys.exit("The source file should only have a *.c extension.")
    progname = source.with_suffix("").name

    tempd = pathlib.Path(dirname).absolute()
    program = tempd / progname
    return Config(
        source=pathlib.Path(args.source),
        testdir=pathlib.Path(args.testdir),
        env=env,
        tempd=tempd,
        obj=program.with_suffix(".o"),
        program=program,
    )


def do_run(cfg: Config) -> None:
    """Run the compiled program, examine the result."""
    command = [
        cfg.program,
        cfg.testdir / "cmocka-old.rpm",
        cfg.testdir / "cmocka-new.rpm",
        cfg.tempd,
    ]
    print(f"Running {command!r}")
    lines = (
        subprocess.check_output(command, shell=False, env=cfg.env,)
        .decode("UTF-8")
        .splitlines()
    )
    print(f"Got {lines!r}")

    if lines != EXPECTED:
        sys.exit(f"The test program output {lines!r} instead of {EXPECTED!r}")


def main() -> None:
    """Parse command-line options, compile a program, run it."""
    with tempfile.TemporaryDirectory() as dirname:
        cfg = parse_args(dirname)
        do_compile(cfg)
        do_run(cfg)
        print("Seems fine!")


if __name__ == "__main__":
    main()

import argparse
import pathlib
import sys

from .snapshot import dump
from .restore import restore, verify_only


def parse() -> argparse.Namespace:
    p = argparse.ArgumentParser("quicksave")
    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("dump", help="dump <pid> …")
    d.add_argument("pid", nargs="+", type=int)

    r = sub.add_parser("restore", help="restore <qsnap>")
    r.add_argument("file", type=str)
    r.add_argument("--verify", action="store_true")
    return p.parse_args()


def main() -> None:
    ns = parse()
    if ns.cmd == "dump":
        dump(ns.pid)
    elif ns.cmd == "restore":
        path = pathlib.Path(ns.file).expanduser()
        ok = verify_only(path) if ns.verify else restore(path)
        sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
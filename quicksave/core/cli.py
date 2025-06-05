import argparse
import sys
import pathlib

from .snapshot import dump
from .restore import restore, verify_only
from .compat import check_compatibility, explain_compat
from .proctree import get_process_tree

def parse() -> argparse.Namespace:
    p = argparse.ArgumentParser("quicksave")
    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("dump", help="dump <pid> …")
    d.add_argument("pid", nargs="+", type=int)
    d.add_argument("--compat", action="store_true", help="check compatibility before dump")

    r = sub.add_parser("restore", help="restore <qsnap>")
    r.add_argument("file", type=str)
    r.add_argument("--verify", action="store_true")
    return p.parse_args()

def main() -> None:
    ns = parse()
    if ns.cmd == "dump":
        all_pids = []
        for pid in ns.pid:
            all_pids += get_process_tree(pid)
        if ns.compat:
            report = check_compatibility(all_pids)
            print(explain_compat(report))
            if ("通过" not in explain_compat(report)):
                print("强制快照风险较高，是否继续？(y/N): ", end="")
                if input().strip().lower() != "y":
                    sys.exit(1)
        dump(ns.pid)
    elif ns.cmd == "restore":
        path = pathlib.Path(ns.file).expanduser()
        ok = verify_only(path) if ns.verify else restore(path)
        sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""fsize - Find large files and directories. Disk usage at a glance.

Usage:
    fsize.py [PATH]                     Top 10 largest items in PATH (default: .)
    fsize.py PATH --depth 2             Recurse 2 levels deep
    fsize.py PATH --min 100M            Only show items >= 100MB
    fsize.py PATH --ext .log            Only show files with extension
    fsize.py --summary PATH             Quick disk summary
"""

import os, sys, argparse
from pathlib import Path

UNITS = [("TB", 1<<40), ("GB", 1<<30), ("MB", 1<<20), ("KB", 1<<10)]

def fmt_size(b: int) -> str:
    for name, thresh in UNITS:
        if b >= thresh:
            return f"{b/thresh:.1f} {name}"
    return f"{b} B"

def parse_size(s: str) -> int:
    s = s.strip().upper()
    for name, mult in [("TB",1<<40),("GB",1<<30),("G",1<<30),("MB",1<<20),("M",1<<20),("KB",1<<10),("K",1<<10)]:
        if s.endswith(name):
            return int(float(s[:-len(name)]) * mult)
    return int(s)

def dir_size(path: Path) -> int:
    total = 0
    try:
        for f in path.rglob("*"):
            try:
                if f.is_file(follow_symlinks=False):
                    total += f.stat().st_size
            except (PermissionError, OSError):
                pass
    except (PermissionError, OSError):
        pass
    return total

def scan(root: Path, depth: int = 1, min_bytes: int = 0, ext: str = None) -> list:
    items = []
    try:
        for entry in sorted(root.iterdir()):
            try:
                if entry.name.startswith('.') and entry.is_dir():
                    # Still include but don't skip hidden dirs
                    pass
                if ext and entry.is_file() and entry.suffix != ext:
                    continue
                if entry.is_file(follow_symlinks=False):
                    size = entry.stat().st_size
                elif entry.is_dir(follow_symlinks=False):
                    size = dir_size(entry)
                else:
                    continue
                if size >= min_bytes:
                    items.append((size, entry))
            except (PermissionError, OSError):
                pass
    except (PermissionError, OSError):
        pass
    return sorted(items, reverse=True)

def cmd_scan(root: Path, n: int, depth: int, min_bytes: int, ext: str):
    items = scan(root, depth, min_bytes, ext)
    if not items:
        print("No items found")
        return
    total = sum(s for s, _ in items)
    for size, path in items[:n]:
        kind = "📁" if path.is_dir() else "📄"
        pct = (size / total * 100) if total else 0
        print(f"  {kind} {fmt_size(size):>10s}  ({pct:4.1f}%)  {path.name}")
    print(f"\n  Total: {fmt_size(total)} across {len(items)} items")

def cmd_summary(root: Path):
    total_files = 0
    total_size = 0
    by_ext = {}
    try:
        for f in root.rglob("*"):
            try:
                if f.is_file(follow_symlinks=False):
                    s = f.stat().st_size
                    total_files += 1
                    total_size += s
                    ext = f.suffix.lower() or "(none)"
                    by_ext[ext] = by_ext.get(ext, 0) + s
            except (PermissionError, OSError):
                pass
    except (PermissionError, OSError):
        pass
    
    print(f"  Path: {root}")
    print(f"  Files: {total_files:,}")
    print(f"  Total: {fmt_size(total_size)}")
    print(f"\n  Top extensions:")
    for ext, size in sorted(by_ext.items(), key=lambda x: -x[1])[:10]:
        print(f"    {ext:10s} {fmt_size(size):>10s}")

def main():
    parser = argparse.ArgumentParser(description="Find large files/dirs")
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument("-n", type=int, default=15)
    parser.add_argument("--depth", type=int, default=1)
    parser.add_argument("--min", dest="min_size", default="0")
    parser.add_argument("--ext", default=None)
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()

    root = Path(args.path).resolve()
    if args.summary:
        cmd_summary(root)
    else:
        cmd_scan(root, args.n, args.depth, parse_size(args.min_size), args.ext)

if __name__ == "__main__":
    main()

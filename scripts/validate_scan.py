#!/usr/bin/env python3
"""Validate a shared scan's manifest, contained paths, map and posed-depth data."""
import argparse
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from jetson_realsense_perception.scan_contract import ScanContractError, validate_scan

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('scan',type=Path)
    args=parser.parse_args()
    try:
        m=validate_scan(args.scan)
    except (ScanContractError,OSError,ValueError) as exc:
        print(f'INVALID: {exc}',file=sys.stderr);return 2
    print(f'VALID v1 {m["source"]} package: {len(m["files"])} assets; geometry quality not assessed')
    return 0

if __name__=='__main__': raise SystemExit(main())

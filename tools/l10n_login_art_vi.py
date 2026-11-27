#!/usr/bin/env python3
"""Thin Vietnamese wrapper for the shared English/Vietnamese login renderer."""

import argparse
import json
from pathlib import Path

import l10n_ui_art_fix as shared


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kr', type=Path, required=True)
    parser.add_argument('--font', type=Path, help='Accepted for compatibility; VI now uses DejaVu Sans')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(argv)
    if args.out.resolve() == args.kr.resolve() or args.kr.resolve() in args.out.resolve().parents:
        parser.error('--out must be outside the KR client')
    args.out.mkdir(parents=True, exist_ok=True)
    _, receipt = shared.render_login(args.kr, None, args.out, lang='vi')
    (args.out / 'receipt.json').write_text(
        json.dumps({'review': 'pending', 'entries': receipt},
                   ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'entries': len(receipt), 'out': str(args.out)}, ensure_ascii=False))


if __name__ == '__main__':
    main()

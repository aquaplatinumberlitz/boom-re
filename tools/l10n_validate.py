#!/usr/bin/env python3
"""Validate the generated catalog against its source cache and translation memories."""
import csv
import re
from collections import Counter

import l10n_extract as L

BAN = re.compile(r'(?<!\w)(xem|nhé|nhỉ|đấy|mũ|tớ|bọn|tao|mày|giao dịch|cửa hàng|nhặt)(?!\w)', re.I)


def read_csv(name, key=None):
    with (L.L10N / name).open(encoding='utf-8', newline='') as f:
        rows = list(csv.DictReader(f))
    if key is None:
        return rows
    assert len(rows) == len({r[key] for r in rows}), f'{name}: duplicate {key}'
    return {r[key]: r for r in rows}


def signature(s):
    return L.placeholders(s, True), L.PRINTF.findall(s)


def main():
    catalog = read_csv('catalog.csv')
    overrides = read_csv('tm_id.csv', 'id')
    read_csv('tm.csv', 'ko')
    source_rows = L.load_sources()
    sources = {r['id']: r for r in source_rows}
    assert Counter(r['id'] for r in catalog) == Counter(r['id'] for r in source_rows), 'catalog/source ID mismatch'
    assert [(r['id'], r['ko'], r['vi_base']) for r in catalog] == [(r['id'], r['ko'], r['vi_base']) for r in source_rows], 'source text changed'
    assert not (overrides.keys() - sources.keys()), 'unknown override ID'
    errors = []
    rewritten = inherited = 0
    for row in catalog:
        i = row['id']
        if BAN.search(row['vi']):
            errors.append(f'{i}: banned word {BAN.search(row["vi"]).group()}')
        if 'untranslated' in row['notes'].split(';'):
            errors.append(f'{i}: untranslated')
        override = overrides.get(i)
        if override and (row['vi'], row['status']) != (override['vi'], override['status']):
            errors.append(f'{i}: override not reflected in catalog')
        if 'nam_bo_rewrite' in row['notes'].split(';'):
            rewritten += 1
            if signature(row['vi_base']) != signature(row['vi']):
                errors.append(f'{i}: rewritten VN placeholders or line breaks changed')
        if 'ko_vi_base_placeholder_mismatch' in row['notes'].split(';'):
            inherited += 1
            if row['status'] != 'review':
                errors.append(f'{i}: inherited placeholder mismatch not marked review')
    # Confirm the three names explicitly settled during H032.
    names = {'전설의 파이터': 'Chiến binh huyền thoại',
             '화이트 엔젤': 'White Angel', '미스터포츈': 'Mister Fortune'}
    for ko, vi in names.items():
        matches = [r for r in catalog if r['ko'] == ko]
        if not matches or any(r['vi'] != vi for r in matches):
            errors.append(f'{ko}: expected {vi}')
    for error in errors:
        print(error)
    print(f'{len(catalog)} rows; statuses: {dict(Counter(r["status"] for r in catalog))}')
    print(f'{rewritten} nam_bo_rewrite overrides; {inherited} inherited placeholder discrepancies')
    print(f'{len(errors)} errors')
    return bool(errors)


if __name__ == '__main__':
    raise SystemExit(main())

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


def reviewed_signature(s):
    """Validate actual markup, not translated labels like <Mọi người>."""
    tokens = [x for x in L.PH.findall(s) if not x.startswith('<')]
    tags = re.findall(r'</?(?:font|br|img|b|i|u|span)(?:\s[^<>]*|\s*/?)>', s, re.I)
    # Consume %% as one token so its second percent cannot become "% p" in Vietnamese.
    printf = [m.group() for m in re.finditer(r'%%|' + L.PRINTF.pattern, s)
              if m.group() != '%%']
    return sorted(tokens), tags, printf, re.findall(r'\r\n|\r|\n', s), s.count('|')


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
        if 'ko_reviewed' in row['notes'].split(';'):
            if row['status'] != 'translated':
                errors.append(f'{i}: accepted review has wrong status')
            ko_sig, vi_sig = reviewed_signature(row['ko']), reviewed_signature(row['vi'])
            # Verse localization can add line breaks; the quiz manifest below checks
            # the exact authored verse. Keep checking format tokens and markup.
            if 'quiz_vi_localized' in row['notes'].split(';'):
                ko_sig, vi_sig = ko_sig[:3] + ko_sig[4:], vi_sig[:3] + vi_sig[4:]
            if ko_sig != vi_sig:
                errors.append(f'{i}: reviewed KO placeholders, tags or line endings changed')
        if 'ko_review_pending' in row['notes'].split(';') and row['status'] != 'review':
            errors.append(f'{i}: pending review has wrong status')
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
    by_id = {r['id']: r for r in catalog}
    quiz = read_csv('quiz_vi.csv', 'question_id')
    if len(quiz) != 15:
        errors.append('expected 15 localized wordplay questions')
    for qi, question in quiz.items():
        n = qi.rsplit('_', 1)[1]
        correct = int(question['correct_option'])
        if correct not in range(1, 5):
            errors.append(f'{qi}: invalid correct option')
            continue
        original = sources[f'q:CAQuiz_A5_{n}_{correct}']['ko'].strip()
        if original != question['ko_correct_answer']:
            errors.append(f'{qi}: original correct answer slot changed')
        if sources[qi]['ko'] != question['ko_question']:
            errors.append(f'{qi}: original question changed')
        if by_id[qi]['vi'] != question['vi_question']:
            errors.append(f'{qi}: localized question not imported')
        options = [question[f'vi_option_{j}'] for j in range(1, 5)]
        if len(set(options)) != 4 or not all(options):
            errors.append(f'{qi}: blank or duplicate choices')
        if options[correct - 1] != question['vi_correct_answer']:
            errors.append(f'{qi}: intended Vietnamese solution is in the wrong slot')
        if not all(question.get(k) for k in ('riddle_type', 'region', 'explanation', 'provenance')):
            errors.append(f'{qi}: missing folk-riddle context or provenance')
        for j, value in enumerate(options, 1):
            answer = by_id[f'q:CAQuiz_A5_{n}_{j}']
            if answer['vi'] != value or answer['status'] != 'translated':
                errors.append(f'{qi}: option {j} not imported')
    audit = read_csv('review_audit.csv', 'id')
    for i, decision in audit.items():
        current = by_id[i]
        if (decision['ko'], decision['vi_base'], decision['vi_after'], decision['status']) != (
                current['ko'], current['vi_base'], current['vi'], current['status']):
            errors.append(f'{i}: review audit does not match catalog')
    pending = read_csv('review_pending.csv', 'id')
    if set(pending) != {r['id'] for r in catalog if r['status'] == 'review'}:
        errors.append('pending review export is stale')
    for error in errors:
        print(error)
    print(f'{len(catalog)} rows; statuses: {dict(Counter(r["status"] for r in catalog))}')
    print(f'{rewritten} nam_bo_rewrite overrides; {inherited} inherited placeholder discrepancies')
    print(f'{len(errors)} errors')
    return bool(errors)


if __name__ == '__main__':
    raise SystemExit(main())

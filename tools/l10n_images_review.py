#!/usr/bin/env python3
"""Export a local KR/VN image review gallery. Game packs remain read-only.

python3 tools/l10n_images_review.py
python3 tools/l10n_images_review.py --serve 8765  # run outside a socket-restricted sandbox
"""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import struct
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from PIL import Image
import idf
import i16
import l10n_extract as L

FIELDS = ['pack', 'entry', 'status', 'notes']
STATES = {'pending', 'translated', 'needs_translation', 'no_text', 'check'}


def index_packs(root, kr):
    result = {}
    for stem in L.pack_stems(root, kr):
        path = root / (stem + '.idx')
        data = path.read_bytes()
        key = struct.unpack_from('<I', data)[0] if kr else idf.KEYS[stem]
        _, entries, _ = idf.parse_idx(idf.decrypt_idx(data, key))
        for name, off, size, key, crc in entries:
            result[(stem, name) if kr else name] = (root / (stem + '.idd'), off, size, key, crc)
    return result


def read_blob(record, name):
    path, offset, size, key, crc = record
    with path.open('rb') as f:
        f.seek(offset)
        blob = f.read(size)
    return idf.unpack_entry(name, blob, key, crc)


def export(kr, vn, out, workers):
    out.mkdir(parents=True, exist_ok=True)
    (out / 'images').mkdir(exist_ok=True)
    with (L.L10N / 'images_todo.csv').open(encoding='utf-8', newline='') as f:
        rows = list(csv.DictReader(f))
    print(f'Indexing KR and VN packs; {len(rows)} candidates', flush=True)
    kr_idx, vn_idx = index_packs(kr, True), index_packs(vn, False)
    cache, cache_lock, blob_locks = {}, threading.Lock(), {}

    def decode(blob):
        digest = hashlib.sha256(blob).hexdigest()[:24]
        # Identical KR/VN assets may be requested simultaneously. Do not read
        # a PNG that another worker has only partly written.
        with cache_lock:
            lock = blob_locks.setdefault(digest, threading.Lock())
        with lock:
            return decode_once(blob, digest)

    def decode_once(blob, digest):
        with cache_lock:
            if digest in cache:
                return cache[digest]
        if blob.startswith(b'\xff\xd8\xff'):
            im = Image.open(io.BytesIO(blob)).convert('RGBA')
            images = [(0, im)]
            image_count, frame_count = 1, 1
        else:
            parsed = i16.parse(blob)
            image_count, frame_count = len(parsed['images']), parsed['nframes']
            images = []
            for n, ((h, w), packed) in enumerate(zip(parsed['sizes'], parsed['images'])):
                if not packed or not w or not h:
                    continue
                path = out / 'images' / f'{digest}-{n}.png'
                if path.exists():
                    images.append((n, None))
                    continue
                rgba, _, _ = i16.decode_image(packed, w, h)
                images.append((n, Image.frombytes('RGBA', (w, h), rgba)))
        exported = []
        for n, im in images:
            full = f'images/{digest}-{n}.png'
            thumb = f'images/{digest}-{n}-thumb.png'
            if im is not None:
                width, height = im.size
                im.save(out / full, optimize=False)
            else:
                im = Image.open(out / full)
                width, height = im.size
            if not (out / thumb).exists():
                preview = im.copy()
                preview.thumbnail((360, 240))
                preview.save(out / thumb, optimize=False)
            exported.append(dict(index=n, width=width, height=height, full=full, thumb=thumb))
            im.close()
        result = dict(images=exported, image_count=image_count, frame_count=frame_count)
        with cache_lock:
            cache[digest] = result
        return result

    def item(pair):
        n, row = pair
        result = dict(row, id=n)
        for side, record in [('kr', kr_idx.get((row['pack'], row['entry']))),
                             ('vn', vn_idx.get(row['entry']) if row['vn_same_name'] != 'no' else None)]:
            if record is None:
                result[side] = None
                continue
            try:
                result[side] = decode(read_blob(record, row['entry']))
            except Exception as e:
                result[side] = dict(error=f'{type(e).__name__}: {e}', images=[])
        return result

    results = [None] * len(rows)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        jobs = {pool.submit(item, pair): pair[0] for pair in enumerate(rows)}
        for done, job in enumerate(as_completed(jobs), 1):
            result = job.result()
            results[result['id']] = result
            if done % 50 == 0 or done == len(rows):
                print(f'{done}/{len(rows)} exported', flush=True)
    errors = [dict(pack=r['pack'], entry=r['entry'], side=s, error=r[s]['error'])
              for r in results for s in ('kr', 'vn') if r[s] and r[s].get('error')]
    data = json.dumps(results, ensure_ascii=False).replace('<', '\\u003c')
    html = Path(__file__).with_suffix('.html').read_text(encoding='utf-8')
    html = html.replace('/*__GALLERY_DATA__*/[]', data)
    (out / 'index.html').write_text(html, encoding='utf-8')
    (out / 'manifest.json').write_text(json.dumps(results, ensure_ascii=False), encoding='utf-8')
    (out / 'decode_errors.json').write_text(json.dumps(errors, ensure_ascii=False, indent=2), encoding='utf-8')
    # No candidate is labeled translated merely because it has a VN counterpart.
    template = out / 'images_review.csv'
    if not template.exists():
        with template.open('w', encoding='utf-8-sig', newline='') as f:
            w = csv.DictWriter(f, FIELDS, lineterminator='\n')
            w.writeheader()
            for r in results:
                w.writerow(dict(pack=r['pack'], entry=r['entry'], status='pending', notes=''))
    print(f'Gallery: {out / "index.html"}', flush=True)
    print(f'Images: {sum(len((r[s] or {}).get("images", [])) for r in results for s in ("kr", "vn"))}; errors: {len(errors)}', flush=True)


def import_decisions(path):
    with (L.L10N / 'images_todo.csv').open(newline='', encoding='utf-8') as f:
        known = {(r['pack'], r['entry']) for r in csv.DictReader(f)}
    with path.open(newline='', encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))
    seen = set()
    for row in rows:
        key = row['pack'], row['entry']
        if key not in known or key in seen or row['status'] not in STATES:
            raise ValueError(f'Unknown/duplicate resource or invalid status: {key}')
        seen.add(key)
    if seen != known:
        raise ValueError('Import must contain all gallery resources; export CSV from the gallery first')
    target = L.L10N / 'images_review.csv'
    tmp = target.with_suffix('.csv.tmp')
    with tmp.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, FIELDS, lineterminator='\n')
        w.writeheader()
        w.writerows({k: r.get(k, '') for k in FIELDS} for r in rows)
    tmp.replace(target)
    print(f'Imported {len(rows)} decisions into {target}')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--kr', type=Path, default=L.DEF_KR)
    p.add_argument('--vn', type=Path, default=L.DEF_VN)
    p.add_argument('--out', type=Path, default=L.L10N / '.cache' / 'image-review')
    p.add_argument('--workers', type=int, default=4)
    p.add_argument('--import-csv', type=Path)
    p.add_argument('--serve', type=int, metavar='PORT')
    a = p.parse_args()
    if a.import_csv:
        import_decisions(a.import_csv)
    elif a.serve:
        from functools import partial
        from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
        handler = partial(SimpleHTTPRequestHandler, directory=str(a.out.resolve()))
        print(f'Open http://127.0.0.1:{a.serve}', flush=True)
        with ThreadingHTTPServer(('127.0.0.1', a.serve), handler) as server:
            server.serve_forever()
    else:
        if a.workers < 1:
            p.error('--workers must be positive')
        export(a.kr, a.vn, a.out, a.workers)


if __name__ == '__main__':
    main()

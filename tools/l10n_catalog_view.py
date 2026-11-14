#!/usr/bin/env python3
"""Trang xem và sửa catalog Hàn / Việt / Anh trong trình duyệt, và nhập lại các chỗ đã sửa.

  python3 tools/l10n_catalog_view.py                      # dựng trang
  firefox file:///home/admin/boom/repos/boom-re-l10n/l10n/.cache/catalog-view/index.html
  python3 tools/l10n_catalog_view.py --import sua.csv     # nhập file "Xuất các chỗ đã sửa"

Trang không ghi vào repo: chỗ sửa lưu trong trình duyệt, bấm "Xuất các chỗ đã sửa" để lấy CSV
(id, lang, ko, old, new). Khi nhập: bản Việt ghi vào tm_id.csv, bản Anh ghi vào en_id.csv, theo mã chuỗi;
rồi dựng lại catalog.csv, catalog_en.csv, chạy l10n_validate.py và dựng lại trang.
"""
import argparse
import csv
import datetime
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
L10N = ROOT / 'l10n'
OUT = L10N / '.cache/catalog-view/index.html'
sys.path.insert(0, str(ROOT / 'tools'))

PAGE = r'''<!doctype html><html lang="vi"><meta charset="utf-8"><title>Catalog bản dịch Boom KR</title>
<style>
:root{color-scheme:dark}body{margin:0;background:#111820;color:#eef4f9;font:14px system-ui,sans-serif}
header{position:sticky;top:0;background:#111820;padding:12px 2vw;border-bottom:1px solid #344657;z-index:1}
h1{font-size:20px;margin:0 0 8px}.bar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-top:6px}
input,select,button,textarea{font:inherit;background:#243444;color:inherit;border:1px solid #344657;border-radius:6px;padding:7px}
button{cursor:pointer}button:hover{border-color:#80dcbb}#q{flex:1;min-width:260px}#info{color:#80dcbb;margin-top:6px}
#notice{color:#ffd38a;min-height:18px}
table{border-collapse:collapse;width:100%;table-layout:fixed}th,td{border-bottom:1px solid #26384a;padding:6px 8px;vertical-align:top;
white-space:pre-wrap;overflow-wrap:anywhere;text-align:left}th{color:#adbdcc;font-weight:600}
td.id{color:#adbdcc;font-size:12px}small{display:block;color:#7f93a6;font-size:11px;margin-top:3px;white-space:normal}
td.ed{cursor:text}td.ed:hover{background:#1c2733}td.changed{background:#21402f}td.bad{background:#4a2626}
td textarea{width:100%;min-height:70px;resize:vertical;white-space:pre-wrap}
.warn{color:#ff9d8a}.pager{display:flex;gap:12px;justify-content:center;align-items:center;padding:12px}main{padding:0 2vw 30px}
</style>
<header><h1>Catalog bản dịch · Hàn / Việt / Anh</h1>
<div class="bar"><input id="q" placeholder="Tìm trong mã, chữ Hàn, Việt hoặc Anh…">
<select id="src"><option value="">Mọi nguồn</option></select>
<select id="vs"><option value="">Việt: mọi trạng thái</option></select>
<select id="es"><option value="">Anh: mọi trạng thái</option></select>
<select id="only"><option value="">Mọi dòng</option><option value="1">Chỉ dòng đã sửa</option></select></div>
<div class="bar"><label><input type="checkbox" id="edit"> Chế độ sửa (bấm vào ô Việt hoặc Anh)</label>
<button id="export">Xuất các chỗ đã sửa (CSV)</button><button id="clear">Bỏ mọi chỗ sửa</button></div>
<div id="info"></div><div id="notice"></div></header>
<main><div class="pager"><button id="prev">← Trước</button><span id="page"></span><button id="next">Sau →</button></div>
<table><colgroup><col style="width:16%"><col style="width:28%"><col style="width:28%"><col style="width:28%"></colgroup>
<thead><tr><th>Mã</th><th>Hàn</th><th>Việt</th><th>Anh</th></tr></thead><tbody id="rows"></tbody></table>
<div class="pager"><button id="prev2">← Trước</button><span id="page2"></span><button id="next2">Sau →</button></div></main>
<script>
'use strict';
const D=/*DATA*/[];const STAMP=/*STAMP*/'';const SIZE=100;const KEY='boom-catalog-edits-v1';let page=0;
const $=i=>document.getElementById(i);const byId=new Map(D.map(r=>[r[0],r]));
const h=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const vis=s=>h(s).replace(/\r?\n/g,'⏎\n');
let E={};try{E=JSON.parse(localStorage.getItem(KEY)||'{}')}catch(e){}
function save(){try{localStorage.setItem(KEY,JSON.stringify(E));$('notice').textContent=Object.keys(E).length+' chỗ đã sửa, lưu trong trình duyệt. Bấm "Xuất các chỗ đã sửa" rồi gửi file cho Claude để nhập vào repo.'}catch(e){$('notice').textContent='Trình duyệt không lưu được, hãy xuất CSV ngay.'}}
const ek=(id,l)=>id+'\t'+l;const val=(r,l)=>{const k=ek(r[0],l);return Object.hasOwn(E,k)?E[k]:r[l==='vi'?2:3]};
// Cùng quy tắc với công cụ dựng: tham số printf đúng số và thứ tự, thẻ font giữ nguyên, % nghĩa đen không đứng trước chữ.
const BAN=/(?<![\p{L}\p{N}_])(?<!lông )(?<!chân )(xem|nhé|nhỉ|đấy|mũ|tớ|bọn|tao|mày|giao dịch|cửa hàng|nhặt)(?![\p{L}\p{N}_])/iu;
const PF=/%(?:\d+\$)?[-+#0 ]*\d*(?:\.\d+)?(?:hh|ll|h|l|I64|z)?[diuoxXfFeEgGaAcspn%]/g,TAG=/\{[^{}]+\}|<\/?font\b[^<>]*>/gi;
function problems(ko,t,l){const p=[];if(l==='vi'){const m=t.match(BAN);if(m)p.push('có từ "'+m[1]+'" ngoài giọng miền Nam, sẽ bị từ chối khi nhập')}const a=(ko.match(PF)||[]).filter(x=>x!=='%%'),b=(t.match(PF)||[]).filter(x=>x!=='%%');
const sa=a.every(x=>x.includes('$'))&&b.every(x=>x.includes('$'))&&a.length?[...a].sort().join():a.join(),sb=a.every(x=>x.includes('$'))&&b.every(x=>x.includes('$'))&&a.length?[...b].sort().join():b.join();
if(sa!==sb)p.push('tham số định dạng khác câu Hàn ('+(a.join(' ')||'không có')+')');
if((ko.match(TAG)||[]).join()!==(t.match(TAG)||[]).join())p.push('thẻ <font> hoặc {…} khác câu Hàn');
const n=s=>(s.match(/\n/g)||[]).length;if(n(ko)!==n(t))p.push('số lần xuống dòng khác câu Hàn ('+n(ko)+')');return p}
for(const [id,k] of [['src',4],['vs',5],['es',6]])for(const v of [...new Set(D.map(r=>r[k]))].sort())$(id).add(new Option(v||'(trống)',v));
function rows(){const q=$('q').value.toLowerCase(),s=$('src').value,v=$('vs').value,e=$('es').value,o=$('only').value;
return D.filter(r=>(!s||r[4]===s)&&(!v||r[5]===v)&&(!e||r[6]===e)&&(!o||Object.hasOwn(E,ek(r[0],'vi'))||Object.hasOwn(E,ek(r[0],'en')))&&(!q||(r[0]+'\n'+r[1]+'\n'+val(r,'vi')+'\n'+val(r,'en')).toLowerCase().includes(q)))}
function cell(r,l){const k=ek(r[0],l),t=val(r,l),ch=Object.hasOwn(E,k),p=ch?problems(r[1],t,l):[];
const meta=l==='vi'?r[5]:r[6]+(r[7]?' · '+r[7]:'');
return '<td class="ed'+(ch?' changed':'')+(p.length?' bad':'')+'" data-id="'+h(r[0])+'" data-l="'+l+'">'+vis(t)+'<small>'+(ch?'đã sửa · ':'')+h(meta)+'</small>'+(p.length?'<small class="warn">'+h(p.join('; '))+'</small>':'')+'</td>'}
function render(){const R=rows(),pages=Math.max(1,Math.ceil(R.length/SIZE));page=Math.min(page,pages-1);
const t='Trang '+(page+1)+' / '+pages;$('page').textContent=$('page2').textContent=t;
$('info').textContent=R.length.toLocaleString('vi')+' / '+D.length.toLocaleString('vi')+' dòng · '+Object.keys(E).length+' chỗ đã sửa · ⏎ là chỗ xuống dòng trong chuỗi gốc · dữ liệu dựng lúc '+STAMP;
$('rows').innerHTML=R.slice(page*SIZE,(page+1)*SIZE).map(r=>'<tr><td class="id">'+h(r[0])+'<small>'+h(r[4])+'</small></td><td>'+vis(r[1])+'</td>'+cell(r,'vi')+cell(r,'en')+'</tr>').join('')}
$('rows').onclick=e=>{if(!$('edit').checked)return;const td=e.target.closest('td.ed');if(!td||td.querySelector('textarea'))return;
const r=byId.get(td.dataset.id),l=td.dataset.l,crlf=/\r\n/.test(r[1]);const ta=document.createElement('textarea');ta.value=val(r,l).replace(/\r\n/g,'\n');
td.innerHTML='';td.appendChild(ta);const b=document.createElement('small');b.textContent='Enter xuống dòng · Ctrl+Enter hoặc bấm ra ngoài để lưu · Esc để huỷ';td.appendChild(b);ta.focus();
let done=false;const finish=keep=>{if(done)return;done=true;if(keep){let v=ta.value;if(crlf)v=v.replace(/\r?\n/g,'\r\n');const orig=r[l==='vi'?2:3];
if(v===orig)delete E[ek(r[0],l)];else E[ek(r[0],l)]=v;save()}render()};
ta.onkeydown=ev=>{if(ev.key==='Escape')finish(false);if(ev.key==='Enter'&&(ev.ctrlKey||ev.metaKey))finish(true)};ta.onblur=()=>finish(true)};
function csvCell(s){return '"'+String(s).replace(/"/g,'""')+'"'}
$('export').onclick=()=>{const lines=[['id','lang','ko','old','new']];for(const [k,v] of Object.entries(E)){const [id,l]=k.split('\t'),r=byId.get(id);if(r)lines.push([id,l,r[1],r[l==='vi'?2:3],v])}
const u=URL.createObjectURL(new Blob(['﻿'+lines.map(x=>x.map(csvCell).join(',')).join('\r\n')+'\r\n'],{type:'text/csv;charset=utf-8'}));
const a=document.createElement('a');a.href=u;a.download='catalog-edits.csv';a.click();setTimeout(()=>URL.revokeObjectURL(u),10000);
$('notice').textContent='Đã xuất '+(lines.length-1)+' chỗ sửa vào catalog-edits.csv (thư mục Tải về).'};
$('clear').onclick=()=>{if(confirm('Bỏ mọi chỗ đã sửa lưu trong trình duyệt?')){E={};save();render()}};
let t;$('q').oninput=()=>{clearTimeout(t);t=setTimeout(()=>{page=0;render()},150)};
for(const i of ['src','vs','es','only'])$(i).onchange=()=>{page=0;render()};
for(const i of ['prev','prev2'])$(i).onclick=()=>{if(page>0){page--;render();scrollTo(0,0)}};
for(const i of ['next','next2'])$(i).onclick=()=>{page++;render();scrollTo(0,0)};
if(Object.keys(E).length)save();render();
</script></html>'''


def build():
    with (L10N / 'catalog_en.csv').open(encoding='utf-8', newline='') as f:
        rows = [[r['id'], r['ko'], r['vi'], r['en'], r['source_kr'].split('+')[0], r['vi_status'], r['en_status'],
                 r['source_en']] for r in csv.DictReader(f)]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(rows, ensure_ascii=False).replace('<', '\\u003c')
    stamp = json.dumps(datetime.datetime.now().strftime('%Y-%m-%d %H:%M'))
    OUT.write_text(PAGE.replace('/*DATA*/[]', data).replace("/*STAMP*/''", stamp), encoding='utf-8')
    print(f'{len(rows)} dòng → {OUT}')


def read(path, key):
    if not path.exists():
        return [], {}
    with path.open(encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    return reader.fieldnames, {r[key]: r for r in rows}


def write(path, fields, rows):
    with path.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fields, lineterminator='\n')
        w.writeheader()
        w.writerows(rows)


def import_edits(path):
    import l10n_extract_en as EN
    from l10n_validate import BAN
    with path.open(encoding='utf-8-sig', newline='') as f:
        edits = list(csv.DictReader(f))
    with (L10N / 'catalog_en.csv').open(encoding='utf-8', newline='') as f:
        catalog = {r['id']: r for r in csv.DictReader(f)}
    today = datetime.date.today().isoformat()
    note = f'sửa tay qua trang catalog {today}'
    tid_fields, tid = read(L10N / 'tm_id.csv', 'id')
    _, en_id = read(L10N / 'en_id.csv', 'id')
    aud_fields, audit = read(L10N / 'review_audit.csv', 'id')
    applied, rejected = [], []
    for e in edits:
        row = catalog.get(e['id'])
        lang, new = e['lang'], e['new']
        if not row or lang not in ('vi', 'en'):
            rejected.append((e['id'], lang, 'mã chuỗi hoặc ngôn ngữ không có trong catalog'))
            continue
        if row['ko'] != e['ko']:
            rejected.append((e['id'], lang, 'câu Hàn trong catalog đã đổi từ lúc xuất'))
            continue
        if not EN.formatting(row['ko'], new) or new.count('\n') != row['ko'].count('\n'):
            rejected.append((e['id'], lang, 'lệch tham số định dạng, thẻ hoặc số lần xuống dòng so với câu Hàn'))
            continue
        if lang == 'vi' and BAN.search(new):
            rejected.append((e['id'], lang, f'có từ "{BAN.search(new).group()}" ngoài giọng miền Nam của bản dịch (xem quy tắc 2b trong README)'))
            continue
        if lang == 'vi':
            old = tid.get(e['id'], {})
            tid[e['id']] = {'id': e['id'], 'vi': new, 'status': 'translated',
                            'notes': ';'.join(x for x in (old.get('notes', ''), note) if x)}
            if e['id'] in audit:
                a = audit[e['id']]
                a.update(vi_before=a['vi_after'], vi_after=new, status='translated', previous_notes=a['reason'], reason=note)
        else:
            en_id[e['id']] = {'id': e['id'], 'en': new, 'notes': note}
        applied.append((e['id'], lang))
    write(L10N / 'tm_id.csv', tid_fields, tid.values())
    write(L10N / 'en_id.csv', ['id', 'en', 'notes'], en_id.values())
    if audit:
        write(L10N / 'review_audit.csv', aud_fields, audit.values())
    for cmd in (['tools/l10n_extract.py', 'catalog'], ['tools/l10n_extract_en.py'], ['tools/l10n_validate.py']):
        r = subprocess.run([sys.executable, *cmd], cwd=ROOT, capture_output=True, text=True)
        tail = (r.stdout + r.stderr).strip().splitlines()[-3:]
        print('$', ' '.join(cmd), '→', ' | '.join(tail))
    with (L10N / 'catalog_en.csv').open(encoding='utf-8', newline='') as f:
        after = {r['id']: r for r in csv.DictReader(f)}
    for i, lang in applied:
        want = next(e['new'] for e in edits if e['id'] == i and e['lang'] == lang)
        got = after[i]['vi' if lang == 'vi' else 'en']
        if got != want:
            print(f'  lưu ý {i} ({lang}): catalog ghi "{got[:60]}" khác bản sửa (quy tắc giọng miền Nam có thể đã đổi từ)')
    print(f'Đã nhập {len(applied)} chỗ sửa; từ chối {len(rejected)}.')
    for i, lang, why in rejected:
        print(f'  từ chối {i} ({lang}): {why}')
    build()


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--import', dest='edits', type=Path, help='CSV xuất từ nút "Xuất các chỗ đã sửa"')
    a = p.parse_args()
    import_edits(a.edits) if a.edits else build()


if __name__ == '__main__':
    main()

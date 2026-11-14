#!/usr/bin/env python3
"""Dựng trang xem catalog Hàn / Việt / Anh để mở bằng trình duyệt (chỉ xem, không sửa).

  python3 tools/l10n_catalog_view.py
  firefox file:///home/admin/boom/repos/boom-re-l10n/l10n/.cache/catalog-view/index.html
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'l10n/.cache/catalog-view/index.html'

PAGE = r'''<!doctype html><html lang="vi"><meta charset="utf-8"><title>Catalog bản dịch Boom KR</title>
<style>
:root{color-scheme:dark}body{margin:0;background:#111820;color:#eef4f9;font:14px system-ui,sans-serif}
header{position:sticky;top:0;background:#111820;padding:12px 2vw;border-bottom:1px solid #344657;z-index:1}
h1{font-size:20px;margin:0 0 8px}.bar{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
input,select,button{font:inherit;background:#243444;color:inherit;border:1px solid #344657;border-radius:6px;padding:7px}
#q{flex:1;min-width:260px}#info{color:#80dcbb;margin-top:6px}
table{border-collapse:collapse;width:100%;table-layout:fixed}th,td{border-bottom:1px solid #26384a;padding:6px 8px;vertical-align:top;
white-space:pre-wrap;overflow-wrap:anywhere;text-align:left}th{color:#adbdcc;font-weight:600}
td.id{color:#adbdcc;font-size:12px}td small{display:block;color:#7f93a6;font-size:11px;margin-top:3px}
.pager{display:flex;gap:12px;justify-content:center;align-items:center;padding:12px}main{padding:0 2vw 30px}
</style>
<header><h1>Catalog bản dịch · Hàn / Việt / Anh</h1>
<div class="bar"><input id="q" placeholder="Tìm trong mã, chữ Hàn, Việt hoặc Anh…">
<select id="src"><option value="">Mọi nguồn</option></select>
<select id="vs"><option value="">Việt: mọi trạng thái</option></select>
<select id="es"><option value="">Anh: mọi trạng thái</option></select></div>
<div id="info"></div></header>
<main><div class="pager"><button id="prev">← Trước</button><span id="page"></span><button id="next">Sau →</button></div>
<table><colgroup><col style="width:16%"><col style="width:28%"><col style="width:28%"><col style="width:28%"></colgroup>
<thead><tr><th>Mã</th><th>Hàn</th><th>Việt</th><th>Anh</th></tr></thead><tbody id="rows"></tbody></table>
<div class="pager"><button id="prev2">← Trước</button><span id="page2"></span><button id="next2">Sau →</button></div></main>
<script>
'use strict';
const D=/*DATA*/[];const SIZE=100;let page=0;const $=i=>document.getElementById(i);
const h=s=>String(s).replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
const vis=s=>h(s).replace(/\r?\n/g,'⏎\n');
for(const [id,k] of [['src',4],['vs',5],['es',6]])for(const v of [...new Set(D.map(r=>r[k]))].sort())$(id).add(new Option(v||'(trống)',v));
function rows(){const q=$('q').value.toLowerCase(),s=$('src').value,v=$('vs').value,e=$('es').value;
return D.filter(r=>(!s||r[4]===s)&&(!v||r[5]===v)&&(!e||r[6]===e)&&(!q||(r[0]+'\n'+r[1]+'\n'+r[2]+'\n'+r[3]).toLowerCase().includes(q)))}
function render(){const R=rows(),pages=Math.max(1,Math.ceil(R.length/SIZE));page=Math.min(page,pages-1);
const t='Trang '+(page+1)+' / '+pages;$('page').textContent=$('page2').textContent=t;
$('info').textContent=R.length.toLocaleString('vi')+' / '+D.length.toLocaleString('vi')+' dòng. ⏎ là chỗ xuống dòng trong chuỗi gốc.';
$('rows').innerHTML=R.slice(page*SIZE,(page+1)*SIZE).map(r=>'<tr><td class="id">'+h(r[0])+'<small>'+h(r[4])+'</small></td><td>'+vis(r[1])+'</td><td>'+vis(r[2])+'<small>'+h(r[5])+'</small></td><td>'+vis(r[3])+'<small>'+h(r[6])+(r[7]?' · '+h(r[7]):'')+'</small></td></tr>').join('')}
let t;$('q').oninput=()=>{clearTimeout(t);t=setTimeout(()=>{page=0;render()},150)};
for(const i of ['src','vs','es'])$(i).onchange=()=>{page=0;render()};
for(const i of ['prev','prev2'])$(i).onclick=()=>{if(page>0){page--;render();scrollTo(0,0)}};
for(const i of ['next','next2'])$(i).onclick=()=>{page++;render();scrollTo(0,0)};
render();
</script></html>'''


def main():
    with (ROOT / 'l10n/catalog_en.csv').open(encoding='utf-8', newline='') as f:
        rows = [[r['id'], r['ko'], r['vi'], r['en'], r['source_kr'].split('+')[0], r['vi_status'], r['en_status'],
                 r['source_en']] for r in csv.DictReader(f)]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(rows, ensure_ascii=False).replace('<', '\\u003c')
    OUT.write_text(PAGE.replace('/*DATA*/[]', data), encoding='utf-8')
    print(f'{len(rows)} dòng → {OUT}')


if __name__ == '__main__':
    main()

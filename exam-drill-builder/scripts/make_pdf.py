#!/usr/bin/env python3
"""bank.json → 無答案練習 PDF（每科一份）＋ 解答對照表 PDF。

需要 wkhtmltopdf 與中文字型（Noto Sans CJK TC 或同等）。
用法:
  python3 make_pdf.py bank.json --outdir ./out
"""
import argparse, html, json, os, subprocess
from pathlib import Path

CSS = """
@page { size: A4; margin: 14mm 12mm; }
body { font-family: "Noto Sans CJK TC","Noto Sans TC",sans-serif; font-size:10.5pt; line-height:1.5; color:#111; }
h1 { font-size:16pt; text-align:center; margin:0 0 2mm; }
h2 { font-size:13pt; margin:5mm 0 2mm; }
.sub { text-align:center; font-size:9pt; color:#555; margin-bottom:6mm; }
.q { margin:0 0 3.2mm; page-break-inside:avoid; }
.qh { font-weight:600; }
.box { display:inline-block; width:9mm; border-bottom:1px solid #333; text-align:center; margin-right:2mm; }
.no { display:inline-block; min-width:9mm; }
.opts { margin:.6mm 0 0 12mm; }
.opt { display:block; }
table.key { border-collapse:collapse; width:100%; font-size:9.5pt; }
table.key td, table.key th { border:1px solid #999; padding:1.2mm 1mm; text-align:center; }
table.key th { background:#eee; }
"""


def page(body):
    return f'<!DOCTYPE html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>{body}</body></html>'


def practice(name, qs):
    rows = []
    for q in qs:
        opts = q.get("opts") or []
        ohtml = ''.join(f'<span class="opt">({i+1}) {html.escape(o)}</span>' for i, o in enumerate(opts))
        rows.append(f'<div class="q"><span class="qh"><span class="box">&nbsp;</span>'
                    f'<span class="no">{q["no"]}.</span> {html.escape(q["stem"])}</span>'
                    f'<div class="opts">{ohtml}</div></div>')
    return page(f'<h1>{html.escape(name)}　練習題（無答案）</h1>'
                f'<div class="sub">共 {len(qs)} 題　·　單選題　·　答案請填於左方橫線</div>'
                + ''.join(rows))


def key_sheet(bank, per_row=10):
    parts = []
    for name, qs in bank.items():
        parts.append(f'<h2>{html.escape(name)}（共 {len(qs)} 題）</h2><table class="key">')
        parts.append('<tr><th>題號</th>' + ''.join(f'<th>+{i}</th>' for i in range(per_row)) + '</tr>')
        for start in range(1, len(qs) + 1, per_row):
            cells = ''.join(f'<td>{qs[start+i-1]["ans"]}</td>' if start + i <= len(qs) else '<td></td>'
                            for i in range(per_row))
            parts.append(f'<tr><th>{start}</th>{cells}</tr>')
        parts.append('</table>')
    return page('<h1>解答對照表</h1>' + ''.join(parts))


def render(htm, out):
    tmp = str(Path(out).with_suffix('.tmp.html'))
    Path(tmp).write_text(htm, encoding='utf-8')
    subprocess.run(['wkhtmltopdf', '--encoding', 'utf-8', '--quiet', tmp, out], check=True)
    os.remove(tmp)
    print('已寫出', out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bank")
    ap.add_argument("--outdir", default=".")
    a = ap.parse_args()
    bank = json.loads(Path(a.bank).read_text(encoding='utf-8'))
    Path(a.outdir).mkdir(parents=True, exist_ok=True)
    for name, qs in bank.items():
        render(practice(name, qs), f'{a.outdir}/{name}-練習題(無答案).pdf')
    render(key_sheet(bank), f'{a.outdir}/解答對照表.pdf')


if __name__ == "__main__":
    main()

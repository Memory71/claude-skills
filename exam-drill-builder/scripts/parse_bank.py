#!/usr/bin/env python3
"""把題庫 PDF 解析成 bank.json。

用法:
  python3 parse_bank.py --inspect  <a.pdf> [b.pdf ...]        # 先驗證，不產檔
  python3 parse_bank.py -o bank.json <a.pdf> [b.pdf ...]      # 產出

預設版型 (profile=leading) 針對「答案在行首括號、題號緊接其後」的題庫，例如:
    (4) 1 下列何者不是金融市場的主要功能？(1)...(2)...(3)...(4)...

科目名稱預設取自檔名（去掉副檔名與開頭的非中文字元），可用 --name 覆寫。
"""
import argparse, json, re, sys, unicodedata
from pathlib import Path

import pdfplumber

PROFILES = {
    # 答案在行首:  (4) 12 題幹...
    "leading": re.compile(r'^\((\d)\)\s*(\d+)\s+(.*)$'),
    # 題號在前、答案在後:  12.(4) 題幹...
    "numfirst": re.compile(r'^(?:第)?(\d+)[.、\s]+\((\d)\)\s*(.*)$'),
}
# 各 profile 的 group 對應 (ans, no, text)
GROUPS = {"leading": (1, 2, 3), "numfirst": (2, 1, 3)}

NOISE = re.compile(r'^(Part\s*[IVX]+\s*[：:].*|答案\s*題號\s*題目|題號\s*答案.*|\d+|第\s*\d+\s*頁.*)$')


def page_lines(path):
    out = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            lines = [l.strip() for l in (page.extract_text() or '').split('\n') if l.strip()]
            while lines and lines[-1].isdigit():      # 去頁尾頁碼
                lines.pop()
            out += lines
    return out


def parse(path, profile="leading"):
    pat = PROFILES[profile]
    gi_ans, gi_no, gi_txt = GROUPS[profile]
    qs, orphans = [], 0
    for line in page_lines(path):
        if NOISE.match(line):
            continue
        m = pat.match(line)
        # 關鍵防呆：題號必須是「下一題」才算新題，否則視為上一題的換行。
        # 這條規則專門擋掉選項換行成 "(3)9 股(4)1 股" 被誤判為新題的情形。
        if m and int(m.group(gi_no)) == len(qs) + 1:
            qs.append({"no": int(m.group(gi_no)), "ans": int(m.group(gi_ans)),
                       "text": m.group(gi_txt)})
        elif qs:
            qs[-1]["text"] += line
        else:
            orphans += 1
    return qs, orphans


def split_opts(text, n_opts=4):
    """順向掃描切出題幹與各選項；切不乾淨就回傳 None。"""
    idx, cur = [], 0
    for n in range(1, n_opts + 1):
        p = text.find(f'({n})', cur)
        if p < 0:
            return None
        idx.append(p)
        cur = p + 3
    stem = text[:idx[0]].strip()
    opts = [text[idx[k] + 3: (idx[k + 1] if k + 1 < n_opts else len(text))].strip()
            for k in range(n_opts)]
    if not stem or not all(opts):
        return None
    return stem, opts


def subject_from(path):
    stem = Path(path).stem
    return re.sub(r'^[^\w\u4e00-\u9fff]+', '', stem).strip() or stem


def build(paths, names=None, profile="leading", n_opts=4):
    bank, report = {}, []
    for i, p in enumerate(paths):
        name = names[i] if names and i < len(names) else subject_from(p)
        qs, orphans = parse(p, profile)
        bad_split, bad_ans = [], []
        for q in qs:
            s = split_opts(q["text"], n_opts)
            if s:
                q["stem"], q["opts"] = s
            else:
                q["stem"], q["opts"] = q["text"], None
                bad_split.append(q["no"])
            if not (1 <= q["ans"] <= n_opts):
                bad_ans.append(q["no"])
        gaps = [i + 1 for i, q in enumerate(qs) if q["no"] != i + 1]
        report.append({"file": p, "subject": name, "count": len(qs), "orphan_lines": orphans,
                       "number_gaps": gaps[:10], "unsplit": bad_split, "bad_answer": bad_ans,
                       "sample": qs[len(qs) // 2] if qs else None})
        bank[name] = qs
    return bank, report


def show(report):
    ok = True
    for r in report:
        print(f"\n=== {r['subject']}  ({r['file']})")
        print(f"    解析題數      : {r['count']}")
        print(f"    題號不連續    : {r['number_gaps'] or '無'}")
        print(f"    選項切不開    : {r['unsplit'] or '無'}")
        print(f"    答案值異常    : {r['bad_answer'] or '無'}")
        print(f"    題前散落行數  : {r['orphan_lines']}")
        if r['count'] == 0 or r['number_gaps'] or r['bad_answer']:
            ok = False
        s = r['sample']
        if s:
            print(f"    抽樣 第{s['no']}題 [答案 {s['ans']}] {s['stem'][:60]}")
            for i, o in enumerate(s['opts'] or []):
                print(f"        ({i+1}) {o[:60]}")
    print("\n" + ("檢查通過。" if ok else "有問題，請調整 --profile 或 regex 後重跑。"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdfs", nargs="+")
    ap.add_argument("-o", "--out", default="bank.json")
    ap.add_argument("--name", action="append", help="科目名稱，可重複，順序對應 pdf")
    ap.add_argument("--profile", default="leading", choices=list(PROFILES))
    ap.add_argument("--options", type=int, default=4, help="每題選項數，預設 4")
    ap.add_argument("--inspect", action="store_true", help="只檢查不產檔")
    a = ap.parse_args()

    bank, report = build(a.pdfs, a.name, a.profile, a.options)
    ok = show(report)
    if a.inspect:
        return
    if not ok:
        print("解析未通過，仍要產出請先用 --inspect 確認。", file=sys.stderr)
        sys.exit(1)
    Path(a.out).write_text(json.dumps(bank, ensure_ascii=False), encoding="utf-8")
    print(f"已寫出 {a.out}")


if __name__ == "__main__":
    main()

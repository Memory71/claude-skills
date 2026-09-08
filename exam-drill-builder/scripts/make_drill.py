#!/usr/bin/env python3
"""bank.json → 單檔 HTML 刷題器。

用法:
  python3 make_drill.py bank.json -o 刷題器.html --title "XXX 刷題器" --pace 36
"""
import argparse, json
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent.parent / "assets" / "drill_template.html"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bank")
    ap.add_argument("-o", "--out", default="drill.html")
    ap.add_argument("--title", default="刷題器")
    ap.add_argument("--pace", type=float, default=36, help="每題目標秒數")
    ap.add_argument("--store-key", default=None, help="瀏覽器儲存用的 key，不同題庫請給不同值")
    a = ap.parse_args()

    bank = json.loads(Path(a.bank).read_text(encoding="utf-8"))
    slim = {k: [{"no": q["no"], "ans": q["ans"],
                 "stem": q["stem"], "opts": q["opts"] or [q["text"]]}
                for q in v] for k, v in bank.items()}

    key = a.store_key or ("drill_" + "".join(ch for ch in a.title if ch.isalnum())[:24] or "drill")
    html = (TEMPLATE.read_text(encoding="utf-8")
            .replace("/*__DATA__*/", json.dumps(slim, ensure_ascii=False, separators=(',', ':')))
            .replace("__PACE__", str(a.pace))
            .replace("__STOREKEY__", key)
            .replace("__TITLE__", a.title))
    Path(a.out).write_text(html, encoding="utf-8")
    total = sum(len(v) for v in slim.values())
    print(f"已寫出 {a.out}（{total} 題，storeKey={key}）")


if __name__ == "__main__":
    main()

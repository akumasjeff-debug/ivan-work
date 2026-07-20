# -*- coding: utf-8 -*-
"""電玩庫存表 匯入轉換

PChome 廠商商品匯出檔（Downloads 的 .xls，實際是 xlsx）→ 六欄 TSV：
  廠商名稱 | 商品編號 | 商品名稱 | 可賣量 | 成本 | 售價

用法：
  py 電玩庫存表\\匯入轉換.py            # 自動抓 Downloads 最新的匯出檔
  py 電玩庫存表\\匯入轉換.py <檔案路徑>  # 指定檔案

輸出：
  1. 電玩庫存表/reports/庫存表_YYYYMMDD.tsv
  2. 同步複製到剪貼簿 → 到 Google Sheet「庫存表」分頁點 A1 直接 Ctrl+V 即自動分欄
"""
import sys
import io
import re
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

import openpyxl

sys.stdout.reconfigure(encoding="utf-8")

DOWNLOADS = Path.home() / "Downloads"
REPORTS = Path(__file__).parent / "reports"

# 匯出檔欄名 → 輸出欄名（照這順序輸出）
COLUMNS = [
    ("廠商名稱", "廠商名稱"),
    ("商品編號(20碼含規格碼)", "商品編號"),
    ("商品名稱", "商品名稱"),
    ("可賣量", "可賣量"),
    ("成本", "成本"),
    ("售價(網路價)", "售價"),
]


def find_latest_export() -> Path:
    """Downloads 裡檔名長得像 2026072013_XXXX.xls 的最新一個。"""
    cands = [p for p in DOWNLOADS.glob("*.xls") if re.match(r"^20\d{8}_", p.name)]
    if not cands:
        sys.exit(f"在 {DOWNLOADS} 找不到 20########_*.xls 匯出檔，請直接給檔案路徑當參數")
    return max(cands, key=lambda p: p.stat().st_mtime)


def load_rows(path: Path):
    # 副檔名是 .xls 但內容是 xlsx，openpyxl 認副檔名，複製改名再開
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td) / "export.xlsx"
        shutil.copy(path, tmp)
        wb = openpyxl.load_workbook(tmp, read_only=True)
        ws = wb.worksheets[0]
        rows = [list(r) for r in ws.iter_rows(values_only=True)]
        wb.close()
    if not rows:
        sys.exit("匯出檔是空的")
    header = [str(c).strip() if c is not None else "" for c in rows[0]]
    try:
        idx = [header.index(src) for src, _ in COLUMNS]
    except ValueError as e:
        sys.exit(f"匯出檔欄位對不上（{e}），實際欄位：{header}")
    out = []
    for r in rows[1:]:
        if r[idx[1]] in (None, ""):  # 沒商品編號的列跳過
            continue
        out.append(["" if r[i] is None else str(r[i]).strip() for i in idx])
    return out


def main():
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else find_latest_export()
    print(f"讀取：{src}")
    data = load_rows(src)

    header = [dst for _, dst in COLUMNS]
    lines = ["\t".join(header)] + ["\t".join(row) for row in data]
    tsv = "\n".join(lines)

    REPORTS.mkdir(exist_ok=True)
    out = REPORTS / f"庫存表_{datetime.now():%Y%m%d}.tsv"
    out.write_text(tsv, encoding="utf-8-sig")

    # 複製到剪貼簿（clip.exe 會把 BOM 留在內容裡，改走 Set-Clipboard）
    subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         f"Set-Clipboard -Value (Get-Content -Raw -Encoding UTF8 '{out}')"],
        check=True)

    zero = sum(1 for r in data if r[3] in ("0", ""))
    print(f"共 {len(data)} 筆商品（其中可賣量 0：{zero} 筆）")
    print(f"已存：{out}")
    print("已複製到剪貼簿 → Google Sheet「庫存表」分頁點 A1，Ctrl+V 貼上即自動分欄")


if __name__ == "__main__":
    main()

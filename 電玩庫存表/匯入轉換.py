# -*- coding: utf-8 -*-
"""電玩庫存表 每週更新（v5）

輸入（Downloads，自動抓最新；也可用參數指定）：
  1. 全站廠商商品匯出 CSV：20########_*.csv（UTF-16、tab 分隔，含全部廠商）
     ※ 已包含 pchome採購（7777）全部商品，舊的採購專用 .xls 不用再下載
  2. 即時業績 xlsx：MMDD-MMDD即時業績.xlsx（一週訂單明細，檔名即週區間）

寫入 Google Sheet（經 GAS Web App；config.local.json 放 webapp_url/token，gitignore）：
  - 庫存表（pchome採購快照）＋含庫存廠商頁（傑仕登/宏碁遊戲）
  - 8 個純銷量廠商頁（品項＋週銷＋業績＋毛利，週銷大→小）
  - 可賣量歷史（一欄一日期）、週銷歷史（一欄一週）

廠商歸戶規則：「來源廠商」有值用它（採購品），否則用「廠商編號」（寄倉品）。

用法：
  py 電玩庫存表\\匯入轉換.py
  py 電玩庫存表\\匯入轉換.py <全站CSV路徑> <業績xlsx路徑>
"""
import json
import re
import shutil
import sys
import tempfile
import urllib.request
from collections import defaultdict
from csv import reader as csv_reader
from datetime import datetime
from pathlib import Path

import openpyxl

sys.stdout.reconfigure(encoding="utf-8")

DOWNLOADS = Path.home() / "Downloads"
REPORTS = Path(__file__).parent / "reports"
CONFIG = Path(__file__).parent / "config.local.json"

# 含庫存的廠商頁（資料來自全站 CSV，格式同庫存表）
STOCK_VENDORS = [
    ("26312", "傑仕登"),
    ("38177", "宏碁遊戲"),  # 匯出檔寫「宏（其＋石）」＝碁字打不出來
]
# 純銷量廠商頁：只有品項＋週銷＋業績＋毛利（可多家合併一頁）
SALES_VENDORS = [
    (("12555",), "壹世代"),
    (("28388",), "瑋琳"),
    (("38237",), "誠碁"),
    (("39634",), "銀科互通"),
    (("39980",), "玥勝"),
    (("40069",), "智冠"),
    (("40617",), "寶可夢台灣"),
    (("41032", "41033"), "英益誠＋艾格瑞"),
]

# 全站 CSV 欄位索引（14 欄）
C_VNAME, C_VID, C_PID, C_PNAME, C_QTY, C_COST, C_PRICE, C_STORE, C_SRC = 0, 1, 2, 3, 5, 6, 7, 12, 13
# 即時業績欄位索引（76 欄）
S_STATUS, S_MUSEUM, S_PID, S_PNAME, S_QTY, S_RETQTY, S_REV, S_COST, S_VID, S_SRC = 0, 5, 8, 9, 10, 11, 12, 13, 28, 30


def find_latest(pattern: str, desc: str) -> Path:
    cands = [p for p in DOWNLOADS.iterdir() if re.match(pattern, p.name)]
    if not cands:
        sys.exit(f"在 {DOWNLOADS} 找不到{desc}（檔名規則 {pattern}）")
    return max(cands, key=lambda p: p.stat().st_mtime)


def num(s, default=0):
    try:
        return int(s)
    except (TypeError, ValueError):
        try:
            return float(s)
        except (TypeError, ValueError):
            return default


def load_csv(path: Path):
    """全站 CSV → list[list]（去掉標題、跳過無商品編號列）。"""
    rows = []
    with open(path, encoding="utf-16", newline="") as f:
        rd = csv_reader(f, delimiter="\t")
        header = next(rd)
        if "商品編號" not in str(header[C_PID]):
            sys.exit(f"CSV 欄位對不上，實際欄位：{header}")
        for r in rd:
            if len(r) >= 14 and r[C_PID].strip():
                rows.append([c.strip() for c in r])
    return rows


def load_sales(path: Path):
    """業績 xlsx → {商品ID: {qty, rev, cost, name, museum, vendor}}
    狀態含「退貨」的明細整筆反向；一般列另扣退貨數量欄。"""
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td) / "s.xlsx"
        shutil.copy(path, tmp)
        wb = openpyxl.load_workbook(tmp)
        rows = list(wb.worksheets[0].iter_rows(values_only=True))[1:]
        wb.close()
    agg = defaultdict(lambda: {"qty": 0, "rev": 0, "cost": 0,
                               "name": "", "museum": "", "vendor": ""})
    for r in rows:
        pid = str(r[S_PID] or "").strip()
        if not pid:
            continue
        sign = -1 if "退貨" in str(r[S_STATUS] or "") else 1
        a = agg[pid]
        a["qty"] += sign * num(r[S_QTY]) - num(r[S_RETQTY])
        a["rev"] += sign * num(r[S_REV])
        a["cost"] += sign * num(r[S_COST])
        a["name"] = str(r[S_PNAME] or a["name"])
        a["museum"] = str(r[S_MUSEUM] or a["museum"])
        src = str(r[S_SRC] or "").strip()
        a["vendor"] = src if src else str(r[S_VID] or "").strip()
    return dict(agg)


def week_label(path: Path) -> str:
    m = re.match(r"^(\d{2})(\d{2})-(\d{2})(\d{2})", path.name)
    if not m:
        sys.exit(f"業績檔名抓不到週區間：{path.name}（預期 MMDD-MMDD 開頭）")
    return f"{m.group(1)}/{m.group(2)}-{m.group(3)}/{m.group(4)}"


def csv_date(path: Path) -> str:
    m = re.match(r"^(20\d{2})(\d{2})(\d{2})", path.name)
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else f"{datetime.now():%Y-%m-%d}"


def eff_vendor(r) -> str:
    return r[C_SRC] if r[C_SRC] else r[C_VID]


def metrics(sales, pid, avail=None):
    """→ [週銷, 可售週數, 業績金額, 毛利額, 毛利率]（可售週數只在有庫存數時算）"""
    s = sales.get(pid)
    qty = s["qty"] if s else 0
    rev = s["rev"] if s else 0
    profit = rev - (s["cost"] if s else 0)
    rate = round(profit / rev, 4) if rev > 0 else ""
    weeks = round(avail / qty, 1) if avail is not None and qty > 0 else ""
    return [qty, weeks, int(rev), int(profit), rate]


def build_payload(csv_rows, sales, label):
    tabs = []
    qty_hist = []      # [pid, name, 可賣量]
    sales_hist = {}    # pid -> (name, 週銷)

    stock_headers = lambda first: [first, "商品編號", "商品名稱", "可賣量", "成本", "售價",
                                   "來源廠商", f"週銷 {label}", "可售週數", "業績金額", "毛利額", "毛利率"]

    def stock_rows(rows, first_col_idx):
        out = []
        for r in rows:
            avail = num(r[C_QTY])
            m = metrics(sales, r[C_PID], avail)
            out.append([r[first_col_idx], r[C_PID], r[C_PNAME], avail,
                        num(r[C_COST]), num(r[C_PRICE]), eff_vendor(r)] + m)
            qty_hist.append([r[C_PID], r[C_PNAME], avail])
            sales_hist[r[C_PID]] = (r[C_PNAME], m[0])
        return out

    # 庫存表＝pchome採購快照（維持匯出檔原順序）
    main = [r for r in csv_rows if r[C_VID] == "7777"]
    tabs.append({"name": "庫存表", "type": "stock",
                 "headers": stock_headers("廠商名稱"),
                 "rows": stock_rows(main, C_VNAME)})

    # 含庫存廠商頁（首欄改館名稱，週銷大→小）
    for vid, name in STOCK_VENDORS:
        rows = [r for r in csv_rows if eff_vendor(r) == vid]
        built = stock_rows(rows, C_STORE)
        built.sort(key=lambda x: -x[7])
        tabs.append({"name": name, "type": "stock",
                     "headers": stock_headers("館名稱"), "rows": built})

    # 純銷量廠商頁：CSV 全品項（含週銷 0）＋本週有銷量但不在匯出檔的商品
    for vids, name in SALES_VENDORS:
        vids = set(vids)
        rows = [r for r in csv_rows if eff_vendor(r) in vids]
        seen = {r[C_PID] for r in rows}
        built = []
        for r in rows:
            m = metrics(sales, r[C_PID])
            built.append([r[C_PID], r[C_PNAME], r[C_STORE]] + [m[0]] + m[2:])
            sales_hist.setdefault(r[C_PID], (r[C_PNAME], m[0]))
        for pid, s in sales.items():
            if s["vendor"] in vids and pid not in seen:
                m = metrics(sales, pid)
                built.append([pid, s["name"], s["museum"] + "（不在匯出檔）"] + [m[0]] + m[2:])
                sales_hist.setdefault(pid, (s["name"], m[0]))
        built.sort(key=lambda x: (-x[3], x[1]))
        tabs.append({"name": name, "type": "sales",
                     "headers": ["商品編號", "商品名稱", "館名稱",
                                 f"週銷 {label}", "業績金額", "毛利額", "毛利率"],
                     "rows": built})

    return tabs, qty_hist, [[pid, n, q] for pid, (n, q) in sales_hist.items()]


def push(payload) -> dict:
    if not CONFIG.exists():
        sys.exit(f"缺 {CONFIG}（webapp_url/token），無法寫入 Google Sheet")
    cfg = json.loads(CONFIG.read_text(encoding="utf-8-sig"))
    url, token = cfg.get("webapp_url"), cfg.get("token")
    if not url or not token:
        sys.exit("config.local.json 缺 webapp_url 或 token")
    payload["token"] = token
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"})
    resp = urllib.request.urlopen(req, timeout=300)  # GAS 會 302 轉址，urllib 會跟過去
    result = json.loads(resp.read().decode("utf-8"))
    if not result.get("ok"):
        sys.exit(f"寫入 Google Sheet 失敗：{result.get('error')}")
    return result


def main():
    if len(sys.argv) > 2:
        csv_path, sales_path = Path(sys.argv[1]), Path(sys.argv[2])
    else:
        csv_path = find_latest(r"^20\d{8}_.*\.csv$", "全站廠商商品匯出 CSV")
        sales_path = find_latest(r"^\d{4}-\d{4}即時業績\.xlsx$", "即時業績檔")
    print(f"全站 CSV：{csv_path}")
    print(f"業績檔　：{sales_path}")

    csv_rows = load_csv(csv_path)
    sales = load_sales(sales_path)
    label = week_label(sales_path)
    print(f"CSV {len(csv_rows)} 筆、業績歸戶 {len(sales)} 個商品、週區間 {label}")

    tabs, qty_hist, sales_hist = build_payload(csv_rows, sales, label)
    payload = {"date": csv_date(csv_path), "weekLabel": label,
               "tabs": tabs, "qtyHistory": qty_hist, "salesHistory": sales_hist}

    REPORTS.mkdir(exist_ok=True)
    backup = REPORTS / f"payload_{datetime.now():%Y%m%d}.json"
    backup.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    result = push(payload)
    print(f"寫入完成（{result['updatedAt']}）：")
    for t in tabs:
        print(f"  {t['name']}：{len(t['rows'])} 筆")
    print(f"  可賣量歷史欄 {payload['date']}、週銷歷史欄 {label}")
    print(f"本機備份：{backup}")


if __name__ == "__main__":
    main()

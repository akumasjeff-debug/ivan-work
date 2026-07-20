# 電玩庫存表 — 專案總覽

PChome 廠商商品的庫存管理，本體是一份 **Google 試算表**。
資料來源＝PChome 後台下載的**廠商商品匯出檔**（Downloads 的 `20########_XXXX.xls`，實際是 xlsx），
用本機腳本轉成六欄貼進試算表。

## 試算表

- 網址：https://docs.google.com/spreadsheets/d/1KTfQSanQiciSfIM5QF2UHKXbBtHa9fGS1DfK_Quevl4/edit
- 「庫存表」分頁七欄＝最新快照：**廠商名稱｜商品編號｜商品名稱｜可賣量｜成本｜售價｜來源廠商**
  可賣量 = 0 整列標紅；標題列有篩選器可依廠商／可賣量排序過濾。
- 「可賣量歷史」分頁＝一列一商品、一欄一匯入日期（取匯出檔檔名日期），
  每次匯入自動加一欄，各週可賣量並排看差距（每週一比對用）。

## 檔案

| 檔案 | 用途 |
|------|------|
| `匯入轉換.py` | 匯出檔 → 六欄 → **直接寫入 Google Sheet**（Web App）；未設定時退回剪貼簿模式。TSV 備份存 `reports/` |
| `apps-script/setup.gs` | 試算表一鍵建置（分頁、格式、缺貨標紅、篩選器）＋ `doPost` 寫入端點，重跑 setup 不清資料 |
| `config.local.json` | Web App 網址＋token（gitignore 僅本機） |

## 每次更新流程

1. PChome 後台下載廠商商品匯出檔（存到 Downloads）
2. `py 電玩庫存表\匯入轉換.py`（自動抓 Downloads 最新匯出檔；也可帶檔案路徑參數）→ 直接寫入試算表，完成

（未部署 Web App 時第 2 步會改複製到剪貼簿，需手動到「庫存表」A1 貼上）

## 未來可擴充

- 串 PChome button API 即時查可賣量（比價程式已有現成邏輯）
- 每次匯入留歷史快照分頁，追蹤可賣量／成本變化
- GAS 定時備份、低庫存提醒

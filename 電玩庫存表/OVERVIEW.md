# 電玩庫存表 — 專案總覽

PChome 廠商商品的庫存管理，本體是一份 **Google 試算表**。
資料來源＝PChome 後台下載的**廠商商品匯出檔**（Downloads 的 `20########_XXXX.xls`，實際是 xlsx），
用本機腳本轉成六欄貼進試算表。

## 試算表

- 網址：https://docs.google.com/spreadsheets/d/1KTfQSanQiciSfIM5QF2UHKXbBtHa9fGS1DfK_Quevl4/edit
- 「庫存表」分頁六欄：**廠商名稱｜商品編號｜商品名稱｜可賣量｜成本｜售價**
- 可賣量 = 0 整列標紅；標題列有篩選器可依廠商／可賣量排序過濾。

## 檔案

| 檔案 | 用途 |
|------|------|
| `匯入轉換.py` | 匯出檔 → 六欄 TSV（存 `reports/`）＋自動進剪貼簿 |
| `apps-script/setup.gs` | 試算表一鍵建置（分頁、格式、缺貨標紅、篩選器），重跑不清資料 |

## 每次更新流程

1. PChome 後台下載廠商商品匯出檔（存到 Downloads）
2. `py 電玩庫存表\匯入轉換.py`（自動抓 Downloads 最新匯出檔；也可帶檔案路徑參數）
3. 到試算表「庫存表」分頁點 **A1** → Ctrl+V 貼上（連標題整份覆蓋）

## 未來可擴充

- 串 PChome button API 即時查可賣量（比價程式已有現成邏輯）
- 每次匯入留歷史快照分頁，追蹤可賣量／成本變化
- GAS 定時備份、低庫存提醒

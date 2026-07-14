# 合成台 Compositor — 專案規則

純前端、**單一 HTML 檔**（`compositor.html`，HTML/CSS/JS 全在裡面）的影像合成工具。
細節（功能清單、資料結構、儲存架構）看 `HANDOVER.md`；功能分類看 `OVERVIEW.md`。

## 執行

- `start.bat` 開本機伺服器後用桌機 Chrome/Edge 開，**不能 `file://` 直接點開**
  （File System Access、IndexedDB、CDN 去背模型都要 http(s)）。
- 去背模型走 jsDelivr CDN（`@imgly/background-removal@1.7.0`），首次需連網下載數十 MB。

## 儲存架構鐵則

- **二進位（圖/字型）一律走 IndexedDB 封裝**：`putBlob / getBlobURL / delBlob`，
  不要直接把圖塞 localStorage。
- localStorage 只放輕量 meta：key `compositor.meta.v6`（`META_KEY`）。
- 新增資料欄位時，load 要給預設值（`x||預設`、`!!x` 風格），保持舊存檔相容；
  版位類欄位統一走 `normPlacement()` 補預設。
- 刪 asset/frame/font 要連帶 `delBlob`，避免孤兒二進位。

## 雲端共享（現況，HANDOVER 部分段落較舊）

- 目前共享走 **Supabase Storage**（`SB_KEY='compositor.supabase.v1'`）；
  上傳檔名必須清成**純 ASCII**（中文檔名會 InvalidKey 400）。
- 舊的「本機共享資料夾」（File System Access 備份）**已移除**，
  HANDOVER 裡相關描述已過時，勿照著恢復。

## 改完必做

1. 語法檢查（node 取出 `<script>` 內容去 import 後 `new Function(body)` 驗證）。
2. `http://localhost` 實測：上傳 → 去背 → 輸出 → **重新整理後資料還在**。
3. 標題有版本標記（如 v2），部署 GitHub Pages 前記得遞增，方便確認頁面已更新。

## 其他

- 輸出的備份圖（png/jpg…）已被 `.gitignore` 排除，不要 commit。
- 已知：素材本體刪除不可 undo。（旋轉時縮放/裁切控點偏移已於 v3 用 `keepAnchored()` 補正）

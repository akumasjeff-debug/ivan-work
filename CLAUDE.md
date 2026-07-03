# ivan-work — 工作區說明

這個 git 倉庫（`ivan-work`）是一個**多專案工作區**，底下放數個彼此獨立的小工具專案。

## 慣例（重要）

- **每個專案各自獨立成一個資料夾。** 一個專案 = 一個資料夾，不要把不同專案的檔案混在根目錄或同一夾。
- 新專案 → 開一個新資料夾，把該專案所有檔案放進去，並各自帶：
  - 主程式檔（例如 `*.html`）
  - `OVERVIEW.md`（專案總覽 / 功能分類）
  - `HANDOVER.md`（交接細節：架構、資料結構、注意事項）
  - 需要時附 `start.bat`（本機啟動用）
- 根目錄只放跨專案共用的東西（本檔 `CLAUDE.md`、`.gitignore`、`.git`、入口頁 `index.html`、共用字型 `fonts/`）。
- **獨立 git repo 的專案，資料夾名稱 = 該 repo 在 GitHub 上的名稱**（例：`air-conditioner/`、`pokemon-funsite/`），並在本 repo 的 `.gitignore` 排除。

## 目前的專案

| 資料夾 | 名稱 | 說明 | 主檔 | 啟動 |
|--------|------|------|------|------|
| `合成台/` | 合成台 Compositor | 純前端、單一 HTML 的影像合成工具（圖層、文字特效、去背 AI/本機/吸管、裁切、版位、批次/備份匯出入） | `合成台/compositor.html` | `合成台/start.bat`（桌面捷徑「影像合成台」） |
| `著色本/` | 著色本 | coloring 工具 | `著色本/coloring.html` | `著色本/start.bat` |
| `遊戲下單數量分析/` | 遊戲下單數量分析 | 實體遊戲商品進貨前的決策分析：聲量調查→需求推估→建議下單量，產出 Markdown 報告（放 `reports/`） | `遊戲下單數量分析/報告範本.md` | 無（純文件） |
| `air-conditioner/` | 冷氣安裝・錄音分析 | 客戶通話錄音→Gemini 逐字稿→AI 抽欄位標色→Firebase RTDB。**獨立 git repo**（github.com/akumasjeff-debug/air-conditioner），已在本 repo `.gitignore` 排除 | `air-conditioner/aircon.html` | `air-conditioner/start.bat`（port 8002） |
| `pokemon-funsite/` | Pokemon 寶可夢旗艦館 | PChome 旗艦館頁面（index.html + img/css/js）。**獨立 git repo**（github.com/akumasjeff-debug/pokemon-funsite），已在本 repo `.gitignore` 排除。改完要打包 zip 放下載區給操作者上傳 PChome | `pokemon-funsite/index.html` | 無（靜態頁） |
| `couple-court/` | Ai公道伯（名稱暫定案） | 手機 App（iOS+Android）：情侶雙人綁定的關係經營工具＋AI 吵架判決。**構想討論階段**，尚無程式碼。暫定 React Native + Expo + Firebase。**獨立 git repo**（github.com/akumasjeff-debug/couple-court），已在本 repo `.gitignore` 排除 | `couple-court/OVERVIEW.md` | 無（尚未建骨架） |

各專案的細節看該資料夾內的 `OVERVIEW.md` 與 `HANDOVER.md`。

## 執行環境備註

- 這些工具多為「桌機 Chrome/Edge + 本機 http server」才能完整運作（用到 File System Access API、IndexedDB、CDN 模型）。用各自的 `start.bat` 開本機伺服器，不要用 `file://` 直接點開。
- `start.bat` 內容請保持**純 ASCII**（中文會被 cmd 用錯誤編碼切碎而失效）。

## Git

- `.gitignore` 會排除：`.claude/`（個人設定）、`合成台/` 的備份輸出圖（`*.png/jpg/...`，屬測試/實際備份產物）、`air-conditioner/` 與 `pokemon-funsite/`（各自獨立 git repo）。專案程式檔仍會被追蹤。
- 遠端：`https://github.com/akumasjeff-debug/ivan-work`（`main`）。

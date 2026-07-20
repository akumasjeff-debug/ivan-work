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
- **每個專案資料夾放一個歸屬標記檔**（檔名即標籤、`_` 開頭排最前），在檔案總管一眼看出上傳歸屬，三種：
  - `_歸屬=ivan-work（會上傳GitHub）.txt` — 主 repo 追蹤
  - `_歸屬=獨立repo <名稱>.txt` — 自己的 GitHub repo（該 repo 的 `.gitignore` 已排除 `_歸屬=*.txt`，標記檔僅存本機）
  - `_歸屬=僅本機（不上傳GitHub）.txt` — 完全不上傳
  - 新專案開資料夾時記得一併放。

## 目前的專案

| 資料夾 | 名稱 | 說明 | 主檔 | 啟動 |
|--------|------|------|------|------|
| `合成台/` | 合成台 Compositor | 純前端、單一 HTML 的影像合成工具（圖層、文字特效、去背 AI/本機/吸管、裁切、版位、批次/備份匯出入） | `合成台/compositor.html` | `合成台/start.bat`（桌面捷徑「影像合成台」） |
| `著色本/` | 著色本 | coloring 工具 | `著色本/coloring.html` | `著色本/start.bat` |
| `PTT彈幕/` | PTT 留言彈幕 | 選 PTT 熱門看板文章，推文化作彈幕、常駐 5 秒輪詢自動更新。主要版本＝桌面覆蓋層（tkinter：透明置頂、滑鼠穿透、可拖曳調位置大小）；另有網頁版（server.py 代理＋App 模式視窗，port 8003） | `PTT彈幕/overlay.pyw` | `PTT彈幕/start.bat`（覆蓋層版，桌面捷徑「PTT Danmaku」）；網頁版 `start-web.bat` |
| `遊戲下單數量分析/` | 遊戲下單數量分析 | 實體遊戲商品進貨前的決策分析：聲量調查→需求推估→建議下單量，產出 Markdown 報告（放 `reports/`） | `遊戲下單數量分析/報告範本.md` | 無（純文件） |
| `air-conditioner/` | 冷氣安裝・錄音分析 | 客戶通話錄音→Gemini 逐字稿→AI 抽欄位標色→Firebase RTDB。**獨立 git repo**（github.com/akumasjeff-debug/air-conditioner），已在本 repo `.gitignore` 排除 | `air-conditioner/aircon.html` | `air-conditioner/start.bat`（port 8002） |
| `pokemon-funsite/` | Pokemon 寶可夢旗艦館 | PChome 旗艦館頁面（index.html + img/css/js）。**獨立 git repo**（github.com/akumasjeff-debug/pokemon-funsite），已在本 repo `.gitignore` 排除。改完要打包 zip 放下載區給操作者上傳 PChome | `pokemon-funsite/index.html` | 無（靜態頁） |
| `couple-court/` | Ai公道伯（名稱暫定案） | 手機 App（iOS+Android）：情侶雙人綁定的關係經營工具＋AI 吵架判決。React Native + Expo SDK 57 + TypeScript。**MVP 畫面 v1 完成（2026-07-14）**：關係列表/配對/連結詳情/個人小檔案/願望清單，跑記憶體假資料層；Firebase 未接。**獨立 git repo**（github.com/akumasjeff-debug/couple-court），已在本 repo `.gitignore` 排除 | `couple-court/OVERVIEW.md` | `couple-court/start.bat`＋手機 Expo Go 掃 QR |
| `pchome-listing/` | 賣場資訊文案 | PChome 24h 商品上架素材（文案 HTML／主圖／GIF／欄位文字），一商品一子資料夾（NS2 主機、PS5×3、NS 節奏天國）。遊戲商品固定流程見該 repo 的 `遊戲商品SOP.md`。**獨立 git repo**（github.com/akumasjeff-debug/pchome-listing，Private），已在本 repo `.gitignore` 排除 | `pchome-listing/OVERVIEW.md` | 無（`detail-預覽.html` 瀏覽器直接開） |
| `內部比價程式/` | 內部比價程式 | PChome 24h 比價 CLI：區域→賣場→商品（過濾無可賣量）→品名搜全站同商品比價，產出 xlsx/md/tsv 報表（放 `reports/`）。**僅存本機、不上傳 GitHub**（已在 `.gitignore` 排除）。API 端點與可賣量判讀見該夾 `HANDOVER.md` | `內部比價程式/比價.py` | `py 內部比價程式\比價.py`（CLI，無伺服器） |
| `外部比價程式/` | 外部比價程式（跨站比價） | 拿 PChome 賣場商品去**外站**比價（v1: momo，站點 adapter 可擴充），一款遊戲一列、預設賣太貴的排前面，產出 HTML/TSV 報表（放 `reports/`）。PChome 端邏輯承襲內部比價程式，另加品牌詞/二手/版本位階/代數等跨站比對規則。**僅存本機、不上傳 GitHub**（已在 `.gitignore` 排除）。momo 解析細節見該夾 `HANDOVER.md` | `外部比價程式/跨站比價.py` | `py 外部比價程式\跨站比價.py <賣場Id>`（CLI，無伺服器） |
| `PS旗艦館/` | PS旗艦館 | PChome PlayStation 品牌旗艦館（sites/playstation）：前台+本機後台+Firebase 資料庫+每日 GAS 自動化（備份/巡檢/PID切換）+每週一缺漏/缺貨例行。**實際檔案在 `C:\工作用資料夾\PlayStation 旗艦店\PS 新旗艦館\`（就地維護、不搬動）**，本資料夾僅登錄點，已在 `.gitignore` 排除。交接細節看實際資料夾的 `HANDOVER.md` | `PS旗艦館/OVERVIEW.md` | 無（改完打增量 zip 上傳 PChome） |
| `Xbox旗艦館/` | Xbox旗艦館 | PChome Xbox 品牌旗艦館（sites/xbox）：前台（控制器/Game Pass/YouTube/Banner）+本機後台+Firebase（與 PS 同一專案）+每日 GAS（GA4 日報/賣場巡檢）+每週一缺漏/缺貨例行（與 PS 一起）。**實際檔案在 `C:\工作用資料夾\Xbox 旗艦店\Xbox旗艦館 (Claude code用)\`（就地維護、不搬動）**，本資料夾僅登錄點，已在 `.gitignore` 排除。交接細節看實際資料夾的 `HANDOVER.md` | `Xbox旗艦館/OVERVIEW.md` | 無（改完打增量 zip 上傳 PChome） |
| `ivan-video/` | 影片大師 | AI 驅動的 9:16 直式短影音生成（遊戲推薦 roundup）：Python pipeline（`tools/pipeline/`＋`tools/overlays/`）＋F5-TTS（家機 GPU）＋Playwright overlay＋FFmpeg 4K 輸出，一專案一夾在 `projects/`。含視覺編輯器、TTS 發音驗證（本機 Whisper）、YT 素材生成。**獨立 git repo**（github.com/akumasjeff-debug/ivan-video），**家機也在開發，動工前先 `git pull`**；已在本 repo `.gitignore` 排除，媒體大檔該 repo 自身已 gitignore | `ivan-video/CLAUDE.md` | 無（指令見 `ivan-video/docs/commands.md`，bash 跑、禁 PowerShell） |
| `任天堂旗艦館/` | 任天堂旗艦館 | PChome Nintendo 品牌旗艦館（sites/nintendo）改造案：**規劃階段（2026-07-14 評估完成，尚未動工）**。目標＝套 PS 館模式（Firebase+後台+GAS+例行）並保留現有角色分區/雙世代導覽優點；另做「翻面」非本家 Switch 遊戲面。**實際檔案在 `C:\工作用資料夾\Nintendo 旗艦館\NS旗艦館-Funsite檔\`（使用者自製、就地維護）**，本資料夾僅登錄點，已在 `.gitignore` 排除。決策與商品源賣場代碼看本夾 `OVERVIEW.md` | `任天堂旗艦館/OVERVIEW.md` | 無（改完打增量 zip 上傳 PChome，`nintendo_YYYYMMDD.zip`） |
| `旗艦館總後台/` | 旗艦館總後台 | PS／Xbox／Nintendo 三館後台合併成單一 `index.html`：一次登入（三館共用 Firebase 專案）＋頂部館別頁籤，寫入邏輯與各館原 admin.html 完全相同。**會上傳 GitHub、走 GitHub Pages 網頁版使用**（比照合成台：改完直接 commit+push，標題 vN 版本標記確認更新）。原三館 admin.html 保留備援；後台功能修改以本檔為主。擴充第四館（如 Pokemon）的步驟見本夾 `OVERVIEW.md` | `旗艦館總後台/OVERVIEW.md` | Pages：`https://akumasjeff-debug.github.io/ivan-work/旗艦館總後台/`（本機雙擊 `index.html` 亦可） |
| `電玩庫存表/` | 電玩庫存表 | PChome 電玩商品庫存＋週銷管理，**本體是 Google 試算表 13 分頁**：庫存表（pchome採購）＋含庫存廠商頁（傑仕登/宏碁遊戲）＋8 純銷量廠商頁＋可賣量/週銷歷史。每週下載兩檔（全站廠商 CSV＋MMDD-MMDD即時業績.xlsx）→ `py 電玩庫存表\匯入轉換.py` → **經 GAS Web App 一鍵寫入**。欄位含週銷/可售週數/業績/毛利，缺貨有銷量＝深紅警示。廠商歸戶＝來源廠商優先。`reports/` 與 `config.local.json` 已 gitignore；細節見本夾 `HANDOVER.md` | `電玩庫存表/OVERVIEW.md` | `py 電玩庫存表\匯入轉換.py`（一鍵更新）；表建置＝Apps Script 跑 `setup.gs` |

**進某個專案工作前，先讀該資料夾的 `CLAUDE.md`（若有，是精簡規則）**；要動架構或資料結構再讀 `HANDOVER.md`（完整交接細節），功能全貌看 `OVERVIEW.md`。目前已有子 `CLAUDE.md` 的專案：`合成台/`、`內部比價程式/`、`外部比價程式/`、`ivan-video/`。

## 執行環境備註

- 這些工具多為「桌機 Chrome/Edge + 本機 http server」才能完整運作（用到 File System Access API、IndexedDB、CDN 模型）。用各自的 `start.bat` 開本機伺服器，不要用 `file://` 直接點開。
- `start.bat` 內容請保持**純 ASCII**（中文會被 cmd 用錯誤編碼切碎而失效）。

## Git

- `.gitignore` 會排除：`.claude/`（個人設定）、`合成台/` 的備份輸出圖（`*.png/jpg/...`，屬測試/實際備份產物）、`air-conditioner/` 與 `pokemon-funsite/`（各自獨立 git repo）。專案程式檔仍會被追蹤。
- 遠端：`https://github.com/akumasjeff-debug/ivan-work`（`main`）。

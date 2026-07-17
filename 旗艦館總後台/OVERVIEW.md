# 旗艦館總後台

三個 PChome 品牌旗艦館（PlayStation／Xbox／Nintendo）的後台合併成**一個 HTML**，
一次登入管三館，頂部頁籤切換館別。

## 使用方式

- **網頁版（主要）**：GitHub Pages
  `https://akumasjeff-debug.github.io/ivan-work/旗艦館總後台/`
  改版後看頁面左上「旗艦館總後台 vN」版本標記確認已更新（有快取按 Ctrl+F5）。
- 本機：直接雙擊 `index.html` 也能用（全 CDN 資源、無相對依賴）。
- 登入：三館共用同一個 Firebase 專案（`game-release-schedule`）與同一組管理員帳號，登入一次即可。

## 架構（單一檔案 `index.html`）

| 區塊 | 說明 |
|------|------|
| 共用層 | Firebase compat SDK 單一初始化、共用登入/登出、館別切換（記住上次停留館別 localStorage）、PChome 透視鏡、jspreadsheet 小工具（右鍵選單、自適應欄寬） |
| `#brand-ps` ＋ `var PS = (…)()` | PS 館：試算表直編（輪播/遊戲/周邊 批次新增＋全量清單）＋三欄前台模擬預覽。Firebase 路徑：`site_banners` / `pchome_games` / `pchome_hardware` |
| `#brand-xbox` ＋ Xbox 全域函式群 | Xbox 館：深色表單分頁（總覽拖曳排序/Banner/控制器/Game Pass/YouTube）。Firebase 路徑：`xbox_site_banners` / `xbox_controllers` / `xbox_gamepass` / `xbox_youtube`。深色 CSS 全部限定在 `#brand-xbox` 下，不影響其他館 |
| `#brand-nintendo` ＋ `var NN = (…)()` | 任天堂館：試算表直編（輪播/遊戲庫 NS2+NS/周邊庫，合併寫回不洗掉新欄位）＋前台分組預覽。Firebase 路徑：`nintendo_banners` / `nintendo_games` / `nintendo_hardware` |

**寫入邏輯與各館原版 admin.html 完全相同**（PS/NN 的 set() 全量同步、NN 的 mergeRow 合併寫回、Xbox 的 push/update/remove），資料結構沒有任何變動。

## 與原本三個 admin.html 的關係

- 原檔不動、繼續存在：
  - `C:\工作用資料夾\PlayStation 旗艦店\PS 新旗艦館\admin.html`
  - `C:\工作用資料夾\Xbox 旗艦店\Xbox旗艦館 (Claude code用)\admin.html`
  - `C:\工作用資料夾\Nintendo 旗艦館\NS旗艦館-Funsite檔\admin.html`
- **後續後台功能修改以本檔（總後台）為主**；若某館前台資料結構改了（例如遊戲庫加欄位），
  要同步改本檔對應館的區塊（必要時原 admin.html 一併改，維持備援可用）。

## 未來擴充：納入第四館（例：Pokemon 旗艦館）

檔案已是「一館一區塊」的註冊表結構，加新館只要四步，不動其他館：

1. **頂欄**加一顆館別按鈕：`<button id="brand-btn-pk" onclick="switchBrand('pk')">`，
   並在 CSS 加 `.brand-btn.active-pk`（品牌色）。
2. **註冊表**各加一筆：`FRONT_LINKS.pk`（前台網址）、`BRAND_PANES.pk = 'brand-pokemon'`、`BRAND_ACTIVE_CLASS.pk = 'active-pk'`。
3. **加一個 pane**：`<div id="brand-pokemon" class="brand-pane">…該館後台 UI…</div>`
   （若要深色/特殊主題，CSS 全部用 `#brand-pokemon` 前綴限定）。
4. **加一個命名空間**：`var PK = (function(){ … })()`，登入後在 `onAuthStateChanged` 裡呼叫 `PK.start()`。

前提：新館的資料也放在同一個 Firebase 專案（各館用自己的節點前綴，如 `pokemon_*`），登入就能共用。
Pokemon 旗艦館目前是純靜態頁（改完打 zip 上傳 PChome、無 Firebase），要納入前得先幫它做 Firebase 化的前台＋資料節點。

## 版本紀錄

- v1（2026-07-17）：初版——PS/Xbox/Nintendo 三館後台合併、單一登入、館別頁籤、共用透視鏡。

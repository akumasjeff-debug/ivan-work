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
| `#brand-ps` ＋ `var PS = (…)()` | PS 館：試算表直編（輪播/遊戲/周邊 批次新增＋全量清單）＋**⭐ 館長推薦與 🔥 期待遊戲挑選器**＋三欄前台模擬預覽。Firebase 路徑：`site_banners`（版頭工作台）/ `pchome_games` / `pchome_hardware` / `ps_featured` / `ps_expected` |
| `#brand-xbox` ＋ Xbox 全域函式群 ＋ `XBLAB` | Xbox 館：深色表單分頁（總覽拖曳排序/**前台模擬**/**版頭工作台**/Banner 舊表單/控制器/Game Pass/YouTube）。Firebase 路徑：`xbox_site_banners` / `xbox_controllers` / `xbox_gamepass` / `xbox_youtube`。深色 CSS 全部限定在 `#brand-xbox` 下，不影響其他館 |
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

## PS 館「⭐ 館長推薦」挑選器（v3 新增）

前台 PS 館左欄最上方那塊輪播的內容來源，寫進 Firebase `ps_featured`。

- **左側候選清單**＝遊戲資料庫（`pchome_games` 有 PID 的）＋前台右欄那四個賣場（`DGCK8B` 主機／`DGCK8C` 手把／`DGCK8D` 配件／`DGCK8E` 數位商品，開頁時用 JSONP 即時抓）。可搜品名或 PID、可依來源過濾，點「＋」加入。
- **右側已選清單**＝由上而下即前台順序，`▲▼` 調序、`✕` 移除；每筆可填自訂標題（留空＝自動抓 PChome 品名）、推薦語、上下架時間（留空＝長期）。
- 存檔用 `set()` 整包覆蓋 `ps_featured`，key 為 `f_000` 遞增、`sort_order` 即列序。
- **只存 PID 與人工覆寫欄位**；品名、白圖、售價、缺貨狀態前台都自己抓，所以不必維護圖片。
- 改完前台重整即生效，**不用打 zip 重傳 PChome**。

## PS 館「🔥 期待遊戲」挑選器（v4 新增）

前台 PS 館左欄那個**純文字榜**的內容來源，寫進 Firebase `ps_expected`。

- **候選只有遊戲**（`pchome_games` 全部，含還沒建商品、沒有 PID 的），預設只列「尚未開放訂購」的，
  可切「全部遊戲」。每列標可訂購狀態：綠＝可訂購、紫＝尚未開放（顯示實際 `ButtonType`）、灰＝無 PID。
  狀態靠開頁時 JSONP 打 `prod/button` 取得。
- **存的是 `game_id`（Firebase key）不是 PID**，所以 GTA6、王國之心4 這種還沒建商品的也選得到。
- 右側已選清單 `▲▼` 調序、`✕` 移除；每筆可填自訂標題、期待語、上下架時間。**沒有圖片欄位**（前台是純文字榜）。
- 存檔用 `set()` 整包覆蓋，key 為 `e_000` 遞增、`sort_order` 即列序。

## Xbox 館一頁式工作台（v6 改版）

Xbox 館**沒有分頁了**，整館就是一頁：捲一頁看完前台六個區塊，**預設什麼都不展開**，
點卡片才從右側滑出抽屜設定細節。程式都在 `var XBLAB = (function(){…})()`。

### 版面（＝前台順序）

| 區塊 | 資料源 | 標示 | 點下去 |
|------|--------|------|--------|
| ① 🖼 版頭 Banner | Firebase `xbox_site_banners` | 可維護 | 開抽屜設定該張 |
| ② 🎮 控制器牆＋Elite | **賣場 `DGBJAH`**（JSONP 即時） | 賣場維護 | 開賣場 |
| ③ 💳 Game Pass | Firebase `xbox_gamepass`（價格顯示現售價） | 可維護 | 抽屜開舊表單並帶入該筆 |
| ④ 🎁 禮品卡與遊戲貨幣 | **賣場 `DGBJI4`**（JSONP 即時） | 賣場維護 | 開賣場 |
| ⑤ 🎬 精選影片 | Firebase `xbox_youtube`（GAS 每日自動） | 可維護 | 抽屜開舊表單並帶入該筆 |

- **①「版頭」把首屏輪播與底部「更多精選」放在同一個區塊**，中間用虛線分隔並標「以下這組在前台會排在最尾巴」。
  兩組相鄰才好互拖；`sort_order` 1–5 ＝首屏、6+ ＝底部，儲存時自動重算，維護者不用碰數字。
- banner 依**現在時間**套上下架、`pending` 的不顯示——所見即前台所見。缺貨商品淡化標「補貨中」。
- 舊的表單分頁（總覽／Banner 舊表單／控制器／Game Pass／YouTube）開機時被收進 `#xb-pane-holder`，
  `openPane()` 用時**把整個節點搬進抽屜**、關閉時搬回去——所以原有欄位、id、事件全部照舊，表單沒有重寫。

### 版頭 Banner 的完整流程

1. **拖圖進「＋」框**（首屏／底部各一個，也可點框選檔）→ canvas 產出
   **PC `1644×604`** ＋ **手機 `900×900`（1:1 正方形）**，jpg 由 q .86 往下壓到單張 < 700KB，
   自動命名 `xb-YYYYMMDD-NN.jpg`／`-m.jpg`（純英數、不與既有檔名重複、不覆蓋舊檔）。
2. **點卡片開抽屜**：PC 預覽／手機方形預覽＋**裁切位置滑桿**／標題／連結／上下架時間／改放另一組／刪除。
3. **拖曳卡片**換順序，兩組之間也能互拖。
4. 上方操作列：**💾 儲存** → **📦 產生上傳包**（JSZip 打成 `xbox_YYYYMMDD.zip`，內含 `img/banner/*.jpg`）
   → 人工上傳 PChome → **✅ 標記已上傳**（解除 `pending`，前台才開始顯示）。

**手機版尺寸為什麼是 1:1（2026-08-18 修正）**

- 本機舊素材 `1200×450` 比例 2.67，跟 PC 版 `1644×604`（2.72）幾乎一樣 → 那種「手機版」只是同一張縮小，**沒有意義**
  （手機直式螢幕上寬版 banner 只有約 146px 高）。
- 線上最新那張（2026-08-05 halo）手機版是 `20260805-462-462.jpg`＝**正方形**，這才是現行慣例。
  工作台改產 900×900（比 462 銳利，仍在 ~200KB 內）。
- 但寬圖裁成正方形會**砍掉約 6 成寬度**，所以抽屜裡一定看得到方形預覽，並提供**水平裁切位置滑桿**；
  滑桿要有「本次載入的原圖」才能重裁（`origImages` 只存在記憶體），重整後想調就重拖一次圖。
- 不想要方形也可以：抽屜按「沿用 PC 圖」清掉 `img_mobile`，前台手機就直接用 PC 那張。

**關鍵限制：後台無法把圖送上 PChome**（沒有 API，一定要人工登入上傳），所以才有 `pending` 這個機制。

- **`pending`（boolean）**：`true` ＝ 資料已建、圖還沒上傳。
  **前台 `xbox/index.html` 的 `loadBanners()` 會直接跳過 `pending` 的 banner**，避免圖沒上傳就開天窗。
- 還沒上傳的圖以 dataURL 暫存在 `localStorage['xblab_pending_v1']`，換電腦或清快取就沒了
  （Firebase 記錄還在，重拖一次圖即可）。按「標記已上傳」後清掉暫存。

## PS 館「🖼 版頭工作台」（v7 新增）

比照 Xbox 的版頭工作台，但**只做 PC 圖 1644×604**——PS 前台不吃手機版 banner
（`site_banners.img_mobile_url` 欄位存在，前台 `bootData` 只讀 `img_url`），做了也用不到。

- 把圖**拖進虛線框**（或點一下選檔）→ 自動置中裁成 1644×604 jpg，超過 700KB 逐級降畫質；
  檔名自動編 `ps-YYYYMMDD-NN.jpg`，卡片可**拖曳排序**，點卡片展開設定（標題／圖檔或網址／連結／上下架／裁切水平位置）。
- **關鍵差異：待上傳的列不寫進 Firebase。** PS 前台不認得 Xbox 那個 `pending` 欄位，
  若先寫進去，圖還沒上 PChome 前台就會破圖。所以新圖只留在瀏覽器 `localStorage`（`psban_pending_v1`），
  按「儲存順序與設定」只寫非待上傳的列；按「✅ 標記已上傳」才把它們一併寫入。**因此前台完全不用改、不用重傳 index.html。**
- 流程：拖圖 → 設定 → 📦 產生上傳包（下載 `playstation_YYYYMMDD.zip`，圖放 zip 根目錄，比照 PS 站台圖檔放站台根的慣例）
  → 上傳 PChome → 回來按「✅ 標記已上傳」。
- 舊的試算表表單收在下方 `<details>` 裡留作備援（貼外部圖網址用）。**兩邊都是 `set()` 整包覆蓋，一次只用一邊。**

## 任天堂館「🖼 版頭工作台」＋「🌱 皮克敏專頁維護」（v8 新增）

版頭工作台比照 PS（v7）架構，任天堂的差異：

- **一張來源圖自動裁兩張**：電腦 1732×626＋手機 768×698（前台 `<picture>` 在 `max-width:768px` 吃 `img_url_mb`），
  檔名接前台既有慣例 `img/banner/topBanner_l-N.jpg`／`topBanner_s-N.jpg`（掃現有列取最大號+1）；
  裁切滑桿電腦手機一起重裁。
- 寫回 **`nintendo_banners` 物件節點**（卡片順序 → `sort_order`，經 `mergeRow` 合併保留未顯示欄位）；
  待上傳邏輯與 PS 相同（localStorage `nnban_pending_v1`、不寫 Firebase、上傳包 `nintendo_YYYYMMDD.zip` 內含 `img/banner/` 路徑）。
- 舊試算表收進 `<details>` 備援；儲存都是整包覆蓋，一次只用一邊。

皮克敏專頁維護（`pikmin.htm` 的兩列商品，**陣列節點**，存檔即生效不用重傳 zip）：

- 左欄 `nintendo_pikmin`（授權商品）、右欄 `nintendo_pikmin_game`（系列遊戲）。
- **貼 PID／商品網址按 Enter** → ecapi JSONP 自動抓品名/價格/圖（**白圖 `Pic.W` 優先**，沒有才用主圖 `Pic.B`）；
  prod API 查不到（未開賣）就建空卡手動填。加入後自動展開編輯（品名要照**原廠規範**改寫，勿直接用賣場品名）。
- 卡片拖曳排序、點卡片改品名/價格/圖/連結，按該欄「儲存」整列覆蓋寫回。

## 版本紀錄

- v1（2026-07-17）：初版——PS/Xbox/Nintendo 三館後台合併、單一登入、館別頁籤、共用透視鏡。
- v2：PS/Xbox/Nintendo 各館維護項目補齊（任天堂區塊加非本家頁「Switch 全部遊戲」管理）。
- v3（2026-08-17）：PS 館新增「⭐ 館長推薦」挑選器（候選＝遊戲庫＋四賣場，寫入 `ps_featured`）。
- v4（2026-08-18）：「特別推薦」更名為「館長推薦」；PS 館新增「🔥 期待遊戲」挑選器（寫入 `ps_expected`，以 `game_id` 為主鍵，支援無 PID 的遊戲）。
- v5（2026-08-18）：Xbox 館新增「👁 前台模擬」與「🖼 版頭工作台」（拖圖→自動裁切命名→拖曳排序→產生上傳 zip→標記已上傳，新增 `pending` 欄位）；
  控制器分頁加註「賣場維護」警語（前台已改吃賣場 DGBJAH）；修掉總覽／Banner 舊表單縮圖用相對路徑看不到圖的問題。
- v6（2026-08-18）：Xbox 館**改成一頁式**——取消分頁，前台模擬即主畫面，點區塊才從側邊抽屜開細節（舊表單整個節點搬進抽屜重用）；
  版頭與底部「更多精選」併成同一區塊、可互拖；**手機版圖從 1200×450 改成 900×900 正方形**並加裁切位置滑桿（舊尺寸與 PC 版同比例、等於沒有手機版）。
- v7（2026-08-18）：PS 館版頭改成拖拉工作台（比照 Xbox，只做 PC 1644×604）；待上傳的圖不寫 Firebase，前台因此免改。
- v8（2026-08-24）：任天堂館版頭改成拖拉工作台（一圖自動裁電腦+手機雙版、檔名接 topBanner 慣例）；新增「🌱 皮克敏專頁維護」區塊（nintendo_pikmin／nintendo_pikmin_game 卡片式管理、貼 PID 自動抓資料白圖優先）。

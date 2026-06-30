# 著色本 — 專案總覽（OVERVIEW）

> 純前端、單一 HTML 檔的線稿上色工具。把一張圖片轉成黑白線稿，接著用油漆桶 / 筆刷在上面塗顏色，最後輸出 PNG。
> **桌機 Chrome / Edge**，建議在 `http://localhost` 下執行（雙擊 `start.bat` 即可；`file://` 直接開也能用，因為沒有用到需要安全來源的 API）。
> 主檔：`coloring.html`（單檔，HTML/CSS/JS 全包，約 470 行）。詳細接手見 `HANDOVER.md`。

---

## 一、功能分類

### 🖼 來源圖片（01）
- 上傳圖片（點「選擇圖片」或直接拖到畫布上）。
- 自動縮到處理解析度上限（長邊 `MAXSIZE = 2000px`），保留比例。
- 載入後白底 paint 層 + 線稿 line 層就緒，標題列顯示實際處理尺寸。

### ✏️ 線稿設定（02）
- 兩種模式：
  - **線稿（描邊）**：Sobel 邊緣偵測 → 門檻 → 黑線（適合照片 / 插畫）。
  - **黑白（剪影）**：亮度門檻，暗的區塊變黑（適合做剪影著色）。
- **靈敏度**：邊緣門檻 / 亮度門檻。
- **線條粗細**：對線條做 0–4 次膨脹（dilate）。
- **降噪 / 平滑**：產生前先做 box blur（近似高斯），數值越大線越乾淨。
- 「重新產生線稿」**只換線條，已塗的顏色保留**。

### 🎨 顏色（03）
- 16 色預設盤 + 系統色票（`<input type=color>`）+ 最近用色（最多 8 個）。
- 目前色顯示為大色塊 + HEX 文字。

### 🛠 上色工具（工具列）
- 🪣 **油漆桶（G）**：flood fill，**會被線條擋住**（以 `lineMask` 為牆），含色差容差吃抗鋸齒邊，不會整片漏色。
- 🖌️ **筆刷（B）**：圓頭連續線，粗細 1–120px。
- 🧽 **橡皮擦（E）**：以白色塗回（背景即白）。
- 💉 **吸管（I）**：點畫面取色，取完自動切回筆刷。
- ↶ ↷ **復原 / 重做**：`Ctrl+Z` / `Ctrl+Shift+Z` / `Ctrl+Y`（只記 paint 層，最多 25 步）。
- **縮放**：20–400%，載入時自動 fit 到畫面。

### 💾 輸出 / 清除（04）
- **清除上色**：把 paint 層填回白底（線稿保留），可 undo。
- **匯出 PNG**：paint 層 + line 層合成成一張白底 PNG，檔名帶尺寸，例 `coloring_1600x1200.png`。

---

## 二、技術架構

### 圖層（兩張疊放的 canvas，同尺寸）
- `#paintCanvas`（下層）：使用者所有上色動作都發生在這裡，起始白底。
- `#lineCanvas`（上層，`pointer-events:none`）：黑線、其餘透明，**永遠蓋在顏色之上** → 塗超出去也不會蓋住線。
- 兩張的像素尺寸 = 處理解析度 `W×H`；顯示尺寸用 CSS 隨 `zoom` 縮放。

### 關鍵全域狀態
```
srcImage        // 原圖 Image（重新產生線稿時重用）
lineMask        // Uint8Array(W*H)，1=線條像素 → 油漆桶的牆
W, H            // 處理解析度
zoom            // 顯示縮放
tool            // 'brush' | 'fill' | 'erase' | 'pick'
curColor        // 目前顏色 HEX
brushSize       // 筆刷直徑
undoStack/redoStack  // ImageData 快照（只含 paint 層）
```

### 線稿產生流程（`generateLineArt()`）
1. 原圖縮到 `W×H` → `toGray()` 灰階。
2. `blur>0` 時 `boxBlur()` 兩次一維近似高斯。
3. edge 模式跑 Sobel 算梯度幅值過門檻；thresh 模式用亮度門檻。
4. `dilate()` 依粗細加粗 → 存成 `lineMask`。
5. 依 mask 畫黑線到 `#lineCanvas`（其餘透明）。

### 油漆桶（`floodFill()`）
- stack-based flood fill，`seen` 用 `Uint8Array` 去重。
- 擴散條件：非線條像素（`lineMask[i]===0`）且與起點顏色差 < 容差（`tol`）。
- 直接改 `getImageData` 的 buffer 後 `putImageData` 寫回。

### 座標換算（`evtPos`）
- `x = (clientX - rect.left) / rect.width * W`（rect 已含 CSS 縮放，故 zoom 任何值都正確）。

---

## 三、執行方式
- 雙擊 `start.bat` → 用 Python `http.server` 起在 **8001 埠**（避開合成台的 8000，可同時開），約 2 秒自動開瀏覽器。
- 關掉黑視窗即停止伺服器。8001 被占用時，把檔內兩處 8001 改成 8081。

## 四、已知限制
- 線稿是傳統影像演算法（Sobel / 門檻），不是 AI 線稿；雜亂照片可能需要調靈敏度 + 降噪。
- 油漆桶以「線條是否封閉」決定填色範圍；線有缺口會漏色 → 可加粗線條或用筆刷補。
- 復原只涵蓋 paint 層（上色 / 清除 / 筆刷 / 橡皮 / 油漆桶），**重新產生線稿不進 undo**。
- 無持久化：重整頁面不保留（目前定位為「丟圖→塗→匯出」一次性流程）。
- 僅桌機 Chrome / Edge。

## 五、仍可再加（可選）
AI 等級線稿（dodge：灰階 ÷ 高斯模糊反相，純前端、更像手繪）、塗色限定在線內（brush 也吃 lineMask）、圖層 / 多色漸層、存檔續做（IndexedDB）、行動裝置觸控優化。

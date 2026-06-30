# 著色本 — 專案交接文件

純前端、單一 HTML 檔的線稿上色工具。流程：**丟一張圖 → 自動轉黑白線稿 → 用油漆桶 / 筆刷上色 → 匯出 PNG**。桌機 Chrome / Edge 使用。

主檔：`coloring.html`（單檔，所有 HTML/CSS/JS 都在裡面）。

---

## 執行環境

- 建議在 `http://localhost` 下開（雙擊 `start.bat`，用 Python `http.server` 起在 **8001 埠**，2 秒後自動開瀏覽器；關黑視窗即停）。
- 沒有用到需要安全來源的 API（無 File System Access / 無 CDN / 無 IndexedDB），所以 `file://` 直接點開也能跑；維持與合成台一致才用 `start.bat`。
- 8001 被占用：把 `start.bat` 內兩處 8001 改 8081。

---

## 目前已完成的功能（全部可用）

**01 來源圖片**
- 「選擇圖片」或拖放載入。縮到長邊 ≤ `MAXSIZE(2000)`，保留比例 → 設定 `W/H`、兩張 canvas、白底 paint 層，並 `generateLineArt()`。

**02 線稿設定**
- 模式：edge（Sobel 邊緣）/ thresh（亮度門檻剪影），seg 切換即時重產。
- 滑桿：靈敏度 `threshold`、線條粗細 `thickness`（dilate 次數 0–4）、降噪 `blur`（box blur 半徑 0–6）。`oninput` 更新數字、`onchange` 重產。
- 「重新產生線稿」= 再跑 `generateLineArt()`，**不動 paint 層**（顏色保留）。

**03 顏色**
- `PALETTE`（16 色）+ `<input type=color>` + `recent`（最近 8 色）。`setColor()` 統一更新目前色、色票 active、HEX 文字。

**工具列**
- 工具 `brush/fill/erase/pick`（`setTool`），筆刷粗細 1–120，縮放 20–400%。
- 復原 / 重做按鈕 + 鍵盤；快捷鍵 B/G/E/I。

**04 輸出 / 清除**
- 清除上色：paint 填白（先 `pushUndo`）。
- 匯出 PNG：離屏 canvas 先畫 paint 再畫 line → `toBlob` 下載，檔名 `coloring_<W>x<H>.png`。

---

## 程式結構（單檔，重要函式）

```
setupImage(img)        載入後設定尺寸 / 清 undo / 產線稿 / 顯示 UI / applyZoom(fit)
generateLineArt()      核心：灰階→(blur)→Sobel或門檻→dilate→lineMask→畫黑線
  toGray / boxBlur / dilate   影像處理小工具（純函式）
floodFill(x,y,hex)     油漆桶，受 lineMask 擋；stack + seen(Uint8Array) + 色差容差 tol
drawDot / drawSeg      筆刷 / 橡皮（strokeStyleNow(): erase→白）
pickColor(p)           吸管，讀 paint 像素 → setColor → 切回 brush
applyZoom(fit)         設 stack/canvas 的 CSS 尺寸；fit=true 時自動縮到畫面內
evtPos(e)              滑鼠座標 → canvas 像素（用 getBoundingClientRect，吃 CSS 縮放）
pushUndo/undo/redo     ImageData 快照堆疊（只含 paint 層，UNDO_MAX=25）
setColor / buildSwatches / renderRecent   調色盤
hexToRgb / rgbToHex
```

**圖層模型**：`#paintCanvas`（下，白底，所有上色）+ `#lineCanvas`（上，黑線透明背景，`pointer-events:none`）。指標事件綁在 paint 上；線永遠視覺在最上層，所以塗出界不會蓋住線。

**關鍵全域**：`srcImage, lineMask(Uint8Array), W, H, zoom, tool, curColor, brushSize, undoStack/redoStack`。

---

## 重要細節 / 雷點

- **lineMask 與 canvas 必須同尺寸**：所有 flood fill 的 index = `y*W+x`，重產線稿時 mask 會重建；換圖會重設 `W/H` 與兩張 canvas。
- **getImageData 用 `willReadFrequently:true`** 已設（pctx/lctx），避免每次讀像素的效能警告。
- **油漆桶容差 `tol=48`**：太小會在抗鋸齒邊留白邊；太大會穿過淡線。要更乾淨可同時調這個與線條粗細。
- **復原只記 paint 層**：筆刷 / 橡皮在 pointerdown 先 `pushUndo()`，油漆桶 / 清除在動作前 `pushUndo()`。**重新產生線稿、換圖不入 undo**（line 層不在快照裡）。
- **座標**：靠 `getBoundingClientRect()` 換算，所以 zoom 任意值都對；不要改成用固定 `W` 推算螢幕座標。
- **效能**：`MAXSIZE=2000` 是 flood fill / Sobel 的成本上限；大圖若卡可調小。

---

## 給接手 Claude 的建議

- 加上色相關功能盡量只動 paint 層與 `lineMask`，別破壞「line 永遠在最上層」這個前提。
- 新增工具：在工具列加按鈕（`data-tool`）+ `setTool` 自動處理 active；在 pointerdown 分支加邏輯；會改 paint 的動作記得先 `pushUndo()`。
- 改完做語法檢查（把 `<script>` 內容丟 `node --check` 或 `new Function`），並實測：載入 → 兩種模式產線稿 → 油漆桶不漏色 → 筆刷 / 橡皮 → undo/redo → 匯出 PNG 正確合成。

---

## 仍可再做（可選，跟我說即可）

- **AI 等級線稿**：dodge 技巧（灰階 ÷ 高斯模糊後反相），純前端、效果更接近手繪線稿，可當第三種模式。
- **筆刷限定線內**：讓 brush 也參考 `lineMask`，塗色不越線。
- **存檔續做**：IndexedDB 存 paint + 設定，重整不丟。
- **多圖層 / 漸層填色 / 圖樣填色**。
- 觸控裝置優化（目前用 pointer 事件，理論上可動但未針對手機調 UI）。

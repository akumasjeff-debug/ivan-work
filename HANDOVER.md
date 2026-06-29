# 影像合成台 — 專案交接文件

這是一個純前端、單一 HTML 檔的影像合成工具。目標是把多張圖片（可去背）疊圖排版，輸出指定尺寸、指定檔案大小上限的 JPG 或 PNG。**僅在桌機 Chrome 使用**（用到 File System Access API 與 IndexedDB 持久化）。

主檔：`compositor.html`（單檔，所有 HTML/CSS/JS 都在裡面）。

---

## 執行環境（重要）

- **必須在 `http://localhost` 或 `https://` 下開啟**，不能用 `file://` 直接點開。
  - 原因：用到 File System Access API（資料夾備份）、IndexedDB 持久化、以及從 CDN 載入去背模型。
  - 本機跑法範例：在檔案資料夾執行 `python -m http.server` 後開 `http://localhost:8000/compositor.html`。
- 去背功能依賴 CDN 動態載入 ML 模型（`@imgly/background-removal@1.7.0`，透過 jsDelivr ESM）。首次去背會下載約數十 MB 模型，需連網。

---

## 目前已完成的功能（全部可用）

**畫布**
- 預設 1000×1000，寬高可獨立自訂（50–5000px）。
- 尺寸快捷記錄：改好尺寸按「＋ 記住此尺寸」存成按鈕，下次點選直接套用，可刪除。輸出尺寸 = 畫布尺寸（所見即所得）。

**01 圖片資料庫**
- 上傳圖片（點擊或拖入），自動命名「圖片 N」、可改名（✎ 圖示或點名稱旁編輯鈕）。
- 點名稱展開小張預覽圖。
- 勾選格：勾起放上畫布，取消勾選從畫布移除。
- 資料夾分類：可新增 / 改名 / 刪除資料夾（「未分類」為固定根，不可刪）。拖動圖片列到資料夾標題可移動分類。
- **真實資料夾備份**：頂端「選擇資料夾」用 File System Access API 指定本機資料夾，之後每張上傳圖（含框架）自動寫一份實體檔（檔名帶時間戳）。授權記在 IndexedDB，下次嘗試恢復。

**02 圖層**
- 顯示目前在畫布上的所有圖層（圖片 / 框架 / 文字混合），上=最前。
- 拖動排序（抓 ⋮⋮ 或整列）調前後。
- 畫布上：拖移、拖右下角圓點縮放（鎖比例）、選取後方向鍵微調（Shift=10px）、Delete 刪除、Esc 取消選取。
- 置換：選取畫布上的圖片圖層後（畫布外框變青綠），回資料庫點任一張即置換內容（保留位置與寬度）。
- 每個圖片圖層有 ✂ 專業去背鈕（AI，任意背景）。去背結果記在該 asset 上，重複使用共用。

**03 加入框架**
- 上傳一張框架圖、按「去背」後，按「加入圖層」進入 02 區。
- 框架是一般可調圖層（預設滿版置頂），可拖移縮放、可在清單調前後順序。清單中有紫色「框架」標籤。已加入時 03 區出現「置頂」一鍵鈕。

**04 紀錄位置模組（綁定尺寸）**
- 排好版按「＋ 記錄目前位置」，記下每個圖層的座標+大小（依前後順序）與當時畫布尺寸。
- 套用：照記錄順序套到目前畫布圖層（第1個套最前層、第2個套第二層…）。數量不符時有幾個套幾個，多的不動、版位多的略過。
- **只有畫布尺寸與模組相同時「套用」鈕才會亮**；尺寸不符會變灰並提示。清單顯示每個模組的尺寸（如 `3層 / 1080×1080`）。

**05 字體庫**
- 上傳 `.ttf/.otf/.woff` 字型檔建立字體庫，可刪除。文字圖層的字型下拉可選用。

**文字圖層**（02 區「＋ 新增文字圖層」）
- 新增後在圖層清單展開編輯面板。
- 內容（多行）、字型、字級、字距、行距、對齊。
- 填色：純色 或 漸層（雙色+角度）。
- 描邊（顏色+粗細）、陰影（顏色+模糊+X/Y）、外發光（顏色+強度）、透明度。
- 弧形排列（滑桿正負拉，文字沿弧線拱起/下彎）。
- 文字渲染成 canvas 圖再當圖層用（特效在預覽與輸出一致）。畫布上可拖拉縮放（連動字級），面板可數值微調 X/Y/寬。

**輸出**
- 格式可選 JPG（白底）/ PNG（保留透明）。
- 可輸入最大 KB 上限（預設 450），超過自動降到達標。
  - JPG：先降品質滑桿值，仍太大再縮輸出尺寸。
  - PNG：無損、無品質參數，只能靠縮小尺寸達標（選 PNG 時品質滑桿自動隱藏）。
- 檔名帶實際輸出尺寸與副檔名，例 `composite_1000x1000.png`。

---

## 儲存架構（已重構為 IndexedDB，這是最新狀態）

**設計原則：二進位存 IndexedDB，輕量設定存 localStorage。**

- IndexedDB（`DB_NAME="compositorDB"`, `DB_VERSION=2`）兩個 object store：
  - `handles`：存 File System Access 的目錄 handle（key `'dir'`）。
  - `blobs`：存所有二進位，key 命名規則：
    - `img:<assetId>` 原圖
    - `cut:<assetId>` 去背結果
    - `img:<frameId>` / `cut:<frameId>` 框架（frameId 形如 `frame_xxxx`）
    - `font:<fontId>` 字型檔
- localStorage（key `META_KEY="compositor.meta.v6"`）只存設定：`version:6`、canvasW/H、sizePresets、folders、templates、fonts 的 meta（id/name/family，**不含檔案**）、assets 的 meta（id/name/folderId/hasCut，**不含圖**）、placements、frameAsset 的 meta、texts（文字參數）。
- 記憶體中 `asset.src` / `asset.cutSrc` 持有 **object URL**（由 blob 即時產生），所以大部分 render/export 程式讀 `a.src`、`a.cutSrc` 都不用改。
- 封裝好的儲存函式（之後加功能盡量只動上層，別動這幾個）：
  - `putBlob(key, blob)` / `getBlobURL(key)`（含 `_urlCache` 快取 object URL）/ `delBlob(key)`
  - `idbPut/idbGet/idbDel(store, key, [val])` 為底層
- 啟動時呼叫 `requestPersistence()`（`navigator.storage.persist()`）降低被瀏覽器自動清除的機率。
- 刪除 asset / frame / font 時會連帶 `delBlob` 清掉對應二進位，避免孤兒資料。
- 容錯：load 每筆 try/catch，單張圖或單支字型失敗不影響整體。存檔有 `version` 欄位，將來結構大改可寫遷移。

**注意**：此版 key 與舊版（`compositor.v5` 等）不相通，沒有寫舊資料遷移（使用者選擇直接換新架構）。

---

## 程式內部關鍵資料結構

```
canvasW, canvasH                  // 畫布/輸出尺寸
sizePresets: [{w,h}]              // 尺寸快捷
folders: [{id,name,open}]        // '_root' 為固定根「未分類」
assets: [{id,name,folderId,src,cutSrc,cutDone,_img,_cutImg}]
                                  // src/cutSrc = object URL；_img/_cutImg = 已 decode 的 Image
placements: [{pid,assetId,kind,x,y,w,h,z,useCut}]
                                  // kind: 'image' | 'frame' | 'text'
                                  // x,y,w,h 以畫布座標（非螢幕像素）為單位
                                  // z 越大越前
frameAsset: {id,name,src,cutSrc,cutDone,_img,_cutImg} | null
                                  // 框架的素材本體，被一個 kind:'frame' 的 placement 引用
texts: { pid: {content,fontId,size,align,lineHeight,letterSpacing,
               fill,useGradient,grad1,grad2,gradAngle,
               strokeOn,strokeColor,strokeWidth,
               shadowOn,shadowColor,shadowBlur,shadowX,shadowY,
               glowOn,glowColor,glowBlur,opacity,curve, _canvas} }
                                  // _canvas = 渲染好的離屏 canvas（不存檔，load 後 rebuild）
fonts: [{id,name,family}]        // 檔案在 IndexedDB font:<id>
templates: [{id,name,cw,ch,slots:[{x,y,w,h}]}]  // slots 依前→後順序；cw/ch 綁定尺寸
```

座標換算：`scaleX()=stage.clientWidth/canvasW`，`scaleY()` 同理。畫布座標 × scale = 螢幕像素。

主要 render 函式：`renderAll()` 呼叫 `renderStage / renderDb / renderLayers / renderFrame / renderTemplates / renderFontLib`。文字改動走 `rebuildText(pid)` 重畫離屏 canvas，再 `renderStage()`。

---

## 已知限制 / 之後可能想做的事

- 去背是 client-side ML，複雜背景可能不完美；需連網載入模型。
- PNG 壓到很小的 KB 上限時，靠縮尺寸達標，照片類內容可能要縮蠻多；如需更激進可加「減色/量化到 256 色」。
- 文字弧形排列是逐字沿圓弧擺放的近似法，極端字距/極短字串已加防呆。
- 尚未做：圖層鎖定、群組、復原/重做（undo/redo）、多選、對齊輔助線、匯出設定模板。這些都是可加項，跟我說即可。
- 行動裝置不支援（File System Access / 持久化僅桌機 Chrome/Edge）。

---

## 給接手 Claude 的建議

- 改功能時，記憶體裡操作的是同步的 `assets` / `placements` / `texts`；只有「存二進位」是非同步（`await putBlob`）。沿用 `putBlob/getBlobURL/delBlob` 三個封裝，不要直接碰 localStorage 存圖。
- 任何新增的資料欄位，請在 load 時給預設值（沿用現有 `x||預設`、`!!x` 風格），保持舊存檔相容。
- 改完務必做語法檢查（可用 node 把 `<script type="module">` 內容去掉 import 後 `new Function(body)` 驗證），並在 `http://localhost` 實測上傳/去背/輸出/重新整理後資料是否還在。

---

## 2026-06-29 更新：進階編輯一批

新增（皆已併入 `compositor.html`，語法檢查通過）：

- **復原/重做**：`undo()/redo()`，快照 `layoutSnapshot()`（placements+texts），`pushHistory()` 在各 mutation 前呼叫；拖移類在 pointerup 比對前後快照才入 `undoStack`。鍵盤 `Ctrl+Z / Ctrl+Shift+Z / Ctrl+Y`。
- **多選**：新增 `selPids:Set`（`selPid` 仍為主要/active）。輔助 `selectedPlacements / selectOne / toggleSel`。`Shift+點選`畫布或圖層列多選。
- **複製/貼上**：`copySel/pasteSel`（`Ctrl+C/V`，剪貼簿存 placement+text 規格）。
- **對齊/符合畫布/滿版**：`alignSel(kind)`，kind = left/right/hc/top/bottom/vc/center/fit/full。對齊列 HTML id `alignBar`，選取時顯示。
- **安全框**：`safeGuide`，切換 `.stage-shell.show-safe`，overlay 為 init 時動態加的 `.safe-overlay`（純顯示，不輸出）。
- **比例快捷**：尺寸列 `.ratios` 按鈕呼叫 `changeSize`。
- **placement 新欄位**：`opacity(預設1) / rotate(度) / flipX / locked / hidden`，統一用 `normPlacement()` 補預設（`load`、`restoreLayout`、`addPlacement` 等都有走）。`save()` 因 `placements.map(p=>({...p}))` 自動含新欄位。
- **renderStage**：隱藏略過、`opacity`、`transform:rotate+scaleX`、鎖定不 attachDrag 且控點隱藏、多選高亮。
- **drawComposite（輸出）**：隱藏略過、`globalAlpha`、以中心點 rotate/flip 繪製。
- **PNG 減色**：`posterize(canvas,levels)`，UI id `pngReduce/pngLevels/reduceRow`。
- **批次輸出**：`batchExport()` 對符合目前尺寸的版位逐一套用並 `exportImage(tag)`。
- **輸出設定記憶**：`saveExportPrefs/loadExportPrefs`，localStorage key `compositor.export.v1`（`EXP_KEY`）。
- **全站備份**：`exportAll/importAll`，把 `ST_BLOBS` 全部（base64）+ meta + export prefs 打成一個 JSON。底層加了 `idbKeys(store)`、`blobToDataURL`。匯入會覆蓋並 `location.reload()`。

注意/限制：
- 旋轉非 0° 時，縮放控點的 resize 數學會略偏（移動與輸出正確）；建議用 ±15° 鈕。
- 文字「樣式」逐項微調未進 undo 堆疊（只記版面層級操作）。
- 刪除「素材」（asset/font 本體）仍不可 undo（二進位已刪）。

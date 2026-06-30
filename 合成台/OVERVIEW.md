# 影像合成台 — 專案總覽（OVERVIEW）

> 純前端、單一 HTML 檔的影像合成工具。把多張圖片（可 AI 去背）疊圖排版，輸出指定尺寸、指定檔案大小上限的 JPG / PNG。
> **僅限桌機 Chrome / Edge**，須在 `http://localhost` 或 `https://` 下執行（用到 File System Access API、IndexedDB、CDN 載入去背模型）。
> 主檔：`compositor.html`（單檔，HTML/CSS/JS 全包，約 895 行）。詳細交接見 `HANDOVER.md`。

---

## 一、功能分類

### 🖼 素材管理（01 圖片資料庫）
- 上傳圖片（點擊／拖入），自動命名「圖片 N」、可改名
- 點名稱展開小張預覽
- 勾選 = 放上畫布；取消勾選 = 移除
- 資料夾分類：新增／改名／刪除（「未分類」為固定根），拖曳移動分類
- 真實資料夾備份：File System Access API 指定本機資料夾，每張上傳圖自動寫實體檔（檔名帶時間戳）

### 🎨 排版編輯（02 圖層）
- 列出畫布上所有圖層（圖片／框架／文字），上 = 最前
- 拖動排序調前後
- 畫布操作：拖移、右下角縮放（鎖比例）、方向鍵微調（Shift = 10px）、Delete 刪除、Esc 取消
- 圖片置換：選取後回資料庫點任一張即換內容（保留位置與寬度）
- 每個圖片圖層有 ✂ AI 去背鈕，結果記在 asset 上共用

### 🪟 框架疊加（03 加入框架）
- 上傳框架圖 → 去背 → 加入圖層（預設滿版置頂）
- 框架是一般可調圖層，可拖移縮放、調前後、一鍵「置頂」

### ✍️ 文字設計（文字圖層 + 05 字體庫）
- 字體庫：上傳 `.ttf/.otf/.woff` 建庫
- 文字圖層：多行內容、字型、字級、字距、行距、對齊
- 填色：純色或漸層（雙色 + 角度）
- 描邊、陰影（色 + 模糊 + X/Y）、外發光、透明度
- 弧形排列（逐字沿圓弧擺放）
- 文字渲染成離屏 canvas 當圖層用（預覽與輸出一致）

### 📐 版位記憶（04 紀錄位置模組，綁定尺寸）
- 「＋ 記錄目前位置」記下各圖層座標 + 大小（依前後順序）與當時畫布尺寸
- 套用：照順序套到目前圖層（第 1 個套最前層…）；數量不符時有幾個套幾個
- **只有畫布尺寸與模組相同時「套用」才會亮**，否則變灰提示

### 💾 輸出
- 格式：JPG（白底）/ PNG（透明）
- KB 上限（預設 450）自動降到達標：
  - JPG：先降品質滑桿，仍太大再縮尺寸
  - PNG：無損，只能靠縮尺寸（選 PNG 時品質滑桿隱藏）
- 檔名帶實際輸出尺寸，例 `composite_1000x1000.png`

### 📏 畫布尺寸
- 預設 1000×1000，寬高各自 50–5000px
- 尺寸快捷：「＋ 記住此尺寸」存成按鈕，可刪除。輸出尺寸 = 畫布尺寸（所見即所得）

---

## 二、技術架構

### 儲存（二進位 IndexedDB + 設定 localStorage）
- **IndexedDB**（`compositorDB` v2）兩個 store：
  - `handles`：File System Access 目錄 handle（key `'dir'`）
  - `blobs`：所有二進位，key 規則 `img:<id>` 原圖 / `cut:<id>` 去背 / `font:<id>` 字型（框架 id 形如 `frame_xxxx`）
- **localStorage**（key `compositor.meta.v6`）：只存設定 meta（尺寸、資料夾、模組、文字參數、asset/font 的 meta，**不含檔案**）
- 記憶體中 `asset.src` / `asset.cutSrc` 持有 object URL（由 blob 即時產生）
- 封裝層（加功能盡量只動上層）：`putBlob` / `getBlobURL`（含 `_urlCache`）/ `delBlob`，底層 `idbPut/idbGet/idbDel`
- 啟動 `requestPersistence()` 降低被清除機率；刪 asset/frame/font 連帶 `delBlob` 避免孤兒

### 關鍵資料結構
```
canvasW, canvasH                  畫布/輸出尺寸
sizePresets: [{w,h}]              尺寸快捷
folders: [{id,name,open}]        '_root' = 固定根
assets: [{id,name,folderId,src,cutSrc,cutDone,_img,_cutImg}]
placements: [{pid,assetId,kind,x,y,w,h,z,useCut}]   kind: image|frame|text；座標為畫布座標；z 越大越前
frameAsset: {...} | null
texts: { pid: {content,fontId,size,align,lineHeight,letterSpacing,fill,useGradient,
               grad1,grad2,gradAngle,strokeOn/Color/Width,shadowOn/Color/Blur/X/Y,
               glowOn/Color/Blur,opacity,curve,_canvas} }
fonts: [{id,name,family}]
templates: [{id,name,cw,ch,slots:[{x,y,w,h}]}]
```

### 渲染流程
- `renderAll()` → `renderStage / renderDb / renderLayers / renderFrame / renderTemplates / renderFontLib`
- 文字改動走 `rebuildText(pid)` 重畫離屏 canvas → `renderStage()`
- 座標換算：`scaleX()=stage.clientWidth/canvasW`（畫布座標 × scale = 螢幕像素）
- 輸出走 `drawComposite(w,h)` 重畫一張高解析 canvas → `toBlob`

---

## 三、進階編輯（2026-06-29 新增）
- **復原 / 重做**：`Ctrl+Z` / `Ctrl+Shift+Z`（或 `Ctrl+Y`）。涵蓋新增、刪除、拖移、縮放、排序、對齊、套版位、貼上、旋轉/翻轉/鎖定等版面操作（最多 60 步）。文字「樣式微調」不逐項記錄。
- **多選**：`Shift+點選`畫布圖層或圖層列可多選，一起拖移、方向鍵微調、刪除、對齊。
- **複製 / 貼上圖層**：`Ctrl+C` / `Ctrl+V`，貼上會偏移 24px 並置頂。
- **對齊列**（選取後出現於畫布上方）：靠左/右、水平置中、靠上/下、垂直置中、正中央。
- **符合畫布**：一鍵把選取圖層等比縮到「當前輸出尺寸內的最大尺寸」並置中 — 丟大圖後先按這個再微調最方便。**滿版**則撐滿整張畫布。
- **安全框**：勾選後畫布顯示 5% 內縮框＋中線參考（僅顯示，不會輸出）。
- **比例快捷**：尺寸列旁 1:1 / 4:5 / 9:16 / 16:9 一鍵切換常用社群尺寸。
- **圖層鎖定 🔒 / 隱藏 👁**：鎖定者不能在畫布上被拖到/選到（改用圖層列操作）；隱藏者不顯示也不輸出。
- **旋轉 / 翻轉**：圖片/框架圖層每列有 ⟲ ⟳（±15°）與 ⇋（水平翻轉）；預覽與輸出一致。
- **圖層透明度**：圖片/框架圖層每列有透明度滑桿（文字用自己的 opacity）。
- **PNG 減色**：選 PNG 時可勾「減色」並設色階（2–32），降低顏色數讓檔案更小。
- **批次輸出**：對「所有符合目前畫布尺寸的版位模組」各套用並各輸出一張。
- **輸出設定記憶**：格式/品質/上限/減色設定會記住，下次開啟自動還原。
- **全站備份匯出 / 匯入**：把所有圖片＋字型＋設定打包成單一 `.json`，可備份或換機還原（匯入會覆蓋現有資料）。

## 四、已知限制
- 去背是 client-side ML，複雜背景可能不完美；需連網載入模型（首次約數十 MB）
- PNG 壓到很小 KB 時靠縮尺寸，照片類可能縮蠻多
- 弧形排列是逐字近似法，極端字距/極短字串已防呆
- **旋轉圖層的「縮放控點」在非 0° 時數學上會略偏**（移動/輸出正常）；目前旋轉建議用 ±15° 鈕
- 僅桌機 Chrome/Edge，不支援行動裝置與 `file://`

## 五、仍可再加（可選）
群組（真正的階層群組）、對齊吸附參考線、任意角度旋轉拖把、文字樣式逐項 undo、PNG 真正調色盤量化（median-cut）

---

## 六、接手須知
1. 記憶體操作（`assets`/`placements`/`texts`）同步，**只有存二進位非同步**（`await putBlob`）
2. 新增資料欄位要在 `load()` 給預設值，保持舊存檔相容；placement 的新欄位（`opacity/rotate/flipX/locked/hidden`）統一走 `normPlacement()` 補預設
3. 任何會改版面的操作，動手前先 `pushHistory()`（拖移類在 pointerup 比對快照後才入堆疊）；選取一律透過 `selectOne / toggleSel / selPids`，不要再直接寫 `selPid`
4. 改完做語法檢查 + 在 `localhost` 實測（上傳／去背／輸出／重整後資料還在）
5. 本版 key 與舊版不相通，無舊資料遷移

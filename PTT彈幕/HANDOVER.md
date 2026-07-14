# PTT 留言彈幕 — 交接文件

兩個版本共用同一套 PTT 解析邏輯（一個在 Python、一個在 JS），改 PTT 選擇器時**兩邊都要改**。

## A. 桌面覆蓋層版（overlay.pyw，主要版本）

### 架構
- 單一 Python 檔，只用標準庫（tkinter / urllib / ctypes / threading）。
- `App`＝控制視窗（Tk 主視窗）：看板/文章 Listbox、播放與滑桿控制、狀態列。
- `Overlay`＝彈幕層（Toplevel）：
  - `overrideredirect(True)`（無邊框、不進工作列）＋`-topmost`（每 3 秒重新斷言一次）。
  - **透明**：`-transparentcolor "#010203"`，canvas 底色就是這個色鍵 → 只剩文字可見。彈幕文字別用到這個顏色。
  - **滑鼠穿透**：ctypes 對 HWND 加 `WS_EX_LAYERED|WS_EX_TRANSPARENT`（`_apply_clickthrough`）；HWND 用 `GetAncestor(canvas.winfo_id(), GA_ROOT=2)` 拿。調整模式會暫時關穿透。
  - **調整位置/大小**：`set_adjust(True)` → canvas 改深色底＋橘框＋右下角 26px 抓把，拖內部＝移動、拖角＝縮放（`_drag_start/_drag_move`），完成後把 `geometry` 寫回 cfg 並存檔。
  - 不透明度用整窗 `-alpha`（色鍵＋alpha 可並用）。
- **執行緒模型**：所有網路抓取走 `async_call`（daemon thread）→ 結果丟 `queue.Queue` → 主執行緒 `pump()`（after 50ms）回呼。tkinter 物件只在主執行緒碰。
- **輪詢**：`live_gen` 世代計數器；換文章/停止/關閉都 +1，舊輪詢的回呼看到世代不符就自動斷鏈。排程用 `root.after(5000)`，下一輪由上一輪回呼再排（不會疊加）。
- 設定存 `overlay-settings.json`（geometry、速度、字級、密度、不透明度、穿透、顯示ID），關閉與完成調整時寫入。

### 彈幕引擎（兩版邏輯相同）
- 60fps 迴圈（`after(16)` / rAF），`dt` 上限 0.1s（視窗凍結恢復時彈幕不會瞬間跳走）。
- 軌道：`lanes[i]` 記「該軌尾巴離開右緣的時刻」，發射挑空軌，全滿挑最快空的。全部彈幕同速所以同軌不追撞。
- 密度：令牌桶（每秒補 `density` 個）。
- 文字畫兩層（黑色 offset 2px 當陰影＋本色）增加可讀性。

## B. 網頁版（danmaku.html + server.py）

```
瀏覽器(App模式) → server.py (localhost:8003)
                    ├─ 靜態檔
                    └─ /ptt/<path> → https://www.ptt.cc/<path>（over18=1）
```
- 代理只收站內路徑（`/` 開頭、擋 `//`），會剝掉 query（前端輪詢加 `?_=時間戳` 防快取用）。
- port **8003**（8002 被 air-conditioner 用）。`start-web.bat` 用 netstat 檢查避免重複開 server。
- 關掉 App 視窗後 server 還在背景（最小化的「ptt-danmaku-server」視窗）。

## PTT 解析對照（改版時對照更新）

| 資料 | 來源頁 | 依據 |
|------|--------|------|
| 熱門看板 | `/bbs/hotboards.html` | `a.board` → `.board-name` `.board-nuser` `.board-title` |
| 文章列表 | `/bbs/<板>/index*.html` | `div.r-ent`；`r-list-sep` 之後是置底（略過）；`.title` 內沒有 `<a>`＝已刪文 |
| 翻頁 | 同上 | `.btn-group-paging a.btn.wide`，「上頁」＝較舊、「下頁」＝較新（列表有 reverse 讓新文在上） |
| 文章+推文 | `/bbs/<板>/M.*.html` | `.article-metaline`（作者/標題）；`div.push` → `.push-tag`（推/噓/→）`.push-userid` `.push-content`（去開頭 `: `） |

## 自動更新（重要！踩過的坑）

### 為什麼不能「每 5 秒重抓文章頁」
PTT 頁面回 `Cache-Control: max-age=900s, public`——文章 HTML 是**烘焙到某個時間點的版本**，快取層可回 15 分鐘內的舊頁，重抓根本拿不到新推文（實測：列表 nrec=6、文章頁 0 推）。

### 正確做法：PTT 官方 longpoll 機制（bbs.js 同款）
文章頁尾有 `<div id="article-polling" data-pollurl=... data-longpollurl=... data-offset=...>`：
1. GET `data-longpollurl`（`/v1/longpoll?id=…`）→ JSON `{size, sig, cacheKey}`＝目前文章檔案大小。
2. `size > offset` 時 GET `pollurl&size=<size>&size-sig=<sig>` → JSON `{success, contentHtml, pollUrl}`；`contentHtml` 是新增推文的 HTML（用同一套 push 解析），下一輪改用回傳的新 `pollUrl`、`offset=size`。
3. `success=false` 且 longpoll 有 `cacheKey` → 原文被編輯，用 `?cacheKey=…&offset=<size>&offset-sig=<sig>` 重建 pollurl「從結尾重新跟隨」。
4. 每輪間隔 1 秒（同官方）；失敗等 5 秒重試。**新推文約 1 秒內到，且頁面快取新舊無所謂**——offset 永遠對應該頁烘焙點，增量會補齊中間全部。

注意：**poll/longpoll 的 query 帶簽名，不可加料不可剝掉**（加 `_=` 防快取參數會 500）。防快取參數只用在 `/bbs/` 頁面（看板列表才拿得到新的）。網頁版代理依此分流（`server.py`）；longpoll 可能掛著等，代理 timeout 設 40 秒（官方前端 28 秒）。

- 兩種播放模式（重播/直播）都常駐即時同步；重播播完無縫接新推文。
- 沒有 polling 資訊的文章（罕見）退回舊式 5 秒整頁重抓（`poll_fallback` / `beginPollFallback`）。
- 控制台/狀態列會顯示最後檢查時間，可目視確認有在同步。

## 注意事項

- `*.bat` 內容保持**純 ASCII**（工作區慣例）→ 桌面捷徑名因此用 ASCII「PTT Danmaku」（`make-shortcut.bat` 產生）。
- 十八禁看板靠 `over18=1` cookie。
- 輪詢 5 秒一次，別調太快以免被 PTT 429。

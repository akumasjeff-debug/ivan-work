# -*- coding: utf-8 -*-
"""PTT 留言彈幕 — 桌面覆蓋層版
彈幕直接飄在桌面最上層（透明背景、滑鼠穿透），控制視窗選看板/文章。
啟動: start.bat（pythonw，無主控台視窗）
"""
import ctypes
import gzip
import html as html_mod
import json
import os
import queue
import re
import threading
import time
import tkinter as tk
import urllib.request
from tkinter import ttk

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_FILE = os.path.join(BASE_DIR, "overlay-settings.json")
PTT = "https://www.ptt.cc"
TRANS = "#010203"          # 透明色鍵（畫面上這個顏色會變全透明）
COLORS = {"推": "#7dff8a", "噓": "#ff6b6b"}
COLOR_ARROW = "#e8ecf5"

try:  # 高 DPI 下座標才不會糊掉/偏移
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass


# ---------------- PTT 抓取 / 解析 ----------------

def fetch(path, timeout=15, bust=True):
    # PTT 頁面回 Cache-Control: max-age=900s，中間快取層會回 15 分鐘內的舊頁；
    # 每次帶不同 query 強制拿最新。/poll、/v1/longpoll 等 API 帶簽名參數，不可加（bust=False）
    if bust:
        path += ("&" if "?" in path else "?") + "_=" + str(time.time_ns())
    req = urllib.request.Request(PTT + path, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Cookie": "over18=1",
        "Accept-Encoding": "gzip",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    })
    with urllib.request.urlopen(req, timeout=timeout) as r:
        body = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            body = gzip.decompress(body)
    return body.decode("utf-8", "replace")


def strip_tags(s):
    return html_mod.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def parse_hotboards(t):
    out = []
    for m in re.finditer(r'<a class="board"[^>]*href="([^"]+)"(.*?)</a>', t, re.S):
        href, body = m.group(1), m.group(2)
        name = re.search(r'board-name">(.*?)</div>', body)
        nuser = re.search(r'board-nuser">(.*?)</div>', body, re.S)
        title = re.search(r'board-title">(.*?)</div>', body)
        out.append({
            "href": href,
            "name": strip_tags(name.group(1)) if name else "?",
            "nuser": strip_tags(nuser.group(1)) if nuser else "",
            "title": strip_tags(title.group(1)) if title else "",
        })
    return out


def parse_index(t):
    main = t.split('r-list-sep')[0]  # 之後是置底文，略過
    items = []
    for m in re.finditer(r'<div class="r-ent">(.*?)<div class="date"', main, re.S):
        b = m.group(1)
        a = re.search(r'<a href="(/bbs/[^"]+)">(.*?)</a>', b)
        if not a:  # 已刪除
            continue
        nrec = re.search(r'"nrec">(.*?)</div>', b, re.S)
        author = re.search(r'"author">(.*?)</div>', b)
        items.append({
            "href": a.group(1),
            "title": strip_tags(a.group(2)),
            "nrec": strip_tags(nrec.group(1)) if nrec else "",
            "author": strip_tags(author.group(1)) if author else "",
        })
    items.reverse()  # 新文在上
    older = newer = None
    for m in re.finditer(r'<a class="btn wide" href="([^"]+)">([^<]+)</a>', t):
        if "上頁" in m.group(2):
            older = m.group(1)
        elif "下頁" in m.group(2):
            newer = m.group(1)
    return items, older, newer


def parse_pushes(t):
    pushes = []
    for m in re.finditer(r'<div class="push">(.*?)</div>', t, re.S):
        b = m.group(1)
        tag = re.search(r'push-tag">(.*?)</span>', b)
        user = re.search(r'push-userid">(.*?)</span>', b)
        content = re.search(r'push-content">(.*?)</span>', b, re.S)
        text = strip_tags(content.group(1)).lstrip(":").strip() if content else ""
        if text:
            pushes.append((strip_tags(tag.group(1)) if tag else "→",
                           strip_tags(user.group(1)) if user else "", text))
    return pushes


def parse_article(t):
    title = author = ""
    for m in re.finditer(r'article-meta-tag">(.*?)</span>'
                         r'<span class="article-meta-value">(.*?)</span>', t):
        if m.group(1) == "標題":
            title = strip_tags(m.group(2))
        elif m.group(1) == "作者":
            author = strip_tags(m.group(2))
    # PTT 官方即時推文機制：文章頁只渲染到 data-offset，之後的推文用
    # longpoll（拿 size+sig）→ pollurl&size&size-sig（拿新增 HTML）接力
    poll = None
    m = re.search(r'<div id="article-polling" ([^>]*)>', t)
    if m:
        attrs = dict(re.findall(r'data-([a-z]+)="([^"]*)"', m.group(1)))
        if "pollurl" in attrs and "longpollurl" in attrs:
            poll = {"pollurl": html_mod.unescape(attrs["pollurl"]),
                    "longpollurl": html_mod.unescape(attrs["longpollurl"]),
                    "offset": int(attrs.get("offset") or 0)}
    return title, author, parse_pushes(t), poll


# ---------------- 彈幕覆蓋層 ----------------

class Overlay:
    def __init__(self, root, cfg):
        self.cfg = cfg
        self.win = tk.Toplevel(root)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.config(bg=TRANS)
        self.win.attributes("-transparentcolor", TRANS)
        self.win.geometry(cfg.get("geometry") or self._default_geometry())
        self.canvas = tk.Canvas(self.win, bg=TRANS, highlightthickness=0, bd=0)
        self.canvas.pack(fill="both", expand=True)

        self.items = []      # {ids:(shadow,text), x, w}
        self.dm_queue = []   # 待發射 (tag, user, text)
        self.lanes = []      # 各軌道尾巴離開右緣的時刻
        self.budget = 0.0
        self.paused = False
        self.adjust = False
        self._drag = None
        self._last = time.perf_counter()

        self.canvas.bind("<ButtonPress-1>", self._drag_start)
        self.canvas.bind("<B1-Motion>", self._drag_move)
        self.win.after(200, self._apply_clickthrough)
        self.win.after(16, self._tick)
        self.win.after(3000, self._keep_topmost)
        self.win.attributes("-alpha", cfg["opacity"])

    @staticmethod
    def _default_geometry():
        sw = ctypes.windll.user32.GetSystemMetrics(0)
        sh = ctypes.windll.user32.GetSystemMetrics(1)
        return "%dx%d+40+40" % (sw - 80, int(sh * 0.45))

    # --- 滑鼠穿透（WS_EX_TRANSPARENT） ---
    def _hwnd(self):
        return ctypes.windll.user32.GetAncestor(self.canvas.winfo_id(), 2)

    def _apply_clickthrough(self):
        GWL_EXSTYLE, WS_EX_LAYERED, WS_EX_TRANSPARENT = -20, 0x80000, 0x20
        try:
            h = self._hwnd()
            st = ctypes.windll.user32.GetWindowLongW(h, GWL_EXSTYLE)
            if self.cfg["clickthrough"] and not self.adjust:
                st |= WS_EX_LAYERED | WS_EX_TRANSPARENT
            else:
                st &= ~WS_EX_TRANSPARENT
            ctypes.windll.user32.SetWindowLongW(h, GWL_EXSTYLE, st)
        except Exception:
            pass

    def _keep_topmost(self):
        try:
            self.win.attributes("-topmost", True)
        except Exception:
            return
        self.win.after(3000, self._keep_topmost)

    # --- 調整位置/大小模式 ---
    def set_adjust(self, on):
        self.adjust = on
        if on:
            self.clear()
            self.canvas.config(bg="#15181f")
            self.win.attributes("-alpha", 0.8)
            self._draw_adjust_hint()
        else:
            self.canvas.delete("adjust")
            self.canvas.config(bg=TRANS)
            self.win.attributes("-alpha", self.cfg["opacity"])
            self.cfg["geometry"] = self.win.geometry()
        self._apply_clickthrough()

    def _draw_adjust_hint(self):
        self.canvas.delete("adjust")
        w, h = self.win.winfo_width(), self.win.winfo_height()
        self.canvas.create_rectangle(2, 2, w - 3, h - 3, outline="#ffb648",
                                     width=2, tags="adjust")
        self.canvas.create_text(w // 2, h // 2,
                                text="拖曳移動位置\n拖右下角調整大小\n調好按控制視窗的「完成調整」",
                                fill="#ffb648", font=("Microsoft JhengHei", 16, "bold"),
                                justify="center", tags="adjust")
        self.canvas.create_rectangle(w - 26, h - 26, w - 2, h - 2,
                                     fill="#ffb648", outline="", tags="adjust")

    def _drag_start(self, e):
        if not self.adjust:
            return
        w, h = self.win.winfo_width(), self.win.winfo_height()
        mode = "resize" if (e.x > w - 40 and e.y > h - 40) else "move"
        self._drag = (mode, e.x_root, e.y_root,
                      self.win.winfo_x(), self.win.winfo_y(), w, h)

    def _drag_move(self, e):
        if not self.adjust or not self._drag:
            return
        mode, sx, sy, wx, wy, ww, wh = self._drag
        dx, dy = e.x_root - sx, e.y_root - sy
        if mode == "move":
            self.win.geometry("+%d+%d" % (wx + dx, wy + dy))
        else:
            nw, nh = max(240, ww + dx), max(120, wh + dy)
            self.win.geometry("%dx%d" % (nw, nh))
            self._draw_adjust_hint()

    # --- 彈幕 ---
    def enqueue(self, pushes):
        self.dm_queue.extend(pushes)

    def clear(self, keep_queue=False):
        for it in self.items:
            for i in it["ids"]:
                self.canvas.delete(i)
        self.items = []
        self.lanes = []
        self.budget = 0.0
        if not keep_queue:
            self.dm_queue = []

    def queue_len(self):
        return len(self.dm_queue)

    def _lane_h(self):
        return int(self.cfg["font"] * 1.6) + 6

    def _pick_lane(self, now, w):
        n = max(1, (self.win.winfo_height() - 10) // self._lane_h())
        if len(self.lanes) != n:
            self.lanes = [0.0] * n
        occupy = now + (w + 60) / max(1, self.cfg["speed"])
        for i in range(n):
            if self.lanes[i] <= now:
                self.lanes[i] = occupy
                return i
        best = min(range(n), key=lambda i: self.lanes[i])
        self.lanes[best] = max(self.lanes[best], now) + (w + 60) / max(1, self.cfg["speed"])
        return best

    def _spawn(self, tag, user, text):
        disp = ("%s: %s" % (user, text)) if (self.cfg["show_uid"] and user) else text
        color = COLORS.get(tag, COLOR_ARROW)
        font = ("Microsoft JhengHei", self.cfg["font"], "bold")
        x = self.win.winfo_width() + 4
        sh = self.canvas.create_text(x + 2, 7, text=disp, font=font,
                                     fill="#000000", anchor="nw")
        bb = self.canvas.bbox(sh)
        w = (bb[2] - bb[0]) if bb else 100
        lane = self._pick_lane(time.perf_counter(), w)
        y = 5 + lane * self._lane_h()
        self.canvas.coords(sh, x + 2, y + 2)
        tx = self.canvas.create_text(x, y, text=disp, font=font,
                                     fill=color, anchor="nw")
        self.items.append({"ids": (sh, tx), "x": float(x), "w": w})

    def _tick(self):
        now = time.perf_counter()
        dt = min(now - self._last, 0.1)
        self._last = now
        if not self.paused and not self.adjust:
            self.budget = min(self.budget + self.cfg["density"] * dt,
                              float(self.cfg["density"]))
            while self.budget >= 1 and self.dm_queue:
                self._spawn(*self.dm_queue.pop(0))
                self.budget -= 1
            dx = -self.cfg["speed"] * dt
            alive = []
            for it in self.items:
                it["x"] += dx
                for i in it["ids"]:
                    self.canvas.move(i, dx, 0)
                if it["x"] + it["w"] > -10:
                    alive.append(it)
                else:
                    for i in it["ids"]:
                        self.canvas.delete(i)
            self.items = alive
        self.win.after(16, self._tick)


# ---------------- 控制視窗 ----------------

class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PTT 留言彈幕 — 控制台")
        self.root.geometry("760x560")
        self.root.minsize(640, 480)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.cfg = {
            "geometry": None, "speed": 150, "font": 26, "density": 4,
            "opacity": 1.0, "clickthrough": True, "show_uid": True,
        }
        self.load_settings()

        self.ui_queue = queue.Queue()
        self.boards = []
        self.articles = []
        self.cur_board = None      # (href, name)
        self.page_older = None
        self.page_newer = None
        self.cur_article = None    # href
        self.cur_title = ""
        self.seen = 0
        self.poll_info = None      # PTT 即時推文 polling 資訊（pollurl/longpollurl/offset）
        self.live_gen = 0          # 換文章/停止時 +1，讓舊輪詢失效

        self.overlay = Overlay(self.root, self.cfg)
        self.build_ui()
        self.root.after(50, self.pump)
        self.status("載入熱門看板中…")
        self.async_call(lambda: parse_hotboards(fetch("/bbs/hotboards.html")),
                        self.on_hotboards)

    # --- 執行緒工具：背景抓、主執行緒回呼 ---
    def async_call(self, fn, cb):
        def run():
            try:
                res, err = fn(), None
            except Exception as e:
                res, err = None, "%s" % e
            self.ui_queue.put((cb, res, err))
        threading.Thread(target=run, daemon=True).start()

    def pump(self):
        try:
            while True:
                cb, res, err = self.ui_queue.get_nowait()
                cb(res, err)
        except queue.Empty:
            pass
        self.root.after(50, self.pump)

    # --- UI ---
    def build_ui(self):
        top = ttk.Frame(self.root, padding=8)
        top.pack(fill="both", expand=True)

        left = ttk.Frame(top)
        left.pack(side="left", fill="y", padx=(0, 8))
        ttk.Label(left, text="熱門看板（雙擊開啟）").pack(anchor="w")
        self.lb_boards = tk.Listbox(left, width=26, activestyle="none")
        self.lb_boards.pack(fill="y", expand=True)
        self.lb_boards.bind("<Double-Button-1>", lambda e: self.open_selected_board())
        row = ttk.Frame(left)
        row.pack(fill="x", pady=(6, 0))
        self.ent_board = ttk.Entry(row, width=14)
        self.ent_board.pack(side="left", fill="x", expand=True)
        self.ent_board.bind("<Return>", lambda e: self.open_typed_board())
        ttk.Button(row, text="開看板", width=7,
                   command=self.open_typed_board).pack(side="left", padx=(4, 0))

        right = ttk.Frame(top)
        right.pack(side="left", fill="both", expand=True)
        hdr = ttk.Frame(right)
        hdr.pack(fill="x")
        self.lbl_board = ttk.Label(hdr, text="← 先選看板", font=("Microsoft JhengHei", 11, "bold"))
        self.lbl_board.pack(side="left")
        ttk.Button(hdr, text="較舊 →", width=8, command=lambda: self.turn_page("older")).pack(side="right")
        ttk.Button(hdr, text="← 較新", width=8, command=lambda: self.turn_page("newer")).pack(side="right", padx=4)
        ttk.Button(hdr, text="重新整理", width=8, command=self.reload_board).pack(side="right")
        ttk.Label(right, text="文章（雙擊＝直播模式；選取後也可按下面按鈕）").pack(anchor="w", pady=(4, 0))
        self.lb_arts = tk.Listbox(right, activestyle="none", font=("Microsoft JhengHei", 10))
        self.lb_arts.pack(fill="both", expand=True)
        self.lb_arts.bind("<Double-Button-1>", lambda e: self.play_selected(live=True))

        ctrl = ttk.LabelFrame(self.root, text="彈幕控制", padding=8)
        ctrl.pack(fill="x", padx=8, pady=(0, 4))
        r1 = ttk.Frame(ctrl)
        r1.pack(fill="x")
        ttk.Button(r1, text="▶ 從頭重播", command=lambda: self.play_selected(live=False)).pack(side="left")
        ttk.Button(r1, text="● 直播模式", command=lambda: self.play_selected(live=True)).pack(side="left", padx=4)
        self.btn_pause = ttk.Button(r1, text="⏸ 暫停", command=self.toggle_pause)
        self.btn_pause.pack(side="left")
        ttk.Button(r1, text="■ 停止/清空", command=self.stop_play).pack(side="left", padx=4)
        self.btn_adjust = ttk.Button(r1, text="調整位置/大小", command=self.toggle_adjust)
        self.btn_adjust.pack(side="left", padx=(16, 0))
        self.var_ct = tk.BooleanVar(value=self.cfg["clickthrough"])
        ttk.Checkbutton(r1, text="滑鼠穿透", variable=self.var_ct,
                        command=self.on_clickthrough).pack(side="left", padx=8)
        self.var_uid = tk.BooleanVar(value=self.cfg["show_uid"])
        ttk.Checkbutton(r1, text="顯示 ID", variable=self.var_uid,
                        command=lambda: self.cfg.update(show_uid=self.var_uid.get())).pack(side="left")

        r2 = ttk.Frame(ctrl)
        r2.pack(fill="x", pady=(8, 0))
        self.add_slider(r2, "速度", 60, 400, "speed")
        self.add_slider(r2, "字級", 14, 48, "font")
        self.add_slider(r2, "密度", 1, 12, "density")
        self.add_slider(r2, "不透明", 30, 100, "opacity",
                        get=lambda: int(self.cfg["opacity"] * 100),
                        set_=self.set_opacity)

        self.lbl_status = ttk.Label(self.root, text="", foreground="#666")
        self.lbl_status.pack(fill="x", padx=10, pady=(0, 6))

    def add_slider(self, parent, label, lo, hi, key, get=None, set_=None):
        f = ttk.Frame(parent)
        f.pack(side="left", padx=(0, 14))
        ttk.Label(f, text=label).pack(side="left")
        var = tk.IntVar(value=get() if get else self.cfg[key])
        def on_change(_v):
            v = var.get()
            if set_:
                set_(v)
            else:
                self.cfg[key] = v
        s = ttk.Scale(f, from_=lo, to=hi, variable=var, command=on_change, length=110)
        s.pack(side="left", padx=4)

    def set_opacity(self, v):
        self.cfg["opacity"] = v / 100.0
        if not self.overlay.adjust:
            self.overlay.win.attributes("-alpha", self.cfg["opacity"])

    def status(self, t):
        self.lbl_status.config(text=t)

    # --- 看板/文章 ---
    def on_hotboards(self, res, err):
        if err:
            self.status("熱門看板載入失敗：" + err)
            return
        self.boards = res
        self.lb_boards.delete(0, "end")
        for b in res:
            self.lb_boards.insert("end", " %-14s %s人" % (b["name"], b["nuser"]))
        self.status("選一個看板（雙擊），或左下輸入看板名")

    def open_selected_board(self):
        sel = self.lb_boards.curselection()
        if sel:
            b = self.boards[sel[0]]
            self.open_board(b["href"], b["name"])

    def open_typed_board(self):
        name = self.ent_board.get().strip()
        if name:
            self.open_board("/bbs/%s/index.html" % urllib.request.quote(name), name)

    def open_board(self, href, name):
        self.cur_board = (href, name)
        self.lbl_board.config(text=name)
        self.status("載入 %s 文章列表中…" % name)
        self.async_call(lambda: parse_index(fetch(href)), self.on_index)

    def reload_board(self):
        if self.cur_board:
            self.open_board("/bbs/%s/index.html" % urllib.request.quote(self.cur_board[1]),
                            self.cur_board[1])

    def turn_page(self, which):
        href = self.page_older if which == "older" else self.page_newer
        if href and self.cur_board:
            self.cur_board = (href, self.cur_board[1])
            self.status("翻頁中…")
            self.async_call(lambda: parse_index(fetch(href)), self.on_index)

    def on_index(self, res, err):
        if err:
            self.status("文章列表載入失敗：" + err + "（看板名打錯？）")
            return
        self.articles, self.page_older, self.page_newer = res
        self.lb_arts.delete(0, "end")
        for a in self.articles:
            self.lb_arts.insert("end", " %-3s %s  (%s)" % (a["nrec"], a["title"], a["author"]))
        self.status("共 %d 篇；雙擊文章開始直播彈幕" % len(self.articles))

    # --- 播放 ---
    def play_selected(self, live):
        sel = self.lb_arts.curselection()
        if not sel:
            self.status("先在右邊選一篇文章")
            return
        art = self.articles[sel[0]]
        self.cur_article = art["href"]
        self.live_gen += 1
        gen = self.live_gen
        self.overlay.paused = False
        self.btn_pause.config(text="⏸ 暫停")
        self.status("載入文章中…")
        self.async_call(lambda: parse_article(fetch(art["href"])),
                        lambda res, err: self.on_article(res, err, live, gen))

    def on_article(self, res, err, live, gen):
        if gen != self.live_gen:
            return
        if err:
            self.status("文章載入失敗：" + err)
            return
        title, author, pushes, poll = res
        self.cur_title = title
        self.seen = len(pushes)
        self.poll_info = poll
        self.overlay.clear()
        if live:
            self.overlay.enqueue(pushes[-5:])  # 暖場
            self.status("● 直播中：%s（目前 %d 推，即時同步）" % (title, self.seen))
        else:
            self.overlay.enqueue(pushes)
            self.status("▶ 重播＋即時同步：%s（共 %d 推）" % (title, self.seen))
        # 兩種模式都常駐即時同步：新推文自動接著播
        self.root.after(1000, lambda: self.live_cycle(gen))

    def live_cycle(self, gen):
        """PTT 官方即時機制：longpoll 問「檔案長大了沒」→ 有就用 pollurl 拿新增推文。
        新推文約 1 秒內到，且不受頁面 15 分鐘快取影響。"""
        if gen != self.live_gen or not self.cur_article:
            return
        info = self.poll_info
        if not info:  # 這篇沒有 polling 資訊（罕見）→ 退回整頁重抓
            self.root.after(5000, lambda: self.poll_fallback(gen))
            return

        def work():
            lp = json.loads(fetch(info["longpollurl"], timeout=35, bust=False))
            if lp.get("size", 0) > info["offset"]:
                url = "%s&size=%s&size-sig=%s" % (info["pollurl"], lp["size"], lp.get("sig", ""))
                return lp, json.loads(fetch(url, bust=False))
            return lp, None

        def cb(res, err):
            if gen != self.live_gen:
                return
            delay = 1000
            if err:
                self.status("連線失敗，%s 重試中" % time.strftime("%H:%M:%S"))
                delay = 5000
            else:
                lp, data = res
                if data is not None:
                    if data.get("success"):
                        news = parse_pushes(data.get("contentHtml", ""))
                        if news:
                            self.overlay.enqueue(news)
                            self.seen += len(news)
                        info["offset"] = lp["size"]
                        if data.get("pollUrl"):
                            info["pollurl"] = data["pollUrl"]
                    elif lp.get("cacheKey"):  # 原文被編輯 → 從結尾重新跟隨
                        info["pollurl"] = "%s?cacheKey=%s&offset=%s&offset-sig=%s" % (
                            info["pollurl"].split("?")[0], lp["cacheKey"],
                            lp["size"], lp.get("sig", ""))
                        info["offset"] = lp["size"]
                self.status("● 即時同步中：%s（%d 推｜%s）"
                            % (self.cur_title, self.seen, time.strftime("%H:%M:%S")))
            self.root.after(delay, lambda: self.live_cycle(gen))

        self.async_call(work, cb)

    def poll_fallback(self, gen):
        """舊式輪詢（整頁重抓比數量），只給沒有 polling 資訊的文章用。"""
        if gen != self.live_gen or not self.cur_article:
            return
        href = self.cur_article
        def cb(res, err):
            if gen != self.live_gen:
                return
            if not err:
                _t, _a, pushes, _p = res
                if len(pushes) > self.seen:
                    self.overlay.enqueue(pushes[self.seen:])
                    self.seen = len(pushes)
                self.status("● 自動更新中：%s（%d 推｜%s 檢查）"
                            % (self.cur_title, self.seen, time.strftime("%H:%M:%S")))
            else:
                self.status("連線失敗，%s 重試中：%s" % (time.strftime("%H:%M:%S"), err))
            self.root.after(5000, lambda: self.poll_fallback(gen))
        self.async_call(lambda: parse_article(fetch(href)), cb)

    def stop_play(self):
        self.live_gen += 1
        self.overlay.clear()
        self.status("已停止")

    def toggle_pause(self):
        self.overlay.paused = not self.overlay.paused
        self.btn_pause.config(text="▶ 繼續" if self.overlay.paused else "⏸ 暫停")

    # --- 覆蓋層設定 ---
    def toggle_adjust(self):
        on = not self.overlay.adjust
        self.overlay.set_adjust(on)
        self.btn_adjust.config(text="完成調整" if on else "調整位置/大小")
        if not on:
            self.save_settings()

    def on_clickthrough(self):
        self.cfg["clickthrough"] = self.var_ct.get()
        self.overlay._apply_clickthrough()

    # --- 設定存取 ---
    def load_settings(self):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
            for k in self.cfg:
                if k in saved:
                    self.cfg[k] = saved[k]
        except Exception:
            pass

    def save_settings(self):
        try:
            self.cfg["geometry"] = self.overlay.win.geometry()
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.cfg, f, ensure_ascii=False, indent=1)
        except Exception:
            pass

    def on_close(self):
        self.live_gen += 1
        self.save_settings()
        self.root.destroy()


if __name__ == "__main__":
    App().root.mainloop()

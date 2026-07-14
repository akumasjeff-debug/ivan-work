# -*- coding: utf-8 -*-
"""PTT 彈幕 - 本機伺服器
靜態檔案 + /ptt/* 代理到 https://www.ptt.cc （帶 over18=1 cookie，繞過瀏覽器 CORS）
啟動: py server.py  → http://localhost:8003/danmaku.html
"""
import gzip
import os
import sys
import time
import urllib.error
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

PORT = 8003
PTT_BASE = "https://www.ptt.cc"

os.chdir(os.path.dirname(os.path.abspath(__file__)))


class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        # 全部不快取：靜態檔改版後瀏覽器才不會抱著舊頁
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_GET(self):
        if self.path.startswith("/ptt/"):
            self.proxy_ptt(self.path[len("/ptt"):])
        else:
            super().do_GET()

    def proxy_ptt(self, path):
        # 只允許代理 ptt.cc 站內路徑（不含跳外部網址）
        if not path.startswith("/") or "//" in path:
            self.send_error(400, "bad path")
            return
        # /bbs/ 頁面：PTT 回 Cache-Control: max-age=900s，中間快取層會回 15 分鐘內
        # 的舊頁 → 把 query 換成每次不同的時間戳強制拿最新。
        # /poll、/v1/longpoll 等 API：query 帶簽名（offset-sig/size-sig），必須原樣轉發。
        base = path.split("?", 1)[0]
        if base.startswith("/bbs/"):
            url = PTT_BASE + base + "?_=" + str(time.time_ns())
        else:
            url = PTT_BASE + path
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Cookie": "over18=1",
            "Accept-Encoding": "gzip",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        })
        try:
            # longpoll 可能掛著等新推文（官方前端 timeout 28 秒），要給比它長
            with urllib.request.urlopen(req, timeout=40) as r:
                body = r.read()
                ctype = r.headers.get("Content-Type", "text/html; charset=utf-8")
                if r.headers.get("Content-Encoding") == "gzip":
                    body = gzip.decompress(body)
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(("PTT HTTP %d" % e.code).encode("utf-8"))
            return
        except Exception as e:
            self.send_response(502)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(("proxy error: %s" % e).encode("utf-8"))
            return
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        # 靜音靜態檔 log，只留代理錯誤（除錯時可拿掉）
        pass


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    print("PTT danmaku server: http://localhost:%d/danmaku.html" % port)
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()

"""aihot.news 官方 Agent API 的最小客户端（热点榜 + 事件详情）。
aihot 声明个人使用免费，商用需向其取得书面授权；不要爬它的网页（会拦截自动化浏览器）。"""
import gzip
import json
import time
import urllib.request

API = "https://aihot.news/api/v1"
UA = {"User-Agent": "nonameskill (personal use)", "Accept-Encoding": "gzip"}


def api_get(path, retries=3):
    for k in range(retries):
        try:
            with urllib.request.urlopen(urllib.request.Request(API + path, headers=UA), timeout=30) as r:
                raw = r.read()
                return json.loads(gzip.decompress(raw) if r.headers.get("Content-Encoding") == "gzip" else raw)
        except Exception:
            if k == retries - 1:
                raise
            time.sleep(5 * (k + 1))


def hot_topics():
    return api_get("/hot-topics")["items"]


def story_id(item):
    return ((item.get("links") or {}).get("story") or "").rstrip("/").split("/")[-1]


def story(item):
    """事件详情：摘要 digest + 相关报道 reports（标题、原文链接）。没有事件聚合时返回 None。"""
    sid = story_id(item)
    return api_get(f"/stories/{sid}")["story"] if sid else None

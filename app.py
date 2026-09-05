import os, re
from urllib.parse import urlparse
import requests
from flask import Flask, jsonify, request, Response, stream_with_context
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": os.getenv("CORS_ORIGINS", "*")}})
ALLOWED_HOSTS = {"instagram.com","www.instagram.com","m.instagram.com"}

def valid_url(url):
    try:
        p=urlparse(url.strip())
        return (p.hostname or "").lower() in ALLOWED_HOSTS and bool(re.match(r"^/(reel|reels|p)/[^/]+/?", p.path or ""))
    except Exception:
        return False

def opts():
    return {
        "quiet":True,"no_warnings":True,"skip_download":True,"noplaylist":True,
        "format":"best[ext=mp4]/best","socket_timeout":25,"retries":2,
        "http_headers":{"User-Agent":"Mozilla/5.0","Referer":"https://www.instagram.com/"}
    }

def extract(url):
    with yt_dlp.YoutubeDL(opts()) as ydl:
        return ydl.extract_info(url, download=False)

def direct_url(info):
    if info.get("url"):
        return info["url"]
    formats=info.get("formats") or []
    c=[f for f in formats if f.get("url") and (f.get("ext")=="mp4" or (f.get("vcodec") not in (None,"none") and f.get("acodec") not in (None,"none")))]
    if not c:
        c=[f for f in formats if f.get("url")]
    return c[-1]["url"] if c else None

@app.get("/health")
def health():
    return jsonify({"ok":True,"version":3})

@app.post("/api/extract")
def api_extract():
    data=request.get_json(silent=True) or {}
    url=str(data.get("url","")).strip()
    if not valid_url(url):
        return jsonify({"ok":False,"error":"Geçerli bir herkese açık Instagram Reels bağlantısı gerekli."}),400
    try:
        info=extract(url)
        if not direct_url(info):
            return jsonify({"ok":False,"error":"Video bağlantısı çözümlenemedi."}),422
        return jsonify({
            "ok":True,
            "title":info.get("title") or "Instagram Reels",
            "thumbnail":info.get("thumbnail"),
            "duration":info.get("duration"),
            "uploader":info.get("uploader"),
            "download_url":"/api/download?url="+requests.utils.quote(url,safe="")
        })
    except Exception:
        return jsonify({"ok":False,"error":"Video şu anda çözümlenemedi."}),422

@app.get("/api/download")
def api_download():
    page_url=str(request.args.get("url","")).strip()
    if not valid_url(page_url):
        return jsonify({"ok":False,"error":"Geçerli Instagram bağlantısı gerekli."}),400
    try:
        info=extract(page_url)
        durl=direct_url(info)
        if not durl:
            return jsonify({"ok":False,"error":"İndirme bağlantısı bulunamadı."}),422

        upstream=requests.get(
            durl,stream=True,timeout=(15,120),
            headers={"User-Agent":"Mozilla/5.0","Referer":"https://www.instagram.com/"}
        )
        upstream.raise_for_status()

        def generate():
            try:
                for chunk in upstream.iter_content(chunk_size=262144):
                    if chunk:
                        yield chunk
            finally:
                upstream.close()

        headers={
            "Content-Disposition":'attachment; filename="reelsindir-video.mp4"',
            "Cache-Control":"no-store",
            "X-Content-Type-Options":"nosniff"
        }
        if upstream.headers.get("Content-Length"):
            headers["Content-Length"]=upstream.headers["Content-Length"]

        return Response(
            stream_with_context(generate()),
            status=200,
            headers=headers,
            content_type=upstream.headers.get("Content-Type","video/mp4")
        )
    except Exception:
        return jsonify({"ok":False,"error":"Dosya indirilemedi. Tekrar deneyin."}),422

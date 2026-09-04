import os, re
from urllib.parse import urlparse
from flask import Flask, jsonify, request, redirect
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": os.getenv("CORS_ORIGINS", "*")}})

ALLOWED_HOSTS = {"instagram.com","www.instagram.com","m.instagram.com"}

def valid_url(url):
    try:
        p = urlparse(url.strip())
        return (p.hostname or "").lower() in ALLOWED_HOSTS and bool(re.match(r"^/(reel|reels|p)/[^/]+/?", p.path or ""))
    except Exception:
        return False

def opts():
    return {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "noplaylist": True,
        "format": "best[ext=mp4]/best",
        "socket_timeout": 20,
        "retries": 2,
    }

def extract(url):
    with yt_dlp.YoutubeDL(opts()) as ydl:
        return ydl.extract_info(url, download=False)

@app.get("/")
def home():
    return jsonify({"service":"reelsindir.com backend","status":"ok"})

@app.get("/health")
def health():
    return jsonify({"ok":True})

@app.post("/api/extract")
def api_extract():
    data = request.get_json(silent=True) or {}
    url = str(data.get("url","")).strip()
    if not valid_url(url):
        return jsonify({"ok":False,"error":"Geçerli bir herkese açık Instagram Reels/gönderi bağlantısı gerekli."}), 400
    try:
        info = extract(url)
        direct = info.get("url")
        if not direct:
            candidates = [f for f in (info.get("formats") or []) if f.get("url")]
            if candidates:
                direct = candidates[-1]["url"]
        if not direct:
            return jsonify({"ok":False,"error":"Video bağlantısı çözümlenemedi."}), 422
        return jsonify({
            "ok":True,
            "title":info.get("title") or "Instagram Reels",
            "thumbnail":info.get("thumbnail"),
            "duration":info.get("duration"),
            "uploader":info.get("uploader"),
            "download_url":direct
        })
    except Exception:
        return jsonify({"ok":False,"error":"Video şu anda çözümlenemedi. Başka bir herkese açık Reels bağlantısı deneyin."}), 422

@app.get("/api/download")
def api_download():
    url = str(request.args.get("url","")).strip()
    if not valid_url(url):
        return jsonify({"ok":False,"error":"Geçerli Instagram bağlantısı gerekli."}), 400
    try:
        info = extract(url)
        direct = info.get("url")
        if not direct:
            candidates = [f for f in (info.get("formats") or []) if f.get("url")]
            if candidates:
                direct = candidates[-1]["url"]
        if not direct:
            return jsonify({"ok":False,"error":"İndirme bağlantısı bulunamadı."}), 422
        return redirect(direct, code=302)
    except Exception:
        return jsonify({"ok":False,"error":"İndirme bağlantısı oluşturulamadı."}), 422

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT","10000")))


import os
import uuid
import json
from pathlib import Path
from urllib.parse import urlparse

from flask import Flask, request, jsonify, render_template_string, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024

ALLOWED = {".mp4", ".mov", ".mkv", ".webm"}

HTML = """
<!DOCTYPE html>
<html lang="my">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Myanmar Movie Recap AI</title>
<style>
*{box-sizing:border-box}
body{margin:0;background:#101522;color:white;font-family:Arial,sans-serif}
header{background:#19243a;padding:22px;text-align:center}
header h2{margin:0;color:#55d6be}
main{max-width:650px;margin:20px auto;padding:15px}
.card{background:#1c2940;padding:20px;border-radius:15px;margin-bottom:18px}
h3{color:#55d6be;margin-top:0}
input,select,button{width:100%;padding:14px;margin-top:10px;
border:0;border-radius:9px;font-size:15px}
input,select{background:#fff;color:#222}
button{background:#14b89a;color:white;font-weight:bold}
button:disabled{opacity:.5}
#status{margin-top:15px;color:#55d6be;word-break:break-word}
small{color:#b8c5d9}
video{width:100%;margin-top:12px;border-radius:10px}
</style>
</head>
<body>
<header>
<h2>Myanmar Movie Recap AI</h2>
<p>မြန်မာဘာသာဖြင့် Video Recap ပြုလုပ်ရန်</p>
</header>

<main>
<div class="card">
<h3>၁။ Video ထည့်ရန်</h3>
<label>ဖုန်းထဲမှ Video Upload လုပ်ရန်</label>
<input type="file" id="video" accept="video/*">
<br><br>
<small>သို့မဟုတ် Video Link ထည့်ပါ</small>
<input type="url" id="videoUrl" placeholder="https://example.com/video">
<button onclick="submitVideo()">Video ထည့်မည်</button>
<div id="status"></div>
<video id="preview" controls hidden></video>
</div>

<div class="card">
<h3>၂။ အသံရွေးရန်</h3>
<select id="voice">
<option value="male">အမျိုးသားအသံ</option>
<option value="female">အမျိုးသမီးအသံ</option>
</select>
</div>

<div class="card">
<h3>၃။ ဘာသာပြန်ရန်</h3>
<p>Video ကို ထည့်ပြီးနောက် မြန်မာဘာသာပြန်ခြင်း၊
စာတန်းထိုးခြင်းနှင့် အသံထည့်ခြင်းတို့ကို
နောက်တစ်ဆင့်တွင် ချိတ်ဆက်ပေးပါမည်။</p>
<button onclick="alert('Processing engine ကို နောက်တစ်ဆင့်တွင် ချိတ်ဆက်ပါမည်။')">
Recap စတင်မည်
</button>
</div>
</main>

<script>
async function submitVideo(){
 const file=document.getElementById('video').files[0];
 const url=document.getElementById('videoUrl').value.trim();
 const status=document.getElementById('status');
 const preview=document.getElementById('preview');

 status.textContent='လုပ်ဆောင်နေပါသည်...';

 const data=new FormData();

 if(file){
   data.append('video',file);
 }else if(url){
   data.append('url',url);
 }else{
   status.textContent='Video သို့မဟုတ် Link ထည့်ပေးပါ။';
   return;
 }

 try{
   const response=await fetch('/api/upload',{
     method:'POST',body:data
   });
   const result=await response.json();

   if(!response.ok) throw new Error(result.error);

   status.textContent=result.message;

   if(file){
     preview.src=URL.createObjectURL(file);
     preview.hidden=false;
   }
 }catch(error){
   status.textContent='Error: '+error.message;
 }
}
</script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML)


@app.route("/api/status")
def status():
    return jsonify({
        "success": True,
        "app": "Myanmar Movie Recap AI",
        "server": "Python Flask Working"
    })


@app.route("/api/upload", methods=["POST"])
def upload():

    file = request.files.get("video")
    video_url = request.form.get("url", "").strip()

    if file and file.filename:
        ext = Path(file.filename).suffix.lower()

        if ext not in ALLOWED:
            return jsonify({"error": "မထောက်ပံ့သော Video Format ဖြစ်သည်။"}), 400

        filename = str(uuid.uuid4()) + ext
        file.save(UPLOAD_DIR / filename)

        return jsonify({
            "success": True,
            "message": "Video Upload အောင်မြင်ပါသည်။",
            "filename": filename
        })

    if video_url:
        parsed = urlparse(video_url)

        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            return jsonify({"error": "မှန်ကန်သော Video Link ထည့်ပါ။"}), 400

        try:
            import yt_dlp

            filename = str(uuid.uuid4())
            options = {
                "format": "best[ext=mp4]/best",
                "outtmpl": str(UPLOAD_DIR / (filename + ".%(ext)s")),
                "noplaylist": True,
                "quiet": True,
                "no_warnings": True,
                "socket_timeout": 30
            }

            with yt_dlp.YoutubeDL(options) as ydl:
                ydl.download([video_url])

            return jsonify({
                "success": True,
                "message": "Video Link မှ Download အောင်မြင်ပါသည်။"
            })

        except ImportError:
            return jsonify({
                "error": "yt-dlp မတပ်ဆင်ရသေးပါ။"
            }), 500

        except Exception as e:
            return jsonify({
                "error": "Video Link ရယူမရပါ။ " + str(e)[:200]
            }), 400

    return jsonify({"error": "Video သို့မဟုတ် Link ထည့်ပါ။"}), 400


@app.route("/uploads/<filename>")
def get_video(filename):
    return send_from_directory(UPLOAD_DIR, filename)


@app.errorhandler(413)
def too_large(e):
    return jsonify({"error": "Video ဖိုင်အရွယ်အစား 500MB ထက် မကျော်ရပါ။"}), 413


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
  

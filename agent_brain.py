import os
import json
import urllib.parse
import requests
import subprocess
from google import genai

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")

STATE_FILE = "agent_state.json"

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {"chat_id": CHAT_ID, "active": True, "daily_target": 10, "uploaded_today": 0, "processed_videos": [], "last_update_id": 0}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def send_telegram(chat_id, msg):
    if not chat_id:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": msg})

def send_telegram_video(chat_id, video_path, caption):
    if not chat_id or not os.path.exists(video_path):
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo"
    with open(video_path, "rb") as video_file:
        r = requests.post(
            url,
            data={"chat_id": chat_id, "caption": caption[:1000]},
            files={"video": video_file}
        )
        return r.status_code == 200

def send_telegram_photo(chat_id, photo_path, caption):
    if not chat_id or not os.path.exists(photo_path):
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    with open(photo_path, "rb") as img:
        requests.post(
            url,
            data={"chat_id": chat_id, "caption": caption[:1000]},
            files={"photo": img}
        )

def check_commands(state):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    params = {"offset": state.get("last_update_id", 0) + 1}
    try:
        res = requests.get(url, params=params, timeout=15).json()
    except:
        return state

    if not res.get("ok"):
        return state

    for update in res.get("result", []):
        state["last_update_id"] = update["update_id"]
        msg = update.get("message", {})
        c_id = msg.get("chat", {}).get("id")
        text = msg.get("text", "").strip()

        if c_id:
            state["chat_id"] = c_id

        if text.startswith("/start"):
            state["active"] = True
            send_telegram(state["chat_id"], "🇮🇳 GTA 6 Hindi Viral Agent Active Hai!\n\nCommands:\n/target 15 - Daily Hindi Reels/Shorts limit set karein (Max 20)\n/status - Live report dekhein\n/reset - Aaj ka counter 0 karein\n/stop - Engine ko pause karein")
        elif text.startswith("/target"):
            parts = text.split()
            if len(parts) > 1 and parts[1].isdigit():
                limit = min(int(parts[1]), 20)
                state["daily_target"] = limit
                send_telegram(state["chat_id"], f"🎯 Target Updated: Ab main roz {limit} Hindi Viral Shorts/Reels edit karke dunga!")
        elif text.startswith("/status"):
            send_telegram(state["chat_id"], f"📊 GTA 6 Hindi Agent Report:\n• Active: {state['active']}\n• Daily Limit: {state['daily_target']}\n• Ready Today: {state['uploaded_today']}\n• Total Clips Processed: {len(state['processed_videos'])}")
        elif text.startswith("/reset"):
            state["uploaded_today"] = 0
            send_telegram(state["chat_id"], "🔄 Aaj ka counter 0 ho gaya hai!")
        elif text.startswith("/stop"):
            state["active"] = False
            send_telegram(state["chat_id"], "⏸ Engine Paused. Wapas chalu karne ke liye /start bhejein.")

    return state

def find_hindi_gta6_videos():
    # Specifically target Indian / Hindi GTA 6 shorts & creators
    queries = [
        "ytsearch10:GTA 6 Hindi shorts viral",
        "ytsearch10:GTA 6 India reaction Hindi gameplay",
        "ytsearch10:GTA 6 hidden details in Hindi",
        "ytsearch10:Techno Gamerz GTA 6 LazyAssassin Hindi"
    ]
    videos = []
    for q in queries:
        cmd = ["yt-dlp", q, "--dump-json", "--no-playlist", "--flat-playlist"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        for line in res.stdout.strip().split("\n"):
            if line:
                try:
                    videos.append(json.loads(line))
                except:
                    pass
    return videos

def generate_hindi_script_and_seo(title, url):
    prompt = f"""
    Trending GTA 6 video for Indian audience: "{title}" ({url})
    Write response strictly in Hinglish (Hindi written in English alphabet) for Indian YouTube Shorts & Instagram Reels:
    1. HINDI_VOICEOVER: Write an exciting 20-second Hindi commentary script (in Devanagari Hindi) that a gamer speaks over this GTA 6 clip.
    2. HOOK_TEXT: Short 4-word shocking Hindi/Hinglish text to show on top of video.
    3. VIRAL_TITLE: Best Hindi/Hinglish title under 60 chars with emojis.
    4. CAPTION_AND_TAGS: Hindi caption + Top 12 Indian Gaming Hashtags (#GTA6Hindi #GTA6India #IndianGaming #Shorts etc.)
    5. COMPETITOR_TECHNIQUE: Why this topic is going viral in India.
    """
    ai_text = None
    try:
        client = genai.Client(api_key=GEMINI_KEY)
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        if response and response.text:
            ai_text = response.text
    except Exception:
        pass

    if not ai_text:
        try:
            encoded = urllib.parse.quote(prompt)
            r = requests.get(f"https://text.pollinations.ai/{encoded}", timeout=25)
            if r.status_code == 200 and len(r.text) > 40:
                ai_text = r.text
        except Exception:
            pass

    voice_script = "भाई लोग! जीटीए सिक्स का ये खतरनाक सीन देखो! रॉकस्टार गेम्स ने इसमें ऐसी रियलिस्टिक डिटेल डाली है जो किसी ने नोटिस नहीं की! वीडियो को आखिर तक देखो और कमेंट में बताओ आपको कैसा लगा!"

    if not ai_text:
        clean_t = title[:40]
        ai_text = (
            f"🇮🇳 HINDI VIRAL SHORT & REEL PACKAGE:\n\n"
            f"📌 Viral Hindi Title: भाई GTA 6 में ये क्या डाल दिया?! 😱🔥 | {clean_t} #GTA6Hindi\n\n"
            f"🪝 3-Sec On-Screen Hook: 'GTA 6 का सबसे बड़ा राज़! 🤯'\n\n"
            f"🎙 AI Hindi Voiceover Added:\n'{voice_script}'\n\n"
            f"📝 Copy-Paste Hindi Caption:\n"
            f"भाई लोग GTA 6 की ये डिटेल देखकर होश उड़ जाएंगे! 😱 क्या आपने ये नोटिस किया था? कमेंट में जरूर बताओ! 👇🔥\n\n"
            f"🏷 Indian Viral Hashtags:\n"
            f"#GTA6 #GTA6Hindi #GTA6India #IndianGaming #TechnoGamerz #GamingShorts #HindiGaming #GTAVI #ViralReelsIndia #YouTubeShortsIndia"
        )
    return ai_text, voice_script

def build_hindi_short_video(vid_id, video_url, voice_script):
    raw_video = "raw_clip.mp4"
    voice_mp3 = "hindi_voice.mp3"
    thumb_jpg = "thumbnail.jpg"
    final_mp4 = "hindi_viral_short.mp4"

    for f in [raw_video, voice_mp3, thumb_jpg, final_mp4]:
        if os.path.exists(f):
            os.remove(f)

    # 1. Generate energetic Indian Hindi Male Voiceover using Edge-TTS (100% Free)
    tts_cmd = [
        "edge-tts",
        "--voice", "hi-IN-MadhurNeural",
        "--rate=+12%",
        "--text", voice_script,
        "--write-media", voice_mp3
    ]
    subprocess.run(tts_cmd, capture_output=True, text=True)

    # 2. Download High-Res Thumbnail for Custom Thumbnail & Fallback Visual
    thumb_url = f"https://i.ytimg.com/vi/{vid_id}/maxresdefault.jpg"
    r = requests.get(thumb_url)
    if r.status_code != 200:
        thumb_url = f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg"
        r = requests.get(thumb_url)
    with open(thumb_jpg, "wb") as f:
        f.write(r.content)

    # 3. Try downloading 25-sec clip using Android Player Client Bypass (avoids YouTube datacenter block)
    dl_cmd = [
        "yt-dlp", video_url,
        "--extractor-args", "youtube:player_client=android,web",
        "--download-sections", "*5-30",
        "-f", "best[height<=720][ext=mp4]/best[ext=mp4]/best",
        "-o", raw_video
    ]
    subprocess.run(dl_cmd, capture_output=True, text=True)

    if os.path.exists(raw_video) and os.path.getsize(raw_video) > 50000:
        # Merge downloaded gameplay + Hindi AI Voiceover + 9:16 Vertical Crop + Color Boost
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-i", raw_video,
            "-i", voice_mp3,
            "-t", "20",
            "-vf", "crop=ih*9/16:ih,scale=720:1280,eq=saturation=1.2:contrast=1.1",
            "-filter_complex", "[0:a]volume=0.25[bg];[1:a]volume=1.5[vo];[bg][vo]amix=inputs=2:duration=shortest[aout]",
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "libx264", "-preset", "fast", "-crf", "26",
            "-c:a", "aac", "-b:a", "128k",
            final_mp4
        ]
        subprocess.run(ffmpeg_cmd, capture_output=True, text=True)

    # 4. Guaranteed Fallback: If YouTube blocks cloud IP, create Dynamic 9:16 Zoom-Pan Hindi Short from HD Frame + Hindi Voiceover
    if not os.path.exists(final_mp4) or os.path.getsize(final_mp4) < 10000:
        ffmpeg_fallback = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", thumb_jpg,
            "-i", voice_mp3,
            "-vf", "scale=1280:720,crop=405:720,scale=720:1280,eq=saturation=1.25:contrast=1.1",
            "-c:v", "libx264", "-t", "16", "-pix_fmt", "yuv420p", "-preset", "fast",
            "-c:a", "aac", "-b:a", "128k", "-shortest",
            final_mp4
        ]
        subprocess.run(ffmpeg_fallback, capture_output=True, text=True)

    return final_mp4, thumb_jpg

def main():
    state = load_state()
    if CHAT_ID and not state.get("chat_id"):
        state["chat_id"] = CHAT_ID

    state = check_commands(state)
    c_id = state.get("chat_id")

    if not c_id or not state["active"] or state["uploaded_today"] >= state["daily_target"]:
        save_state(state)
        return

    videos = find_hindi_gta6_videos()
    for v in videos:
        vid_id = v.get("id")
        title = v.get("title", "GTA 6 Hindi Clip")
        if vid_id and vid_id not in state["processed_videos"]:
            url = f"https://www.youtube.com/watch?v={vid_id}"
            send_telegram(c_id, f"🇮🇳 Naya Trending Hindi GTA 6 Video Mila!\n🎬 Title: {title}\n🔗 {url}\n\n⏳ Ab main isme Hindi Voiceover, 9:16 Vertical Edit, Custom Thumbnail aur Hindi SEO taiyar kar raha hu...")

            seo_text, voice_script = generate_hindi_script_and_seo(title, url)
            final_mp4, thumb_jpg = build_hindi_short_video(vid_id, url, voice_script)

            # Send Custom Thumbnail First
            if os.path.exists(thumb_jpg):
                send_telegram_photo(c_id, thumb_jpg, f"🖼 Ready Custom Thumbnail (#{state['uploaded_today'] + 1}/{state['daily_target']})")

            # Send Edited 9:16 Hindi Video + SEO Package
            sent = send_telegram_video(c_id, final_mp4, f"🎬 READY 9:16 HINDI SHORT VIDEO (#{state['uploaded_today'] + 1}/{state['daily_target']})\n\n{seo_text}")
            if not sent:
                send_telegram(c_id, seo_text)

            state["processed_videos"].append(vid_id)
            state["uploaded_today"] += 1
            break

    save_state(state)

if __name__ == "__main__":
    main()

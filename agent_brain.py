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
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo"
    with open(video_path, "rb") as video_file:
        requests.post(
            url,
            data={"chat_id": chat_id, "caption": caption[:1000]},
            files={"video": video_file}
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
            send_telegram(state["chat_id"], "✅ GTA 6 Autonomous Viral Engine Active Hai!\n\nCommands:\n/target 15 - Daily reels limit set karein (Max 20)\n/status - Live report aur analytics dekhein\n/reset - Aaj ka counter 0 karein\n/stop - Engine ko pause karein")
        elif text.startswith("/target"):
            parts = text.split()
            if len(parts) > 1 and parts[1].isdigit():
                limit = min(int(parts[1]), 20)
                state["daily_target"] = limit
                send_telegram(state["chat_id"], f"🎯 Target Updated: Ab main roz {limit} Viral Shorts/Reels cut aur edit karke dunga!")
        elif text.startswith("/status"):
            send_telegram(state["chat_id"], f"📊 GTA 6 Agent Live Report:\n• Engine Active: {state['active']}\n• Daily Limit: {state['daily_target']}\n• Ready Today: {state['uploaded_today']}\n• Total Viral Clips Processed: {len(state['processed_videos'])}")
        elif text.startswith("/reset"):
            state["uploaded_today"] = 0
            send_telegram(state["chat_id"], "🔄 Aaj ka counter 0 ho gaya hai! Ab naye clips banenge.")
        elif text.startswith("/stop"):
            state["active"] = False
            send_telegram(state["chat_id"], "⏸ Engine Paused. Wapas chalu karne ke liye /start bhejein.")

    return state

def find_viral_gta6():
    queries = [
        "ytsearch8:GTA 6 viral shorts clips",
        "ytsearch8:GTA 6 trailer hidden details reaction",
        "ytsearch8:GTA VI leaks gameplay analysis"
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

def analyze_with_ai(title, url):
    prompt = f"""
    Trending GTA 6 video: "{title}" ({url})
    Create a ready-to-post Viral YouTube Short & Instagram Reel package in Hinglish:
    1. Competitor Viral Technique (Why people are watching this)
    2. 3-Second On-Screen Hook Text
    3. Best Viral Title (with emojis, under 60 chars)
    4. Copy-Paste Caption & Top 12 Viral Hashtags (#GTA6 #GTAVI #Shorts #Reels etc.)
    """
    # Engine 1: Try User's Gemini Key (AQ... or AIza...)
    try:
        client = genai.Client(api_key=GEMINI_KEY)
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        if response and response.text:
            return response.text
    except Exception as e:
        print("Primary Gemini key notice:", e)

    # Engine 2: 100% Free Unlimited AI Fallback (No Key Needed)
    try:
        encoded = urllib.parse.quote(prompt)
        r = requests.get(f"https://text.pollinations.ai/{encoded}", timeout=25)
        if r.status_code == 200 and len(r.text) > 40:
            return r.text
    except Exception as e:
        print("Secondary AI notice:", e)

    # Engine 3: Built-in Pro Template
    clean_title = title[:45]
    return (
        f"🔥 VIRAL SHORT/REEL SEO PACKAGE:\n\n"
        f"📌 Viral Title: Wait for this detail in GTA 6! 😱🔥 | {clean_title} #GTA6\n\n"
        f"🪝 3-Sec Hook Text: '99% People Missed This in GTA 6! 👀'\n\n"
        f"📝 Copy-Paste Caption:\n"
        f"Did you notice this crazy detail in GTA 6? Drop your thoughts in the comments! 👇🔥\n\n"
        f"🏷 Viral Hashtags:\n"
        f"#GTA6 #GTAVI #GTA6Trailer #RockstarGames #GamingShorts #GTA6Leaks #ViralClips #YouTubeShorts #TrendingReels #GTACommunity"
    )

def download_and_edit_short(video_url, output_file="viral_short.mp4"):
    raw_file = "raw_clip.mp4"
    for f in [raw_file, output_file]:
        if os.path.exists(f):
            os.remove(f)

    # Download best 35-second viral segment (from 00:05 to 00:40)
    dl_cmd = [
        "yt-dlp", video_url,
        "--download-sections", "*5-40",
        "-f", "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "--merge-output-format", "mp4",
        "-o", raw_file
    ]
    subprocess.run(dl_cmd, capture_output=True, text=True)

    if not os.path.exists(raw_file):
        return False

    # FFmpeg Pro Edit: 9:16 Vertical Center Crop + Anti-Copyright Color Boost + 1.03x Speed
    ffmpeg_cmd = [
        "ffmpeg", "-y", "-i", raw_file,
        "-t", "30",
        "-vf", "crop=ih*9/16:ih,scale=720:1280,eq=saturation=1.15:contrast=1.08,setpts=PTS/1.03",
        "-af", "atempo=1.03",
        "-c:v", "libx264", "-preset", "fast", "-crf", "26",
        "-c:a", "aac", "-b:a", "128k",
        output_file
    ]
    subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
    return os.path.exists(output_file)

def main():
    state = load_state()
    if CHAT_ID and not state.get("chat_id"):
        state["chat_id"] = CHAT_ID

    state = check_commands(state)
    c_id = state.get("chat_id")

    if not c_id:
        print("Chat ID not found.")
        return

    if not state["active"]:
        save_state(state)
        return

    if state["uploaded_today"] >= state["daily_target"]:
        save_state(state)
        return

    videos = find_viral_gta6()
    for v in videos:
        vid_id = v.get("id")
        title = v.get("title", "GTA 6 Viral Clip")
        if vid_id and vid_id not in state["processed_videos"]:
            url = f"https://www.youtube.com/watch?v={vid_id}"
            send_telegram(c_id, f"🔍 New Trending GTA 6 Video Found!\n🎬 Title: {title}\n🔗 {url}\n\n⏳ Ab main iska 30-sec viral part cut kar raha hu, 9:16 Reels/Shorts mein edit kar raha hu aur SEO taiyar kar raha hu...")

            seo_package = analyze_with_ai(title, url)
            edited_ok = download_and_edit_short(url, "viral_short.mp4")

            if edited_ok:
                send_telegram_video(c_id, "viral_short.mp4", f"✅ Edited 9:16 Viral Short Ready! (#{state['uploaded_today'] + 1}/{state['daily_target']})\n\n{seo_package}")
            else:
                send_telegram(c_id, f"🚀 Viral Strategy & SEO Ready (#{state['uploaded_today'] + 1}/{state['daily_target']}):\n\n{seo_package}")

            state["processed_videos"].append(vid_id)
            state["uploaded_today"] += 1
            break

    save_state(state)

if __name__ == "__main__":
    main()

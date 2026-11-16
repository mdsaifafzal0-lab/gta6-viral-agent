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
            send_telegram(state["chat_id"], "🔥 GTA 6 Pro Editor Agent Active Hai!\n\nCommands:\n/target 15 - Daily Reels limit set karein (Max 20)\n/status - Live report dekhein\n/reset - Counter 0 karein\n/stop - Pause karein")
        elif text.startswith("/target"):
            parts = text.split()
            if len(parts) > 1 and parts[1].isdigit():
                limit = min(int(parts[1]), 20)
                state["daily_target"] = limit
                send_telegram(state["chat_id"], f"🎯 Target Set: Roz {limit} Pro Edited Shorts/Reels!")
        elif text.startswith("/status"):
            send_telegram(state["chat_id"], f"📊 Live Status:\nActive: {state['active']}\nDaily Limit: {state['daily_target']}\nCompleted Today: {state['uploaded_today']}\nTotal Edited: {len(state['processed_videos'])}")
        elif text.startswith("/reset"):
            state["uploaded_today"] = 0
            send_telegram(state["chat_id"], "🔄 Counter 0 ho gaya hai!")
        elif text.startswith("/stop"):
            state["active"] = False
            send_telegram(state["chat_id"], "⏸ Paused.")

    return state

def find_viral_gta6_shorts():
    # Search actual high-energy GTA 6 edits, comparisons & Indian streamer reactions
    queries = [
        "ytsearch12:GTA 6 vs GTA 5 edit #shorts",
        "ytsearch12:GTA 6 crazy details edit #shorts",
        "ytsearch12:GTA 6 Hindi reaction Techno Gamerz BeastBoyShub #shorts"
    ]
    videos = []
    for q in queries:
        cmd = ["yt-dlp", q, "--dump-json", "--no-playlist", "--flat-playlist"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        for line in res.stdout.strip().split("\n"):
            if line:
                try:
                    v = json.loads(line)
                    # Prefer short punchy videos under 90 seconds
                    dur = v.get("duration") or 30
                    if dur <= 120:
                        videos.append(v)
                except:
                    pass
    return videos

def download_real_video(vid_id, url, out_path="raw_clip.mp4"):
    if os.path.exists(out_path):
        os.remove(out_path)

    # Strategy 1: yt-dlp with iOS / TV Embedded client (Bypasses GitHub IP blocks!)
    clients = ["ios", "tv_embedded", "mweb", "android_vr"]
    for c in clients:
        cmd = [
            "yt-dlp", url,
            "--extractor-args", f"youtube:player_client={c}",
            "-f", "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "--merge-output-format", "mp4",
            "--max-filesize", "40M",
            "-o", out_path
        ]
        subprocess.run(cmd, capture_output=True, text=True, timeout=45)
        if os.path.exists(out_path) and os.path.getsize(out_path) > 150000:
            return True

    # Strategy 2: Piped / Invidious Public API Mirror Fallback (Guaranteed real video stream)
    mirrors = [
        f"https://pipedapi.kavin.rocks/streams/{vid_id}",
        f"https://pipedapi.tokhmi.xyz/streams/{vid_id}"
    ]
    for m in mirrors:
        try:
            r = requests.get(m, timeout=15).json()
            streams = r.get("videoStreams", [])
            for s in streams:
                if s.get("format") == "MPEG_4" and not s.get("videoOnly", False):
                    v_data = requests.get(s["url"], timeout=25).content
                    if len(v_data) > 150000:
                        with open(out_path, "wb") as f:
                            f.write(v_data)
                        return True
        except:
            pass

    return False

def create_neon_subtitles(hook_top, label_1, label_2, ass_file="captions.ass"):
    # Creates glowing neon green/yellow dynamic captions exactly like OPiKAT / Hormozi edits
    ass_content = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 720
PlayResY: 1280

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: TopHook,Liberation Sans,52,&H0000FFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,1,0,1,4,2,8,30,30,90,1
Style: NeonCenter,DejaVu Sans,68,&H0055FF00,&H000000FF,&H00003300,&H80000000,-1,0,0,0,100,100,2,0,1,5,4,2,30,30,360,1
Style: SubWhite,Liberation Sans,46,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,1,0,1,4,2,2,30,30,295,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,0:00:03.50,TopHook,,0,0,0,,{{\\fad(150,150)}}{hook_top}
Dialogue: 0,0:00:00.20,0:00:07.50,NeonCenter,,0,0,0,,{{\\fad(200,200)}}{label_1}
Dialogue: 0,0:00:00.20,0:00:07.50,SubWhite,,0,0,0,,WAIT FOR THE END 💀🔥
Dialogue: 0,0:00:07.60,0:00:22.00,NeonCenter,,0,0,0,,{{\\fad(200,200)}}{label_2}
Dialogue: 0,0:00:07.60,0:00:22.00,SubWhite,,0,0,0,,NEXT LEVEL REALISM 😱
"""
    with open(ass_file, "w", encoding="utf-8") as f:
        f.write(ass_content)
    return ass_file

def edit_pro_short(raw_file, hook_top, label_1, label_2, output_file="pro_viral_short.mp4"):
    if os.path.exists(output_file):
        os.remove(output_file)

    ass_file = create_neon_subtitles(hook_top, label_1, label_2)

    # Pro Editing Pipeline:
    # 1. Top 72% (720x920): Crisp HD Gameplay with Unsharp Mask + High Contrast/Saturation (like video_2.mp4)
    # 2. Bottom 28% (720x360): Zoomed Action/Streamer Cam Split-Screen with glowing divider
    # 3. Burned-in Neon Colored Captions (captions.ass)
    # 4. Original Audio + Bass Boost + 1.04x Anti-Copyright Pitch/Speed
    filter_complex = (
        "[0:v]setpts=PTS/1.04,split=2[vtop][vbot];"
        "[vtop]crop=ih*9/16:ih,scale=720:920:flags=lanczos,"
        "unsharp=5:5:1.2:5:5:0.0,eq=contrast=1.14:saturation=1.28:brightness=0.02[top_ready];"
        "[vbot]crop=iw*0.6:ih*0.4,scale=720:360:flags=lanczos,"
        "eq=contrast=1.18:saturation=1.2[bot_ready];"
        "[top_ready][bot_ready]vstack=inputs=2,"
        "drawbox=x=0:y=916:w=720:h=8:color=#00FF55@1:t=fill,"
        f"ass={ass_file}[vout];"
        "[0:a]atempo=1.04,aecho=0.8:0.88:20:0.15,bass=g=5:f=110:w=0.6[aout]"
    )

    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-ss", "2", "-t", "18",
        "-i", raw_file,
        "-filter_complex", filter_complex,
        "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "22",
        "-c:a", "aac", "-b:a", "160k",
        output_file
    ]
    res = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)

    # If video had no audio stream, run video-only filter
    if not os.path.exists(output_file) or os.path.getsize(output_file) < 30000:
        v_only_filter = (
            "[0:v]setpts=PTS/1.04,split=2[vtop][vbot];"
            "[vtop]crop=ih*9/16:ih,scale=720:920,unsharp=5:5:1.2:5:5:0.0,eq=contrast=1.14:saturation=1.28[top_ready];"
            "[vbot]crop=iw*0.6:ih*0.4,scale=720:360[bot_ready];"
            f"[top_ready][bot_ready]vstack=inputs=2,ass={ass_file}[vout]"
        )
        subprocess.run([
            "ffmpeg", "-y", "-ss", "2", "-t", "18", "-i", raw_file,
            "-filter_complex", v_only_filter, "-map", "[vout]",
            "-c:v", "libx264", "-preset", "fast", "-crf", "22", output_file
        ], capture_output=True, text=True)

    return os.path.exists(output_file) and os.path.getsize(output_file) > 30000

def generate_human_hinglish_seo(title):
    prompt = f"""
    Aap ek Indian Gen-Z Gaming Content Creator ho (jaise BeastBoyShub / Techno Gamerz ke editors).
    Video topic: "{title}"
    
    STRICT RULES:
    - Bilkul Devanagari Hindi (भाई लोग) MAT use karna! Sirf Roman Hinglish (English letters mein Hindi) likho.
    - AI jaisa formal mat likho. Bilkul casual, human-friendly, viral tone rakho.
    
    Format:
    TITLE: (Under 55 chars, casual Hinglish + 2 emojis + #shorts #gta6)
    CAPTION: (2 punchy Hinglish lines asking a question to boost comments)
    TAGS: (Top 10 viral tags)
    PINNED_COMMENT: (1 controversial/engaging Hinglish comment to pin)
    """
    seo_text = None
    try:
        client = genai.Client(api_key=GEMINI_KEY)
        r = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        if r and r.text:
            seo_text = r.text
    except:
        pass

    if not seo_text:
        try:
            encoded = urllib.parse.quote(prompt)
            r = requests.get(f"https://text.pollinations.ai/{encoded}", timeout=20)
            if r.status_code == 200 and len(r.text) > 40:
                seo_text = r.text
        except:
            pass

    if not seo_text:
        seo_text = (
            "📌 TITLE:\n"
            "GTA 5 vs GTA 6 Graphics Evolution is INSANE 💀🔥 #gta6 #shorts\n\n"
            "📝 INSTAGRAM & YOUTUBE CAPTION:\n"
            "Bhai Rockstar ne GTA 6 mein detailing kis level pe pahuncha di hai 😳🔥 Last wala part notice kiya kya? Comments mein batao!\n\n"
            "📌 PINNED COMMENT (Copy-Paste in Comments):\n"
            "0:09 pe bike aur dog ki physics dekho bhai, real life lag raha hai ya game? 💀👇\n\n"
            "🏷 VIRAL TAGS:\n"
            "#gta6 #gtavi #gta6india #indiangaming #gta5vsgta6 #rockstargames #gamingreels #viralshorts #technogamerz #gta6graphics"
        )
    return seo_text

def main():
    state = load_state()
    if CHAT_ID and not state.get("chat_id"):
        state["chat_id"] = CHAT_ID

    state = check_commands(state)
    c_id = state.get("chat_id")

    if not c_id or not state["active"] or state["uploaded_today"] >= state["daily_target"]:
        save_state(state)
        return

    videos = find_viral_gta6_shorts()
    for v in videos:
        vid_id = v.get("id")
        title = v.get("title", "GTA 6 Evolution Edit")
        if vid_id and vid_id not in state["processed_videos"]:
            url = f"https://www.youtube.com/watch?v={vid_id}"
            state["processed_videos"].append(vid_id)

            # Only proceed if REAL moving video downloads (Never send static image!)
            if download_real_video(vid_id, url, "raw_clip.mp4"):
                send_telegram(c_id, f"🎬 Real Viral GTA 6 Video Downloaded!\nSource: {title}\n\n⚡ Applying Split-Screen, Sharp HD Filter, Bass Boost & Neon Captions...")

                ok = edit_pro_short(
                    "raw_clip.mp4",
                    hook_top="WAIT FOR GTA 6 GRAPHICS",
                    label_1="GTA V  2013",
                    label_2="GTA VI 2026",
                    output_file="pro_viral_short.mp4"
                )

                seo = generate_human_hinglish_seo(title)
                if ok:
                    send_telegram_video(
                        c_id,
                        "pro_viral_short.mp4",
                        f"🔥 PRO EDITED SHORT (#{state['uploaded_today'] + 1}/{state['daily_target']})\n\n{seo}"
                    )
                    state["uploaded_today"] += 1
                    break

    save_state(state)

if __name__ == "__main__":
    main()

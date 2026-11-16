import os
import json
import requests
import subprocess
from google import genai

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")

STATE_FILE = "agent_state.json"

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {"active": True, "daily_target": 10, "uploaded_today": 0, "processed_videos": []}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def check_telegram_commands(state):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    res = requests.get(url).json()
    if not res.get("ok"):
        return state
    
    for update in res.get("result", []):
        msg = update.get("message", {})
        text = msg.get("text", "")
        if str(msg.get("chat", {}).get("id")) != str(CHAT_ID):
            continue
            
        if text.startswith("/start"):
            state["active"] = True
            send_telegram("✅ *GTA 6 Viral Agent Activated!*\nMain 24/7 YouTube monitor kar raha hu.\n\nCommands:\n`/target 15` - Daily limit set karein (Max 20)\n`/status` - Abhi ka report dekhein\n`/stop` - Agent ko rokein")
        elif text.startswith("/target"):
            parts = text.split()
            if len(parts) > 1 and parts[1].isdigit():
                limit = min(int(parts[1]), 20)
                state["daily_target"] = limit
                send_telegram(f"🎯 *Target Updated:* Aaj main `{limit}` Viral Shorts/Reels banaunga aur analyze karunga.")
        elif text.startswith("/status"):
            send_telegram(f"📊 *Agent Live Status:*\n• Active: `{state['active']}`\n• Aaj ka Target: `{state['daily_target']}`\n• Completed Today: `{state['uploaded_today']}`\n• Total Clips Analyzed: `{len(state['processed_videos'])}`")
        elif text.startswith("/stop"):
            state["active"] = False
            send_telegram("⏸ *Agent Paused.* Wapas chalu karne ke liye `/start` bhejein.")
            
    return state

def spy_and_find_gta6_viral(state):
    # Search top trending GTA 6 shorts & videos
    cmd = [
        "yt-dlp", "ytsearch5:GTA 6 viral clips shorts trailer",
        "--dump-json", "--no-playlist", "--flat-playlist"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    videos = []
    for line in result.stdout.strip().split("\n"):
        if line:
            try:
                videos.append(json.loads(line))
            except:
                pass
    return videos

def analyze_with_gemini(video_title, video_url):
    client = genai.Client(api_key=GEMINI_KEY)
    prompt = f"""
    You are a Viral GTA 6 Content Strategist & Video Editor Agent.
    A trending GTA 6 video was found: "{video_title}" ({video_url})
    
    Generate a complete Viral Package in Hinglish/English:
    1. Competitor Viral Hook Technique (Why is this getting views?)
    2. Exact 3-Second On-Screen Hook Text to add on our Reel/Short
    3. Best Viral Title for YouTube Shorts & Instagram Reels (under 60 chars)
    4. Copy-Paste SEO Description & Top 10 Viral Hashtags
    5. Editing Instruction (Cut pacing & music style)
    """
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return response.text

def main():
    state = load_state()
    state = check_telegram_commands(state)
    
    if not state["active"]:
        save_state(state)
        return
        
    if state["uploaded_today"] >= state["daily_target"]:
        send_telegram("🎉 Aaj ka Daily Target pura ho chuka hai! Kal subah fir se shuru karunga.")
        save_state(state)
        return

    videos = spy_and_find_gta6_viral(state)
    for v in videos:
        vid_id = v.get("id")
        title = v.get("title")
        if vid_id and vid_id not in state["processed_videos"]:
            url = f"https://www.youtube.com/watch?v={vid_id}"
            send_telegram(f"🔍 *New Trending GTA 6 Video Found!*\n🎬 Title: `{title}`\n🔗 {url}\n\n⏳ *Competitor Analysis & Viral Plan taiyar ho raha hai...*")
            
            analysis = analyze_with_gemini(title, url)
            send_telegram(f"🚀 *Viral Short/Reel Strategy Ready:*\n\n{analysis}")
            
            state["processed_videos"].append(vid_id)
            state["uploaded_today"] += 1
            break
            
    save_state(state)

if __name__ == "__main__":
    main()

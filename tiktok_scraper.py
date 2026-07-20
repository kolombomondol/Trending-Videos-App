import json
import os
import requests
from datetime import datetime, timezone

# 🔐 GitHub Secrets / Environment Variable থেকে নিরাপদভাবে API Key রিড করবে
RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY")
RAPIDAPI_HOST = "tiktok-api23.p.rapidapi.com"

TIKTOK_VIDEOS_FILE = "tiktok_videos.json"
TIKTOK_SEEN_IDS_FILE = "tiktok_seen_ids.json"

if not RAPIDAPI_KEY:
    raise ValueError("❌ RAPIDAPI_KEY পাওয়া যায়নি! GitHub Secrets-এ এটি সেট করুন।")

now = datetime.now(timezone.utc)

# ১. আগের জমানো সেকশন/দেখা ভিডিও আইডি লোড করা
seen_ids = {}
if os.path.exists(TIKTOK_SEEN_IDS_FILE):
    try:
        with open(TIKTOK_SEEN_IDS_FILE, "r", encoding="utf-8") as f:
            seen_ids = json.load(f)
    except Exception as e:
        print(f"⚠️ Error loading seen IDs: {e}")

def fetch_tiktok_trending():
    url = f"https://{RAPIDAPI_HOST}/api/search/general"
    
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST
    }
    
    params = {
        "keyword": "viral shorts",
        "count": "20",
        "cursor": "0"
    }

    all_videos = []
    new_videos_count = 0

    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()

        items = data.get("data", []) or data.get("item_list", []) or []

        for item in items:
            video_id = str(item.get("id") or item.get("aweme_id") or "")
            if not video_id:
                continue

            # firstSeenAt লজিক
            if video_id not in seen_ids:
                first_seen = now.isoformat()
                seen_ids[video_id] = {"firstSeenAt": first_seen}
                new_videos_count += 1
            else:
                first_seen = seen_ids[video_id].get("firstSeenAt", now.isoformat())

            video_obj = {
                "id": video_id,
                "title": item.get("desc", "TikTok Viral Video"),
                "author": item.get("author", {}).get("nickname", item.get("author", {}).get("unique_id", "TikTok User")),
                "playUrl": item.get("video", {}).get("play_addr", {}).get("url_list", [""])[0],
                "thumbnailUrl": item.get("video", {}).get("cover", {}).get("url_list", [""])[0],
                "viewCount": str(item.get("stats", {}).get("play_count", item.get("stats", {}).get("playCount", 0))),
                "publishedAt": now.isoformat(),
                "firstSeenAt": first_seen
            }
            all_videos.append(video_obj)

    except Exception as e:
        print(f"❌ TikTok Fetch Error: {e}")

    return all_videos, new_videos_count

print("🚀 Fetching TikTok Videos safely...")
tiktok_videos, new_count = fetch_tiktok_trending()

with open(TIKTOK_VIDEOS_FILE, "w", encoding="utf-8") as f:
    json.dump({"tiktok": tiktok_videos}, f, indent=4, ensure_ascii=False)

with open(TIKTOK_SEEN_IDS_FILE, "w", encoding="utf-8") as f:
    json.dump(seen_ids, f, indent=4)

print(f"✅ Saved {len(tiktok_videos)} videos ({new_count} new) to {TIKTOK_VIDEOS_FILE}")

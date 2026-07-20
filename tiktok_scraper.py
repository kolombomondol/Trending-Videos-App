import json
import os
import requests
from datetime import datetime, timezone

# 🔑 GitHub Secrets থেকে এপিআই চাবি রিড করবেimport json
import os
import requests
from datetime import datetime, timezone

RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY")
RAPIDAPI_HOST = "tiktok-api23.p.rapidapi.com"

TIKTOK_VIDEOS_FILE = "tiktok_videos.json"
TIKTOK_SEEN_IDS_FILE = "tiktok_seen_ids.json"

if not RAPIDAPI_KEY:
    raise ValueError("❌ RAPIDAPI_KEY পাওয়া যায়নি! Secrets চেক করুন।")

now = datetime.now(timezone.utc)

seen_ids = {}
if os.path.exists(TIKTOK_SEEN_IDS_FILE):
    try:
        with open(TIKTOK_SEEN_IDS_FILE, "r", encoding="utf-8") as f:
            seen_ids = json.load(f)
    except Exception as e:
        print(f"⚠️ Error loading seen IDs: {e}")

def fetch_global_tiktok_videos():
    url = f"https://{RAPIDAPI_HOST}/api/search/general"
    
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST
    }
    
    # অনুসন্ধানের জন্য কিওয়ার্ড
    keywords = ["viral", "funny"]
    
    all_videos = []
    new_videos_count = 0
    added_ids = set()

    for kw in keywords:
        params = {
            "keyword": kw,
            "count": "10",
            "cursor": "0"
        }

        try:
            print(f"🔍 Fetching for keyword: '{kw}'...")
            response = requests.get(url, headers=headers, params=params, timeout=15)
            print(f"📡 Status Code: {response.status_code}")
            
            if response.status_code != 200:
                print(f"❌ API Error Response: {response.text}")
                continue

            data = response.json()
            
            # API Response Structure পরীক্ষা
            items = []
            if isinstance(data, dict):
                items = data.get("data", []) or data.get("item_list", []) or data.get("itemList", []) or []
                if not items and "data" in data and isinstance(data["data"], dict):
                    items = data["data"].get("videos", []) or data["data"].get("posts", [])

            print(f"📦 Total items found for '{kw}': {len(items)}")

            if len(items) == 0:
                print(f"⚠️ Raw Response Sample: {str(data)[:300]}")

            for item in items:
                # Video ID বের করা
                video_id = str(item.get("id") or item.get("aweme_id") or item.get("video_id") or "")
                
                if not video_id or video_id in added_ids:
                    continue
                
                added_ids.add(video_id)

                if video_id not in seen_ids:
                    first_seen = now.isoformat()
                    seen_ids[video_id] = {"firstSeenAt": first_seen}
                    new_videos_count += 1
                else:
                    first_seen = seen_ids[video_id].get("firstSeenAt", now.isoformat())

                # ডাটা এক্সট্র্যাক্ট করা
                title = item.get("desc") or item.get("title") or "TikTok Viral Video"
                author = item.get("author", {}).get("nickname") or item.get("author", {}).get("unique_id") or "TikTok User"
                
                play_url = ""
                if isinstance(item.get("video"), dict):
                    play_addr = item.get("video", {}).get("play_addr", {})
                    if isinstance(play_addr, dict):
                        url_list = play_addr.get("url_list", [])
                        if url_list:
                            play_url = url_list[0]
                    elif isinstance(play_addr, str):
                        play_url = play_addr

                thumbnail_url = ""
                if isinstance(item.get("video"), dict):
                    cover = item.get("video", {}).get("cover", {})
                    if isinstance(cover, dict):
                        url_list = cover.get("url_list", [])
                        if url_list:
                            thumbnail_url = url_list[0]
                    elif isinstance(cover, str):
                        thumbnail_url = cover

                stats = item.get("stats", {}) or item.get("statistics", {})
                view_count = str(stats.get("play_count") or stats.get("playCount") or stats.get("digg_count") or "0")

                video_obj = {
                    "id": video_id,
                    "title": title,
                    "author": author,
                    "playUrl": play_url,
                    "thumbnailUrl": thumbnail_url,
                    "viewCount": view_count,
                    "publishedAt": now.isoformat(),
                    "firstSeenAt": first_seen
                }
                all_videos.append(video_obj)

        except Exception as e:
            print(f"❌ Exception fetching keyword '{kw}': {e}")

    return all_videos, new_videos_count

print("🚀 Fetching Global TikTok Videos...")
tiktok_videos, new_count = fetch_global_tiktok_videos()

with open(TIKTOK_VIDEOS_FILE, "w", encoding="utf-8") as f:
    json.dump({"tiktok": tiktok_videos}, f, indent=4, ensure_ascii=False)

with open(TIKTOK_SEEN_IDS_FILE, "w", encoding="utf-8") as f:
    json.dump(seen_ids, f, indent=4)

print(f"✅ Saved {len(tiktok_videos)} TikTok videos ({new_count} new) to {TIKTOK_VIDEOS_FILE}")
RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY")
RAPIDAPI_HOST = "tiktok-api23.p.rapidapi.com"

# 📂 টিকটকের জন্য আলাদা ফাইল
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

def fetch_global_tiktok_videos():
    url = f"https://{RAPIDAPI_HOST}/api/search/general"
    
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST
    }
    
    keywords = ["viral shorts", "trending fyp", "funny tiktok"]
    
    all_videos = []
    new_videos_count = 0
    added_ids = set()

    for kw in keywords:
        params = {
            "keyword": kw,
            "count": "15",
            "cursor": "0"
        }

        try:
            response = requests.get(url, headers=headers, params=params)
            data = response.json()

            items = data.get("data", []) or data.get("item_list", []) or []

            for item in items:
                video_id = str(item.get("id") or item.get("aweme_id") or "")
                
                if not video_id or video_id in added_ids:
                    continue
                
                added_ids.add(video_id)

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
            print(f"❌ Error fetching keyword '{kw}': {e}")

    return all_videos, new_videos_count

print("🚀 Fetching Global TikTok Videos...")
tiktok_videos, new_count = fetch_global_tiktok_videos()

# 💾 শুধু টিকটকের ডেটা আলাদা জেসন ফাইলে সেভ করা হচ্ছে
with open(TIKTOK_VIDEOS_FILE, "w", encoding="utf-8") as f:
    json.dump({"tiktok": tiktok_videos}, f, indent=4, ensure_ascii=False)

with open(TIKTOK_SEEN_IDS_FILE, "w", encoding="utf-8") as f:
    json.dump(seen_ids, f, indent=4)

print(f"✅ Saved {len(tiktok_videos)} TikTok videos ({new_count} new) to {TIKTOK_VIDEOS_FILE}")

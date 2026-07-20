import json
import os
import requests
from datetime import datetime, timezone

TIKTOK_VIDEOS_FILE = "tiktok_videos.json"
TIKTOK_SEEN_IDS_FILE = "tiktok_seen_ids.json"

now = datetime.now(timezone.utc)

# ১. আগে জমানো ভিডিও আইডি লোড করা
seen_ids = {}
if os.path.exists(TIKTOK_SEEN_IDS_FILE):
    try:
        with open(TIKTOK_SEEN_IDS_FILE, "r", encoding="utf-8") as f:
            seen_ids = json.load(f)
    except Exception as e:
        print(f"⚠️ Error loading seen IDs: {e}")

def fetch_country_viral_videos():
    url = "https://www.tikwm.com/api/feed/list"
    
    # 🌍 যে দেশগুলোর ভিডিও আনতে চান (দেশ কোড ও নাম)
    countries = {
        "BD": "Bangladesh",
        "US": "United States",
        "IN": "India",
        "GB": "United Kingdom",
        "BR": "Brazil",
        "ID": "Indonesia",
        "JP": "Japan"
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    country_videos_map = {}
    new_videos_count = 0

    print("🚀 Fetching 50 Viral Videos per Country...")

    for code, country_name in countries.items():
        print(f"🌍 Fetching 50 videos for: {country_name} ({code})...")
        country_videos = []
        added_ids = set()

        # ৫০টি ভিডিও কভার করতে ২ থেকে ৩টি ফেচ লুপ চালানো
        for page in range(1, 4):
            if len(country_videos) >= 50:
                break

            params = {
                "region": code,
                "count": 25
            }

            try:
                response = requests.get(url, params=params, headers=headers, timeout=15)
                if response.status_code != 200:
                    continue

                data = response.json()
                items = data.get("data", []) or []

                for item in items:
                    if len(country_videos) >= 50:
                        break

                    video_id = str(item.get("video_id") or item.get("id") or "")
                    if not video_id or video_id in added_ids:
                        continue

                    added_ids.add(video_id)

                    if video_id not in seen_ids:
                        first_seen = now.isoformat()
                        seen_ids[video_id] = {"firstSeenAt": first_seen}
                        new_videos_count += 1
                    else:
                        first_seen = seen_ids[video_id].get("firstSeenAt", now.isoformat())

                    # লিঙ্ক ও থাম্বনেইল
                    play_url = item.get("play") or item.get("wmplay") or ""
                    if play_url and not play_url.startswith("http"):
                        play_url = f"https://www.tikwm.com{play_url}"

                    thumbnail_url = item.get("cover") or ""
                    if thumbnail_url and not thumbnail_url.startswith("http"):
                        thumbnail_url = f"https://www.tikwm.com{thumbnail_url}"

                    video_obj = {
                        "id": video_id,
                        "title": item.get("title", f"Viral TikTok Video - {country_name}"),
                        "author": item.get("author", {}).get("nickname", "TikTok Creator"),
                        "playUrl": play_url,
                        "thumbnailUrl": thumbnail_url,
                        "viewCount": str(item.get("play_count", 0)),
                        "country": country_name,
                        "countryCode": code,
                        "publishedAt": now.isoformat(),
                        "firstSeenAt": first_seen
                    }
                    country_videos.append(video_obj)

            except Exception as e:
                print(f"❌ Error fetching {country_name}: {e}")

        country_videos_map[code] = country_videos
        print(f"✅ Fetched {len(country_videos)} videos for {country_name}")

    return country_videos_map, new_videos_count

tiktok_data, new_count = fetch_country_viral_videos()

# JSON ফাইলে সেভ করা
with open(TIKTOK_VIDEOS_FILE, "w", encoding="utf-8") as f:
    json.dump({"tiktok_by_country": tiktok_data}, f, indent=4, ensure_ascii=False)

with open(TIKTOK_SEEN_IDS_FILE, "w", encoding="utf-8") as f:
    json.dump(seen_ids, f, indent=4)

print(f"🎉 Saved Videos for All Countries Successfully ({new_count} new)!")

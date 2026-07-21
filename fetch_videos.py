import json
import os
import time
from datetime import datetime, timezone
from googleapiclient.discovery import build
import firebase_admin
from firebase_admin import credentials, messaging

# কনফিগারেশন - সব API_KEY_ স্বয়ংক্রিয়ভাবে লোড হবে
API_KEYS = [value for key, value in os.environ.items() if key.startswith("API_KEY_")]
API_KEYS = [key for key in API_KEYS if key]
VIDEOS_FILE = "videos.json"
NEW_VIDEOS_FILE = "new_videos.json"
SEEN_IDS_FILE = "seen_ids.json"

if not API_KEYS:
    raise ValueError("❌ Error: No API Keys found!")
else:
    print(f"✅ Total {len(API_KEYS)} API Keys loaded.")

region_codes = ["US", "BD", "IN", "GB", "SA", "AE", "PK", "CA", "AU", "DE", "FR", "JP", "KR", "ID", "NG", "MY", "SG", "TR", "IT", "ES", "DZ", "AR", "AT", "AZ", "BH", "BY", "BE", "BO", "BA", "BR", "BG", "CL", "CO", "CR", "HR", "CY", "CZ", "DK", "DO", "EC", "EG", "SV", "EE", "FI", "GE", "GH", "GR", "GT", "HN", "HK", "HU", "IS", "IQ", "IE", "IL", "JM", "JO", "KZ", "KE", "KW", "LV", "LB", "LY", "LI", "LT", "LU", "MK", "MT", "MX", "ME", "MA", "NP", "NL", "NZ", "NI", "NO", "OM", "PA", "PG", "PY", "PE", "PH", "PL", "PT", "QA", "RO", "RU", "SN", "RS", "SK", "SI", "ZA", "LK", "SE", "CH", "TW", "TZ", "TH", "TN", "UG", "UA", "UY", "VE", "VN", "YE", "ZW"]
category_map = {"comedy": "23", "song": "10", "news": "25", "sports": "17", "vlog": "22"}

now = datetime.now(timezone.utc)

seen_ids = {}
if os.path.exists(SEEN_IDS_FILE):
    with open(SEEN_IDS_FILE, "r", encoding="utf-8") as f:
        seen_ids = json.load(f)

def fetch_videos(youtube_client, region, cat_id):
    request = youtube_client.videos().list(part="snippet,statistics", chart="mostPopular", regionCode=region, videoCategoryId=cat_id, maxResults=25)
    response = request.execute()
    
    all_videos = []
    new_videos = []
    for item in response.get("items", []):
        video_id = item["id"]
        snippet = item["snippet"]
        stats = item["statistics"]
        
        # 🟢 ভিডিওটি প্রথম কখন দেখা গেছে তা বের করা
        if video_id not in seen_ids:
            first_seen = now.strftime("%Y-%m-%dT%H:%M:%SZ")
            seen_ids[video_id] = {"firstSeenAt": first_seen}
            is_brand_new = True
        else:
            first_seen = seen_ids[video_id].get("firstSeenAt", now.isoformat())
            is_brand_new = False

        # 🟢 video_obj-এর ভেতর 'firstSeenAt' যুক্ত করা হলো
        video_obj = {
            "id": video_id,
            "title": snippet["title"],
            "channelTitle": snippet["channelTitle"],
            "thumbnailUrl": snippet["thumbnails"]["high"]["url"],
            "viewCount": stats.get("viewCount", "0"),
            "publishedAt": snippet["publishedAt"],
            "firstSeenAt": first_seen  # 👈 এই ফিল্ডটি আগে মিসিং ছিল!
        }
        
        all_videos.append(video_obj)
        if is_brand_new:
            new_videos.append(video_obj)

    return all_videos, new_videos

final_data, new_only_data = {}, {}
total_videos_fetched, total_new_videos = 0, 0

for i, region in enumerate(region_codes):
    youtube = build("youtube", "v3", developerKey=API_KEYS[i // 20 % len(API_KEYS)])
    final_data[region], new_only_data[region] = {}, {}
    for cat_name, cat_id in category_map.items():
        try:
            all_v, new_v = fetch_videos(youtube, region, cat_id)
            final_data[region][cat_name] = all_v
            if new_v: new_only_data[region][cat_name] = new_v
            total_videos_fetched += len(all_v)
            total_new_videos += len(new_v)
        except Exception as e:
            continue
    if not new_only_data[region]: del new_only_data[region]

print(f"DEBUG: Total videos in final_data: {total_videos_fetched}")
print(f"DEBUG: Total new videos: {total_new_videos}")

with open(VIDEOS_FILE, "w", encoding="utf-8") as f: json.dump(final_data, f, indent=4, ensure_ascii=False)
with open(NEW_VIDEOS_FILE, "w", encoding="utf-8") as f: json.dump(new_only_data, f, indent=4, ensure_ascii=False)
with open(SEEN_IDS_FILE, "w", encoding="utf-8") as f: json.dump(seen_ids, f)

firebase_secret = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
if firebase_secret and total_new_videos > 0:
    try:
        if not firebase_admin._apps:
            firebase_admin.initialize_app(credentials.Certificate(json.loads(firebase_secret)))
        message = messaging.Message(
            notification=messaging.Notification(title="🔥 New Videos!", body=f"{total_new_videos} new viral videos found!"),
            topic="all_users"
        )
        messaging.send(message)
    except Exception as e: print(f"⚠️ Error: {e}")

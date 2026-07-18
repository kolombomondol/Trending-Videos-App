import json
import os
from datetime import datetime, timezone, timedelta
from googleapiclient.discovery import build
import firebase_admin
from firebase_admin import credentials, messaging

# গিটহাব সিক্রেট (Environment Variables) থেকে ৫টি এপিআই কি লোড করা হচ্ছে
API_KEYS = [
    os.environ.get("API_KEY_1"),
    os.environ.get("API_KEY_2"),
    os.environ.get("API_KEY_3"),
    os.environ.get("API_KEY_4"),
    os.environ.get("API_KEY_5")
]

API_KEYS = [key for key in API_KEYS if key]

if not API_KEYS:
    raise ValueError("❌ Error: No API Keys found in Environment Variables! Please check GitHub Secrets.")

# ১০৪টি দেশের কোড লিস্ট
region_codes = [
    "US", "BD", "IN", "GB", "SA", "AE", "PK", "CA", "AU", "DE", "FR", "JP", "KR",
    "ID", "NG", "MY", "SG", "TR", "IT", "ES", "DZ", "AR", "AT", "AZ", "BH", "BY",
    "BE", "BO", "BA", "BR", "BG", "CL", "CO", "CR", "HR", "CY", "CZ", "DK", "DO",
    "EC", "EG", "SV", "EE", "FI", "GE", "GH", "GR", "GT", "HN", "HK", "HU", "IS",
    "IQ", "IE", "IL", "JM", "JO", "KZ", "KE", "KW", "LV", "LB", "LY", "LI", "LT",
    "LU", "MK", "MT", "MX", "ME", "MA", "NP", "NL", "NZ", "NI", "NO", "OM", "PA",
    "PG", "PY", "PE", "PH", "PL", "PT", "QA", "RO", "RU", "SN", "RS", "SK", "SI",
    "ZA", "LK", "SE", "CH", "TW", "TZ", "TH", "TN", "UG", "UA", "UY", "VE", "VN",
    "YE", "ZW"
]

# অ্যান্ড্রয়েড অ্যাপের ৫টি ক্যাটাগরি
category_map = {
    "comedy": "23",
    "song": "10",
    "news": "25",
    "sports": "17",
    "vlog": "22"
}

VIDEOS_FILE = "videos.json"          # প্রতি রানে পুরো ফ্রেশ স্ন্যাপশট (ওভাররাইট হয়)
NEW_VIDEOS_FILE = "new_videos.json"  # শুধু এই রানের নতুন ভিডিওগুলো (ওভাররাইট হয়, জমে থাকে না)
SEEN_IDS_FILE = "seen_ids.json"      # "কোন আইডি কখন প্রথম দেখা হয়েছিল" -- পুরনো হলে নিজে থেকে মুছে যায়

RETENTION_DAYS = 3  # এর চেয়ে পুরনো seen আইডি বাদ দেওয়া হবে (ফাইল যেন চিরকাল না বাড়ে)

final_data = {}
new_only_data = {}
total_videos_fetched = 0
total_new_videos = 0

now = datetime.now(timezone.utc)

# ---------- আগের seen_ids লোড + পুরনোগুলো ছেঁটে ফেলা ----------
seen_ids = {}  # video_id -> ISO timestamp যখন প্রথম দেখা হয়েছিল
if os.path.exists(SEEN_IDS_FILE):
    try:
        with open(SEEN_IDS_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
        cutoff = now - timedelta(days=RETENTION_DAYS)
        for vid, ts in raw.items():
            try:
                if datetime.fromisoformat(ts) >= cutoff:
                    seen_ids[vid] = ts
            except Exception:
                pass  # নষ্ট টাইমস্ট্যাম্প থাকলে বাদ
        print(f"ℹ️ পূর্বে দেখা ভিডিও (এখনো বৈধ): {len(seen_ids)}টি (মোছা হয়েছে: {len(raw) - len(seen_ids)}টি পুরনো)")
    except Exception as e:
        print(f"⚠️ seen_ids.json পড়তে সমস্যা: {e}")
else:
    print("ℹ️ কোনো পুরনো seen_ids.json নেই, প্রথম রান ধরে নেওয়া হচ্ছে।")


def fetch_videos(youtube_client, region, cat_id):
    global total_videos_fetched, total_new_videos

    request = youtube_client.videos().list(
        part="snippet,statistics",
        chart="mostPopular",
        regionCode=region,
        videoCategoryId=cat_id,
        maxResults=25
    )
    response = request.execute()

    all_videos = []
    new_videos = []

    for item in response.get("items", []):
        snippet = item["snippet"]
        stats = item["statistics"]
        video_id = item["id"]

        video_obj = {
            "id": video_id,
            "title": snippet["title"],
            "channelTitle": snippet["channelTitle"],
            "thumbnailUrl": snippet["thumbnails"]["high"]["url"],
            "viewCount": stats.get("viewCount", "0"),
            "publishedAt": snippet["publishedAt"]
        }

        all_videos.append(video_obj)
        total_videos_fetched += 1

        if video_id not in seen_ids:
            new_videos.append(video_obj)
            total_new_videos += 1

        # প্রতি রানে টাইমস্ট্যাম্প রিফ্রেশ হবে -- তাই এখনো ট্রেন্ডিং থাকা ভিডিও কখনো এক্সপায়ার হবে না
        seen_ids[video_id] = now.isoformat()

    return all_videos, new_videos


# দেশগুলোকে ২০টি করে গ্রুপে ভাগ করে লুপ চালানো
for i, region in enumerate(region_codes):
    key_index = i // 20
    if key_index >= len(API_KEYS):
        key_index = len(API_KEYS) - 1

    current_key = API_KEYS[key_index]
    youtube = build("youtube", "v3", developerKey=current_key)

    print(f"Processing Country {i+1}/{len(region_codes)}: {region}")
    final_data[region] = {}
    new_only_data[region] = {}

    for cat_name, cat_id in category_map.items():
        try:
            all_vids, new_vids = fetch_videos(youtube, region, cat_id)
            final_data[region][cat_name] = all_vids
            if new_vids:
                new_only_data[region][cat_name] = new_vids
        except Exception as e:
            final_data[region][cat_name] = []
            print(f"⚠️ {region}/{cat_name} ফেচ করতে সমস্যা: {e}")

    if not new_only_data[region]:
        del new_only_data[region]

# ---------- মূল স্ন্যাপশট সেভ (প্রতি রানে সম্পূর্ণ প্রতিস্থাপিত হয়) ----------
with open(VIDEOS_FILE, "w", encoding="utf-8") as f:
    json.dump(final_data, f, indent=4, ensure_ascii=False)

# ---------- এই রানের নতুন ভিডিও -- আগের রানের new_videos.json সম্পূর্ণ প্রতিস্থাপিত হয় ----------
with open(NEW_VIDEOS_FILE, "w", encoding="utf-8") as f:
    json.dump(new_only_data, f, indent=4, ensure_ascii=False)

# ---------- seen_ids আপডেট (এক্সপায়ার্ড আইডি বাদ দিয়ে) ----------
with open(SEEN_IDS_FILE, "w", encoding="utf-8") as f:
    json.dump(seen_ids, f)

print(f"✅ videos.json generated. Total videos fetched: {total_videos_fetched}")
print(f"✨ new_videos.json generated. Total NEW videos this run: {total_new_videos}")

# 🔔 ফায়ারবেস পুশ নোটিফিকেশন (শুধু নতুন ভিডিও থাকলেই)
firebase_secret = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
if firebase_secret and total_new_videos > 0:
    try:
        cred_dict = json.loads(firebase_secret)
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)

        message = messaging.Message(
            notification=messaging.Notification(
                title="🔥 নতুন ভাইরাল ভিডিও অ্যালার্ট!",
                body=f"গত ৬ ঘণ্টায় বিশ্বজুড়ে নতুন ভাইরাল ভিডিও যুক্ত হয়েছে। এখনই অ্যাপ খুলে দেখুন!"
            ),
            topic="all_users"
        )

        response = messaging.send(message)
        print(f"🔔 Notification sent successfully! Message ID: {response}")
    except Exception as e:
        print(f"⚠️ Failed to send notification: {e}")
elif not firebase_secret:
    print("⚠️ Firebase secret not found. Skipping notification.")
else:
    print("ℹ️ কোনো নতুন ভিডিও পাওয়া যায়নি, তাই নোটিফিকেশন পাঠানো হয়নি।")

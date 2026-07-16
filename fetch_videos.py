import json
import os
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

# খালি বা নাল (None) কীগুলো ফিল্টার করে বাদ দেওয়া হচ্ছে
API_KEYS = [key for key in API_KEYS if key]

# যদি একটি কী-ও খুঁজে না পাওয়া যায় তবে স্ক্রিপ্ট বন্ধ হয়ে সতর্ক করবে
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
    "PG", "PY", "PE", "PH", "POL", "PT", "QA", "RO", "RU", "SN", "RS", "SK", "SI", 
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

final_data = {}
total_videos_fetched = 0  # মোট ভাইরাল ভিডিওর সংখ্যা গণনার জন্য

def fetch_videos(youtube_client, region, cat_id):
    global total_videos_fetched
    request = youtube_client.videos().list(
        part="snippet,statistics",
        chart="mostPopular",
        regionCode=region,
        videoCategoryId=cat_id,
        maxResults=25  # ২৫টি করে ভিডিও আসবে
    )
    response = request.execute()
    
    videos = []
    for item in response.get("items", []):
        snippet = item["snippet"]
        stats = item["statistics"]
        videos.append({
            "id": item["id"],
            "title": snippet["title"],
            "channelTitle": snippet["channelTitle"],
            "thumbnailUrl": snippet["thumbnails"]["high"]["url"],
            "viewCount": stats.get("viewCount", "0"),
            "publishedAt": snippet["publishedAt"]
        })
        total_videos_fetched += 1  # প্রতিটি সফল ভিডিওর জন্য ১ যোগ হবে
    return videos

# দেশগুলোকে ২০টি করে গ্রুপে ভাগ করে লুপ চালানো
for i, region in enumerate(region_codes):
    key_index = i // 20
    if key_index >= len(API_KEYS):
        key_index = len(API_KEYS) - 1
        
    current_key = API_KEYS[key_index]
    youtube = build("youtube", "v3", developerKey=current_key)
    
    print(f"Processing Country {i+1}/{len(region_codes)}: {region}")
    final_data[region] = {}
    
    for cat_name, cat_id in category_map.items():
        try:
            final_data[region][cat_name] = fetch_videos(youtube, region, cat_id)
        except Exception as e:
            final_data[region][cat_name] = []

# JSON ফাইলে ডেটা সেভ করা
with open("videos.json", "w", encoding="utf-8") as f:
    json.dump(final_data, f, indent=4, ensure_ascii=False)

print(f"✅ Videos.json generated. Total videos fetched: {total_videos_fetched}")

# 🔔 ফায়ারবেস পুশ নোটিফিকেশন পাঠানোর অংশ
firebase_secret = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
if firebase_secret:
    try:
        cred_dict = json.loads(firebase_secret)
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
        
        # নোটিফিকেশন মেসেজ কনফিগারেশন
        message = messaging.Message(
            notification=messaging.Notification(
                title="🔥 নতুন ভাইরাল ভিডিও অ্যালার্ট!",
                body=f"গত ৬ ঘণ্টায় বিশ্বজুড়ে মোট {total_videos_fetched}টি নতুন ভাইরাল ভিডিও যুক্ত হয়েছে। এখনই অ্যাপ খুলে দেখুন!"
            ),
            topic="all_users"  # সব ইউজার এই টপিকে সাবস্ক্রাইবড থাকবে
        )
        
        response = messaging.send(message)
        print(f"🔔 Notification sent successfully! Message ID: {response}")
    except Exception as e:
        print(f"⚠️ Failed to send notification: {e}")
else:
    print("⚠️ Firebase secret not found. Skipping notification.")

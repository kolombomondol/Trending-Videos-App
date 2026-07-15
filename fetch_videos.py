import json
import os
from googleapiclient.discovery import build

# আপনার ইউটিউব এপিআই কি (Google Cloud Console থেকে আনুন)
API_KEY = "AIzaSyCMupxt2iqOpClzlubti-6lpIKmFh2pZmY"
youtube = build("youtube", "v3", developerKey=API_KEY)

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

# ইউটিউব ক্যাটাগরি ম্যাপিং
# "all" এর জন্য কোনো আইডি লাগে না, শুধু chart="mostPopular"
category_map = {
    "all": None,
    "comedy": "23",
    "song": "10",
    "news": "25",
    "sports": "17",
    "vlog": "22"
}

final_data = {}

def fetch_videos(region, cat_id):
    request = youtube.videos().list(
        part="snippet,statistics",
        chart="mostPopular",
        regionCode=region,
        videoCategoryId=cat_id,
        maxResults=10
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
    return videos

# মূল লুপ
for region in region_codes:
    print(f"Processing: {region}...")
    final_data[region] = {}
    for cat_name, cat_id in category_map.items():
        try:
            final_data[region][cat_name] = fetch_videos(region, cat_id)
        except Exception as e:
            print(f"Error fetching {cat_name} for {region}: {e}")
            final_data[region][cat_name] = []

# JSON ফাইলে সেভ করা
with open("videos.json", "w", encoding="utf-8") as f:
    json.dump(final_data, f, indent=4, ensure_ascii=False)

print("videos.json generated successfully!")

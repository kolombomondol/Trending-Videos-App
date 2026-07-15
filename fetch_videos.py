import json
import os
from googleapiclient.discovery import build

# আপনার ৫টি ভিন্ন ভিন্ন এপিআই কি এখানে বসান
API_KEYS = [
    "AIzaSyCMupxt2iqOpClzlubti-6lpIKmFh2pZmY", 
 # ১ম ২০টি দেশের জন্য
    "AIzaSyCL-wjhJ8a105xQmTZdsgQ4VQxn9RWKUR0",  
# ২য় ২০টি দেশের জন্য
    "AIzaSyDa83kAFLcf-pwvzsaBDmiFPN34GHMQv7w", 
 # ৩য় ২০টি দেশের জন্য
    "AIzaSyCESGAh7Ya5s8CHd6XmZZ__LCT1g2fIw50",  
# ৪থ ২০টি দেশের জন্য
    "AIzaSyBD6fv3hSW61zgAa_yWINRLRQn5BrsLVO4"   
# বাকি ২৪টি দেশের জন্য
]

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

# অল বাদে ৫টি ক্যাটাগরি
category_map = {
    "comedy": "23",
    "song": "10",
    "news": "25",
    "sports": "17",
    "vlog": "22"
}

final_data = {}

def fetch_videos(youtube_client, region, cat_id):
    request = youtube_client.videos().list(
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

# দেশগুলোকে ২০টি করে গ্রুপে ভাগ করে লুপ চালানো
for i, region in enumerate(region_codes):
    # ইনডেক্স অনুযায়ী কোন API Key ব্যবহার হবে তা নির্ধারণ (প্রতি ২০টি দেশের জন্য ১টি করে চাবি পরিবর্তন)
    key_index = i // 20
    
    # যদি ১০৪টি দেশের কারণে ভাগফল ৫ বা তার বেশি হয়, তবে শেষ চাবিটি (Index 4) ব্যবহার হবে
    if key_index >= len(API_KEYS):
        key_index = len(API_KEYS) - 1
        
    current_key = API_KEYS[key_index]
    
    # বর্তমান চাবি দিয়ে ইউটিউব ক্লায়েন্ট তৈরি
    youtube = build("youtube", "v3", developerKey=current_key)
    
    print(f"Processing Country {i+1}: {region} using API Key Index: {key_index}")
    final_data[region] = {}
    
    for cat_name, cat_id in category_map.items():
        try:
            final_data[region][cat_name] = fetch_videos(youtube, region, cat_id)
        except Exception as e:
            print(f"⚠️ Error fetching {cat_name} for {region} using Key Index {key_index}: {e}")
            final_data[region][cat_name] = []

# JSON ফাইলে সেভ করা
with open("videos.json", "w", encoding="utf-8") as f:
    json.dump(final_data, f, indent=4, ensure_ascii=False)

print("✅ Static partitioned videos.json generated successfully!")

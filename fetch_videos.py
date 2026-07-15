import os
import json
import urllib.request
import urllib.parse

# ২০টি দেশ এবং তাদের ক্যাটাগরি ম্যাপিং
countries = {
    "US": "United States", "BD": "Bangladesh", "IN": "India", "GB": "United Kingdom", 
    "SA": "Saudi Arabia", "AE": "UAE", "PK": "Pakistan", "CA": "Canada", 
    "AU": "Australia", "DE": "Germany", "FR": "France", "JP": "Japan", 
    "KR": "South Korea", "ID": "Indonesia", "NG": "Nigeria", "MY": "Malaysia", 
    "SG": "Singapore", "TR": "Turkey", "IT": "Italy", "ES": "Spain"
}

# ক্যাটাগরি আইডি (সব দেশেই এগুলো সাধারণত সেম থাকে)
# "" = All, "23" = Comedy, "10" = Music, "25" = News, "17" = Sports, "22" = Vlog
categories = {
    "all": "",
    "comedy": "23",
    "music": "10",
    "news": "25",
    "sports": "17",
    "vlog": "22"
}

# GitHub Secrets থেকে API Key রিড করা হবে
API_KEY = os.environ.get("YOUTUBE_API_KEY")

def fetch_videos_for_country_and_category(region_code, category_id, limit=30):
    """একটি নির্দিষ্ট দেশ এবং ক্যাটাগরির জন্য ভিডিও ফেচ করে"""
    category_param = f"&videoCategoryId={category_id}" if category_id else ""
    url = (
        f"https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics&chart=mostPopular"
        f"&regionCode={region_code}{category_param}&maxResults={limit}&key={API_KEY}"
    )
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            video_list = []
            for item in data.get("items", []):
                snippet = item.get("snippet", {})
                stats = item.get("statistics", {})
                
                video_list.append({
                    "id": item.get("id", ""),
                    "title": snippet.get("title", "No Title"),
                    "channelTitle": snippet.get("channelTitle", "Unknown"),
                    "thumbnailUrl": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
                    "viewCount": stats.get("viewCount", "0"),
                    "publishedAt": snippet.get("publishedAt", "")
                })
            return video_list
    except Exception as e:
        print(f"Error fetching data for {region_code} (Category: {category_id}): {e}")
        return []

def main():
    if not API_KEY:
        print("API Key not found in Environment Variables!")
        return

    # ফাইনাল স্ট্রাকচার: {"US": {"all": [...], "music": [...]}, "BD": {...}}
    final_data = {}

    for region_code in countries.keys():
        print(f"Fetching videos for {region_code}...")
        final_data[region_code] = {}
        
        for cat_name, cat_id in categories.items():
            # All ক্যাটাগরির জন্য আমরা ৫০টি নিচ্ছি, বাকিগুলোর জন্য ২৫টি করে নিচ্ছি
            limit = 50 if cat_name == "all" else 25
            videos = fetch_videos_for_country_and_category(region_code, cat_id, limit)
            final_data[region_code][cat_name] = videos

    # videos.json ফাইলে রাইট করা
    with open("videos.json", "w", encoding="utf-8") as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
    print("videos.json file successfully updated!")

if __name__ == "__main__":
    main()

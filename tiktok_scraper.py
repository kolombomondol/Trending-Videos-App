import json
import os
from datetime import datetime, timezone

import yt_dlp

TIKTOK_VIDEOS_FILE = "tiktok_videos.json"
TIKTOK_SEEN_IDS_FILE = "tiktok_seen_ids.json"

now = datetime.now(timezone.utc)

# ১. আগের জমানো ভিডিও আইডি লোড
seen_ids = {}
if os.path.exists(TIKTOK_SEEN_IDS_FILE):
    try:
        with open(TIKTOK_SEEN_IDS_FILE, "r", encoding="utf-8") as f:
            seen_ids = json.load(f)
    except Exception as e:
        print(f"⚠️ Error loading seen IDs: {e}")

# 🌍 দেশের তালিকা (Android অ্যাপের spinner-এর সাথে মিলিয়ে)
COUNTRIES = {
    "BD": "Bangladesh", "IN": "India", "PK": "Pakistan", "NP": "Nepal", "LK": "Sri Lanka",
    "ID": "Indonesia", "JP": "Japan", "KR": "South Korea", "PH": "Philippines", "VN": "Vietnam",
    "TH": "Thailand", "MY": "Malaysia", "SG": "Singapore", "SA": "Saudi Arabia",
    "AE": "United Arab Emirates", "QA": "Qatar", "KW": "Kuwait", "TR": "Turkey",
    "US": "United States", "CA": "Canada", "MX": "Mexico", "BR": "Brazil",
    "GB": "United Kingdom", "DE": "Germany", "FR": "France", "IT": "Italy", "ES": "Spain",
    "NL": "Netherlands", "AU": "Australia", "EG": "Egypt", "ZA": "South Africa", "NG": "Nigeria",
}

# 🔥 ভাইরাল/ট্রেন্ডিং হ্যাশট্যাগ — TikTok-এর পার্সোনালাইজড ফিড লগইন ছাড়া পাওয়া যায় না,
# তাই জনপ্রিয় হ্যাশট্যাগ পেজ থেকে ভিডিও নেওয়া হচ্ছে (এটাই সবচেয়ে কাছের বাস্তবসম্মত বিকল্প)
VIRAL_HASHTAGS = ["fyp", "viral", "foryou", "trending", "viralvideo"]

MAX_PER_HASHTAG = 40

YDL_OPTS = {
    "quiet": True,
    "no_warnings": True,
    "extract_flat": True,   # প্রতিটা ভিডিও আলাদাভাবে না খুলে দ্রুত লিস্ট বের করা
    "skip_download": True,
    "playlistend": MAX_PER_HASHTAG,
    "socket_timeout": 15,
}


def fetch_hashtag_videos(hashtag: str):
    """yt-dlp দিয়ে সরাসরি TikTok হ্যাশট্যাগ পেজ থেকে ভিডিও লিস্ট বের করে।"""
    url = f"https://www.tiktok.com/tag/{hashtag}"
    results = []

    try:
        with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
            info = ydl.extract_info(url, download=False)
            entries = info.get("entries", []) if info else []

            for entry in entries:
                if not entry:
                    continue

                video_id = str(entry.get("id", ""))
                webpage_url = entry.get("url") or entry.get("webpage_url", "")
                if not video_id or not webpage_url:
                    continue

                results.append({
                    "video_id": video_id,
                    "webpage_url": webpage_url,
                    "title": entry.get("title") or "",
                    "author": entry.get("uploader") or entry.get("uploader_id") or "",
                    "thumbnail": entry.get("thumbnail") or "",
                    "view_count": entry.get("view_count") or 0,
                })
    except Exception as e:
        print(f"  ⏩ Hashtag #{hashtag} failed: {e}")

    return results


def get_direct_play_url(webpage_url: str):
    """
    হ্যাশট্যাগ লিস্টিং থেকে সরাসরি .mp4 লিংক পাওয়া যায় না (extract_flat=True দ্রুত হওয়ার জন্য),
    তাই প্রতিটা ভিডিওর আসল প্লে-লিংক বের করতে এই ফাংশনটা আলাদাভাবে খুলে চেক করে।
    """
    opts = {"quiet": True, "no_warnings": True, "skip_download": True, "socket_timeout": 15}
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(webpage_url, download=False)
            return info.get("url", "")
    except Exception:
        return ""


def fetch_worldwide_viral_videos():
    print(f"🚀 Fetching Viral Videos for {len(COUNTRIES)} Countries via yt-dlp...")

    # প্রথমে সব হ্যাশট্যাগ থেকে একটা কমন ভাইরাল পুল বানানো হচ্ছে
    viral_pool = []
    seen_pool_ids = set()

    for tag in VIRAL_HASHTAGS:
        print(f"🔎 Fetching hashtag #{tag}...")
        videos = fetch_hashtag_videos(tag)
        print(f"   → {len(videos)} videos found")
        for v in videos:
            if v["video_id"] not in seen_pool_ids:
                seen_pool_ids.add(v["video_id"])
                viral_pool.append(v)

    print(f"📦 Total unique viral pool: {len(viral_pool)} videos")
    print("🎬 Resolving direct play URLs (this takes a while)...")

    resolved_videos = []
    new_videos_count = 0

    for i, v in enumerate(viral_pool):
        play_url = get_direct_play_url(v["webpage_url"])
        if not play_url:
            continue

        video_id = v["video_id"]

        if video_id not in seen_ids:
            first_seen = now.isoformat()
            seen_ids[video_id] = {"firstSeenAt": first_seen}
            new_videos_count += 1
        else:
            first_seen = seen_ids[video_id].get("firstSeenAt", now.isoformat())

        resolved_videos.append({
            "id": video_id,
            "title": v["title"] or "Viral TikTok Video",
            "author": v["author"] or "TikTok Creator",
            "playUrl": play_url,
            "thumbnailUrl": v["thumbnail"],
            "viewCount": str(v["view_count"]),
            "publishedAt": now.isoformat(),
            "firstSeenAt": first_seen,
        })

        if (i + 1) % 10 == 0:
            print(f"   ...resolved {i + 1}/{len(viral_pool)}")

    print(f"✅ Resolved {len(resolved_videos)} playable videos")

    # 🌍 প্রতিটা দেশের জন্য একই ভাইরাল পুল থেকে ভিডিও দেওয়া হচ্ছে
    # (TikTok হ্যাশট্যাগ পেজ দেশ দিয়ে ফিল্টার করা যায় না — এটা একটা সীমাবদ্ধতা)
    country_videos_map = {}
    for code, name in COUNTRIES.items():
        country_specific = []
        for v in resolved_videos:
            v_copy = dict(v)
            v_copy["country"] = name
            v_copy["countryCode"] = code
            country_specific.append(v_copy)
        country_videos_map[code] = country_specific

    country_videos_map["GLOBAL"] = resolved_videos[:600]

    return country_videos_map, new_videos_count


tiktok_data, new_count = fetch_worldwide_viral_videos()

with open(TIKTOK_VIDEOS_FILE, "w", encoding="utf-8") as f:
    json.dump({"tiktok_by_country": tiktok_data}, f, indent=4, ensure_ascii=False)

with open(TIKTOK_SEEN_IDS_FILE, "w", encoding="utf-8") as f:
    json.dump(seen_ids, f, indent=4)

print(f"🎉 Successfully Generated Viral TikTok Videos ({new_count} new)!")

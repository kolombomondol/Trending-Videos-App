import json
import os
import time
import requests
from datetime import datetime, timezone

TIKTOK_VIDEOS_FILE = "tiktok_videos.json"
TIKTOK_SEEN_IDS_FILE = "tiktok_seen_ids.json"

now = datetime.now(timezone.utc)
RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY", "")

# 🎯 অন্তত ২ মিলিয়ন (২০ লাখ) লাইক
MIN_LIKES = 2_000_000

seen_ids = {}
if os.path.exists(TIKTOK_SEEN_IDS_FILE):
    try:
        with open(TIKTOK_SEEN_IDS_FILE, "r", encoding="utf-8") as f:
            seen_ids = json.load(f)
    except Exception as e:
        print(f"⚠️ Error loading seen IDs: {e}")

COUNTRIES = {
    "BD": "Bangladesh", "IN": "India", "PK": "Pakistan", "NP": "Nepal", "LK": "Sri Lanka",
    "MV": "Maldives", "BT": "Bhutan", "ID": "Indonesia", "JP": "Japan", "KR": "South Korea",
    "PH": "Philippines", "VN": "Vietnam", "TH": "Thailand", "MY": "Malaysia", "SG": "Singapore",
    "MM": "Myanmar", "KH": "Cambodia", "LA": "Laos", "BN": "Brunei", "MN": "Mongolia",
    "SA": "Saudi Arabia", "AE": "United Arab Emirates", "QA": "Qatar", "KW": "Kuwait",
    "OM": "Oman", "BH": "Bahrain", "TR": "Turkey", "IQ": "Iraq", "JO": "Jordan",
    "LB": "Lebanon", "IL": "Israel", "YE": "Yemen", "KZ": "Kazakhstan", "UZ": "Uzbekistan",
    "KG": "Kyrgyzstan", "TJ": "Tajikistan", "TM": "Turkmenistan", "AF": "Afghanistan",
    "US": "United States", "CA": "Canada", "MX": "Mexico", "BR": "Brazil", "AR": "Argentina",
    "CL": "Chile", "CO": "Colombia", "PE": "Peru", "VE": "Venezuela", "EC": "Ecuador",
    "BO": "Bolivia", "PY": "Paraguay", "UY": "Uruguay", "CR": "Costa Rica", "PA": "Panama",
    "GT": "Guatemala", "HN": "Honduras", "SV": "El Salvador", "NI": "Nicaragua", "DO": "Dominican Republic",
    "JM": "Jamaica", "TT": "Trinidad and Tobago", "CUB": "Cuba", "HT": "Haiti",
    "GB": "United Kingdom", "DE": "Germany", "FR": "France", "IT": "Italy", "ES": "Spain",
    "NL": "Netherlands", "PL": "Poland", "SE": "Sweden", "NO": "Norway", "FI": "Finland",
    "DK": "Denmark", "CH": "Switzerland", "AT": "Austria", "BE": "Belgium", "PT": "Portugal",
    "GR": "Greece", "IE": "Ireland", "RO": "Romania", "HU": "Hungary", "CZ": "Czech Republic",
    "SK": "Slovakia", "BG": "Bulgaria", "HR": "Croatia", "RS": "Serbia", "UA": "Ukraine",
    "RU": "Russia", "BY": "Belarus", "LT": "Lithuania", "LV": "Latvia", "EE": "Estonia",
    "IS": "Iceland", "AL": "Albania", "MK": "North Macedonia", "CY": "Cyprus", "LU": "Luxembourg",
    "EG": "Egypt", "ZA": "South Africa", "NG": "Nigeria", "KE": "Kenya", "MA": "Morocco",
    "DZ": "Algeria", "TN": "Tunisia", "GH": "Ghana", "ET": "Ethiopia", "TZ": "Tanzania",
    "UG": "Uganda", "CM": "Cameroon", "CIV": "Ivory Coast", "SN": "Senegal", "ZW": "Zimbabwe",
    "AO": "Angola", "MZ": "Mozambique", "SD": "Sudan", "LY": "Libya", "MAD": "Madagascar",
    "AU": "Australia", "NZ": "New Zealand", "FJ": "Fiji", "PG": "Papua New Guinea"
}

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def normalize_video(item, country_name, country_code, source):
    video_id = str(item.get("video_id") or item.get("id") or "")
    if not video_id:
        return None

    play_url = item.get("play") or item.get("wmplay") or item.get("playUrl") or ""
    if play_url and not play_url.startswith("http"):
        play_url = f"https://www.tikwm.com{play_url}"

    thumbnail_url = item.get("cover") or item.get("thumbnailUrl") or ""
    if thumbnail_url and not thumbnail_url.startswith("http"):
        thumbnail_url = f"https://www.tikwm.com{thumbnail_url}"

    author_field = item.get("author", {})
    if isinstance(author_field, dict):
        author_name = author_field.get("nickname", "TikTok Creator")
    else:
        author_name = str(author_field or item.get("author", "TikTok Creator"))

    like_count = item.get("digg_count", item.get("likeCount", 0))
    try:
        like_count = int(like_count)
    except (TypeError, ValueError):
        like_count = 0

    if video_id not in seen_ids:
        first_seen = now.isoformat()
        seen_ids[video_id] = {"firstSeenAt": first_seen}
    else:
        first_seen = seen_ids[video_id].get("firstSeenAt", now.isoformat())

    return {
        "id": video_id,
        "title": item.get("title", f"Viral TikTok Video - {country_name}"),
        "author": author_name,
        "playUrl": play_url,
        "thumbnailUrl": thumbnail_url,
        "viewCount": str(item.get("play_count", item.get("viewCount", 0))),
        "likeCount": like_count,
        "country": country_name,
        "countryCode": country_code,
        "publishedAt": now.isoformat(),
        "firstSeenAt": first_seen,
        "source": source,
    }

def fetch_from_tikwm(country_code, country_name, max_retries=3):
    url = "https://www.tikwm.com/api/feed/list"
    params = {"region": country_code, "count": 30}
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            timeout = 8 + (attempt * 3)
            response = requests.get(url, params=params, headers=HEADERS, timeout=timeout)
            response.raise_for_status()
            data = response.json()
            items = data.get("data", []) or []

            if not items:
                last_error = "empty response"
                if attempt < max_retries:
                    time.sleep(1)
                continue

            videos = []
            added_ids = set()
            for item in items:
                video = normalize_video(item, country_name, country_code, source="tikwm")
                if not video or video["id"] in added_ids:
                    continue
                if video["likeCount"] < MIN_LIKES:
                    continue
                added_ids.add(video["id"])
                videos.append(video)

            return videos
        except Exception as e:
            last_error = e
            if attempt < max_retries:
                time.sleep(1)
            continue
    raise Exception(f"Failed after {max_retries} attempts: {last_error}")

def fetch_from_rapidapi(country_code, country_name):
    if not RAPIDAPI_KEY:
        return []
    url = "https://tiktok-scraper7.p.rapidapi.com/feed/list"
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "tiktok-scraper7.p.rapidapi.com",
    }
    params = {"region": country_code, "count": "30"}
    response = requests.get(url, headers=headers, params=params, timeout=8)
    response.raise_for_status()
    data = response.json()
    items = data.get("data", {}).get("videos", []) if isinstance(data.get("data"), dict) else data.get("data", [])

    videos = []
    added_ids = set()
    for item in items or []:
        video = normalize_video(item, country_name, country_code, source="rapidapi")
        if not video or video["id"] in added_ids:
            continue
        if video["likeCount"] < MIN_LIKES:
            continue
        added_ids.add(video["id"])
        videos.append(video)

    return videos

def fetch_country_videos(country_code, country_name):
    try:
        videos = fetch_from_tikwm(country_code, country_name)
        if videos:
            return videos, "tikwm"
    except Exception as e:
        pass

    try:
        videos = fetch_from_rapidapi(country_code, country_name)
        if videos:
            return videos, "rapidapi"
    except Exception as e:
        pass

    return [], None

def fetch_worldwide_viral_videos():
    print(f"🚀 Fetching Viral Videos (2M+ likes) for {len(COUNTRIES)} Countries...")
    country_videos_map = {}
    country_video_queues = {}
    added_global_ids = set()

    for code, country_name in COUNTRIES.items():
        print(f"🌍 Fetching: {country_name} ({code})...")
        videos, used_source = fetch_country_videos(code, country_name)

        if videos:
            country_videos_map[code] = videos
            country_video_queues[code] = list(videos)
            print(f"✅ Saved {len(videos)} videos for {country_name}")
        else:
            print(f"❌ 0 videos found for {country_name}")
        time.sleep(0.3)

    # 🌐 GLOBAL মিক্সড লজিক: প্রতি দেশ থেকে পরপর ২টি করে নেওয়া হচ্ছে
    all_global_videos = []
    has_more = True
    while has_more:
        has_more = False
        for code in COUNTRIES.keys():
            queue = country_video_queues.get(code, [])
            # প্রতি দেশ থেকে ২ টি করে ভিডিও নিয়ে GLOBAL লিস্টে যোগ হবে
            take_count = min(2, len(queue))
            if take_count > 0:
                has_more = True
                for _ in range(take_count):
                    v = queue.pop(0)
                    if v["id"] not in added_global_ids:
                        added_global_ids.add(v["id"])
                        all_global_videos.append(v)

    country_videos_map["GLOBAL"] = all_global_videos[:800]
    return country_videos_map, len(added_global_ids)

tiktok_data, total_count = fetch_worldwide_viral_videos()

with open(TIKTOK_VIDEOS_FILE, "w", encoding="utf-8") as f:
    json.dump({"tiktok_by_country": tiktok_data}, f, indent=4, ensure_ascii=False)

with open(TIKTOK_SEEN_IDS_FILE, "w", encoding="utf-8") as f:
    json.dump(seen_ids, f, indent=4)

print(f"\n🎉 Generated {total_count} unique videos interleaved 2 per country!")

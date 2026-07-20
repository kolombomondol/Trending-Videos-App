import json
import os
import requests
from datetime import datetime, timezone

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

def fetch_worldwide_viral_videos():
    url = "https://www.tikwm.com/api/feed/list"
    
    # 🌍 ১১০+ দেশের তালিকা (Country Codes & Names)
    countries = {
        # South Asia & East Asia
        "BD": "Bangladesh", "IN": "India", "PK": "Pakistan", "NP": "Nepal", "LK": "Sri Lanka",
        "MV": "Maldives", "BT": "Bhutan", "ID": "Indonesia", "JP": "Japan", "KR": "South Korea",
        "PH": "Philippines", "VN": "Vietnam", "TH": "Thailand", "MY": "Malaysia", "SG": "Singapore",
        "MM": "Myanmar", "KH": "Cambodia", "LA": "Laos", "BN": "Brunei", "MN": "Mongolia",
        
        # Middle East & Central Asia
        "SA": "Saudi Arabia", "AE": "United Arab Emirates", "QA": "Qatar", "KW": "Kuwait",
        "OM": "Oman", "BH": "Bahrain", "TR": "Turkey", "IQ": "Iraq", "JO": "Jordan",
        "LB": "Lebanon", "IL": "Israel", "YE": "Yemen", "KZ": "Kazakhstan", "UZ": "Uzbekistan",
        "KG": "Kyrgyzstan", "TJ": "Tajikistan", "TM": "Turkmenistan", "AF": "Afghanistan",
        
        # Americas
        "US": "United States", "CA": "Canada", "MX": "Mexico", "BR": "Brazil", "AR": "Argentina",
        "CL": "Chile", "CO": "Colombia", "PE": "Peru", "VE": "Venezuela", "EC": "Ecuador",
        "BO": "Bolivia", "PY": "Paraguay", "UY": "Uruguay", "CR": "Costa Rica", "PA": "Panama",
        "GT": "Guatemala", "HN": "Honduras", "SV": "El Salvador", "NI": "Nicaragua", "DO": "Dominican Republic",
        "JM": "Jamaica", "TT": "Trinidad and Tobago", "CUB": "Cuba", "HT": "Haiti",
        
        # Europe
        "GB": "United Kingdom", "DE": "Germany", "FR": "France", "IT": "Italy", "ES": "Spain",
        "NL": "Netherlands", "PL": "Poland", "SE": "Sweden", "NO": "Norway", "FI": "Finland",
        "DK": "Denmark", "CH": "Switzerland", "AT": "Austria", "BE": "Belgium", "PT": "Portugal",
        "GR": "Greece", "IE": "Ireland", "RO": "Romania", "HU": "Hungary", "CZ": "Czech Republic",
        "SK": "Slovakia", "BG": "Bulgaria", "HR": "Croatia", "RS": "Serbia", "UA": "Ukraine",
        "RU": "Russia", "BY": "Belarus", "LT": "Lithuania", "LV": "Latvia", "EE": "Estonia",
        "IS": "Iceland", "AL": "Albania", "MK": "North Macedonia", "CY": "Cyprus", "LU": "Luxembourg",
        
        # Africa
        "EG": "Egypt", "ZA": "South Africa", "NG": "Nigeria", "KE": "Kenya", "MA": "Morocco",
        "DZ": "Algeria", "TN": "Tunisia", "GH": "Ghana", "ET": "Ethiopia", "TZ": "Tanzania",
        "UG": "Uganda", "CM": "Cameroon", "CIV": "Ivory Coast", "SN": "Senegal", "ZW": "Zimbabwe",
        "AO": "Angola", "MZ": "Mozambique", "SD": "Sudan", "LY": "Libya", "MAD": "Madagascar",
        
        # Oceania
        "AU": "Australia", "NZ": "New Zealand", "FJ": "Fiji", "PG": "Papua New Guinea"
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
    }

    country_videos_map = {}
    new_videos_count = 0
    all_global_videos = []
    added_global_ids = set()

    print(f"🚀 Fetching Viral Videos for {len(countries)} Countries...")

    for code, country_name in countries.items():
        print(f"🌍 Fetching videos for: {country_name} ({code})...")
        raw_country_videos = []
        added_ids = set()
        cursor = 0

        for attempt in range(3):
            if len(raw_country_videos) >= 50:
                break

            params = {
                "region": code,
                "count": 30,
                "cursor": cursor
            }

            try:
                response = requests.get(url, params=params, headers=headers, timeout=5)
                if response.status_code != 200:
                    continue

                data = response.json()
                items = data.get("data", {}).get("videos", []) or data.get("data", []) or []

                if not items:
                    break

                for item in items:
                    if len(raw_country_videos) >= 50:
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

                    # 🚀 ফাস্ট ও এইচডি প্লে ইউআরএল চয়েস
                    play_url = item.get("hdplay") or item.get("play") or item.get("wmplay") or ""
                    if play_url and not play_url.startswith("http"):
                        play_url = f"https://www.tikwm.com{play_url}"

                    thumbnail_url = item.get("cover") or ""
                    if thumbnail_url and not thumbnail_url.startswith("http"):
                        thumbnail_url = f"https://www.tikwm.com{thumbnail_url}"

                    view_count_val = int(item.get("play_count", 0))

                    video_obj = {
                        "id": video_id,
                        "title": item.get("title", f"Viral TikTok Video - {country_name}"),
                        "author": item.get("author", {}).get("nickname", "TikTok Creator"),
                        "playUrl": play_url,
                        "thumbnailUrl": thumbnail_url,
                        "viewCount": str(view_count_val),
                        "country": country_name,
                        "countryCode": code,
                        "publishedAt": now.isoformat(),
                        "firstSeenAt": first_seen
                    }
                    raw_country_videos.append(video_obj)

                cursor = data.get("data", {}).get("cursor", cursor + 30) if isinstance(data.get("data"), dict) else cursor + 30

            except Exception as e:
                print(f"⏩ Skipped request for {country_name} (Attempt {attempt+1}) due to timeout/error")

        # 🚀 ফিল্টারিং: ১ মিলিয়ন+ (১০,০০,০০০) ভিউ ফিল্টার
        filtered_videos = [v for v in raw_country_videos if int(v.get("viewCount", 0)) >= 1000000]

        if filtered_videos:
            # ভিউ সংখ্যা অনুযায়ী ক্রমানুসারে (বড় থেকে ছোট) সাজানো
            filtered_videos.sort(key=lambda x: int(x.get("viewCount", 0)), reverse=True)
            country_videos_map[code] = filtered_videos
            print(f"✅ Saved {len(filtered_videos)} viral videos (1M+ views) for {country_name}")
            
            for v in filtered_videos:
                if v["id"] not in added_global_ids:
                    added_global_ids.add(v["id"])
                    all_global_videos.append(v)
        else:
            # যদি ১ মিলিয়নের ওপর ভিডিও না থাকে, তবে সর্বোচ্চ ভিউ হওয়া সেরা ভিডিওগুলো রাখবে (Fallback)
            raw_country_videos.sort(key=lambda x: int(x.get("viewCount", 0)), reverse=True)
            country_videos_map[code] = raw_country_videos[:15]
            print(f"⚠️ No 1M+ videos found for {country_name}, saved top viewed ones.")
            
            for v in raw_country_videos[:15]:
                if v["id"] not in added_global_ids:
                    added_global_ids.add(v["id"])
                    all_global_videos.append(v)

    # 🌐 Global (All Countries) অপশন
    all_global_videos.sort(key=lambda x: int(x.get("viewCount", 0)), reverse=True)
    country_videos_map["GLOBAL"] = all_global_videos[:600]

    return country_videos_map, new_videos_count

tiktok_data, new_count = fetch_worldwide_viral_videos()

# JSON ফাইল সেভ
with open(TIKTOK_VIDEOS_FILE, "w", encoding="utf-8") as f:
    json.dump({"tiktok_by_country": tiktok_data}, f, indent=4, ensure_ascii=False)

with open(TIKTOK_SEEN_IDS_FILE, "w", encoding="utf-8") as f:
    json.dump(seen_ids, f, indent=4)

print(f"🎉 Successfully Generated Viral TikTok Videos ({new_count} new)!")

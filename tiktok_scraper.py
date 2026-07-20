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
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    country_videos_map = {}
    new_videos_count = 0
    all_global_videos = []
    added_global_ids = set()

    print(f"🚀 Fetching Viral Videos for {len(countries)} Countries...")

    for code, country_name in countries.items():
        print(f"🌍 Fetching 50 videos for: {country_name} ({code})...")
        country_videos = []
        added_ids = set()

        for page in range(1, 3):  # গতি বজায় রাখার জন্য ২ পেইজ রান করবে
            if len(country_videos) >= 50:
                break

            params = {
                "region": code,
                "count": 30
            }

            try:
                # রেসপন্স ফাস্ট রাখার জন্য ৫ সেকেন্ডের টাইমআউট
                response = requests.get(url, params=params, headers=headers, timeout=5)
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

                    if video_id not in added_global_ids:
                        added_global_ids.add(video_id)
                        all_global_videos.append(video_obj)

            except Exception as e:
                print(f"⏩ Skipped {country_name} due to timeout/error")

        if country_videos:
            country_videos_map[code] = country_videos
            print(f"✅ Saved {len(country_videos)} videos for {country_name}")

    # 🌐 Global (All Countries) অপশন (বিশ্বের নানা দেশের মিক্সড ১০০টি ভিডিও)
    country_videos_map["GLOBAL"] = all_global_videos[:600]

    return country_videos_map, new_videos_count

tiktok_data, new_count = fetch_worldwide_viral_videos()

# JSON ফাইল সেভ
with open(TIKTOK_VIDEOS_FILE, "w", encoding="utf-8") as f:
    json.dump({"tiktok_by_country": tiktok_data}, f, indent=4, ensure_ascii=False)

with open(TIKTOK_SEEN_IDS_FILE, "w", encoding="utf-8") as f:
    json.dump(seen_ids, f, indent=4)

print(f"🎉 Successfully Generated 110+ Countries Viral TikTok Videos ({new_count} new)!")

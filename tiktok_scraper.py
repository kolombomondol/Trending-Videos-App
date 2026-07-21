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

    countries = {
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

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    country_videos_map = {}
    new_videos_count = 0
    all_global_videos = []
    added_global_ids = set()

    print(f"🚀 Fetching Viral Videos for {len(countries)} Countries...")

    for code, country_name in countries.items():
        print(f"🌍 Fetching videos for: {country_name} ({code})...")
        country_videos = []
        added_ids = set()

        params = {
            "region": code,
            "count": 30
        }

        try:
            response = requests.get(url, params=params, headers=headers, timeout=6)
            if response.status_code != 200:
                print(f"  ⚠️ Status {response.status_code} for {country_name}, skipping")
                continue

            data = response.json()
            items = data.get("data", []) or []

            for item in items:
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

                author_field = item.get("author", {})
                author_name = author_field.get("nickname", "TikTok Creator") if isinstance(author_field, dict) else str(author_field or "TikTok Creator")

                video_obj = {
                    "id": video_id,
                    "title": item.get("title", f"Viral TikTok Video - {country_name}"),
                    "author": author_name,
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
            print(f"⏩ Skipped {country_name} due to: {e}")
            continue

        # 🔑 যত ভিডিও পাওয়া গেছে, ঠিক ততগুলোই সেভ হবে — ০টা হলে ওই country বাদ যাবে
        if country_videos:
            country_videos_map[code] = country_videos
            print(f"✅ Saved {len(country_videos)} videos for {country_name}")
        else:
            print(f"❌ 0 videos found for {country_name}")

    country_videos_map["GLOBAL"] = all_global_videos[:600]

    return country_videos_map, new_videos_count


tiktok_data, new_count = fetch_worldwide_viral_videos()

with open(TIKTOK_VIDEOS_FILE, "w", encoding="utf-8") as f:
    json.dump({"tiktok_by_country": tiktok_data}, f, indent=4, ensure_ascii=False)

with open(TIKTOK_SEEN_IDS_FILE, "w", encoding="utf-8") as f:
    json.dump(seen_ids, f, indent=4)

print(f"🎉 Successfully Generated Viral TikTok Videos ({new_count} new)!")

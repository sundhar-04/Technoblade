# ── Step 1: data_collector.py ─────────────────────────────────────────────
# Replaces: fetch_train_history() + get_avg_delay_at()
# New job: write rows to CSV instead of just returning avg_delay

import csv, os, re, requests
from bs4 import BeautifulSoup
from datetime import datetime
from time import sleep

HEADERS = {"User-Agent": "Mozilla/5.0"}
CSV_PATH = "train_delay_dataset.csv"

FIELDNAMES = [
    "train_num", "train_name", "station_code",
    "avg_delay",                    # scraped
    "max_delay",                    # scraped
    "route_popularity",             # = t1 + t2 count from hub page
    "time_of_day",                  # engineered: 0=morning 1=afternoon 2=night
    "day_of_week",                  # engineered from runs pattern (0=Sun..6=Sat)
    "season",                       # engineered: 0=summer 1=monsoon 2=winter
    "is_major_station",             # 1 if hub in MAJOR_STATIONS else 0
    "actual_delay_at_hub",          # TARGET LABEL — what we predict
]

def time_of_day(dep_str):
    h = int(dep_str.split(':')[0])
    if 5 <= h < 12:  return 0  # morning
    if 12 <= h < 18: return 1  # afternoon
    return 2                   # night

def season_now():
    m = datetime.now().month
    if m in [3,4,5]:   return 0  # summer
    if m in [6,7,8,9]: return 1  # monsoon
    return 2                     # winter

def scrape_to_csv(train_num, train_name, dep_time, station_code,
                  route_popularity, is_major):
    slug = '-'.join(w.capitalize() for w in train_name.split())
    url  = f"https://etrain.info/train/{slug}-{train_num}/history?d=1y"
    try:
        soup = BeautifulSoup(
            requests.get(url, headers=HEADERS, timeout=15).text, "html.parser"
        )
        text = soup.get_text(separator=" ")

        # Per-station avg delay (already working in your scraper)
        delays = {}
        for m in re.finditer(
            r'\(([A-Z0-9]{2,6})\)\s+Avg\.\s+Delay:\s+(\d+)\s+Min', text
        ):
            delays[m.group(1)] = int(m.group(2))

        # Max delay from the page summary
        max_m = re.search(r'Maximum\s*:\s*(\d+)', text)
        max_d = int(max_m.group(1)) if max_m else None

        avg_d = delays.get(station_code)
        if avg_d is None:
            return  # no data for this station — skip row

        row = {
            "train_num":           train_num,
            "train_name":          train_name,
            "station_code":        station_code,
            "avg_delay":           avg_d,
            "max_delay":           max_d if max_d is not None else avg_d,
            "route_popularity":    route_popularity,
            "time_of_day":         time_of_day(dep_time),
            "day_of_week":         datetime.now().weekday(),
            "season":              season_now(),
            "is_major_station":    int(is_major),
            "actual_delay_at_hub": avg_d,   # using avg as label for now
                                            # swap with live NTES data later
        }

        write_header = not os.path.exists(CSV_PATH)
        with open(CSV_PATH, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            if write_header:
                writer.writeheader()
            writer.writerow(row)
        print(f"  [CSV] {train_num} @ {station_code} -> avg {avg_d}m")

    except Exception as e:
        print(f"  [!] {train_num}: {e}")
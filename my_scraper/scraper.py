"""
scraper.py — Intelligent Train Transit Finder
─────────────────────────────────────────────
Run this file directly:  python scraper.py

Phase 1  get_hubs()    : Playwright  (transit list is JS-rendered)
Phase 2  get_trains()  : requests    (via-schedule pages are plain HTML)
Phase 3  history       : history_fetcher.py
                           fast_history()  — requests, avg only, used during scan
                           full_history()  — Playwright, real max/p90, final top-3 only
"""

import re
import csv
import os
from itertools import product
from time import sleep
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# ── Other modules in the same folder ─────────────────────────────────────
try:
    from predictor import predict_delay
except ImportError:
    def predict_delay(avg_delay, max_delay, route_popularity,
                      dep_time_str, is_major_station):
        return round(avg_delay + (max_delay - avg_delay) * 0.25)

from history_fetcher import (
    fast_history,
    full_history,
    get_avg_delay,
    get_max_delay,
)

# ── Config ────────────────────────────────────────────────────────────────
DELAY_BUFFER_MINS = 60
MIN_WAIT_MINS     = 120
MAX_WAIT_MINS     = 720
TOP_HUBS          = 5
TOP_HUBS_MAX      = 15
MIN_RESULTS       = 3
TOP_RESULTS       = 5

MAJOR_STATIONS = {
    "NDLS","NZM","BCT","CSTM","HWH","MAS","SBC","BPL",
    "NGP","ET","AGC","GWL","KOTA","JP","ADI","PUNE"
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

CSV_PATH   = "train_delay_dataset.csv"
CSV_FIELDS = [
    "train_num","train_name","station_code",
    "avg_delay","max_delay","route_popularity",
    "time_of_day","day_of_week","season","is_major_station",
    "actual_delay_at_hub",
]

# ── Math helpers ──────────────────────────────────────────────────────────
def to_mins(t):
    h, m = map(int, t.strip().split(':'))
    return h * 60 + m

def wait_time(eff_arr_mins, dep2_mins):
    diff = dep2_mins - eff_arr_mins
    if diff < 0:
        diff += 1440          # overnight wrap
    return diff

def effective_arrival(arr_str, hist_delay=0):
    return to_mins(arr_str) + DELAY_BUFFER_MINS + hist_delay

def days_overlap(d1, d2):
    return bool(set(d1) & set(d2))

def is_valid_wait(w):
    return MIN_WAIT_MINS <= w <= MAX_WAIT_MINS

def hub_score(connections, hub_code, best_wait):
    major_bonus = 15 if hub_code in MAJOR_STATIONS else 0
    return (20 * len(connections)) + major_bonus - (best_wait / 10)

def reliability_score(avg_delay):
    if avg_delay is None:
        return 50
    return max(0, 100 - avg_delay * 2)

def reliability_label(avg_delay):
    s = reliability_score(avg_delay)
    if s >= 80: return "Excellent"
    if s >= 60: return "Good"
    if s >= 40: return "Fair"
    return "Poor"

# ── Small utilities ───────────────────────────────────────────────────────
def _time_of_day(dep_str):
    try:
        h = int(dep_str.split(':')[0])
        if 5 <= h < 12:  return 0
        if 12 <= h < 18: return 1
        return 2
    except Exception:
        return 1

def _season():
    m = datetime.now().month
    if m in [3,4,5]:   return 0
    if m in [6,7,8,9]: return 1
    return 2

def day_label(day_indices):
    names = ['Su','Mo','Tu','We','Th','Fr','Sa']
    return ' '.join(names[i] for i in day_indices) or 'N/A'

def extract_hub_code(text):
    m = re.search(r'\(([A-Z0-9]{2,7})\)\s*$', text.strip())
    return m.group(1) if m else ''

def mins_to_hhmm(m):
    m = int(m) % 1440
    return f"{m//60:02d}:{m%60:02d}"

# ── CSV writer ────────────────────────────────────────────────────────────
_csv_seen = set()

def write_to_csv(train_num, train_name, station_code,
                 avg_d, max_d, route_pop, dep_time, is_major):
    if avg_d is None:
        return
    key = (train_num, station_code)
    if key in _csv_seen:
        return
    _csv_seen.add(key)
    row = {
        "train_num":           train_num,
        "train_name":          train_name,
        "station_code":        station_code,
        "avg_delay":           avg_d,
        "max_delay":           max_d if max_d is not None else avg_d * 2,
        "route_popularity":    route_pop,
        "time_of_day":         _time_of_day(dep_time),
        "day_of_week":         datetime.now().weekday(),
        "season":              _season(),
        "is_major_station":    int(is_major),
        "actual_delay_at_hub": avg_d,
    }
    write_header = not os.path.exists(CSV_PATH)
    with open(CSV_PATH, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if write_header:
            writer.writeheader()
        writer.writerow(row)

# ══════════════════════════════════════════════════════════════════════════
# PHASE 1 — Hub list via Playwright
# ══════════════════════════════════════════════════════════════════════════
def get_hubs(from_code, to_code):
    hubs = []
    print(f"\n[Phase 1] Opening transit page: {from_code} → {to_code}")

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page    = browser.new_page()
        page.goto("https://etrain.info/transit", wait_until="networkidle")

        page.locator("#transstn1").click()
        page.keyboard.type(from_code, delay=100)
        page.wait_for_timeout(1500)
        page.keyboard.press("ArrowDown")
        page.keyboard.press("Enter")
        page.wait_for_timeout(500)

        page.locator("#transstn2").click()
        page.keyboard.type(to_code, delay=100)
        page.wait_for_timeout(1500)
        page.keyboard.press("ArrowDown")
        page.keyboard.press("Enter")
        page.wait_for_timeout(500)

        page.locator("button.trstbtngo").click()
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)

        body_text  = page.inner_text("body")
        has_direct = ("Direct Train" in body_text and
                      "No Direct Trains" not in body_text)
        if has_direct:
            print("  ✓ Direct train also available on this route.")

        page_num = 1
        while True:
            print(f"  Scraping hub page {page_num}...", end=" ", flush=True)
            rows_before = len(hubs)

            try:
                page.wait_for_selector("table tbody tr", timeout=5000)
            except Exception:
                print("(no table — stopping)")
                break

            for row in page.query_selector_all("table tbody tr"):
                cells = row.query_selector_all("td")
                if len(cells) != 6:
                    continue
                try:
                    hub_cell = cells[2].inner_text().replace("Show", "").strip()
                    hub_code = extract_hub_code(hub_cell)
                    if not hub_code:
                        continue
                    t1   = int(cells[1].inner_text().strip())
                    t2   = int(cells[3].inner_text().strip())
                    dist = int(re.sub(r'[^\d]', '', cells[5].inner_text().strip()))
                    hubs.append({
                        "name": hub_cell, "code": hub_code,
                        "t1": t1, "t2": t2, "dist": dist,
                    })
                except (ValueError, AttributeError):
                    continue

            print(f"{len(hubs) - rows_before} hubs")

            next_btn = page.query_selector(
                f".pagination a:text('{page_num + 1}')"
            )
            if not next_btn:
                break
            next_btn.click()
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(1500)
            page_num += 1

        browser.close()

    print(f"  Total hubs found: {len(hubs)}\n")
    return sorted(hubs, key=lambda x: (-(x["t1"] + x["t2"]), x["dist"]))

# ══════════════════════════════════════════════════════════════════════════
# PHASE 2 — Per-hub train schedule via requests
# ══════════════════════════════════════════════════════════════════════════
def build_via_url(from_code, to_code, hub, from_name="", to_name=""):
    def slugify(name):
        clean = re.sub(r'\([^)]*\)', '', name).strip()
        return '-'.join(w.capitalize() for w in clean.split())
    fn = slugify(from_name) if from_name else from_code
    tn = slugify(to_name)   if to_name   else to_code
    hn = slugify(hub["name"])
    return (
        f"https://etrain.info/trains/"
        f"{fn}-{from_code}-to-{tn}-{to_code}-via-{hn}-{hub['code']}"
    )

def get_trains(from_code, to_code, hub, from_name="", to_name=""):
    url = build_via_url(from_code, to_code, hub, from_name, to_name)
    print(f"    Fetching: {url}")
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
    except Exception as e:
        print(f"    [!] Request failed: {e}")
        return [], []

    soup       = BeautifulSoup(resp.text, "html.parser")
    leg1, leg2 = [], []
    table_idx  = 0

    for table in soup.find_all("table"):
        has_data = False
        for row in table.find_all("tr"):
            cols = row.find_all("td")
            if len(cols) != 15:
                continue
            dep = cols[3].get_text(strip=True)
            arr = cols[5].get_text(strip=True)
            if ':' not in dep or ':' not in arr:
                continue
            try:
                to_mins(dep); to_mins(arr)
            except ValueError:
                continue
            entry = {
                "num":  cols[0].get_text(strip=True),
                "name": cols[1].get_text(strip=True),
                "dep":  dep, "arr": arr,
                "days": [i for i, c in enumerate(cols[7:14])
                         if c.get_text(strip=True) == 'Y'],
            }
            (leg1 if table_idx == 0 else leg2).append(entry)
            has_data = True
        if has_data:
            table_idx += 1
        if table_idx >= 2:
            break

    return leg1, leg2

# ══════════════════════════════════════════════════════════════════════════
# PHASE 3 — Score a single hub
# ══════════════════════════════════════════════════════════════════════════
def scan_hub(hub, from_code, to_code, from_name="", to_name=""):
    print(f"\n  Hub: {hub['name']}  ({hub['t1']}+{hub['t2']} trains)")

    leg1, leg2 = get_trains(from_code, to_code, hub, from_name, to_name)
    print(f"    Leg1: {len(leg1)} | Leg2: {len(leg2)}", end="")
    if not leg1 or not leg2:
        print(" → skipped")
        return None
    print()

    # Tier 1: fast avg-only history for all Leg-1 trains
    seen = set()
    for t1 in leg1:
        if t1["num"] not in seen:
            print(f"    History (fast): {t1['num']} {t1['name']}")
            fast_history(t1["num"], t1["name"])
            seen.add(t1["num"])
            sleep(0.3)

    # Compute catchable pairs
    connections = []
    for t1, t2 in product(leg1, leg2):
        avg_d = get_avg_delay(t1["num"], hub["code"])
        max_d = get_max_delay(t1["num"], hub["code"])  # None until full_history runs

        # CSV is written in upgrade_top_hubs() AFTER full_history() populates
        # the real max. Writing here would lock the row in _csv_seen with avg*2.

        train_info_l1 = {
            'train_name': t1['name'],
            'train_no': t1['num'],
            'source': from_code,
            'destination': hub['code'],
            'dep': t1['dep']
        }

        hist_delay = predict_delay(
            avg_delay        = avg_d or 15,
            max_delay        = max_d or 60,
            route_popularity = hub["t1"] + hub["t2"],
            dep_time_str     = t1["dep"],
            is_major_station = hub["code"] in MAJOR_STATIONS,
            train_info       = train_info_l1
        )

        eff_arr = effective_arrival(t1["arr"], hist_delay)
        wait    = wait_time(eff_arr, to_mins(t2["dep"]))

        if not days_overlap(t1["days"], t2["days"]):
            continue
        if not is_valid_wait(wait):
            continue

        connections.append({
            "t1":         t1,
            "t2":         t2,
            "wait":       wait,
            "hist_delay": hist_delay,
            "r_score":    reliability_score(avg_d),
        })

    if not connections:
        print(f"    → 0 valid pairs")
        return None

    connections.sort(key=lambda x: (-x["r_score"], x["wait"]))
    best_wait = connections[0]["wait"]
    score     = hub_score(connections, hub["code"], best_wait)
    print(f"    → {len(connections)} pairs | best wait {best_wait}m | score {score:.1f}")

    return {
        "hub":         hub,
        "connections": connections,
        "leg1_trains": leg1,
        "best_wait":   best_wait,
        "score":       score,
    }

# ══════════════════════════════════════════════════════════════════════════
# PHASE 4 — Upgrade top-3 with real max delay via Playwright
# ══════════════════════════════════════════════════════════════════════════
def upgrade_top_hubs(scored_hubs):
    print("\n[Phase 4] Fetching real max delay for top hubs (Playwright)...")
    for entry in scored_hubs[:3]:
        hub  = entry["hub"]
        seen = set()
        print(f"  Hub: {hub['name']}")
        for t1 in entry["leg1_trains"]:
            if t1["num"] not in seen:
                print(f"    full_history: {t1['num']} @ {hub['code']}")
                full_history(t1["num"], t1["name"], [hub["code"]])
                seen.add(t1["num"])
                sleep(0.5)

    # Re-score with updated predictions AND write CSV with real max
    for entry in scored_hubs[:3]:
        hub = entry["hub"]

        # FIX 1: Write CSV for ALL leg1 trains, not just those in connections.
        # Iterating connections misses trains that had no valid pairs after
        # re-scoring — e.g. 12641 and 16787 at NZM were fetched but never written.
        for t1 in entry["leg1_trains"]:
            avg_d = get_avg_delay(t1["num"], hub["code"])
            max_d = get_max_delay(t1["num"], hub["code"])
            write_to_csv(
                t1["num"], t1["name"], hub["code"],
                avg_d, max_d, hub["t1"] + hub["t2"],
                t1["dep"], hub["code"] in MAJOR_STATIONS,
            )

        for conn in entry["connections"]:
            t1    = conn["t1"]
            avg_d = get_avg_delay(t1["num"], hub["code"])
            max_d = get_max_delay(t1["num"], hub["code"])

            train_info_l1 = {
                'train_name': t1['name'],
                'train_no': t1['num'],
                # Source for entry['connections'] is the original from_code
                # We don't have it here easily, but we can assume NDLS/HWH or look it up
                'dep': t1['dep']
            }

            conn["hist_delay"] = predict_delay(
                avg_delay        = avg_d or 15,
                max_delay        = max_d or 60,
                route_popularity = hub["t1"] + hub["t2"],
                dep_time_str     = t1["dep"],
                is_major_station = hub["code"] in MAJOR_STATIONS,
                train_info       = train_info_l1
            )
            eff_arr      = effective_arrival(t1["arr"], conn["hist_delay"])
            conn["wait"] = wait_time(eff_arr, to_mins(conn["t2"]["dep"]))

        entry["connections"] = [c for c in entry["connections"]
                                 if is_valid_wait(c["wait"])]
        if entry["connections"]:
            entry["connections"].sort(key=lambda x: (-x["r_score"], x["wait"]))
            entry["best_wait"] = entry["connections"][0]["wait"]
            entry["score"]     = hub_score(
                entry["connections"], hub["code"], entry["best_wait"]
            )

# ── Print results ─────────────────────────────────────────────────────────
def print_results(scored_hubs, from_code, to_code):
    scored_hubs.sort(key=lambda x: -x["score"])
    n = min(TOP_RESULTS, len(scored_hubs))

    print(f"\n{'='*68}")
    print(f"  TOP {n} SAFEST ROUTES  :  {from_code}  →  {to_code}")
    print(f"  Buffer = {DELAY_BUFFER_MINS}m base + ML predicted delay")
    print(f"  Wait window : {MIN_WAIT_MINS}–{MAX_WAIT_MINS} min")
    print(f"{'='*68}")

    for i, entry in enumerate(scored_hubs[:TOP_RESULTS]):
        hub   = entry["hub"]
        label = "★ BEST" if i == 0 else f"Option {i+1}"
        print(f"\n[{label}]  via {hub['name']}  |  Score: {entry['score']:.1f}")
        if hub["code"] in MAJOR_STATIONS:
            print("  [+] Major station — good facilities for longer waits")

        for j, conn in enumerate(entry["connections"][:3], 1):
            t1, t2     = conn["t1"], conn["t2"]
            wait       = conn["wait"]
            hist_delay = conn["hist_delay"]
            eff        = effective_arrival(t1["arr"], hist_delay)
            avg_d      = get_avg_delay(t1["num"], hub["code"])
            max_d      = get_max_delay(t1["num"], hub["code"])
            tag        = "  ← recommended" if j == 1 else ""

            print(f"\n  {'─'*60}")
            print(f"  Combo {j}{tag}")
            print(f"    LEG 1 : [{t1['num']}] {t1['name']}")
            print(f"            dep {t1['dep']}  →  arr {t1['arr']} at {hub['code']}")
            print(f"            Safe arr  : {mins_to_hhmm(eff)}"
                  f"  (+{DELAY_BUFFER_MINS}m base, +{hist_delay}m predicted)")
            if avg_d is not None:
                max_str = str(max_d) if max_d is not None else "no data"
                print(f"            Delay hist : avg {avg_d}m  |  max {max_str}m"
                      f"  [{reliability_label(avg_d)}]"
                      f"  {reliability_score(avg_d):.0f}/100")
            else:
                print("            Delay hist : no data")
            print(f"            Runs on   : {day_label(t1['days'])}")
            print(f"    WAIT  : {wait//60}h {wait%60}m  "
                  f"(safe if L1 is ≤ {wait}m late)")
            print(f"    LEG 2 : [{t2['num']}] {t2['name']}")
            print(f"            dep {t2['dep']}  →  arr {t2['arr']} at {to_code}")
            print(f"            Runs on   : {day_label(t2['days'])}")

        print()

    print(f"{'='*68}")
    print(f"[CSV] ML training data → {CSV_PATH}")
    print("      Run  train_model.py  once you have 50+ rows.\n")

# ── Main ──────────────────────────────────────────────────────────────────
def find_safest_combos(from_code, to_code):
    print(f"\n{'='*68}")
    print(f"  INTELLIGENT TRAIN TRANSIT FINDER")
    print(f"  {from_code}  →  {to_code}")
    print(f"{'='*68}")

    all_hubs = get_hubs(from_code, to_code)
    if not all_hubs:
        print("\n[!] No hubs found. Check codes at etrain.info/transit")
        return

    print(f"[Phase 2+3] Scanning ({len(all_hubs)} hubs total)...")
    scored_hubs, scanned = [], 0

    for hub in all_hubs:
        if scanned >= TOP_HUBS_MAX:
            break
        result = scan_hub(hub, from_code, to_code)
        scanned += 1
        if result:
            scored_hubs.append(result)
        if len(scored_hubs) >= MIN_RESULTS and scanned >= TOP_HUBS:
            print(f"\n  [OK] {len(scored_hubs)} valid hubs after {scanned} scans.")
            break
        sleep(0.5)

    if not scored_hubs:
        print("\nNo valid combinations found.")
        print("Try: raise MAX_WAIT_MINS or lower DELAY_BUFFER_MINS")
        return

    upgrade_top_hubs(scored_hubs)
    print_results(scored_hubs, from_code, to_code)


if __name__ == "__main__":
    fc = input("Enter FROM station code: ").strip().upper()
    tc = input("Enter TO   station code: ").strip().upper()
    find_safest_combos(fc, tc)
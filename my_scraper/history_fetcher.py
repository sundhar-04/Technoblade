"""
history_fetcher.py
──────────────────
Two-tier delay history fetcher for etrain.info

Tier 1  fast_history()   : requests — scrapes per-station avg delay from
                           the static history page (always works)

Tier 2  full_history()   : Playwright — clicks each station bar modal,
                           reads the hidden chart <table>, extracts
                           per-run delay values → real min / max / std_dev

Use fast_history() during hub scanning (speed matters).
Use full_history() only for the final top-3 hubs (accuracy matters).
"""

import re
import time
from bs4 import BeautifulSoup
import requests

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# ── Cache: {train_num: {STATION_CODE: {avg, min, max, runs, p75, p90}}} ──
_history_cache: dict = {}


# ════════════════════════════════════════════════════════════════════
# TIER 1 — requests  (avg only, fast)
# ════════════════════════════════════════════════════════════════════
def fast_history(train_num: str, train_name: str) -> dict:
    """
    Scrapes the static history page via requests.
    Returns: {STATION_CODE: avg_delay_mins, ...}
    No min/max — those require JS modal clicks.
    """
    if train_num in _history_cache:
        return _history_cache[train_num]

    slug = '-'.join(w.capitalize() for w in train_name.split())
    url  = f"https://etrain.info/train/{slug}-{train_num}/history?d=1y"

    result = {}
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        text = BeautifulSoup(resp.text, "html.parser").get_text(separator=" ")

        # Pattern present in static HTML:
        # "LUDHIANA JN (LDH)  Avg. Delay: 40 Min's"
        for m in re.finditer(
            r'\(([A-Z0-9]{2,7})\)\s+Avg\.\s+Delay:\s+(\d+)\s+Min', text
        ):
            result[m.group(1)] = {"avg": int(m.group(2))}

    except Exception as e:
        print(f"      [!] fast_history failed for {train_num}: {e}")

    _history_cache[train_num] = result
    return result


# ════════════════════════════════════════════════════════════════════
# TIER 2 — Playwright  (avg + min + max + p75 + p90, slower)
# ════════════════════════════════════════════════════════════════════
def full_history(train_num: str, train_name: str,
                 station_codes: list[str]) -> dict:
    r"""
    For each station_code in station_codes, clicks its bar on the
    history page, reads the hidden chart <table> from the modal,
    and computes: avg, min, max, p75, p90 from actual run data.

    Returns: {
        STATION_CODE: {
            "avg": int, "min": int, "max": int,
            "p75": int, "p90": int, "runs": int
        }, ...
    }

    BUG that was here before:
        The old code did:  re.search(r'Maximum' + r'\s*:\s*' + r'(\d+)', text)
        That summary line ("Average:40 | Minimum:0 | Maximum:212")
        is inside the JS modal — requests never sees it, so the
        regex always failed, and the code fell back to avg * 2.

    This function fixes it by using Playwright to click each station
    bar and read the real per-run data table from the modal.
    """
    from playwright.sync_api import sync_playwright

    slug = '-'.join(w.capitalize() for w in train_name.split())
    url  = f"https://etrain.info/train/{slug}-{train_num}/history?d=1y"

    # Seed with fast_history avg values first
    fast = fast_history(train_num, train_name)
    result = {code: dict(fast.get(code, {})) for code in station_codes}

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page    = browser.new_page()
        page.goto(url, wait_until="networkidle")
        page.wait_for_timeout(1500)

        for code in station_codes:
            try:
                # Each station is a link: <a href="#NZM" ...>(NZM)</a>
                # Clicking it opens the modal with the chart table
                trigger = page.locator(f'a[href="#{code}"]').first
                if not trigger.is_visible():
                    print(f"        [skip] no bar for {code}")
                    continue

                trigger.click()
                # Wait for the hidden aria table inside the modal to appear
                page.wait_for_selector(
                    "div.hisStnData table tbody tr", timeout=5000
                )
                page.wait_for_timeout(300)

                # Parse the hidden <table> (aria-hidden but in DOM)
                # Structure: <tr><td>Mar 31, 2025</td><td>16</td></tr>
                modal_html = page.inner_html("div.hisStnData")
                soup       = BeautifulSoup(modal_html, "html.parser")

                delay_vals = []
                for row in soup.select("table tbody tr"):
                    cells = row.find_all("td")
                    if len(cells) >= 2:
                        try:
                            # FIX: clamp to 0 — etrain.info records early arrivals
                            # as negative (e.g. -19), which is meaningless for
                            # delay prediction and would corrupt min/avg/p75/p90.
                            val = int(cells[1].get_text(strip=True))
                            delay_vals.append(max(0, val))
                        except ValueError:
                            pass

                if not delay_vals:
                    print(f"        [!] No run data parsed for {code}")
                    continue

                delay_vals.sort()
                n   = len(delay_vals)
                avg = round(sum(delay_vals) / n)
                mn  = delay_vals[0]
                mx  = delay_vals[-1]
                p75 = delay_vals[int(n * 0.75)]
                p90 = delay_vals[int(n * 0.90)]

                result[code] = {
                    "avg":  avg,
                    "min":  mn,
                    "max":  mx,
                    "p75":  p75,
                    "p90":  p90,
                    "runs": n,
                }
                print(f"        [{code}] avg={avg} min={mn} max={mx}"
                      f" p75={p75} p90={p90} ({n} runs)")

                # Close modal before clicking next station
                close_btn = page.locator("div.hisStnData a.modalCloseBtn").first
                if close_btn.is_visible():
                    close_btn.click()
                    page.wait_for_timeout(300)

            except Exception as e:
                print(f"        [!] full_history failed for {code}: {e}")

        browser.close()

    _history_cache[train_num] = result
    return result


# ════════════════════════════════════════════════════════════════════
# Helpers used by scraper.py
# ════════════════════════════════════════════════════════════════════
def get_avg_delay(train_num: str, station_code: str) -> int | None:
    data = _history_cache.get(train_num, {}).get(station_code)
    return data.get("avg") if data else None

def get_max_delay(train_num: str, station_code: str) -> int | None:
    """
    Returns REAL max from full_history() if available.
    Falls back to p90 if available.
    Falls back to None — never avg*2.
    """
    data = _history_cache.get(train_num, {}).get(station_code)
    if not data:
        return None
    # Prefer real max → p90 → None  (never fabricate avg*2)
    return data.get("max") or data.get("p90") or None

def get_p90_delay(train_num: str, station_code: str) -> int | None:
    data = _history_cache.get(train_num, {}).get(station_code)
    return data.get("p90") if data else None


# ════════════════════════════════════════════════════════════════════
# Quick test
# ════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    train_num  = "16787"
    train_name = "TEN SVDK EXP"

    print("── Tier 1 (fast, requests) ──")
    fast = fast_history(train_num, train_name)
    for code, data in list(fast.items())[:5]:
        print(f"  {code}: avg={data['avg']}")

    print("\n── Tier 2 (full, Playwright) for LDH and NZM ──")
    full = full_history(train_num, train_name, ["LDH", "NZM"])
    for code, data in full.items():
        print(f"  {code}: {data}")

    # Expected for LDH:
    # avg=40  min=0  max=212  p75=~51  p90=~112
"""Live checks against the public sites. Standard library only.

  * the website and the GitHub Pages backup load
  * the live concert list is the one in this repo (after a push: waits for Netlify to publish it)
  * the Android app can download the list (CORS header)
  * the morning update is still running (data/status.json not older than 36 hours, during the season)

Usage: python3 tests/check_live.py [--wait-for-deploy]
"""
import json
import sys
import time
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

R = Path(__file__).resolve().parent.parent
SITE = "https://kutcheri-dec.netlify.app"
BACKUP = "https://sunithi2000-lab.github.io/kutcheri/"
# the morning update must have run within this many hours, between these dates (UTC)
FRESH_HOURS, FRESH_FROM, FRESH_TO = 36, datetime(2026, 10, 14, tzinfo=timezone.utc), datetime(2027, 2, 1, tzinfo=timezone.utc)
problems, notes = [], []


def get(url):
    req = urllib.request.Request(url + ("&" if "?" in url else "?") + f"t={int(time.time())}",
                                 headers={"User-Agent": "kutcheri-health-check", "Origin": "https://localhost", "Cache-Control": "no-cache"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status, dict(r.headers), r.read()


repo_c = json.loads((R / "data/concerts.json").read_text())
repo_status = json.loads((R / "data/status.json").read_text())

# 1. website
try:
    s, h, body = get(SITE + "/")
    if s != 200 or b"Marghazhi Kutcheri Planner" not in body:
        problems.append(f"website {SITE} answered {s} without the planner page")
except Exception as e:  # noqa: BLE001
    problems.append(f"website {SITE} is not reachable: {e}")

# 2. live data = repo data (Netlify publishes ~1 minute after a push; a failed data check blocks the deploy)
deadline = time.time() + (420 if "--wait-for-deploy" in sys.argv else 0)
while True:
    try:
        s, h, body = get(SITE + "/data/status.json")
        live_status = json.loads(body)
        if live_status.get("built_at") == repo_status.get("built_at"):
            s, h, body = get(SITE + "/data/concerts.json")
            live_c = json.loads(body)
            if live_c != repo_c:
                problems.append("live concert list differs from the repo even though the build stamp matches")
            if h.get("Access-Control-Allow-Origin") != "*":
                problems.append("live /data/concerts.json lacks the CORS header, so the Android app cannot refresh its list (check _headers)")
            break
        if time.time() > deadline:
            problems.append(f"live site still serves the build from {live_status.get('built_at')}, repo has {repo_status.get('built_at')} — "
                            "the Netlify deploy may have failed (a failing data check stops it; see Netlify → Deploys)")
            break
    except Exception as e:  # noqa: BLE001
        if time.time() > deadline:
            problems.append(f"cannot read the live data: {e}")
            break
    time.sleep(20)

# 3. morning update still running
now = datetime.now(timezone.utc)
try:
    built = datetime.fromisoformat(live_status["built_at"].replace("Z", "+00:00"))
    age = now - built
    notes.append(f"last data build {built:%Y-%m-%d %H:%M} UTC ({age.total_seconds() / 3600:.0f} h ago)")
    if FRESH_FROM <= now <= FRESH_TO and age > timedelta(hours=FRESH_HOURS):
        problems.append(f"the morning update has not run for {age.days} day(s) {age.seconds // 3600} h (last build {built:%d %b %H:%M} UTC) — check the scheduled task")
except Exception as e:  # noqa: BLE001
    problems.append(f"cannot tell when the data was last built: {e}")

# 4. backup site
try:
    s, h, body = get(BACKUP)
    if s != 200:
        problems.append(f"backup site {BACKUP} answered {s}")
except Exception as e:  # noqa: BLE001
    problems.append(f"backup site {BACKUP} is not reachable: {e}")

for n in notes:
    print("note:", n)
if problems:
    print(f"LIVE CHECK FAILED — {len(problems)} problem(s):")
    for p in problems:
        print(" -", p)
    sys.exit(1)
print(f"live OK: website, backup, live data = repo ({len(repo_c)} concerts), app download header, update freshness")

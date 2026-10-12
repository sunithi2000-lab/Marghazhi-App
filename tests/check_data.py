"""Safety checks on the concert data. Standard library only.

Runs (1) inside every Netlify deploy, before the site is published: if a check fails the deploy
stops and the previous site stays live; (2) in the GitHub "Health checks" workflow, which reports
failures to the owner.

Usage: python3 tests/check_data.py [--previous URL_OF_LIVE_concerts.json]
Bypass the "big drop" check once (e.g. new season reset): create the file tests/ALLOW_BIG_CHANGE.
"""
import json
import re
import sys
import urllib.request
from datetime import date, datetime
from pathlib import Path

R = Path(__file__).resolve().parent.parent
SEASON = (date(2026, 11, 1), date(2027, 1, 31))
ENTRY = ("Free", "Ticketed", "Not stated")
STATUSES = {"Schedule published", "Dates announced", "Awaiting 2026–27 schedule", "Some dates via artists' websites"}
NOT_STATED = "Organiser not stated"
HHMM = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")
problems, notes = [], []


def bad(msg):
    problems.append(msg)


def load(rel):
    try:
        return json.loads((R / rel).read_text())
    except Exception as e:  # noqa: BLE001
        bad(f"{rel}: cannot read JSON ({e})")
        return None


c = load("data/concerts.json")
o = load("data/organisations.json")
st = load("data/status.json")

if isinstance(c, list) and isinstance(o, list):
    if len(c) < 20:
        bad(f"only {len(c)} concerts in data/concerts.json (expected at least 20)")
    org_names = [x.get("name", "") for x in o]
    if len(set(org_names)) != len(org_names):
        bad("duplicate organisation names in data/organisations.json")
    if NOT_STATED in org_names:
        bad(f'"{NOT_STATED}" must not be listed as an organisation')
    for x in o:
        if not x.get("name"):
            bad(f"organisation without a name: {x}")
        if x.get("status") not in STATUSES:
            bad(f'{x.get("name")}: unknown status "{x.get("status")}"')
    ids, keys = set(), set()
    for i, x in enumerate(c):
        who = f'concert {x.get("id") or i} ({x.get("date")} {x.get("main_artist")})'
        for f in ("id", "date", "start", "main_artist", "main_instrument", "organisation", "venue", "area", "source_url", "entry"):
            if not str(x.get(f) or "").strip():
                bad(f"{who}: missing {f}")
        if x.get("id") in ids:
            bad(f"{who}: duplicate id")
        ids.add(x.get("id"))
        k = (x.get("date"), x.get("start"), (x.get("main_artist") or "").lower())
        if k in keys:
            bad(f"{who}: duplicate concert (same date, start time and main artist)")
        keys.add(k)
        try:
            d = date.fromisoformat(x.get("date", ""))
            if not SEASON[0] <= d <= SEASON[1]:
                bad(f"{who}: date outside the 2026–27 season")
        except ValueError:
            bad(f"{who}: invalid date")
        if x.get("start") and not HHMM.match(x["start"]):
            bad(f'{who}: invalid start time "{x["start"]}"')
        if x.get("end"):
            if not HHMM.match(x["end"]):
                bad(f'{who}: invalid end time "{x["end"]}"')
            elif x.get("start") and x["end"] <= x["start"]:
                bad(f"{who}: ends before it starts")
        if not str(x.get("source_url", "")).startswith("https://"):
            bad(f"{who}: source link is not https")
        if not str(x.get("entry", "")).startswith(ENTRY):
            bad(f'{who}: unexpected entry value "{x.get("entry")}"')
        perf = x.get("performers") or []
        if not any(p.get("role") == "main" for p in perf):
            bad(f"{who}: no main performer")
        if x.get("organisation") not in org_names and x.get("organisation") != NOT_STATED:
            bad(f'{who}: organisation "{x.get("organisation")}" is not in organisations.json')

if isinstance(st, dict):
    try:
        datetime.fromisoformat(st["built_at"].replace("Z", "+00:00"))
    except Exception:  # noqa: BLE001
        bad("data/status.json: built_at missing or invalid")
    if isinstance(c, list) and st.get("concerts") != len(c):
        bad(f"data/status.json says {st.get('concerts')} concerts but concerts.json has {len(c)}")

# compare with the version that is live now: block big unexpected drops
if "--previous" in sys.argv and isinstance(c, list):
    url = sys.argv[sys.argv.index("--previous") + 1]
    try:
        with urllib.request.urlopen(url, timeout=20) as r:
            prev = json.loads(r.read())
        lost = len(prev) - len(c)
        if lost > max(5, 0.2 * len(prev)):
            if (R / "tests/ALLOW_BIG_CHANGE").exists():
                notes.append(f"concerts dropped {len(prev)} -> {len(c)}, allowed by tests/ALLOW_BIG_CHANGE")
            else:
                bad(f"concerts dropped from {len(prev)} (live) to {len(c)} — more than 20%. If intended, add tests/ALLOW_BIG_CHANGE")
        notes.append(f"live site has {len(prev)} concerts, this build has {len(c)}")
    except Exception as e:  # noqa: BLE001
        notes.append(f"could not read the live data for comparison ({e}); skipped the drop check")

for n in notes:
    print("note:", n)
if problems:
    print(f"DATA CHECK FAILED — {len(problems)} problem(s):")
    for p in problems[:60]:
        print(" -", p)
    sys.exit(1)
print(f"data OK: {len(c)} concerts, {len(o)} organisations")

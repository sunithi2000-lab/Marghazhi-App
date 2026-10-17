"""Build the Margazhi 2026-27 concert repository from the raw schedule transcriptions.

Only 2026-27 season data published on official organiser websites is used.
Outputs: data/concerts.json, data/concerts.csv, data/organisations.json
"""
import csv, json, re
from pathlib import Path

ROOT = Path(__file__).parent
OUT = ROOT / "data"
OUT.mkdir(exist_ok=True)
FETCHED = "2026-10-12"

ACCOMP = {"violin", "viola", "mridangam", "ghatam", "kanjira", "moharsing", "morsing", "thavil"}
TITLE = re.compile(r"Sangita Kalanidhi\s+")

def slot(start):
    h = int(start[:2])
    return "Morning" if h < 12 else ("Afternoon" if h < 16 else "Evening")

def classify(main_instr):
    i = main_instr.lower()
    duet = "duet" in i or "&" in i
    if "vocal" in i:
        return ("Vocal duet" if duet else "Vocal"), "Vocal"
    base = i.replace("duet", "").strip()
    inst = "Nagaswaram" if "nagaswaram" in base else base.title()
    return ("Instrumental duet" if duet else "Instrumental"), inst

def split_people(s):
    # "Name (Instr), Name (Instr)" -> [(name, instr)]
    return [(n.strip(), ins.strip()) for n, ins in re.findall(r"([^,()][^()]*?)\s*\(([^)]*)\)", s)]

ORG = {
    "music-academy": dict(
        name="The Music Academy, Madras", festival="100th Annual Conference & Concerts",
        venue="Music Academy Auditorium, New No. 168, T.T.K. Road, Chennai 600014", area="Alwarpet / TTK Road",
        url="https://musicacademymadras.in/100th-annual-concerts-2026/"),
    "bharat-kalachar": dict(
        name="Bharat Kalachar", festival="38th Marghazhi Mahotsav",
        venue="Sri YGP Auditorium, No. 17, Thirumalai Road, T. Nagar, Chennai 600017", area="T. Nagar",
        url="https://www.bharatkalachar.com/38-bharat-kalachar.html"),
    "sri-krishna-gana-sabha": dict(
        name="Sri Krishna Gana Sabha", festival="70th Margazhi Mela",
        venue="Dr. Nalli Gana Vihar, Sri Krishna Gana Sabha, 20 Maharajapuram Santhanam Salai, T. Nagar, Chennai 600017",
        area="T. Nagar",
        url="https://krishnaganasabha.com/assets/images/nkc/margazhimela2026/MM_schedule(2026).pdf"),
    "charsur": dict(
        name="Charsur Arts Foundation", festival="DVAYAM – Sounds of Duality (December Season Music Festival 2026)",
        venue="My Bungalow, 40 Eldams Road, Teynampet, Chennai 600018", area="Teynampet",
        url="https://mdnd.in/ViewEvents/Carnatic?ci=101&c=3659&eMode=All&Date=All&mc=8&mcName=Carnatic"),
}

concerts = []

# Music Academy: full line-ups
for line in (ROOT / "raw_music_academy_2026.txt").read_text().splitlines():
    if not line or line.startswith("#"):
        continue
    date, start, end, entry, musicians = line.split("|", 4)
    people = split_people(musicians)
    # main artist(s) = everyone before the first accompanist instrument
    mains, accs = [], []
    for n, ins in people:
        (accs if (accs or ins.lower() in ACCOMP) and mains else mains).append((n, ins))
    # nagaswaram ensembles: thavil players are accompanists, all nagaswaram players are main
    ctype, instrument = classify(mains[0][1])
    o = ORG["music-academy"]
    concerts.append(dict(
        id=f"ma-{date}-{start.replace(':','')}", date=date, start=start, end=end, slot=slot(start),
        main_artist=" & ".join(TITLE.sub("", n) for n, _ in mains),
        main_instrument=instrument, concert_type=ctype,
        performers=[dict(name=TITLE.sub("", n), instrument=i, role="main") for n, i in mains] +
                   [dict(name=TITLE.sub("", n), instrument=i, role="accompanist") for n, i in accs],
        entry=entry, organisation=o["name"], festival=o["festival"], venue=o["venue"], area=o["area"],
        source_url=o["url"], fetched=FETCHED))

# Bharat Kalachar: main artist only (page lists no accompanists or end times)
for line in (ROOT / "raw_bharat_kalachar_2026.txt").read_text().splitlines():
    if not line or line.startswith("#"):
        continue
    date, start, entry, artist, form = line.split("|")
    ctype, instrument = classify(form)
    o = ORG["bharat-kalachar"]
    concerts.append(dict(
        id=f"bk-{date}-{start.replace(':','')}-{re.sub(r'[^a-z]', '', artist.lower())[:10]}",
        date=date, start=start, end="", slot=slot(start),
        main_artist=artist, main_instrument=instrument, concert_type=ctype,
        performers=[dict(name=artist, instrument=form, role="main")],
        entry=entry, organisation=o["name"], festival=o["festival"], venue=o["venue"], area=o["area"],
        source_url=o["url"], fetched=FETCHED))

# Sri Krishna Gana Sabha: full line-ups, no end times (Music Academy pattern, plus a note column)
def is_acc(ins):
    return re.sub(r"\b(duet|trio)\b", "", ins.lower()).strip() in ACCOMP
for line in (ROOT / "raw_sri_krishna_gana_sabha_2026.txt").read_text().splitlines():
    if not line or line.startswith("#"):
        continue
    date, start, entry, musicians, note = line.split("|")
    people = split_people(musicians)
    mains, accs = [], []
    for n, ins in people:
        (accs if (accs or is_acc(ins)) and mains else mains).append((n, ins))
    first = mains[0][1]
    if "trio" in first.lower():
        ctype, instrument = "Instrumental ensemble", re.sub(r"(?i)\s*trio", "", first).strip().title()
    else:
        ctype, instrument = classify(first)
    if len(mains) == 2:
        ctype = "Vocal duet" if all(i.lower() == "vocal" for _, i in mains) else "Duet"
    elif len(mains) > 2:
        ctype = "Instrumental ensemble"
    o = ORG["sri-krishna-gana-sabha"]
    concerts.append(dict(
        id=f"skgs-{date}-{start.replace(':','')}", date=date, start=start, end="", slot=slot(start),
        main_artist=" & ".join(n for n, _ in mains), main_instrument=instrument, concert_type=ctype,
        performers=[dict(name=n, instrument=i, role="main") for n, i in mains] +
                   [dict(name=n, instrument=i, role="accompanist") for n, i in accs],
        entry=entry, organisation=o["name"], festival=o["festival"], venue=o["venue"], area=o["area"],
        source_url=o["url"], note=note, fetched="2026-10-16"))

# Charsur Arts Foundation (DVAYAM): main artist only, from the MDnD listing (Bharat Kalachar pattern + note column)
for line in (ROOT / "raw_charsur_2026.txt").read_text().splitlines():
    if not line or line.startswith("#"):
        continue
    date, start, entry, artist, form, note = line.split("|")
    if form == "Not stated":
        ctype, instrument = "Not stated", "Not stated"
    elif form == "Ensemble":
        ctype, instrument = "Instrumental ensemble", "Ensemble"
    else:
        ctype, instrument = classify(form)
    o = ORG["charsur"]
    concerts.append(dict(
        id=f"ch-{date}-{start.replace(':','')}",
        date=date, start=start, end="", slot=slot(start),
        main_artist=artist, main_instrument=instrument, concert_type=ctype,
        performers=[dict(name=artist, instrument=form, role="main")],
        entry=entry, organisation=o["name"], festival=o["festival"], venue=o["venue"], area=o["area"],
        source_url=o["url"], source_label="MDnD listing", note=note, fetched="2026-10-18"))

# Artists' own websites / listings: concerts not in any organiser schedule
for line in (ROOT / "raw_artist_sites_2026.txt").read_text().splitlines():
    if not line or line.startswith("#"):
        continue
    date, start, end, entry, org, fest, venue, area, musicians, url, label, note = line.split("|")
    people = split_people(musicians)
    mains = [(n, i) for n, i in people if i.lower() not in ACCOMP]
    accs = [(n, i) for n, i in people if i.lower() in ACCOMP]
    ctype, instrument = classify(mains[0][1])
    if len(mains) > 1:
        ctype = "Instrumental duet" if instrument != "Vocal" else "Vocal duet"
    concerts.append(dict(
        id=f"as-{date}-{start.replace(':','')}-{re.sub(r'[^a-z]', '', mains[0][0].lower())[:10]}",
        date=date, start=start, end=end, slot=slot(start),
        main_artist=" & ".join(n for n, _ in mains), main_instrument=instrument, concert_type=ctype,
        performers=[dict(name=n, instrument=i, role="main") for n, i in mains] +
                   [dict(name=n, instrument=i, role="accompanist") for n, i in accs],
        entry=entry, organisation=org, festival=fest, venue=venue, area=area,
        source_url=url, source_label=label, note=note, fetched=FETCHED))

for c in concerts:
    c.setdefault("source_label", "Organiser's schedule")
    c.setdefault("note", "")

concerts.sort(key=lambda c: (c["date"], c["start"], c["organisation"]))

# Organisation directory: 2026-27 status only (no past-season dates)
orgs = [
    dict(name="The Music Academy, Madras", area="Alwarpet / TTK Road", venue=ORG["music-academy"]["venue"],
         status="Schedule published", festival_2026="100th Annual Concerts", dates_2026="15 Dec 2026 – 1 Jan 2027",
         note="Conference sessions daily 8–10 am, 16 Dec – 1 Jan. Dance festival 3–9 Jan 2027.",
         url="https://musicacademymadras.in/100th-annual-concerts-2026/"),
    dict(name="Bharat Kalachar", area="T. Nagar", venue=ORG["bharat-kalachar"]["venue"],
         status="Schedule published", festival_2026="38th Marghazhi Mahotsav", dates_2026="13 Dec 2026 – 17 Jan 2027",
         note="Advance booking at venue from 7 Dec 2026; ticketed shows also on BookMyShow.",
         url="https://www.bharatkalachar.com/38-bharat-kalachar.html"),
    dict(name="Kartik Fine Arts", area="Alwarpet / TTK Road", venue="Narada Gana Sabha, TTK Road",
         status="Dates announced", festival_2026="December Season festival", dates_2026="From 1 Dec 2026",
         note="Hosts the first part of the season at Narada Gana Sabha.",
         url="https://www.mylaporetimes.com/2026/10/december-season-2026-narada-gana-sabha-is-improving-its-audio-systems/"),
    dict(name="Narada Gana Sabha", area="Alwarpet / TTK Road", venue="TTK Road, Teynampet",
         status="Dates announced", festival_2026="December Season 2026", dates_2026="Concerts from 1 Dec 2026",
         note="Top-billed concerts to start by 3.30 pm and end by 8.30–8.45 pm; new audio system.",
         url="https://www.mylaporetimes.com/2026/10/december-season-2026-narada-gana-sabha-is-improving-its-audio-systems/"),
    dict(name="Sri Krishna Gana Sabha", area="T. Nagar", venue="No. 20, Maharajapuram Santhanam Salai, T. Nagar",
         status="Schedule published", festival_2026="70th Margazhi Mela", dates_2026="12 Dec 2026 – 3 Jan 2027",
         note="Natya Kala Conference (dance) 26–28 Dec 2026.",
         url="https://krishnaganasabha.com/assets/images/nkc/margazhimela2026/MM_schedule(2026).pdf"),
]
AWAIT = [
    ("Bharatiya Vidya Bhavan, Chennai Kendra", "Mylapore", "East Mada Street, Mylapore", "https://bhavanchennai.org/"),
    ("Sri Thyaga Brahma Gana Sabha", "T. Nagar", "Vani Mahal, G.N. Road, T. Nagar", ""),
    ("Mylapore Fine Arts Club", "Mylapore", "45, Musiri Subramaniam Road, Mylapore", ""),
    ("Sri Parthasarathy Swami Sabha", "Mylapore", "Vidya Bharathi, Bheemasena Garden Road, Mylapore", "https://parthasarathyswamisabha.com/"),
    ("The Indian Fine Arts Society", "Alwarpet / TTK Road", "Ethiraja Kalyana Nilayam, TTK Road, Alwarpet", ""),
    ("Brahma Gana Sabha", "Mylapore", "Sivagami Pethachi Auditorium, Mylapore", ""),
    ("Rasika Ranjani Sabha", "Mylapore", "Dakshinamoorthy Auditorium, Mylapore", "https://rrsabha.org/"),
    ("Naada Inbam", "Mylapore", "Ragasudha Hall, Luz Avenue, Mylapore", ""),
    ("Charsur Arts Foundation", "Mylapore", "Sri Ramanujar Millennium Hall, D'Silva Road, Mylapore", ""),
    ("Tamil Isai Sangam", "George Town", "Rajah Annamalai Mandram, Esplanade Road", ""),
    ("Nada Sudha", "Velachery", "Sri Ganapathy Sachchidananda Ashram, Velachery", ""),
    ("Sunaadalahari (Indira Ranganathan Trust)", "Abhiramapuram", "52, C.P. Ramaswamy Road, Abhiramapuram", ""),
    ("Carnatica / Paddhathi Music Fest", "Mylapore", "Desiga Vidya Bhavanam, Venkatesa Agraharam Road, Mylapore", "https://carnatica.net/"),
    ("MDnD Anandha Margazhi", "Mylapore", "MDnD Performance Centre, Luz Church Road, Mylapore", "https://www.mdnd.in/seasontickets"),
    ("Chennai Fine Arts", "", "", ""),
    ("Hamsadhwani", "Adyar", "", ""),
    ("Asthika Samajam", "Alwarpet", "Venus Colony, Alwarpet", ""),
    ("Madhuradhwani", "Mylapore", "Arkay Convention Centre, Mylapore", ""),
    ("Gayatri Fine Arts Global", "Mylapore", "Sri Krishna Saras Hall, Mylapore", ""),
    ("Shakthi Sangita Sabha", "Valasaravakkam", "Anbu Nagar, Valasaravakkam", ""),
    ("SASTRA Satsangh", "", "", ""),
    ("Sruthi Laya Kendra", "Mylapore", "Bharatiya Vidya Bhavan Mini Hall", ""),
]
for n, a, v, u in AWAIT:
    orgs.append(dict(name=n, area=a, venue=v, status="Awaiting 2026–27 schedule", festival_2026="",
                     dates_2026="", note="", url=u))

(OUT / "concerts.json").write_text(json.dumps(concerts, indent=1, ensure_ascii=False))
# moved to organisations.py: (OUT / "organisations.json").write_text(json.dumps(orgs, indent=1, ensure_ascii=False))
with open(OUT / "concerts.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["date", "start", "end", "slot", "main_artist", "main_instrument", "concert_type",
                "accompanists", "entry", "organisation", "festival", "area", "venue", "source_url", "fetched"])
    for c in concerts:
        acc = "; ".join(f"{p['name']} ({p['instrument']})" for p in c["performers"] if p["role"] == "accompanist")
        w.writerow([c["date"], c["start"], c["end"], c["slot"], c["main_artist"], c["main_instrument"],
                    c["concert_type"], acc, c["entry"], c["organisation"], c["festival"], c["area"], c["venue"],
                    c["source_url"], c["fetched"]])

print(len(concerts), "concerts;", len(orgs), "organisations")
from collections import Counter
print(Counter(c["concert_type"] for c in concerts))
print(Counter(c["main_instrument"] for c in concerts))
for c in concerts[:3] + [x for x in concerts if "Nagaswaram" in x["main_instrument"]][:1]:
    print(c["date"], c["start"], c["main_artist"], "|", c["main_instrument"], "|",
          [p["name"] for p in c["performers"] if p["role"] == "accompanist"])

"""Master list of Chennai Margazhi-season Carnatic organisers, with 2026-27 status.

Only definite organisations / sabhas belong here. Concerts whose source names no organiser use
organisation = "Organiser not stated"; that label is NOT an organisation and is not listed.

Status values: "Schedule published", "Dates announced", "Awaiting 2026–27 schedule".
Writes data/organisations.json. Names for published organisers must match concerts.json.
"""
import json
from pathlib import Path

PUB, ANN, AW = "Schedule published", "Dates announced", "Awaiting 2026–27 schedule"
MAJOR, OTHER, FEST = "Major sabha", "Other sabha", "Festival / arts organisation"

# name, group, status, area, venue, 2026-27 festival + dates, note, url
ORGS = [
    ("The Music Academy, Madras", MAJOR, PUB, "Alwarpet / TTK Road", "Music Academy Auditorium, 168 TTK Road",
     "100th Annual Concerts · 15 Dec 2026 – 1 Jan 2027", "Conference sessions daily 8–10 am; dance festival 3–9 Jan 2027.",
     "https://musicacademymadras.in/100th-annual-concerts-2026/"),
    ("Bharat Kalachar", MAJOR, PUB, "T. Nagar", "Sri YGP Auditorium, 17 Thirumalai Road",
     "38th Marghazhi Mahotsav · 13 Dec 2026 – 17 Jan 2027", "Advance booking at venue from 7 Dec 2026.",
     "https://www.bharatkalachar.com/38-bharat-kalachar.html"),
    ("Kartik Fine Arts", MAJOR, ANN, "Alwarpet / TTK Road", "Narada Gana Sabha, TTK Road",
     "December Season festival · from 1 Dec 2026", "Concert list not yet published.",
     "https://www.mylaporetimes.com/2026/10/december-season-2026-narada-gana-sabha-is-improving-its-audio-systems/"),
    ("Narada Gana Sabha", MAJOR, ANN, "Alwarpet / TTK Road", "TTK Road, Teynampet",
     "December Season 2026 · from 1 Dec 2026", "Top-billed concerts to start by 3.30 pm. Concert list not yet published.",
     "https://www.mylaporetimes.com/2026/10/december-season-2026-narada-gana-sabha-is-improving-its-audio-systems/"),
    ("Sri Krishna Gana Sabha", MAJOR, AW, "T. Nagar", "20 Maharajapuram Santhanam Salai", "", "Only its dance Natya Kala Conference (26–28 Dec) is announced.", "https://www.krishnaganasabha.org/"),
    ("Sri Thyaga Brahma Gana Sabha", MAJOR, AW, "T. Nagar", "Vani Mahal, G.N. Road", "", "", "https://www.vanimahal.com/"),
    ("Brahma Gana Sabha", MAJOR, AW, "Mylapore", "Sivagami Pethachi Auditorium", "", "", ""),
    ("Mylapore Fine Arts Club", MAJOR, AW, "Mylapore", "45 Musiri Subramaniam Road", "", "", ""),
    ("Sri Parthasarathy Swami Sabha", MAJOR, AW, "Mylapore", "Vidya Bharathi, Bheemasena Garden Road", "", "", "https://parthasarathyswamisabha.com/"),
    ("The Indian Fine Arts Society", MAJOR, AW, "Alwarpet / TTK Road", "Ethiraja Kalyana Nilayam, TTK Road", "", "", ""),
    ("Rasika Ranjani Sabha", MAJOR, AW, "Mylapore", "Dakshinamoorthy Auditorium", "", "", "https://rrsabha.org/"),
    ("Bharatiya Vidya Bhavan, Chennai Kendra", MAJOR, AW, "Mylapore", "East Mada Street", "", "Its festival usually opens the season in late November.", ""),
    ("Tamil Isai Sangam", MAJOR, AW, "George Town", "Rajah Annamalai Mandram, Esplanade Road", "", "", ""),
    ("Hamsadhwani", MAJOR, AW, "", "", "", "", ""),
    ("Asthika Samajam", MAJOR, AW, "Alwarpet", "Venus Colony", "", "", ""),
    ("Chromepet Cultural Academy", OTHER, AW, "Chromepet", "", "", "Margazhi Festival.", ""),
    ("Thrimoorthi Sangeetha Sabha", OTHER, AW, "", "", "", "", ""),
    ("Sri Krishna Fine Arts Society", OTHER, AW, "Nanganallur", "", "", "", ""),
    ("Meenakshi Sundararajan Fine Arts Academy", OTHER, AW, "", "", "", "", ""),
    ("Music Education Trust", OTHER, AW, "", "", "", "", ""),
    ("Shri Purandaradaasar Trust", OTHER, AW, "", "", "", "Music festival.", ""),
    ("Sampoornam Foundation for Music and Arts", FEST, AW, "Mylapore", "Arkay Convention Centre", "", "Margazhi Music Festival.", ""),
    ("Naadhabrahmam", FEST, AW, "Mylapore", "Srinivasa Sastri Hall, Luz", "", "Sangeetha Raga Mahothsavam.", ""),
    ("Trinity Arts", FEST, AW, "", "", "", "Trinity Arts Festival.", ""),
    ("Parampara", FEST, AW, "", "", "", "Ragasudharasa Music Festival series.", ""),
    ("Parivadini", FEST, AW, "", "", "", "Concert series, also recorded online.", ""),
    ("Maha Periyava Anusham Trust", FEST, AW, "Mylapore", "Mylai Maha-periyava Temple, Pichupillai Street", "", "Margazhi Sangeetha Upasana early-morning concerts, with Mani Mohanam Academy.", ""),
    ("SciArtsRUs", FEST, AW, "Mylapore", "Bharatiya Vidya Bhavan; P.S. High School; IIT Madras", "", "Margazhi Matram festival.", ""),
    ("Bharat Sangeet Utsav", FEST, AW, "Alwarpet / TTK Road", "Narada Gana Sabha", "", "Held in early November, before Margazhi. Organiser name not found; listed under the festival name.", ""),
    ("Sruti Foundation & The Music Forum", FEST, AW, "Mylapore", "Bharatiya Vidya Bhavan Mini Hall", "", "LecDem Mela (lecture-demonstrations).", ""),
    ("Neelakanta Sivan Cultural Academy", OTHER, AW, "Sholinganallur", "", "", "Runs the Neelakanta Sivan School of Art and Culture. 2026–27 dates not yet found online.", ""),
    ("Kapali Fine Arts", OTHER, AW, "Mylapore", "", "", "", ""),
    ("Nungambakkam Cultural Academy", OTHER, AW, "Nungambakkam", "", "", "", ""),
    ("Kalarasana", OTHER, AW, "", "", "", "", ""),
    ("Nadopasana", OTHER, AW, "", "", "", "", ""),
    ("Sri Rama Bhaktha Jana Samaj", OTHER, AW, "", "", "", "", ""),
    ("Nandi Fine Arts", OTHER, AW, "", "", "", "", ""),
    ("Perambur Sangeetha Sabha", OTHER, AW, "Perambur", "", "", "", ""),
    ("Sat Sangam Sabha", OTHER, AW, "Madipakkam", "", "", "", ""),
    ("Chennai Cultural Academy Trust", OTHER, AW, "", "", "", "", ""),
    ("Naada Inbam", FEST, AW, "Mylapore", "Ragasudha Hall, Luz Avenue", "", "", ""),
    ("Charsur Arts Foundation", FEST, AW, "Mylapore", "Sri Ramanujar Millennium Hall, D'Silva Road", "", "", ""),
    ("Chennai Fine Arts", FEST, AW, "", "", "", "", ""),
    ("Madhuradhwani", FEST, AW, "Mylapore", "Arkay Convention Centre", "", "ACC Anniversary festival.", ""),
    ("Sunaadalahari", FEST, AW, "Abhiramapuram", "Indira Ranganathan Trust, 52 C.P. Ramaswamy Road", "", "Garden-setting concerts.", ""),
    ("Carnatica", FEST, AW, "Mylapore", "Desiga Vidya Bhavanam (Paddhathi Music Fest)", "", "Also runs the Global Heritage Music Fest.", "https://carnatica.net/"),
    ("MDnD", FEST, AW, "Mylapore", "MDnD Performance Centre, Luz Church Road", "", "Anandha Margazhi; also sells season tickets for many sabhas.", "https://www.mdnd.in/seasontickets"),
    ("Nada Sudha", FEST, AW, "Velachery", "Sri Ganapathy Sachchidananda Ashram", "", "", ""),
    ("Sruthi Laya Kendra", FEST, AW, "Mylapore", "Bharatiya Vidya Bhavan Mini Hall", "", "Winter Music Festival.", ""),
    ("Gayatri Fine Arts Global", FEST, AW, "Mylapore", "Sri Krishna Saras Hall, P.S. Sivaswamy Salai", "", "", ""),
    ("Shakthi Sangita Sabha", FEST, AW, "Valasaravakkam", "Anbu Nagar", "", "", ""),
    ("SASTRA Satsangh", FEST, AW, "", "", "", "Margazhi Mela.", ""),
    ("TTVV Trust & Cleveland Thyagaraja Festival", FEST, AW, "Teynampet", "Tattvaloka Hall, Eldams Road", "", "Margazhi Mela.", ""),
    ("VVS Foundation & SaMaa Arts", FEST, AW, "Mylapore", "Raghavendra Swami Mutt, Salai Street", "", "Swagatham and Ekaantha Sangeetha Seva festivals.", ""),
    ("Kauvery Margazhi Maha Utsavam", FEST, AW, "", "", "", "Organiser name not found; listed under the festival name.", ""),
    ("Lalitha Jewellery", FEST, AW, "Valasaravakkam", "Jyothi Indira Thirumana Mandapam", "", "Runs the Jyothi Indira Margazhi Yuvautsav.", ""),
    ("Lakshman Sruthi", FEST, AW, "", "", "", "Runs the Chennaiyil Thiruvaiyaru festival.", ""),
    ("Chennaiyil Sangeeth Utsav", FEST, AW, "Neelankarai", "AMRK Banquet Hall", "", "Organiser name not found; listed under the festival name.", ""),
    ("RASOHAM", FEST, AW, "", "Multiple venues", "", "Runs the Kutty Kutchery Festival.", "https://rasoham.org/"),
    ("Medai The Stage", FEST, AW, "Alwarpet", "1st Cross St, Co-operative Colony", "", "", ""),
    ("Triplicane Music Festival", FEST, AW, "Triplicane", "NKT Muthu Hall", "", "Organiser name not found; listed under the festival name.", ""),
    ("TAPAS", FEST, AW, "", "", "", "Runs the TAPAS Music and Dance Festival.", ""),
]

PART = "Some dates via artists' websites"
ORGS += [
    ("Mudhra", OTHER, PART, "T. Nagar", "Sri Thyaga Brahma Gana Sabha (Vani Mahal)", "", "Date found on Shashank's website.", ""),
    ("Sanjay Subrahmanyan", FEST, PART, "", "Muthamizh Peravai; Asian College of Journalism", "", "Presents his own Sanjay Sabha Live concert series.", "https://sanjaysub.com/"),
]
# organisers whose individual dates appear on artists' websites, before their own schedule is out
for i, row in enumerate(ORGS):
    if row[0] in {"Brahma Gana Sabha", "Sruthi Laya Kendra", "Sri Parthasarathy Swami Sabha"}:
        ORGS[i] = row[:2] + (PART,) + row[3:6] + ("Own schedule not yet published; dates found on artists' websites.",) + row[7:]
out = [dict(name=n, group=g, status=s, area=a, venue=v, festival_2026=f, note=note, url=u)
       for n, g, s, a, v, f, note, u in ORGS]
assert len({o["name"] for o in out}) == len(out), "duplicate organisation"
Path(__file__).parent.joinpath("data/organisations.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
print(len(out), "organisations:", {s: sum(o["status"] == s for o in out) for s in (PUB, ANN, AW)})

# Margazhi 2026–27 Carnatic concert repository

**Public site:** https://kutcheri-dec.netlify.app — hosted on Netlify, which redeploys automatically on every push to `main` (settings in `netlify.toml`: publish the repo root, no build step). Backup copy: https://sunithi2000-lab.github.io/kutcheri/ (GitHub Pages, same `index.html`). Anyone can open either without signing in. Favourites are saved in each visitor's own browser.

Current-season (2026–27) Chennai Carnatic concerts only, from organisers' and artists' public listings.
Live page: **Margazhi Concert List 2026–27** — https://claude.ai/artifact/LT7DXaZZFwqiqWTc8gs7Nw

## Files (all in this project folder `margazhi-data/`)
| File | Purpose |
|---|---|
| `raw_music_academy_2026.txt` | Music Academy 100th Annual Concerts, one concert per line |
| `raw_bharat_kalachar_2026.txt` | Bharat Kalachar 38th Marghazhi Mahotsav (Carnatic music only) |
| `raw_artist_sites_2026.txt` | Concerts found on artists' websites / listings, not in any organiser schedule |
| `build_data.py` | Raw files → `data/concerts.json` + `data/concerts.csv` |
| `organisations.py` | Master list of 50 organisers with 2026–27 status → `data/organisations.json` |
| `list_template.html` + `build_list.py` | Embed the data in the concert list page → `margazhi-concert-list.html` |
| `concerts_2026-27.csv`, `organisations_2026-27.json` | Latest built outputs |
| `UPDATE_LOG.md` | One line per daily update run |
| `BACKLOG.md` | Planned features |

## Rebuild
Put all files in one folder with a `data/` subfolder, then:
`python3 build_data.py && python3 organisations.py && python3 build_list.py && node --check _check.js`

## Rules for adding concerts
- Only 2026–27 season dates (15 Nov 2026 – 31 Jan 2027) in Chennai. No past seasons.
- Carnatic music only: vocal and instrumental concerts incl. nagaswaram. Exclude dance, drama, harikatha/discourse, fusion, film/light music, inaugurations and awards.
- Organiser schedules: add a `raw_<sabha>_2026.txt` file and a parser block in `build_data.py` (copy the Music Academy pattern if the page lists accompanists, the Bharat Kalachar pattern if it lists main artists only).
- Artist sites and other listings: add lines to `raw_artist_sites_2026.txt`. Use "Organiser not stated" when the source names no organiser; never assume the venue's sabha.
- Skip a concert already present (same date, start time and main artist).
- Every organisation used must exist in `organisations.py`; update its status when its schedule is published.
- A changed or cancelled concert: edit or remove its line, and note it in `UPDATE_LOG.md`.

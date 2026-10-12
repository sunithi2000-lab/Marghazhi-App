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
| `organisations.py` | Master list of organisers / sabhas with 2026–27 status → `data/organisations.json` |
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
- Every organisation used must exist in `organisations.py`; update its status when its schedule is published. `organisations.py` lists only definite organisations / sabhas (it feeds the Sabhas tab and the sabha filter). "Organiser not stated" is a label on concerts, not an organisation, and must not be added there.
- Daily: review every organisation in `organisations.py`, one by one, for a new or changed 2026–27 schedule; also try to find the real organiser of each "Organiser not stated" concert.
- A changed or cancelled concert: edit or remove its line, and note it in `UPDATE_LOG.md`.

## Health checks and error reporting
- `tests/check_data.py` — data rules (fields, dates in season, times, duplicates, organisations, no sudden drop of more than 20% versus the live site). **Netlify runs it before every deploy**: if it fails, the deploy stops and the previous site stays live. To allow an intended big change once (e.g. new season), add an empty file `tests/ALLOW_BIG_CHANGE` and delete it afterwards.
- `tests/check_page.py` — opens the page in headless Chrome at phone size (light and dark, large text) and uses it: list, search, date strip, calendar, My plan, Sabhas tab, pinned strip, no overlapping times, no JavaScript errors, error capture.
- `tests/check_live.py` — website and GitHub Pages backup load; live data equals the repo (deploy succeeded); the Android app's download header (CORS) is present; the morning update ran within 36 h (14 Oct 2026 – 31 Jan 2027).
- `.github/workflows/health.yml` runs all three after every push and every 6 hours. On failure it opens or updates an issue labelled **health-check** (assigned to the owner, so GitHub emails and notifies) and fails the run; when checks pass again it closes the issue.
- `data/status.json` is written by every build (`build_list.py`) as a heartbeat. The morning job must push it every day, even when no concert changed.
- Error reporting: the page catches JavaScript errors (from the very start of loading) and sends up to 5 per visit to GoatCounter as events named `web error: …` / `app error: …` — see the Events list at https://kutcheri.goatcounter.com.

## Contributions (Netlify Forms)
- Two forms on the page: **Add a missing concert** (`missing-concert`; under the concert list and in the Sabhas tab) and **Send your schedule** for organisers (`organiser-schedule`; Sabhas tab). Both accept a link and a photo/PDF (up to 8 MB). They are shown on the public sites and in the app, which posts to the Netlify site; hidden in previews (force with `?forms=1`).
- Netlify detects the forms from `index.html` at deploy (Forms must stay enabled in Netlify). Submissions appear in Netlify → kutcheri-dec → Forms, and are emailed to the owner (Netlify → Project configuration → Notifications → Form submission notifications).
- Every report is verified against a public source before it is added (README rules). Spam is filtered by a honeypot field and Netlify's filter. Free tier: 100 submissions / 10 MB uploads a month.

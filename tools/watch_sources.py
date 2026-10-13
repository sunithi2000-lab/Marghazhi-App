"""Daily source watcher: open every page in sources/sources.json in a real (headless) browser,
save its visible text, read linked PDF schedules, and report what changed since the last run.

Runs on GitHub Actions (.github/workflows/watch.yml), which can reach sites the morning research
session cannot (JavaScript-only pages, sites that block simple fetching, "Load More" buttons, PDFs).
Outputs (committed, then served at https://kutcheri-dec.netlify.app/sources/...):
  sources/text/<slug>.txt   visible text of each page (+ linked PDF text), normalised
  sources/CHANGES.md        today's report: changed pages with added lines, failures, season keywords
  sources/status.json       per-source result (ok / changed / failed, length, error)
Needs: pip install playwright pypdf && python -m playwright install --with-deps chromium
"""
import difflib
import io
import json
import re
import sys
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright

R = Path(__file__).resolve().parent.parent
S = R / "sources"
TXT = S / "text"
TXT.mkdir(parents=True, exist_ok=True)
cfg = json.loads((S / "sources.json").read_text())["sources"]
UA = "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Mobile Safari/537.36 KutcheriPlannerWatcher/1.0 (+https://kutcheri-dec.netlify.app)"
SEASON = re.compile(r"(2026|2027|december|margazhi|marghazhi|season|kutcheri|concert)", re.I)
MAX_PDFS, MAX_PDF_BYTES = 4, 8_000_000


def norm(text):
    lines = [re.sub(r"[ \t ]+", " ", ln).strip() for ln in text.splitlines()]
    out, prev = [], None
    for ln in lines:
        if ln and ln != prev:
            out.append(ln)
        prev = ln
    return "\n".join(out)


def pdf_text(data):
    try:
        from pypdf import PdfReader
        r = PdfReader(io.BytesIO(data))
        return "\n".join((p.extract_text() or "") for p in r.pages[:40])
    except Exception as e:  # noqa: BLE001
        return f"[PDF could not be read: {e}]"


now = datetime.now(timezone.utc)
status, report_changed, report_failed, report_new = {}, [], [], []

with sync_playwright() as p:
    b = p.chromium.launch()
    # ignore_https_errors: several sabha and artist sites have expired certificates; we only read public text
    ctx = b.new_context(user_agent=UA, viewport={"width": 412, "height": 900}, locale="en-IN", ignore_https_errors=True)
    for src in cfg:
        slug, url = src["slug"], src["url"]
        st = {"url": url, "kind": src.get("kind", ""), "checked": now.strftime("%Y-%m-%dT%H:%MZ")}
        pg = ctx.new_page()
        try:
            resp = pg.goto(url, wait_until="domcontentloaded", timeout=45000)
            try:
                pg.wait_for_load_state("networkidle", timeout=15000)
            except Exception:  # noqa: BLE001
                pass
            pg.wait_for_timeout(src.get("wait_ms", 2500))  # let late scripts fill the page
            for label in src.get("click", []):
                for _ in range(6):  # press "Load More" until it disappears
                    btn = pg.get_by_text(label, exact=False)
                    if btn.count() == 0 or not btn.first.is_visible():
                        break
                    btn.first.click(timeout=5000)
                    pg.wait_for_timeout(1500)
            code = resp.status if resp else 0
            text = pg.evaluate("document.body ? document.body.innerText : ''")
            pdfs = []
            if src.get("follow_pdfs"):
                hrefs = pg.evaluate("[...document.querySelectorAll('a[href]')].map(a => a.href)")
                pdfs = [h for h in dict.fromkeys(hrefs) if h.lower().split("?")[0].endswith(".pdf")][:MAX_PDFS]
                for h in pdfs:
                    try:
                        r = ctx.request.get(h, timeout=45000)
                        body = r.body()
                        if r.ok and len(body) <= MAX_PDF_BYTES:
                            text += f"\n\n===== PDF: {h} =====\n" + pdf_text(body)
                        else:
                            text += f"\n\n===== PDF: {h} ===== [skipped: status {r.status}, {len(body)} bytes]"
                    except Exception as e:  # noqa: BLE001
                        text += f"\n\n===== PDF: {h} ===== [error: {e}]"
            text = norm(text)
            if code >= 400 or len(text) < 40:
                raise RuntimeError(f"HTTP {code}, {len(text)} characters of text")
            f = TXT / f"{slug}.txt"
            old = f.read_text() if f.exists() else None
            f.write_text(f"# {url}\n# fetched {st['checked']}\n{text}\n")
            st.update(result="ok", chars=len(text), pdfs=len(pdfs))
            if old is None:
                st["result"] = "new"
                report_new.append((src, text))
            else:
                old_body = "\n".join(old.splitlines()[2:])
                if old_body.strip() != text.strip():
                    diff = [ln for ln in difflib.unified_diff(old_body.splitlines(), text.splitlines(), lineterm="", n=0)
                            if ln[:1] in "+-" and not ln.startswith(("+++", "---"))]
                    added = [ln[1:] for ln in diff if ln.startswith("+")]
                    removed = [ln[1:] for ln in diff if ln.startswith("-")]
                    st.update(result="changed", added=len(added), removed=len(removed))
                    report_changed.append((src, added, removed))
        except Exception as e:  # noqa: BLE001
            msg = (str(e).strip().splitlines() or ["error"])[0][:200]
            st.update(result="failed", error=msg)
            report_failed.append((src, msg))
        finally:
            pg.close()
        status[slug] = st
        print(f"{st['result']:8} {slug}")
    b.close()

(S / "status.json").write_text(json.dumps({"run": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "sources": status}, indent=1) + "\n")


def season_mark(line):
    return " **[season]**" if SEASON.search(line) else ""


md = [f"# Source watcher — {now:%Y-%m-%d %H:%M} UTC",
      "",
      f"{len(cfg)} sources checked: {len(report_changed)} changed, {len(report_new)} new, {len(report_failed)} failed, "
      f"{len(cfg) - len(report_changed) - len(report_new) - len(report_failed)} unchanged.",
      "Full page text for every source: `sources/text/<slug>.txt` (https://kutcheri-dec.netlify.app/sources/text/<slug>.txt).",
      "Lines marked **[season]** mention 2026/2027, December, Margazhi, season, kutcheri or concert.", ""]
if report_changed:
    md += ["## Changed since the last run", ""]
    for src, added, removed in report_changed:
        md += [f"### {src['slug']} ({src.get('kind', '')}) — {src['url']}",
               f"{len(added)} line(s) added, {len(removed)} removed. Full text: sources/text/{src['slug']}.txt", ""]
        for ln in added[:40]:
            md.append(f"- + {ln[:240]}{season_mark(ln)}")
        if len(added) > 40:
            md.append(f"- … {len(added) - 40} more added lines")
        for ln in removed[:10]:
            md.append(f"- − {ln[:240]}")
        md.append("")
if report_new:
    md += ["## Newly watched (first snapshot)", ""]
    for src, text in report_new:
        hits = [ln for ln in text.splitlines() if re.search(r"2026|2027", ln) and SEASON.search(ln)][:8]
        md.append(f"- **{src['slug']}** — {src['url']} ({len(text)} chars)" + ("".join(f"\n  - {h[:200]}" for h in hits)))
    md.append("")
if report_failed:
    md += ["## Could not be read (check by web search instead)", ""]
    md += [f"- **{src['slug']}** — {src['url']}: {err}" for src, err in report_failed]
    md.append("")
(S / "CHANGES.md").write_text("\n".join(md) + "\n")
print(f"done: {len(report_changed)} changed, {len(report_new)} new, {len(report_failed)} failed")

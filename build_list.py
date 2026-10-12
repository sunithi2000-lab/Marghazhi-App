"""Build the concert app from data/ + list_template.html.

Writes:
  margazhi-concert-list.html  - body-only version for the Claude artifact page (the artifact adds its own <head>)
  index.html                  - full HTML document for GitHub Pages (doctype, phone viewport, home-screen app tags)
  manifest.webmanifest, icon.svg - let phones "Add to Home Screen" as an app
  _check.js                   - the page script, for `node --check _check.js`
"""
import json, re
from pathlib import Path

R = Path(__file__).parent
c = json.loads((R / "data/concerts.json").read_text())
o = json.loads((R / "data/organisations.json").read_text())
missing = {x["organisation"] for x in c} - {x["name"] for x in o}
assert not missing, f"organisations missing from organisations.py: {missing}"
j = lambda d: json.dumps(d, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
t = (R / "list_template.html").read_text().replace("/*__CONCERTS__*/[]", j(c)).replace("/*__ORGS__*/[]", j(o))
(R / "margazhi-concert-list.html").write_text(t)

head, body = t.split("</style>", 1)
doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#0E6A57">
<meta name="description" content="Carnatic concerts in Chennai for the 2026–27 Margazhi season: search artists, filter by date, sabha and area, and plan your day.">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="Kutcheri">
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" href="icon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="icon.svg">
{head}</style>
</head>
<body>
{body}
</body>
</html>
"""
(R / "index.html").write_text(doc)

(R / "manifest.webmanifest").write_text(json.dumps({
    "name": "Margazhi Kutcheri 2026–27", "short_name": "Kutcheri",
    "description": "Chennai Margazhi season Carnatic concerts",
    "start_url": "./", "scope": "./", "display": "standalone",
    "background_color": "#F6F7F3", "theme_color": "#0E6A57",
    "icons": [{"src": "icon.svg", "sizes": "any", "type": "image/svg+xml", "purpose": "any"}],
}, ensure_ascii=False, indent=1))

(R / "icon.svg").write_text("""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
<rect width="512" height="512" rx="112" fill="#0E6A57"/>
<circle cx="256" cy="330" r="104" fill="none" stroke="#E2AE4E" stroke-width="28"/>
<path d="M256 226V88" stroke="#E2AE4E" stroke-width="28" stroke-linecap="round"/>
<path d="M226 104h60M226 148h60" stroke="#F6F7F3" stroke-width="16" stroke-linecap="round"/>
<circle cx="256" cy="330" r="22" fill="#F6F7F3"/>
</svg>
""")

(R / "_check.js").write_text(re.search(r"<script>(.*)</script>", t, re.S).group(1))
print(f"{len(c)} concerts, {len(o)} organisations -> margazhi-concert-list.html, index.html; run: node --check _check.js")

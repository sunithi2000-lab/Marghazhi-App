"""Build the concert app from data/ + list_template.html.

Writes:
  margazhi-concert-list.html  - body-only version for the Claude artifact page (the artifact adds its own <head>)
  index.html                  - full HTML document for GitHub Pages (doctype, phone viewport, home-screen app tags)
  manifest.webmanifest, icon.svg (+ committed icon-192/512.png, apple-touch-icon.png) - let phones "Add to Home Screen" as an app
  _check.js                   - the page script, for `node --check _check.js`
  data/status.json            - when this build ran (checked by tests/check_live.py)
"""
import json, re
from pathlib import Path

R = Path(__file__).parent
c = json.loads((R / "data/concerts.json").read_text())
o = json.loads((R / "data/organisations.json").read_text())
missing = {x["organisation"] for x in c} - {x["name"] for x in o} - {"Organiser not stated"}  # label, not an organisation
assert not missing, f"organisations missing from organisations.py: {missing}"
j = lambda d: json.dumps(d, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
t = (R / "list_template.html").read_text().replace("/*__CONCERTS__*/[]", j(c)).replace("/*__ORGS__*/[]", j(o))
(R / "margazhi-concert-list.html").write_text(t)

# heartbeat: when this build ran; the health checks alert if it gets old during the season
from datetime import datetime, timezone
(R / "data/status.json").write_text(json.dumps({
    "built_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "concerts": len(c), "organisations": len(o)}, indent=1) + "\n")

head, body = t.split("</style>", 1)
doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#F39C1E">
<meta name="description" content="Carnatic concerts in Chennai for the 2026–27 Margazhi season: search artists, filter by date, sabha and area, and plan your day.">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="Kutcheri Planner">
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" href="icon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
{head}</style>
</head>
<body>
{body}
</body>
</html>
"""
(R / "index.html").write_text(doc)

(R / "manifest.webmanifest").write_text(json.dumps({
    "name": "Marghazhi Kutcheri Planner", "short_name": "Kutcheri Planner",
    "description": "Chennai Margazhi season Carnatic concerts",
    "start_url": "./", "scope": "./", "display": "standalone",
    "background_color": "#F39C1E", "theme_color": "#F39C1E",
    "icons": [{"src": "icon.svg", "sizes": "any", "type": "image/svg+xml", "purpose": "any"},
              {"src": "icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any maskable"},
              {"src": "icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"}],
}, ensure_ascii=False, indent=1))

(R / "icon.svg").write_text("""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"><rect width="512" height="512" rx="112" fill="#F39C1E"/><g transform="translate(256,256) scale(0.9090909090909091) translate(-262,-256)"><g fill="#5A1212">
<ellipse cx="168" cy="368" rx="64" ry="46" transform="rotate(-22 168 368)"/>
<ellipse cx="356" cy="328" rx="64" ry="46" transform="rotate(-22 356 328)"/>
<rect x="208" y="140" width="24" height="222" rx="4"/>
<rect x="396" y="100" width="24" height="222" rx="4"/>
<polygon points="208,132 420,88 420,146 208,190"/>
</g></g></svg>
""")

(R / "_check.js").write_text(re.search(r"<script>\n(.*)</script>", t, re.S).group(1))
print(f"{len(c)} concerts, {len(o)} organisations -> margazhi-concert-list.html, index.html; run: node --check _check.js")

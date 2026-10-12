"""Inject data/concerts.json and data/organisations.json into list_template.html -> margazhi-concert-list.html"""
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
(R / "index.html").write_text(t)  # GitHub Pages entry point
(R / "_check.js").write_text(re.search(r"<script>(.*)</script>", t, re.S).group(1))
print(f"{len(c)} concerts, {len(o)} organisations -> margazhi-concert-list.html; run: node --check _check.js")

import os
import datetime
import json
import urllib.request

USER = os.environ.get("GH_USER", "ncrod7")
TOKEN = os.environ["GITHUB_TOKEN"]
today = datetime.date.today()
year = today.year
start = datetime.date(year, 1, 1)

QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""

payload = json.dumps({
    "query": QUERY,
    "variables": {
        "login": USER,
        "from": f"{start}T00:00:00Z",
        "to": f"{today}T23:59:59Z",
    },
}).encode()

req = urllib.request.Request(
    "https://api.github.com/graphql",
    data=payload,
    headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"},
)
with urllib.request.urlopen(req) as r:
    data = json.load(r)

weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
counts = {
    datetime.date.fromisoformat(d["date"]): d["contributionCount"]
    for w in weeks for d in w["contributionDays"]
}

days = sorted(d for d in counts if d <= today)

# Racha más larga del año
longest = cur = 0
longest_end = None
for d in days:
    if counts[d] > 0:
        cur += 1
        if cur > longest:
            longest, longest_end = cur, d
    else:
        cur = 0

# Racha actual: si hoy aún no tiene contribuciones, cuenta desde ayer
check = today if counts.get(today, 0) > 0 else today - datetime.timedelta(days=1)
current = 0
d = check
while counts.get(d, 0) > 0:
    current += 1
    d -= datetime.timedelta(days=1)

total_days = sum(1 for d in days if counts[d] > 0)

svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="420" height="160" viewBox="0 0 420 160">
  <rect width="420" height="160" rx="10" fill="#0e1013"/>
  <text x="210" y="30" text-anchor="middle" font-family="Segoe UI, Ubuntu, sans-serif" font-size="16" fill="#8394ff">Racha {year}</text>
  <text x="105" y="90" text-anchor="middle" font-family="Segoe UI, Ubuntu, sans-serif" font-size="34" font-weight="700" fill="#eceef1">{current}</text>
  <text x="105" y="115" text-anchor="middle" font-family="Segoe UI, Ubuntu, sans-serif" font-size="13" fill="#959ba6">actual</text>
  <text x="315" y="90" text-anchor="middle" font-family="Segoe UI, Ubuntu, sans-serif" font-size="34" font-weight="700" fill="#eceef1">{longest}</text>
  <text x="315" y="115" text-anchor="middle" font-family="Segoe UI, Ubuntu, sans-serif" font-size="13" fill="#959ba6">más larga</text>
  <text x="210" y="145" text-anchor="middle" font-family="Segoe UI, Ubuntu, sans-serif" font-size="12" fill="#959ba6">{total_days} días con actividad</text>
</svg>
"""

with open("streak-2026.svg", "w", encoding="utf-8") as f:
    f.write(svg)

MONTHS = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
SHADES = ["#1b1d22", "#1e2766", "#2a3db5", "#3653f5", "#8394ff"]
peak = max(counts.values(), default=0) or 1
total = sum(counts.values())
cell, x0, y0 = 13, 40, 62
cols = len(weeks)
width = x0 + cols * cell + 24
cells, labels, last_month = [], [], None
for c, w in enumerate(weeks):
    for d in w["contributionDays"]:
        day = datetime.date.fromisoformat(d["date"])
        if day > today:
            continue
        n = d["contributionCount"]
        level = 0 if n == 0 else min(4, 1 + 4 * (n - 1) // peak)
        cells.append(
            f'<rect x="{x0 + c * cell}" y="{y0 + day.isoweekday() % 7 * cell}" width="10" height="10" rx="2" '
            f'fill="{SHADES[level]}" style="animation-delay:{c * 0.025:.3f}s"><title>{day}: {n}</title></rect>'
        )
        if day.day <= 7 and day.month != last_month:
            last_month = day.month
            labels.append(f'<text x="{x0 + c * cell}" y="{y0 - 10}">{MONTHS[day.month - 1]}</text>')

legend_x = width - 54 - 5 * cell
heatmap = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="190" viewBox="0 0 {width} 190" role="img" aria-label="{total} contribuciones en {year}">
  <style>
    text{{font-family:'JetBrains Mono',ui-monospace,Consolas,monospace;font-size:11px;fill:#959ba6}}
    rect[style]{{opacity:0;animation:in .4s ease forwards}}
    @keyframes in{{to{{opacity:1}}}}
    @media (prefers-reduced-motion:reduce){{rect[style]{{animation:none;opacity:1}}}}
  </style>
  <rect width="{width}" height="190" rx="10" fill="#0e1013"/>
  <text x="{x0}" y="28" style="font-size:13px;fill:#eceef1">// {total} contribuciones en {year}</text>
  {''.join(labels)}
  {''.join(cells)}
  <text x="{legend_x - 46}" y="{y0 + 7 * cell + 21}">menos</text>
  {''.join(f'<rect x="{legend_x + i * cell}" y="{y0 + 7 * cell + 12}" width="10" height="10" rx="2" fill="{s}"/>' for i, s in enumerate(SHADES))}
  <text x="{legend_x + 5 * cell + 4}" y="{y0 + 7 * cell + 21}">más</text>
</svg>
"""
with open("contrib-2026.svg", "w", encoding="utf-8") as f:
    f.write(heatmap)

print(f"actual={current} más_larga={longest} días_activos={total_days}")

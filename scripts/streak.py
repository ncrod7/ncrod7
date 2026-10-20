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
  <rect width="420" height="160" rx="0" fill="#fcfcfa" stroke="#fcfcfa"/>
  <text x="210" y="30" text-anchor="middle" font-family="Segoe UI, Ubuntu, sans-serif" font-size="16" fill="#e23726">Racha {year}</text>
  <text x="105" y="90" text-anchor="middle" font-family="Segoe UI, Ubuntu, sans-serif" font-size="34" font-weight="700" fill="#0e0f12">{current}</text>
  <text x="105" y="115" text-anchor="middle" font-family="Segoe UI, Ubuntu, sans-serif" font-size="13" fill="#6b6b6b">actual</text>
  <text x="315" y="90" text-anchor="middle" font-family="Segoe UI, Ubuntu, sans-serif" font-size="34" font-weight="700" fill="#0e0f12">{longest}</text>
  <text x="315" y="115" text-anchor="middle" font-family="Segoe UI, Ubuntu, sans-serif" font-size="13" fill="#6b6b6b">más larga</text>
  <text x="210" y="145" text-anchor="middle" font-family="Segoe UI, Ubuntu, sans-serif" font-size="12" fill="#6b6b6b">{total_days} días con actividad</text>
</svg>
"""

with open("streak-2026.svg", "w", encoding="utf-8") as f:
    f.write(svg)

print(f"actual={current} más_larga={longest} días_activos={total_days}")

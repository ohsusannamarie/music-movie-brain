#!/usr/bin/env python3
"""Weekly refresh for Susanna's Music Movie Brain.
Pulls US streaming for every tracked title, new music releases and the release radar from TMDB,
diffs against last week's snapshot, and writes fresh.js for the page.
Usage: python3 refresh.py --key KEY --tracked tracked.json --prev fresh.js|base.json --out fresh.js
"""
import json, re, sys, argparse, subprocess, datetime, concurrent.futures as cf

ap = argparse.ArgumentParser()
ap.add_argument('--key', required=True)
ap.add_argument('--tracked', required=True)
ap.add_argument('--prev', required=True)
ap.add_argument('--out', required=True)
ap.add_argument('--today', default=datetime.date.today().isoformat())
ap.add_argument('--mine', default='Prime Video,Prime Video (free),HBO Max,Netflix,Hulu,Disney+,YouTube Premium,YouTube (free)')
a = ap.parse_args()
B = "https://api.themoviedb.org/3"
TODAY = datetime.date.fromisoformat(a.today)
MINE = set(a.mine.split(','))

def get(path, q=""):
    for _ in range(4):
        r = subprocess.run(["curl", "-sS", "-m", "30", f"{B}{path}?api_key={a.key}{q}"], capture_output=True, text=True)
        try:
            d = json.loads(r.stdout)
            if 'status_code' in d and d.get('success') is False and d['status_code'] in (7, 10):
                sys.exit("TMDB rejected the API key: " + d.get('status_message', ''))
            return d
        except json.JSONDecodeError:
            pass
    return {}

KEEP = {"YouTube Premium", "YouTube TV", "Peacock", "Paramount+"}
def canon(n):
    n = re.sub(r'\s+', ' ', n).strip()
    if n in KEEP: return n
    if n.upper() == "VIX": return "ViX"
    fixed = {"Amazon Prime Video": "Prime Video", "Amazon Prime Video with Ads": "Prime Video",
             "Amazon Prime Video Free with Ads": "Prime Video (free)", "Disney Plus": "Disney+",
             "YouTube": "YouTube (free)", "YouTube Free": "YouTube (free)", "Tubi TV": "Tubi",
             "The Roku Channel": "Roku Channel", "fuboTV": "Fubo", "Fandango at Home Free": "Fandango at Home (free)",
             "Plex Channel": "Plex", "Qello Concerts by Stingray": "Qello Concerts", "Broadway HD": "BroadwayHD",
             "MGM Plus": "MGM+", "AMC Plus": "AMC+", "Max": "HBO Max", "Netflix Kids": "Netflix"}
    if n in fixed: return fixed[n]
    for suf in (" Amazon Channel", " Roku Premium Channel", " Apple TV channel", " Apple TV Channel"):
        if n.endswith(suf):
            return canon(n[:-len(suf)])
    n2 = re.sub(r' (Standard with Ads|with Ads|Premium Plus|Premium|Essential|Basic with Ads)$', '', n)
    if n2 != n: return canon(n2)
    n2 = re.sub(r' Plus$', '+', n)
    if n2 != n: return canon(n2)
    return fixed.get(n, n)

FREE = re.compile(r'\(free\)|^Tubi$|^Pluto TV$|^Roku Channel$|^Plex$|^Fawesome$|^Kanopy$|^Hoopla$|^Amazon MX Player$|^Xumo Play$|^Crackle$', re.I)

def prov(item):
    key, (kind, i) = item
    d = get(f"/{kind}/{i}/watch/providers")
    if not d: return key, None
    us = d.get("results", {}).get("US", {})
    s, f = [], []
    for p in us.get("flatrate", []) + us.get("free", []) + us.get("ads", []):
        c = canon(p["provider_name"])
        (f if FREE.search(c) else s).append(c)
    s = list(dict.fromkeys(s)); f = [x for x in dict.fromkeys(f) if x not in s]
    return key, [s, f, 1 if (us.get("rent") or us.get("buy")) else 0]

# ---------- mood rules for new arrivals (same rules as the deep-cut auto tags)
GV = {35: 'f', 10749: 'r', 27: 'd', 53: 'd', 80: 'd', 10752: 'd', 14: 'w', 878: 'w', 10751: 'g', 16: 'g', 12: 'p', 28: 'l', 36: 'p'}
KV = [(r'\bconcert|\blive (at|in|from)|\btour\b|festival|stadium', 'e'), (r'tragic|tragedy|death of|died|dies\b|grief|heartbreak|cancer|suicide|overdose|addiction', 'h'),
      (r'inspir|triumph|overcom|against all odds|dream of|dreams of|underdog|comeback', 'n'), (r'fall(s)? in love|romance|love story|lovers|romantic', 'r'),
      (r'comedy|hilarious|comedic|mockumentary|spoof|parody|satir', 'f'), (r'\bpunk|metal|thrash|hardcore', 'l'), (r'\bdanc|choreograph', 'e'),
      (r'surreal|experimental|bizarre|psychedel|avant', 'w'), (r'intimate|portrait|personal|reflect|quiet|solitude', 'i'), (r'chaos|chaotic|riot|wild|anarch', 'c'),
      (r'murder|crime|gang|drug|violence|dark side|abuse', 'd'), (r'joy|uplifting|feel-good|celebrat|heartwarming|charming|delightful', 'g'),
      (r'epic|legend|empire|dynasty|saga|rise and fall', 'p'), (r'musical number|sing-along|singalong|belt|show-stopping|showstopper|anthem', 'b')]
SV = [(r'hip.?hop|\brap\b|rapper|\bmc\b|graffiti|breakdanc', 'hh'), (r'\bpunk', 'pk'), (r'heavy metal|\bmetal\b|thrash', 'me'), (r'\bjazz|bebop|swing band|big band', 'jz'),
      (r'\bcountry\b|nashville|honky|bluegrass', 'co'), (r'\bfolk\b|singer-songwriter|troubadour', 'fo'), (r'\bblues|\bsoul\b|motown|r&b|gospel|funk\b', 'so'),
      (r'reggae|jamaica|ska\b', 're'), (r'classical|orchestra|symphon|\bopera\b|composer|pianist|violin|cellist|conductor|ballet', 'cl'),
      (r'electronic|\bdj\b|techno|\bedm\b|house music|rave|synth', 'el'), (r'disco|dance floor|dancer|dancing|step team|dance crew|\bdance\b', 'da'),
      (r'latin|salsa|cuba|mexic|brazil|samba|tango|bollywood|k-pop|kpop|reggaeton|afrobeat|flamenco', 'wo'),
      (r'boy band|girl group|pop star|popstar|\bpop\b', 'po'), (r'\brock\b|rock band|guitar|grunge|\bband\b', 'rk')]
CONC = re.compile(r'\bconcert\b|\blive (at|in|from)\b|\btour\b', re.I)

def rule(t, ov, g, kind):
    text = (t + ' ' + ov).lower(); v = []
    for x in g:
        c = GV.get(x)
        if c and c not in v: v.append(c)
    for rx, c in KV:
        if c not in v and re.search(rx, text): v.append(c)
    if kind == 'C' and 'e' not in v: v.insert(0, 'e')
    if kind == 'D' and not any(c in v for c in 'ihnd'): v.append('i')
    if kind == 'M' and 'g' not in v and 'd' not in v: v.append('g')
    if not v: v = ['g']
    s = None
    for rx, c in SV:
        if re.search(rx, text): s = c; break
    return ''.join(v[:4]), s or ('sh' if kind == 'M' else 'po')

BASEQ = "&with_genres=10402&with_original_language=en&include_adult=false"
def pull(q, maxp=10):
    first = get("/discover/movie", BASEQ + q + "&page=1"); out = list(first.get("results", []))
    pages = min(first.get("total_pages", 0) or 0, maxp)
    with cf.ThreadPoolExecutor(6) as ex:
        for d in ex.map(lambda p: get("/discover/movie", BASEQ + q + f"&page={p}"), range(2, pages + 1)):
            out += d.get("results", [])
    return out

def kw_ids(window):
    tags = {}
    for name, kw in [("musical", "4344|155710|165241|220201"), ("bio", "5565"), ("concert", "156205|318730")]:
        tags[name] = {r['id'] for r in pull(f"&with_keywords={kw}" + window, 5)}
    return tags

def kind_of(r, tags):
    g = set(r.get('genre_ids', [])); t = r.get('title', ''); ov = (r.get('overview') or '')
    if r['id'] in tags['concert'] or (99 in g and CONC.search(t + ' ' + ov[:200])): return 'C'
    if 99 in g: return 'D'
    if r['id'] in tags['bio']: return 'B'
    if r['id'] in tags['musical'] or 16 in g: return 'M'
    return 'F'

# ---------- load inputs
tracked = json.load(open(a.tracked))
keys = tracked['keys']; known = set(tracked['known'])
prev_txt = open(a.prev, encoding='utf8').read()
prev_txt = re.sub(r'^\s*window\.FRESH\s*=\s*', '', prev_txt).rstrip().rstrip(';')
prev = json.loads(prev_txt)
if 'N' in prev:  # fresh.js format: index form
    N0 = prev['N']; prevP = {k: [[N0[i] for i in v[0]], [N0[i] for i in v[1]], v[2]] for k, v in prev['P'].items()}
else:
    prevP = prev['P']
def ccan(v):
    s = list(dict.fromkeys(canon(n) for n in v[0])); f = [x for x in dict.fromkeys(canon(n) for n in v[1]) if x not in s]
    return [s, f, v[2]]
prevP = {k: ccan(v) for k, v in prevP.items() if k in keys or k.startswith('t:')}
prevNEW = {x[0]: x for x in prev.get('NEW', [])}
prevL = prev.get('L', []); prevX = prev.get('X', [])

# ---------- new releases (last 120 days) and radar
lo = (TODAY - datetime.timedelta(days=120)).isoformat(); hi = TODAY.isoformat()
win = f"&primary_release_date.gte={lo}&primary_release_date.lte={hi}"
tags = kw_ids(win)
newr = {r['id']: r for r in pull(win + "&sort_by=popularity.desc")}
for s in tags.values():
    for i in s:
        if i not in newr:
            d = get(f"/movie/{i}")
            if d.get('id') and d.get('original_language') == 'en': d['genre_ids'] = [g['id'] for g in d.get('genres', [])]; newr[i] = d
NEW = dict(prevNEW)
for i, r in newr.items():
    if i in known or i in NEW: continue
    ov = (r.get('overview') or '').strip()
    if not ov or (r.get('vote_count', 0) < 1 and r.get('popularity', 0) < 1.5): continue
    k = kind_of(r, tags); v, s = rule(r['title'], ov, r.get('genre_ids', []), k)
    NEW[i] = [i, r['title'], r.get('release_date', ''), k, round(r.get('vote_average', 0) * 10), r.get('vote_count', 0), ov, v, s, hi]
uwin = f"&primary_release_date.gte={(TODAY + datetime.timedelta(days=1)).isoformat()}&primary_release_date.lte={(TODAY + datetime.timedelta(days=1100)).isoformat()}"
utags = kw_ids(uwin)
R = []
for r in pull(uwin + "&sort_by=popularity.desc", 6):
    ov = (r.get('overview') or '').strip()
    if not ov or not r.get('release_date'): continue
    k = kind_of(r, utags); v, s = rule(r['title'], ov, r.get('genre_ids', []), k)
    R.append([r['id'], r['title'], r['release_date'], k, ov, round(r.get('popularity', 0), 1), v, s])
R.sort(key=lambda x: x[2])

# ---------- providers for everything
jobs = dict((k, tuple(v)) for k, v in keys.items())
for i in NEW: jobs['t:%d' % i] = ('movie', i)
with cf.ThreadPoolExecutor(12) as ex:
    P = {k: v for k, v in ex.map(prov, jobs.items())}
failed = [k for k, v in P.items() if v is None]
for k in failed:  # keep last week's data for anything that failed to load
    if k in prevP: P[k] = prevP[k]
P = {k: v for k, v in P.items() if v is not None and (v[0] or v[1] or v[2])}

# ---------- diff
cut = (TODAY - datetime.timedelta(days=28)).isoformat()
def avail(v): return set(v[0] + v[1]) if v else set()
L = [x for x in prevL if x[2] >= cut]; X = [x for x in prevX if x[2] >= cut]
seenL = {(x[0], n) for x in L for n in x[1]}; seenX = {(x[0], n) for x in X for n in x[1]}
for k in set(P) | set(prevP):
    if k in failed: continue
    now, was = avail(P.get(k)), avail(prevP.get(k))
    add = sorted(n for n in now - was if (k, n) not in seenL)
    rem = sorted(n for n in was - now if (k, n) not in seenX)
    if add: L.append([k, add, hi])
    if rem: X.append([k, rem, hi])
# names table + index form
names = sorted({n for v in P.values() for n in v[0] + v[1]} | {n for x in L + X for n in x[1]})
ix = {n: i for i, n in enumerate(names)}
out = {'asof': hi, 'N': names,
       'P': {k: [[ix[n] for n in v[0]], [ix[n] for n in v[1]], v[2]] for k, v in P.items()},
       'L': L, 'X': X, 'NEW': sorted(NEW.values(), key=lambda x: x[2], reverse=True), 'R': R,
       'stats': {'checked': len(jobs), 'failed': len(failed), 'streaming': len(P)}}
with open(a.out, 'w', encoding='utf8') as fh:
    fh.write('window.FRESH = ' + json.dumps(out, ensure_ascii=False, separators=(',', ':')) + ';\n')

# ---------- summary for the run report
thisL = [x for x in L if x[2] == hi]; thisX = [x for x in X if x[2] == hi]
titles = {}
for i, x in NEW.items(): titles['t:%d' % i] = x[1]
def mine(x): return [n for n in x[1] if n in MINE]
week_new = [x for x in NEW.values() if x[9] == hi]
week_rel = [x for x in R if x[2] <= (TODAY + datetime.timedelta(days=7)).isoformat()]
print(json.dumps({'asof': hi, 'checked': len(jobs), 'failed_lookups': len(failed), 'streaming_now': len(P),
                  'landed_this_week': len(thisL), 'landed_on_my_services': sum(1 for x in thisL if mine(x)),
                  'left_this_week': len(thisX), 'new_releases_added': len(week_new),
                  'new_release_titles': [x[1] for x in week_new][:15], 'radar_total': len(R),
                  'radar_next_7_days': [x[1] + ' (' + x[2] + ')' for x in week_rel][:15]}, ensure_ascii=False, indent=1))

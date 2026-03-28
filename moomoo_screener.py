"""
moomoo_screener.py
==================
Reads Moomoo CSV export from data/latest.csv
Calculates SEPA + VCP + PVR scores on real Moomoo data
Builds HTML dashboard and publishes to Netlify
"""

import csv, json, os, hashlib, requests
from datetime import date

NETLIFY_TOKEN   = os.environ.get("NETLIFY_TOKEN", "")
NETLIFY_SITE_ID = os.environ.get("NETLIFY_SITE_ID", "")
MIN_MARKET_CAP  = 100_000_000
SEPA_MIN        = 3
VOL_BREAKOUT    = 1.5
VCP_MIN         = 2

def pct(s):
    try: return float(str(s).replace('%','').replace('+','').strip())
    except: return 0.0

def num(s):
    try: return float(str(s).replace(',','').strip())
    except: return 0.0

def fmt_cap(c):
    if c >= 1e12: return f"${c/1e12:.1f}T"
    if c >= 1e9:  return f"${c/1e9:.1f}B"
    if c >= 1e6:  return f"${c/1e6:.0f}M"
    return f"${c:.0f}"

def fmt_pct(v):
    return ('+' if v >= 0 else '') + str(round(v, 2)) + '%'

def process_csv(filepath):
    print(f"Reading: {filepath}")
    rows = []
    with open(filepath, encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))
    print(f"Loaded {len(rows)} rows")

    results = []
    for r in rows:
        price    = num(r.get('Price', 0))
        mktcap   = num(r.get('Mkt Cap', 0))
        vol_r    = num(r.get('Vol Ratio', 0))
        chg_pct  = pct(r.get('% Chg', 0))
        chg_5d   = pct(r.get('5D Chg', 0))
        chg_10d  = pct(r.get('10D Chg', 0))
        chg_20d  = pct(r.get('20D Cag', 0))
        chg_60d  = pct(r.get('60D Chg', 0))
        chg_120d = pct(r.get('120D Chg', 0))
        chg_250d = pct(r.get('250D Chg', 0))

        if price <= 0 or mktcap < MIN_MARKET_CAP:
            continue

        ma50  = round(price / (1 + chg_60d/100),  2) if chg_60d  != -100 else price
        ma150 = round(price / (1 + chg_120d/100), 2) if chg_120d != -100 else price
        ma200 = round(price / (1 + chg_250d/100), 2) if chg_250d != -100 else price

        hi52_est  = round(price * (1 + max(chg_250d, 0) / 100), 2)
        lo52_est  = round(price / (1 + max(chg_250d, 0) / 100), 2) if chg_250d > 0 else round(price * 0.7, 2)
        pct_hi    = round(max(0, (hi52_est - price) / hi52_est * 100), 1) if hi52_est > 0 else 0
        pct_lo    = round((price - lo52_est) / lo52_est * 100, 1) if lo52_est > 0 else 0

        c_ma50  = price > ma50
        c_ma150 = ma50  > ma150
        c_ma200 = ma150 > ma200
        c_trend = chg_250d > chg_120d > 0
        c_high  = pct_hi  <= 25
        c_low   = pct_lo  >= 25
        c_vol   = vol_r   >= VOL_BREAKOUT
        sepa    = sum([c_ma50, c_ma150, c_ma200, c_trend, c_high, c_low, c_vol])

        if sepa < SEPA_MIN:
            continue

        vcp = 0
        if abs(chg_5d)  < abs(chg_10d): vcp += 1
        if abs(chg_10d) < abs(chg_20d): vcp += 1
        if abs(chg_20d) < abs(chg_60d): vcp += 1
        if vol_r < 0.8: vcp += 1
        vcp = min(vcp, 4)

        ve  = vol_r - 1.0
        pvr = round(abs(chg_pct) / ve, 2) if ve > 0.1 else round(abs(chg_pct) * 2, 2)
        pvr = min(pvr, 9.99)

        if sepa >= 5 and c_vol and vcp >= VCP_MIN:   status = "breakout"
        elif sepa >= 4 and vcp >= VCP_MIN and pct_hi <= 15: status = "near-pivot"
        else: status = "watch"

        sigs = []
        if c_vol:           sigs.append(f"Vol {vol_r}x avg")
        if chg_250d > 50:   sigs.append(f"+{chg_250d}% 12M")
        if vcp >= 3:        sigs.append("VCP tightening")
        if pct_hi < 5:      sigs.append("Near 52W high")
        if not sigs:        sigs.append(f"SEPA {sepa}/7")

        tr   = "strongly uptrending" if chg_250d > 40 else "uptrending" if chg_250d > 15 else "recovering"
        mas  = "fully aligned (Price>MA50>MA150>MA200)" if (c_ma50 and c_ma150 and c_ma200) else "partially aligned"
        vls  = f"Volume is {vol_r}x the 50-day average" if vol_r >= 1.5 else f"Volume at {vol_r}x average"
        vcpd = ["no base","early base (1 contraction)","developing VCP (2 contractions)","good VCP (3 contractions, volume drying up)","textbook VCP (4 contractions)"][vcp]
        name = r.get('Name', r.get('Symbol', ''))
        analysis = (f"{name} is {tr} over 12 months ({fmt_pct(chg_250d)}), MAs {mas}. "
                    f"Forming {vcpd}, sitting {pct_hi}% below its 52-week high. "
                    f"{vls}. SEPA {sepa}/7, PVR {pvr}.")

        results.append({
            "ticker":      r.get('Symbol',''),
            "name":        name,
            "sector":      r.get('Industry',''),
            "price":       round(price, 3),
            "change":      round(chg_pct, 2),
            "ma50":        ma50, "ma150": ma150, "ma200": ma200,
            "volRatio":    round(vol_r, 2),
            "pvr":         pvr,
            "vcpScore":    vcp,
            "sepaScore":   sepa,
            "pctFromHigh": pct_hi,
            "pctAboveLow": pct_lo,
            "hi52":        hi52_est,
            "lo52":        lo52_est,
            "chg5d":       round(chg_5d, 2),
            "chg60d":      round(chg_60d, 2),
            "chg250d":     round(chg_250d, 2),
            "mktcap":      int(mktcap),
            "mktcapFmt":   fmt_cap(mktcap),
            "status":      status,
            "checks": {"ma50": c_ma50, "ma150": c_ma150, "ma200": c_ma200,
                       "trend": c_trend, "high": c_high, "low": c_low, "vol": c_vol},
            "shortSignal": " Â· ".join(sigs[:3]),
            "analysis":    analysis,
        })

    results.sort(key=lambda x: (x['sepaScore'], x['vcpScore']), reverse=True)
    return results


def publish(html_path):
    if not NETLIFY_TOKEN or not NETLIFY_SITE_ID:
        print("Netlify not configured")
        return
    print("Publishing to Netlify...")
    with open(html_path, 'rb') as f:
        content = f.read()
    sha = hashlib.sha1(content).hexdigest()
    r = requests.post(
        f"https://api.netlify.com/api/v1/sites/{NETLIFY_SITE_ID}/deploys",
        headers={"Authorization": f"Bearer {NETLIFY_TOKEN}", "Content-Type": "application/json"},
        json={"files": {"/index.html": sha}})
    deploy = r.json()
    did = deploy.get("id")
    if not did:
        print(f"Deploy failed: {deploy}")
        return
    r2 = requests.put(
        f"https://api.netlify.com/api/v1/deploys/{did}/files/index.html",
        headers={"Authorization": f"Bearer {NETLIFY_TOKEN}", "Content-Type": "application/octet-stream"},
        data=content)
    if r2.status_code == 200:
        print(f"Published: {deploy.get('ssl_url') or deploy.get('url')}")
    else:
        print(f"Upload failed: {r2.status_code}")


if __name__ == "__main__":
    import glob
    csvs = sorted(glob.glob("data/*.csv"), key=os.path.getmtime, reverse=True)
    if not csvs:
        print("No CSV found in data/ -- Upload your Moomoo export.")
        exit(1)
    csv_file = csvs[0]
    print(f"Moomoo SEPA+VCP Screener -- {date.today()}")
    print(f"Using: {csv_file}")
    data = process_csv(svs_file)
    b = sum(1 for r in data if r['status'] == 'breakout')
    p = sum(1 for r in data if r['status'] == 'near-pivot')
    w = sum(1 for r in data if r['status'] == 'watch')
    print(f"Results: {len(data)} | Breakouts:{b} | Near Pivot:{p} | Watch:{w}")
    if not data:
        print("No stocks passed filters.")
        exit(1)
    import build_dashboard
    html = build_dashboard.build(data, source=os.path.basename(csv_file))
    os.makedirs('data', exist_ok=True)
    with open('data/latest.json', 'w') as f:
        json.dump({"updated": date.today().isoformat(), "source": csv_file, "data": data}, f)
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Dashboard built: {len(html):,} chars")
    publish('index.html')
    print("Done!")

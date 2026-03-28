"""
build_dashboard.py — builds the HTML dashboard from screener data
Called by fetch_and_build.py
"""
from datetime import date
import json, os

def fmt_pct(v):
    return ("+" if v >= 0 else "") + str(round(v, 2)) + "%"

def build(data, source="Yahoo Finance (live)"):
    today_str = date.today().strftime("%d %b %Y")
    json_data = json.dumps(data)
    n = len(data)
    breakouts = [r for r in data if r["status"] == "breakout"]
    pivots    = [r for r in data if r["status"] == "near-pivot"]
    watching  = [r for r in data if r["status"] == "watch"]
    sectors   = sorted(set(r["sector"] for r in data if r["sector"]))
    sector_opts = "".join(f'<option value="{s}">{s}</option>' for s in sectors)

    top = sorted(breakouts + [r for r in pivots if r["sepaScore"] >= 5],
                 key=lambda x: (x["sepaScore"], x["vcpScore"], x["volRatio"]), reverse=True)[:10]
    medals = ["🥇","🥈","🥉","4","5","6","7","8","9","🔟"]

    top_html = ""
    for i, r in enumerate(top):
        sc = r["sepaScore"]
        pips  = "".join(f'<div class="pip {"pg" if j<sc else "po"}"></div>' for j in range(7))
        vpips = "".join(f'<div class="vp {"von" if j<r["vcpScore"] else "voff"}"></div>' for j in range(4))
        col = "#2ea043" if r["status"] == "breakout" else "#388bfd"
        p250c = "#2ea043" if r["chg250d"] >= 0 else "#f85149"
        badge_bg = "46,160,67" if r["status"]=="breakout" else "56,139,253"
        badge_label = "BREAKOUT" if r["status"]=="breakout" else "NEAR PIVOT"
        top_html += f'''<div class="tc" onclick="jmp(\'{r["ticker"]}\')">
          <span style="font-size:20px;flex-shrink:0">{medals[i]}</span>
          <div class="tc-body">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:3px">
              <span style="font-weight:800;font-size:15px;font-family:monospace;color:#fff">{r["ticker"]}</span>
              <span style="padding:2px 7px;border-radius:20px;font-size:10px;font-weight:700;background:rgba({badge_bg},.15);color:{col};border:1px solid rgba({badge_bg},.35)">{badge_label}</span>
            </div>
            <div style="font-size:11px;color:#7d8590;margin-bottom:6px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{r["name"]}</div>
            <div style="display:flex;gap:6px;margin-bottom:6px"><div class="pips">{pips}</div><div class="vpips">{vpips}</div></div>
            <div style="display:flex;gap:10px;font-size:11px;font-family:monospace;flex-wrap:wrap">
              <span style="color:#fff;font-weight:700">${r["price"]}</span>
              <span style="color:{p250c}">{fmt_pct(r["chg250d"])} 12M</span>
              <span style="color:{"#2ea043" if r["volRatio"]>=1.5 else "#d29922"}">{r["volRatio"]}x vol</span>
            </div>
            <div style="font-size:11px;color:#7d8590;margin-top:5px;line-height:1.4">{r["shortSignal"]}</div>
          </div>
        </div>'''

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>SEPA+VCP ASX Screener — {today_str}</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
:root{{--bg:#0d1117;--bg2:#161b22;--bg3:#21262d;--border:#30363d;--b2:#1c2128;--text:#e6edf3;--muted:#7d8590;--green:#2ea043;--blue:#388bfd;--amber:#d29922;--red:#f85149}}
body{{font-family:'Inter',sans-serif;background:var(--bg);color:var(--text);font-size:13px}}
nav{{background:#010409;border-bottom:1px solid var(--border);padding:12px 28px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:100;gap:12px;flex-wrap:wrap}}
.nlogo{{font-weight:800;font-size:15px;color:#fff;display:flex;align-items:center;gap:8px}}
.ndot{{width:9px;height:9px;background:var(--green);border-radius:50%;animation:pulse 2s infinite}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.35}}}}
.nlinks{{display:flex;gap:20px}}.nlinks a{{color:var(--muted);font-size:12px;text-decoration:none}}.nlinks a:hover{{color:var(--text)}}
.nbadge{{background:rgba(46,160,67,.12);color:var(--green);border:1px solid rgba(46,160,67,.3);border-radius:20px;padding:3px 11px;font-size:11px;font-weight:600;white-space:nowrap}}
.hero{{background:linear-gradient(180deg,#010409,var(--bg));padding:56px 28px 40px;text-align:center;border-bottom:1px solid var(--border)}}
.hero h1{{font-size:38px;font-weight:800;color:#fff;letter-spacing:-1px;line-height:1.1}}
.hero h1 span{{background:linear-gradient(90deg,var(--green),var(--blue));-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
.hero p{{font-size:15px;color:var(--muted);margin:12px auto 0;max-width:580px;line-height:1.7}}
.hero-stats{{display:flex;justify-content:center;gap:36px;margin-top:30px;flex-wrap:wrap}}
.hs{{text-align:center}}.hs-n{{font-size:34px;font-weight:800;font-family:'JetBrains Mono'}}.hs-l{{font-size:12px;color:var(--muted);margin-top:2px}}
.section{{padding:44px 28px;border-bottom:1px solid var(--border)}}
.stitle{{font-size:22px;font-weight:800;color:#fff;margin-bottom:5px}}.ssub{{font-size:14px;color:var(--muted);margin-bottom:28px}}
.picks-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:10px}}
.tc{{background:var(--bg2);border:1px solid var(--border);border-radius:10px;padding:14px;cursor:pointer;transition:border-color .15s;display:flex;gap:10px}}.tc:hover{{border-color:var(--blue)}}
.tc-body{{flex:1;min-width:0}}
.pips,.vpips{{display:flex;gap:2px}}.pip{{width:7px;height:7px;border-radius:1px}}.pg{{background:var(--green)}}.pa{{background:var(--amber)}}.pr{{background:var(--red)}}.po{{background:var(--bg3);border:1px solid var(--border)}}
.vp{{width:8px;height:8px;border-radius:2px}}.von{{background:var(--blue)}}.voff{{background:var(--bg3);border:1px solid var(--border)}}
.toolbar{{padding:10px 28px;display:flex;gap:7px;align-items:center;flex-wrap:wrap;background:var(--bg);border-bottom:1px solid var(--b2);position:sticky;top:49px;z-index:90}}
.fbtn{{padding:4px 11px;border-radius:20px;font-size:11px;font-weight:600;cursor:pointer;border:1px solid var(--border);background:var(--bg3);color:var(--muted);transition:all .12s;white-space:nowrap}}
.fbtn.on{{border-color:var(--blue);background:rgba(56,139,253,.12);color:var(--blue)}}.fbtn:hover:not(.on){{border-color:var(--muted);color:var(--text)}}
input.srch,select{{background:var(--bg3);border:1px solid var(--border);color:var(--text);border-radius:6px;padding:5px 9px;font-size:11px;outline:none;font-family:'Inter'}}
input.srch{{width:150px}}input.srch::placeholder{{color:var(--muted)}}input.srch:focus,select:focus{{border-color:var(--blue)}}
.cnt{{font-size:11px;color:var(--muted);margin-left:auto;white-space:nowrap}}
.twrap{{margin:0 28px 28px;border:1px solid var(--border);border-radius:10px;overflow:hidden;overflow-x:auto}}
table{{width:100%;border-collapse:collapse;min-width:860px}}
thead th{{background:var(--bg2);padding:9px 11px;text-align:left;font-size:10px;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.6px;border-bottom:1px solid var(--border);white-space:nowrap}}
tbody tr{{border-bottom:1px solid var(--b2);cursor:pointer;transition:background .08s}}tbody tr:hover{{background:var(--bg2)}}tbody tr:last-child{{border-bottom:none}}
tbody td{{padding:9px 11px;vertical-align:middle}}
.tkr{{font-weight:800;font-size:14px;font-family:'JetBrains Mono';color:#fff}}.co{{font-size:10px;color:var(--muted);margin-top:1px;max-width:110px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.badge{{display:inline-flex;padding:2px 7px;border-radius:20px;font-size:10px;font-weight:700}}
.bb{{background:rgba(46,160,67,.15);color:var(--green);border:1px solid rgba(46,160,67,.35)}}.bp{{background:rgba(56,139,253,.15);color:var(--blue);border:1px solid rgba(56,139,253,.35)}}.bw{{background:rgba(210,153,34,.15);color:var(--amber);border:1px solid rgba(210,153,34,.35)}}
.pv{{font-family:'JetBrains Mono';font-size:13px;font-weight:600}}.gn{{color:var(--green)}}.rd{{color:var(--red)}}.gy{{color:var(--muted)}}
.vhigh{{color:var(--green);font-weight:700}}.vmed{{color:var(--amber);font-weight:600}}.vlow{{color:var(--muted)}}
.pvg{{color:var(--green);font-weight:600}}.pvo{{color:var(--amber)}}.pvw{{color:var(--muted)}}
.sec{{font-size:10px;color:#8b949e;max-width:95px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}.sig{{font-size:11px;color:#c9d1d9;line-height:1.4;max-width:190px}}.mc{{font-family:'JetBrains Mono';font-size:11px;color:#8b949e}}
.drow td{{padding:0;background:#0a0e14}}.dpanel{{padding:16px 16px 16px 44px;display:grid;grid-template-columns:210px 170px 1fr;gap:18px;border-top:1px solid var(--b2)}}
.dh{{font-size:10px;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.7px;margin-bottom:7px}}
.cl{{display:flex;flex-direction:column;gap:3px}}.cr{{display:flex;align-items:flex-start;gap:5px;font-size:11px;line-height:1.5}}.cr.ok{{color:var(--green)}}.cr.no{{color:#484f58}}.ci{{width:12px;flex-shrink:0;font-size:10px;margin-top:1px}}
.mat{{width:100%;border-collapse:collapse;font-size:11px}}.mat td{{padding:2px 0}}.mlb{{color:var(--muted);width:50px}}.mbar{{padding:2px 6px;width:110px}}.mbw{{height:5px;background:var(--bg3);border-radius:3px;overflow:hidden}}.mbi{{height:100%;border-radius:3px}}.mvl{{font-family:'JetBrains Mono';color:#8b949e;text-align:right;width:62px}}
.abox{{background:var(--bg2);border-radius:8px;padding:13px;border-left:3px solid var(--border);font-size:12px;color:#8b949e;line-height:1.8}}.aact{{margin-top:9px;font-weight:700;font-size:12px;padding:7px 11px;border-radius:6px}}
.abuy{{color:var(--green);background:rgba(46,160,67,.08);border:1px solid rgba(46,160,67,.2)}}.awch{{color:var(--blue);background:rgba(56,139,253,.08);border:1px solid rgba(56,139,253,.2)}}.ahld{{color:var(--amber);background:rgba(210,153,34,.08);border:1px solid rgba(210,153,34,.2)}}
.pg2{{display:grid;grid-template-columns:1fr 1fr;gap:3px;font-size:10px;margin-top:9px}}.pi{{display:flex;justify-content:space-between;padding:3px 0;border-bottom:1px solid var(--b2)}}.pi:last-child{{border:none}}.pk{{color:var(--muted)}}
.empty{{text-align:center;padding:50px;color:var(--muted)}}
footer{{background:#010409;border-top:1px solid var(--border);padding:20px 28px;text-align:center;font-size:11px;color:var(--muted)}}
</style>
</head>
<body>
<nav>
  <div class="nlogo"><div class="ndot"></div>SEPA+VCP ASX Screener</div>
  <div class="nlinks"><a href="#picks">Top Picks</a><a href="#screener">Screener</a></div>
  <span class="nbadge">● {today_str} · Auto-updated daily</span>
</nav>
<div class="hero">
  <h1>ASX Stock Screener<br><span>SEPA + VCP + PVR</span></h1>
  <p>Minervini's Stage 2 Trend Template · Volatility Contraction Pattern · Price Volume Ratio · Breakout Volume — every ASX stock with market cap over $100M AUD. Auto-updated every trading day.</p>
  <div class="hero-stats">
    <div class="hs"><div class="hs-n" style="color:var(--green)">{len(breakouts)}</div><div class="hs-l">Breakouts</div></div>
    <div class="hs"><div class="hs-n" style="color:var(--blue)">{len(pivots)}</div><div class="hs-l">Near Pivot</div></div>
    <div class="hs"><div class="hs-n" style="color:var(--amber)">{len(watching)}</div><div class="hs-l">Watch</div></div>
    <div class="hs"><div class="hs-n" style="color:var(--text)">{n}</div><div class="hs-l">Screened</div></div>
  </div>
</div>
<div class="section" id="picks">
  <div class="stitle">🏆 Top 10 ASX Picks Today</div>
  <div class="ssub">Highest conviction SEPA+VCP setups. Click any card to jump to full analysis.</div>
  <div class="picks-grid">{top_html}</div>
</div>
<div id="screener">
<div class="toolbar">
  <button class="fbtn on" onclick="setF('all',this)">All ({n})</button>
  <button class="fbtn" onclick="setF('breakout',this)">🟢 Breakout ({len(breakouts)})</button>
  <button class="fbtn" onclick="setF('near-pivot',this)">🔵 Near Pivot ({len(pivots)})</button>
  <button class="fbtn" onclick="setF('watch',this)">🟡 Watch ({len(watching)})</button>
  <input class="srch" id="srch" placeholder="🔍 Ticker or name..." oninput="render()">
  <select id="srt" onchange="render()"><option value="sepa">↓ SEPA Score</option><option value="vcp">↓ VCP Score</option><option value="vol">↓ Volume Ratio</option><option value="p250">↓ 12M Perf</option><option value="mc">↓ Market Cap</option></select>
  <select id="sec" onchange="render()"><option value="">All Sectors</option>{sector_opts}</select>
  <span class="cnt" id="cnt"></span>
</div>
<div class="twrap"><table>
  <thead><tr><th>#</th><th>Ticker</th><th>Signal</th><th>SEPA /7</th><th>VCP /4</th><th>Price</th><th>Today</th><th>Rel.Vol</th><th>PVR</th><th>12M</th><th>Mkt Cap</th><th>Sector</th><th>Description</th></tr></thead>
  <tbody id="tbody"></tbody>
</table></div>
</div>
<footer>SEPA+VCP ASX Screener · Data via Yahoo Finance · Auto-updated daily · {today_str}<br>
<span style="font-size:11px;opacity:.6">⚠️ Educational purposes only. Not financial advice. Consult a licensed financial adviser before investing.</span></footer>
<script>
const D={json_data};
let filt='all';
function setF(f,el){{filt=f;document.querySelectorAll('.fbtn').forEach(b=>b.classList.remove('on'));el.classList.add('on');render();}}
function jmp(t){{document.getElementById('screener').scrollIntoView({{behavior:'smooth'}});document.getElementById('srch').value=t;setTimeout(()=>{{render();const r=document.querySelector('#tbody tr');if(r)r.click();}},400);}}
function render(){{
  const srt=document.getElementById('srt').value,q=document.getElementById('srch').value.toLowerCase(),sec=document.getElementById('sec').value;
  let d=D.filter(r=>{{if(filt!=='all'&&r.status!==filt)return false;if(sec&&r.sector!==sec)return false;if(q&&!r.ticker.toLowerCase().includes(q)&&!r.name.toLowerCase().includes(q))return false;return true;}});
  d.sort((a,b)=>{{if(srt==='sepa')return(b.sepaScore*10+b.vcpScore)-(a.sepaScore*10+a.vcpScore);if(srt==='vcp')return b.vcpScore-a.vcpScore;if(srt==='vol')return b.volRatio-a.volRatio;if(srt==='p250')return b.chg250d-a.chg250d;if(srt==='mc')return b.mktcap-a.mktcap;return 0;}});
  document.getElementById('cnt').textContent=d.length+' shown';
  if(!d.length){{document.getElementById('tbody').innerHTML='<tr><td colspan="13"><div class="empty">No stocks match</div></td></tr>';return;}}
  document.getElementById('tbody').innerHTML=d.map((r,i)=>row(r,i)).join('');
}}
function row(r,i){{
  const sc=r.sepaScore,pc=sc>=6?'pg':sc>=4?'pa':'pr';
  const ps=Array.from({{length:7}},(_,j)=>`<div class="pip ${{j<sc?pc:'po'}}"></div>`).join('');
  const vs=Array.from({{length:4}},(_,j)=>`<div class="vp ${{j<r.vcpScore?'von':'voff'}}"></div>`).join('');
  const bdg=r.status==='breakout'?'<span class="badge bb">BREAKOUT</span>':r.status==='near-pivot'?'<span class="badge bp">NEAR PIVOT</span>':'<span class="badge bw">WATCH</span>';
  const cc=r.change>0?'gn':r.change<0?'rd':'gy',vc=r.volRatio>=2?'vhigh':r.volRatio>=1.5?'vmed':'vlow',p2=r.pvr>=1.5?'pvg':r.pvr>=1?'pvo':'pvw',q2=r.chg250d>=0?'gn':'rd';
  return `<tr onclick="tog(${{i}})"><td style="color:#484f58;font-size:10px">${{i+1}}</td><td><div class="tkr">${{r.ticker}}</div><div class="co" title="${{r.name}}">${{r.name}}</div></td><td>${{bdg}}</td><td><div style="display:flex;align-items:center;gap:3px"><div class="pips">${{ps}}</div><span style="font-size:10px;color:var(--muted)">${{sc}}</span></div></td><td><div class="vpips">${{vs}}</div></td><td><span class="pv">$${{r.price}}</span></td><td><span class="${{cc}}">${{(r.change>0?'+':'')+r.change}}%</span></td><td><span class="${{vc}}">${{r.volRatio}}x</span></td><td><span class="${{p2}}">${{r.pvr}}</span></td><td><span class="${{q2}}">${{(r.chg250d>=0?'+':'')+r.chg250d}}%</span></td><td class="mc">${{r.mktcapFmt}}</td><td class="sec" title="${{r.sector}}">${{r.sector||''}}</td><td class="sig">${{r.shortSignal}}</td></tr><tr class="drow" id="d${{i}}" style="display:none"><td colspan="13">${{det(r)}}</td></tr>`;
}}
function det(r){{
  const c=r.checks;
  const cr=[[c.ma50,`Price ($${{r.price}}) > MA50 ($${{r.ma50}})`],[c.ma150,`MA50 > MA150 ($${{r.ma150}})`],[c.ma200,`MA150 > MA200 ($${{r.ma200}})`],[c.trend,`200-day MA trending up (12M: ${{(r.chg250d>=0?'+':'')+r.chg250d}}%)`],[c.high,`Within 25% of 52W high (${{r.pctFromHigh}}% below)`],[c.low,`25%+ above 52W low (${{r.pctAboveLow}}% above)`],[c.vol,`Volume breakout ≥1.5x (${{r.volRatio}}x) + PVR ${{r.pvr}}`]].map(([ok,l])=>`<div class="cr ${{ok?'ok':'no'}}"><span class="ci">${{ok?'✓':'✗'}}</span>${{l}}</div>`).join('');
  const mx=Math.max(r.price,r.ma50,r.ma150,r.ma200);
  const mb=(lb,v,col)=>`<tr><td class="mlb">${{lb}}</td><td class="mbar"><div class="mbw"><div class="mbi" style="width:${{Math.round(v/mx*100)}}%;background:${{col}}"></div></div></td><td class="mvl">$${{v}}</td></tr>`;
  const vd=['No contraction','Weak (1/4)','Moderate (2/4)','Good (3/4) — VCP forming','Ideal (4/4) — textbook base'][r.vcpScore];
  const ac=r.status==='breakout'?'abuy':r.status==='near-pivot'?'awch':'ahld';
  const at=r.status==='breakout'?'→ BUY ZONE: Consider entry. Stop-loss below MA50. Risk 1-2% portfolio.':r.status==='near-pivot'?'→ WATCHLIST: Set alert at pivot high. Enter on breakout with vol >1.5x.':'→ MONITOR: Wait for VCP to tighten and volume to dry up.';
  return `<div class="dpanel"><div><div class="dh">SEPA Checklist — ${{r.sepaScore}}/7</div><div class="cl">${{cr}}</div></div><div><div class="dh">Moving Averages</div><table class="mat">${{mb('Price',r.price,'#e6edf3')}}${{mb('MA50',r.ma50,c.ma50?'#2ea043':'#f85149')}}${{mb('MA150',r.ma150,c.ma150?'#2ea043':'#f85149')}}${{mb('MA200',r.ma200,c.ma200?'#2ea043':'#f85149')}}</table><div style="margin-top:10px"><div class="dh">VCP: ${{r.vcpScore}}/4</div><div style="font-size:10px;color:#8b949e;margin-top:2px;line-height:1.4">${{vd}}</div></div><div class="pg2"><div class="pi"><span class="pk">5D</span><span class="${{r.chg5d>=0?'gn':'rd'}}">${{(r.chg5d>=0?'+':'')+r.chg5d}}%</span></div><div class="pi"><span class="pk">60D</span><span class="${{r.chg60d>=0?'gn':'rd'}}">${{(r.chg60d>=0?'+':'')+r.chg60d}}%</span></div><div class="pi"><span class="pk">12M</span><span class="${{r.chg250d>=0?'gn':'rd'}}">${{(r.chg250d>=0?'+':'')+r.chg250d}}%</span></div><div class="pi"><span class="pk">Cap</span><span style="color:#8b949e">${{r.mktcapFmt}}</span></div></div></div><div class="abox">${{r.analysis}}<div class="aact ${{ac}}">${{at}}</div></div></div>`;
}}
function tog(i){{const el=document.getElementById('d'+i);el.style.display=el.style.display==='none'?'table-row':'none';}}
render();
</script>
</body>
</html>"""

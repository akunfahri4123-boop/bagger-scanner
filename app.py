
import os
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

# --- PWA polish (best-effort, never breaks the app if it fails) -----------
# Streamlit doesn't natively support a custom <head>, so this patches
# Streamlit's own shell HTML once per server start to add the manifest/icon
# links. If anything goes wrong (permissions, future Streamlit versions,
# etc.) it silently does nothing and the app runs exactly as before.
def _inject_pwa_head():
    try:
        idx = os.path.join(os.path.dirname(st.__file__), "static", "index.html")
        with open(idx, "r", encoding="utf-8") as fh:
            html = fh.read()
        marker = "<!-- deandra-pwa -->"
        if marker not in html and "<head>" in html:
            tags = (
                marker
                + '<link rel="manifest" href="/app/static/manifest.webmanifest">'
                + '<meta name="theme-color" content="#111827">'
                + '<link rel="apple-touch-icon" href="/app/static/icon-512.svg">'
            )
            html = html.replace("<head>", "<head>" + tags, 1)
            with open(idx, "w", encoding="utf-8") as fh:
                fh.write(html)
    except Exception:
        pass

_inject_pwa_head()
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Deandra Bagger Scanner v4.0",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
.block-container {padding-top: 1.2rem; padding-bottom: 2rem;}
.small {font-size: 0.82rem; color: #6b7280;}
.score {font-size: 2rem; font-weight: 800;}
</style>
""", unsafe_allow_html=True)

st.title("📈 Deandra Bagger Scanner v4.0")
st.caption("BEI Stock Screener • Price Action • Volume • Momentum • Accumulation • Fundamental Filter • Risk/Reward")

DEFAULT = """BBCA,BBRI,BMRI,BBNI,ANTM,ASII,TLKM,ICBP,INDF,MYOR,
PTSN,SRSN,BBSS,PADI,BBUM,DEWA,BUMI,CUAN,INET,BIPI,TRIN,TRUE"""

with st.sidebar:
    st.header("⚙️ Scanner")
    ticker_text = st.text_area("Universe saham BEI", DEFAULT, height=140)
    min_score = st.slider("Minimum Bagger Score", 0, 100, 60)
    period = st.selectbox("Historical data", ["1y","2y","5y"], index=0)
    liquidity_floor = st.number_input("Min. average value traded (Rp)", min_value=0, value=500_000_000, step=100_000_000)
    run = st.button("🔎 RUN BAGGER SCANNER", type="primary", use_container_width=True)

    st.divider()
    st.markdown("**Bobot v4.0**")
    st.write("Price Action 25 • Volume 25 • Breakout 15 • RS 10 • Accumulation 10 • Fundamental 5 • Catalyst 5 • R/R 5")
    st.caption("Fundamental/catalyst scoring memakai data yang tersedia dari Yahoo Finance; untuk BEI, verifikasi laporan resmi sebelum mengambil keputusan.")

def download(ticker, period):
    x = yf.download(f"{ticker}.JK", period=period, auto_adjust=False, progress=False)
    if isinstance(x.columns, pd.MultiIndex):
        x.columns = x.columns.get_level_values(0)
    return x.dropna(subset=["Open","High","Low","Close","Volume"])

def indicators(x):
    x=x.copy()
    c,h,l,v=x.Close,x.High,x.Low,x.Volume
    x["MA20"]=c.rolling(20).mean()
    x["MA50"]=c.rolling(50).mean()
    x["MA200"]=c.rolling(200).mean()
    x["VMA20"]=v.rolling(20).mean()
    x["RVOL"]=v/x.VMA20
    d=c.diff()
    gain=d.clip(lower=0).rolling(14).mean()
    loss=(-d.clip(upper=0)).rolling(14).mean()
    rs=gain/loss.replace(0,np.nan)
    x["RSI"]=100-(100/(1+rs))
    x["HH20"]=h.rolling(20).max().shift(1)
    x["LL20"]=l.rolling(20).min().shift(1)
    x["Ret20"]=c.pct_change(20)
    x["Ret60"]=c.pct_change(60)
    x["Value"]=c*v
    return x

@st.cache_data(ttl=900, show_spinner=False)
def fundamentals(ticker):
    try:
        info=yf.Ticker(f"{ticker}.JK").info
        def num(k):
            v=info.get(k, np.nan)
            return float(v) if v is not None else np.nan
        return {
            "ROE": num("returnOnEquity"),
            "DER": num("debtToEquity"),
            "PER": num("trailingPE"),
            "PBV": num("priceToBook"),
            "PEG": num("pegRatio"),
            "RevGrowth": num("revenueGrowth"),
            "ProfitGrowth": num("earningsGrowth"),
            "Margin": num("profitMargins"),
        }
    except:
        return {}

def fundamental_score(f):
    s=0
    if np.isfinite(f.get("ROE",np.nan)) and f["ROE"]>0.15: s+=1
    if np.isfinite(f.get("DER",np.nan)) and f["DER"]<100: s+=1
    if np.isfinite(f.get("RevGrowth",np.nan)) and f["RevGrowth"]>0.10: s+=1
    if np.isfinite(f.get("ProfitGrowth",np.nan)) and f["ProfitGrowth"]>0.10: s+=1
    if np.isfinite(f.get("Margin",np.nan)) and f["Margin"]>0: s+=1
    return s

def score(t, x, f):
    if len(x)<210: return None
    a=x.iloc[-1]; p=x.iloc[-2]
    price=float(a.Close)

    pa=(7 if price>a.MA20 else 0)+(7 if a.MA20>a.MA50 else 0)+(6 if a.MA50>a.MA200 else 0)+(5 if price>p.Close else 0)
    vol=(10 if a.RVOL>=1.5 else 6 if a.RVOL>=1.2 else 0)+(8 if a.RVOL>=1.5 and price>=p.Close else 0)+(7 if a.Value>=liquidity_floor else 0)
    br=(10 if price>a.HH20 else 0)+(5 if a.Ret20>0.05 else 0)
    rs=(5 if a.Ret20>0 else 0)+(5 if a.Ret60>0 else 0)
    acc=(5 if a.RVOL>1.2 and a.Ret20>0 else 0)+(5 if price>a.MA50 and a.MA50>=p.MA50 else 0)
    fund=fundamental_score(f)
    # Catalyst is deliberately conservative: no score without a verified event.
    catalyst=0

    support=float(a.LL20) if np.isfinite(a.LL20) else price*0.95
    sl=max(support*0.99, 0.0)
    risk=max(price-sl, price*0.01)
    tp1=price+2*risk
    tp2=price+3*risk
    rr=(tp1-price)/risk
    rr_score=5 if rr>=2 else 3

    total = min(pa,25)+min(vol,25)+min(br,15)+rs+acc+fund+catalyst+rr_score
    signal="🟢 STRONG WATCH" if total>=80 else "🟡 WATCH" if total>=65 else "⚪ NEUTRAL"

    return {
        "Ticker":t,"Price":round(price,2),"Score":int(total),"Signal":signal,
        "RSI":round(float(a.RSI),1) if np.isfinite(a.RSI) else np.nan,
        "RVOL":round(float(a.RVOL),2) if np.isfinite(a.RVOL) else np.nan,
        "20D %":round(float(a.Ret20*100),2),
        "60D %":round(float(a.Ret60*100),2),
        "Support":round(support,2),"SL":round(sl,2),
        "TP1 (2R)":round(tp1,2),"TP2 (3R)":round(tp2,2),
        "ROE":round(f.get("ROE",np.nan)*100,1) if np.isfinite(f.get("ROE",np.nan)) else np.nan,
        "DER":round(f.get("DER",np.nan),1) if np.isfinite(f.get("DER",np.nan)) else np.nan,
        "PER":round(f.get("PER",np.nan),1) if np.isfinite(f.get("PER",np.nan)) else np.nan,
        "PBV":round(f.get("PBV",np.nan),2) if np.isfinite(f.get("PBV",np.nan)) else np.nan,
        "Rev Growth":round(f.get("RevGrowth",np.nan)*100,1) if np.isfinite(f.get("RevGrowth",np.nan)) else np.nan,
        "Profit Growth":round(f.get("ProfitGrowth",np.nan)*100,1) if np.isfinite(f.get("ProfitGrowth",np.nan)) else np.nan,
    }

if run:
    tickers=[x.strip().upper() for x in ticker_text.replace("\n",",").split(",") if x.strip()]
    rows=[]; warnings=[]
    bar=st.progress(0)
    for i,t in enumerate(tickers):
        try:
            raw=download(t,period)
            d=indicators(raw)
            f=fundamentals(t)
            r=score(t,d,f)
            if r: rows.append(r)
            else: warnings.append(f"{t}: histori kurang dari 210 sesi.")
        except Exception as e:
            warnings.append(f"{t}: {str(e)[:120]}")
        bar.progress((i+1)/len(tickers))
    bar.empty()

    res=pd.DataFrame(rows)
    if not res.empty:
        res=res.sort_values(["Score","RVOL"],ascending=[False,False]).reset_index(drop=True)
        shown=res[res.Score>=min_score].copy()

        st.subheader("🏆 Bagger Ranking")
        if shown.empty:
            st.warning("Tidak ada saham yang mencapai minimum score. Turunkan threshold atau perluas universe.")
        else:
            a,b,c,d=st.columns(4)
            a.metric("Top Ticker",shown.iloc[0].Ticker)
            b.metric("Top Score",shown.iloc[0].Score)
            c.metric("Candidates",len(shown))
            d.metric("Scan Time",datetime.now().strftime("%H:%M:%S"))

            st.dataframe(shown,use_container_width=True,hide_index=True)
            st.download_button("⬇️ Export CSV",shown.to_csv(index=False).encode("utf-8"),"bagger_v4_results.csv","text/csv")

            st.divider()
            st.subheader("🔬 Detail Kandidat")
            selected=st.selectbox("Pilih ticker",shown.Ticker.tolist())
            raw=indicators(download(selected,period))
            last=raw.iloc[-1]
            f=fundamentals(selected)
            rr=shown[shown.Ticker==selected].iloc[0]
            m1,m2,m3,m4=st.columns(4)
            m1.metric("Score",int(rr.Score))
            m2.metric("Price",rr.Price)
            m3.metric("RSI",rr.RSI)
            m4.metric("RVOL",rr.RVOL)
            st.write("**Setup:**",rr.Signal)
            st.write(f"**Support:** {rr.Support}  |  **SL:** {rr.SL}  |  **TP1:** {rr['TP1 (2R)']}  |  **TP2:** {rr['TP2 (3R)']}")
            st.line_chart(raw[["Close","MA20","MA50","MA200"]].tail(120))
            st.caption("Chart di atas adalah indikasi teknikal, bukan prediksi pasti.")
    else:
        st.error("Tidak ada data valid. Periksa ticker dan koneksi internet.")
    if warnings:
        with st.expander("⚠️ Warnings"):
            st.write("\n".join(warnings))
else:
    st.info("Tekan **RUN BAGGER SCANNER** untuk mulai.")
    st.markdown("""
### Formula Bagger Score v4.0

| Faktor | Bobot |
|---|---:|
| Price Action / Market Structure | 25 |
| Volume & Order Flow proxy | 25 |
| Breakout & Momentum | 15 |
| Relative Strength | 10 |
| Accumulation / Distribution proxy | 10 |
| Fundamental Filter | 5 |
| Catalyst | 5 |
| Risk / Reward | 5 |
| **Total** | **100** |

**Interpretasi:** 80+ = Strong Watch • 65–79 = Watch • <65 = Neutral.

> Sistem ini adalah alat screening, bukan jaminan profit. Data fundamental dari sumber pihak ketiga perlu diverifikasi dengan laporan emiten/BEI sebelum keputusan investasi.
""")

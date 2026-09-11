import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import requests
from datetime import datetime, timezone

st.set_page_config(page_title="Meridian Commodity Hedge Desk", page_icon="◈", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
.stApp{background:radial-gradient(circle at 80% -20%,#142033 0,#07090d 36%),#07090d;color:#eef2f6}
.block-container{padding:.65rem 1.2rem 2rem;max-width:1700px}
header[data-testid="stHeader"]{background:transparent}
h1,h2,h3{color:#eef2f6!important} h1{font-size:1.35rem!important;margin:0!important}
h2{font-size:1.02rem!important;margin:.2rem 0 .45rem!important} h3{font-size:.88rem!important}
[data-testid="stMetric"]{background:linear-gradient(180deg,#0e141c,#0a0f15);border:1px solid #202a37;border-radius:8px;padding:10px 12px}
[data-testid="stMetricLabel"] p{color:#9aa5b4!important;font-size:.68rem!important}
[data-testid="stMetricValue"]{color:#eef2f6!important;font-family:ui-monospace,monospace;font-size:1.12rem!important}
[data-testid="stMetricDelta"]{font-size:.68rem!important}
.desk-card{background:linear-gradient(180deg,#0e141c,#0a0f15);border:1px solid #202a37;border-radius:8px;padding:12px 13px;min-height:100%}
.eyebrow{color:#8e9aab;text-transform:uppercase;letter-spacing:.13em;font-size:.64rem;font-weight:800;margin:.9rem 0 .42rem}
.big-signal{font:800 1.65rem ui-monospace,monospace;margin:.25rem 0}
.green{color:#35d39a}.red{color:#ff6670}.amber{color:#f2ad4b}.cyan{color:#53c8e8}
.muted{color:#9aa5b4;font-size:.73rem}.small{color:#c8d0da;font-size:.72rem}.tiny{color:#9aa5b4;font-size:.63rem}
.signal-row{display:flex;justify-content:space-between;gap:10px;padding:7px 0;border-bottom:1px solid #17202b}.signal-row:last-child{border-bottom:0}
.tag{display:inline-block;border:1px solid #303b4a;border-radius:4px;padding:3px 6px;color:#c8d0da;font:600 .61rem ui-monospace,monospace}
.status{border:1px solid #254735;border-radius:20px;padding:4px 8px;color:#9ee8c8;font:700 .62rem ui-monospace,monospace}
div[data-testid="stDataFrame"]{border:1px solid #202a37;border-radius:7px;overflow:hidden}
.stTabs [data-baseweb="tab"]{font-size:.72rem} hr{border-color:#202a37!important}
</style>
""", unsafe_allow_html=True)

YAHOO = {
    "WTI":"CL=F","Brent":"BZ=F","Nat Gas":"NG=F","Gold":"GC=F","Silver":"SI=F",
    "Copper":"HG=F","Aluminum":"ALI=F","DXY":"DX-Y.NYB","USD/INR":"INR=X",
    "S&P 500 Fut.":"ES=F","VIX":"^VIX","India VIX":"^INDIAVIX","US 10Y":"^TNX","US 2Y":"^IRX"
}
PRICE_DECIMALS={"WTI":2,"Brent":2,"Nat Gas":3,"Gold":2,"Silver":3,"Copper":4,"Aluminum":2,
                "DXY":2,"USD/INR":2,"S&P 500 Fut.":2,"VIX":2,"India VIX":2,"US 10Y":2,"US 2Y":2}

@st.cache_data(ttl=60, show_spinner=False)
def fetch_yahoo(symbols):
    out={}
    for name,symbol in symbols.items():
        try:
            df=yf.download(symbol,period="10d",interval="1d",auto_adjust=False,progress=False,threads=False)
            if df is None or df.empty:
                out[name]={"price":np.nan,"chg":np.nan,"history":pd.DataFrame()}; continue
            if isinstance(df.columns,pd.MultiIndex): df.columns=df.columns.get_level_values(0)
            close=df["Close"].dropna()
            if close.empty:
                out[name]={"price":np.nan,"chg":np.nan,"history":df}; continue
            last=float(close.iloc[-1]); prev=float(close.iloc[-2]) if len(close)>1 else np.nan
            chg=(last/prev-1)*100 if prev else np.nan
            out[name]={"price":last,"chg":chg,"history":df}
        except Exception:
            out[name]={"price":np.nan,"chg":np.nan,"history":pd.DataFrame()}
    return out

@st.cache_data(ttl=900, show_spinner=False)
def fred_series(series_id,limit=120):
    url=f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    try:
        r=requests.get(url,timeout=12,headers={"User-Agent":"MeridianCommodityDesk/1.0"})
        r.raise_for_status()
        df=pd.read_csv(pd.io.common.BytesIO(r.content))
        df.columns=["date","value"]; df["date"]=pd.to_datetime(df["date"],errors="coerce")
        df["value"]=pd.to_numeric(df["value"],errors="coerce")
        return df.dropna().tail(limit)
    except Exception:
        return pd.DataFrame(columns=["date","value"])

def fmt_price(name,x):
    if pd.isna(x): return "—"
    return f"{x:,.{PRICE_DECIMALS.get(name,2)}f}"
def pct(x):
    return "—" if pd.isna(x) else f"{x:+.2f}%"
def tone(x):
    if pd.isna(x): return "muted"
    return "green" if x>0 else "red" if x<0 else "amber"

data=fetch_yahoo(YAHOO)

st.markdown(
    '<div style="display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #202a37;padding:5px 0 10px">'
    '<div><span style="font-size:20px;font-weight:850">◈ MERIDIAN</span> <span style="color:#9aa5b4;font-size:12px">/ COMMODITY HEDGE DESK</span></div>'
    '<div class="status">● DATA FEED · YAHOO FINANCE</div></div>', unsafe_allow_html=True)

tape_names=["WTI","Brent","Gold","Silver","Copper","DXY","USD/INR","US 10Y","VIX","India VIX"]
for col,name in zip(st.columns(len(tape_names),gap="small"),tape_names):
    d=data[name]
    with col: st.metric(name.upper(),fmt_price(name,d["price"]),pct(d["chg"]))
st.caption("Source: Yahoo Finance via yfinance. Quotes may be delayed; this is not an exchange-direct execution feed.")

tabs=st.tabs(["DESK OVERVIEW","RISK","ENERGY","METALS","CURVE & RV","POSITIONING","MACRO","CALENDAR"])

with tabs[0]:
    st.markdown('<div class="eyebrow">01 · Global Market Regime</div>',unsafe_allow_html=True)
    components=[]
    for val,positive in [(data["S&P 500 Fut."]["chg"],True),(data["VIX"]["chg"],False),(data["DXY"]["chg"],False),(data["US 10Y"]["chg"],False)]:
        if not pd.isna(val): components.append(1 if (val>0)==positive else 0)
    score=round(50+(sum(components)/len(components)-.5)*60) if components else 50
    regime="RISK-ON" if score>=60 else "RISK-OFF" if score<=40 else "MIXED"
    regime_cls="green" if regime=="RISK-ON" else "red" if regime=="RISK-OFF" else "amber"
    c1,c2,c3,c4,c5=st.columns([1.25,1,1,1,1])
    with c1:
        st.markdown(f'<div class="desk-card"><div class="tiny">DESK REGIME</div><div class="big-signal {regime_cls}">{regime}</div><div class="small">Cross-asset rule score · {score}/100</div><div style="margin-top:9px;height:5px;background:#18212d;border-radius:5px"><div style="height:100%;width:{score}%;background:#35d39a;border-radius:5px"></div></div><div class="tiny" style="margin-top:9px">USD / rates / volatility / equity-futures composite</div></div>',unsafe_allow_html=True)
    for col,name,label in [(c2,"S&P 500 Fut.","Equity risk appetite"),(c3,"DXY","USD pressure"),(c4,"US 10Y","Rates / real-rate watch"),(c5,"VIX","Volatility regime")]:
        with col:
            d=data[name]; st.metric(name,fmt_price(name,d["price"]),pct(d["chg"])); st.caption(label)
    st.markdown('<div class="eyebrow">Desk read-through</div>',unsafe_allow_html=True)
    r1,r2,r3=st.columns(3)
    with r1: st.markdown('<div class="desk-card"><b>USD</b><div class="muted">A stronger dollar is normally a headwind for USD-denominated commodities. Confirm with gold/copper momentum.</div></div>',unsafe_allow_html=True)
    with r2: st.markdown('<div class="desk-card"><b>Rates</b><div class="muted">Higher US yields raise the hurdle for precious metals and tighten financial conditions.</div></div>',unsafe_allow_html=True)
    with r3: st.markdown('<div class="desk-card"><b>Demand</b><div class="muted">Use copper/energy momentum plus China and macro releases as the demand confirmation layer.</div></div>',unsafe_allow_html=True)

with tabs[1]:
    st.markdown('<div class="eyebrow">02 · Risk Factor Stack</div>',unsafe_allow_html=True)
    c1,c2,c3,c4=st.columns(4)
    for col,(label,name,desc) in zip([c1,c2,c3,c4],[("USD","DXY","FX pressure"),("RATES","US 10Y","Discount-rate pressure"),("VOL","VIX","Risk appetite"),("INR","USD/INR","India FX translation")]):
        d=data[name]
        with col: st.markdown(f'<div class="desk-card"><div class="tiny">{label}</div><div style="font:700 1.15rem ui-monospace,monospace">{fmt_price(name,d["price"])}</div><div class="{tone(d["chg"])}" style="font:700 .72rem ui-monospace,monospace">{pct(d["chg"])}</div><div class="tiny" style="margin-top:8px">{desc}</div></div>',unsafe_allow_html=True)
    risk_df=pd.DataFrame({"Factor":["USD","US Rates","Volatility","India FX","Equity Futures"],"Level":[data[x]["price"] for x in ["DXY","US 10Y","VIX","USD/INR","S&P 500 Fut."]],"1D":[pct(data[x]["chg"]) for x in ["DXY","US 10Y","VIX","USD/INR","S&P 500 Fut."]],"Desk implication":["Commodity headwind","Gold headwind","Risk appetite","INR translation","Risk appetite"]})
    st.dataframe(risk_df,hide_index=True,use_container_width=True)

with tabs[2]:
    st.markdown('<div class="eyebrow">03 · Energy Market</div>',unsafe_allow_html=True)
    st.dataframe(pd.DataFrame([[n,fmt_price(n,data[n]["price"]),pct(data[n]["chg"])] for n in ["WTI","Brent","Nat Gas"]],columns=["Contract","Last","1D"]),hide_index=True,use_container_width=True)
    ec1,ec2=st.columns([1.5,1])
    with ec1:
        chart=pd.DataFrame({k:data[k]["history"]["Close"] if not data[k]["history"].empty else pd.Series(dtype=float) for k in ["WTI","Brent","Nat Gas"]}).dropna(how="all")
        if not chart.empty: st.line_chart(chart,height=280)
        else: st.info("Yahoo Finance history unavailable for this refresh.")
    with ec2:
        st.markdown('<div class="desk-card"><div class="signal-row"><span>WTI vs Brent</span><span class="tag">SPREAD WATCH</span></div><div class="signal-row"><span>Front / back curve</span><span class="tag">ADD CURVE DATA</span></div><div class="signal-row"><span>Nat Gas</span><span class="tag">VOLATILE</span></div><div class="tiny" style="margin-top:10px">Yahoo futures quotes provide the price layer. True forward-curve analytics require a dedicated curve source or exchange/broker feed.</div></div>',unsafe_allow_html=True)

with tabs[3]:
    st.markdown('<div class="eyebrow">04 · Metals Market</div>',unsafe_allow_html=True)
    metals=["Gold","Silver","Copper","Aluminum"]
    st.dataframe(pd.DataFrame([[n,fmt_price(n,data[n]["price"]),pct(data[n]["chg"])] for n in metals],columns=["Metal","Last","1D"]),hide_index=True,use_container_width=True)
    mc1,mc2=st.columns([1.5,1])
    with mc1:
        chart=pd.DataFrame({k:data[k]["history"]["Close"] if not data[k]["history"].empty else pd.Series(dtype=float) for k in metals}).dropna(how="all")
        if not chart.empty: st.line_chart(chart,height=280)
    with mc2:
        for n in metals: st.markdown(f'<div class="signal-row"><b>{n}</b><span class="{tone(data[n]["chg"])}">{pct(data[n]["chg"])}</span></div>',unsafe_allow_html=True)
        st.caption("Provider coverage for some base-metal contracts can vary. The app shows — instead of inventing a value.")

with tabs[4]:
    st.markdown('<div class="eyebrow">05 · Curve & Relative Value</div>',unsafe_allow_html=True)
    c1,c2,c3=st.columns(3)
    w,b=data["WTI"]["price"],data["Brent"]["price"]; g,s=data["Gold"]["price"],data["Silver"]["price"]
    with c1: st.metric("Brent − WTI","—" if pd.isna(w) or pd.isna(b) else f"${b-w:,.2f}")
    with c2: st.metric("Gold / Silver","—" if pd.isna(g) or pd.isna(s) else f"{g/s:,.1f}x")
    with c3: st.metric("Copper 1D",pct(data["Copper"]["chg"]))
    st.info("This build does not fabricate M1–M24 futures curves from spot prices. Connect a free/open curve dataset or exchange/broker feed for true term-structure analytics.")

with tabs[5]:
    st.markdown('<div class="eyebrow">06 · Positioning</div>',unsafe_allow_html=True)
    st.markdown('<div class="desk-card"><b>CFTC COT integration point</b><div class="muted" style="margin-top:6px">Positioning is intentionally not populated with made-up values. Connect the official CFTC Commitments of Traders dataset to calculate net speculative positioning, percentile and z-score.</div></div>',unsafe_allow_html=True)
    st.warning("COT values are not populated until the official CFTC dataset is connected. Price data remains provider-fed.")

with tabs[6]:
    st.markdown('<div class="eyebrow">07 · Macro Context · FRED</div>',unsafe_allow_html=True)
    fred_map={"US 10Y":"DGS10","US 2Y":"DGS2","CPI":"CPIAUCSL","Fed Funds":"FEDFUNDS"}
    for col,(label,sid) in zip(st.columns(4),fred_map.items()):
        df=fred_series(sid,5); val=df["value"].iloc[-1] if not df.empty else np.nan
        with col:
            st.metric(label,"—" if pd.isna(val) else f"{val:,.2f}")
            if not df.empty: st.caption(df["date"].iloc[-1].strftime("%Y-%m-%d"))
    df10=fred_series("DGS10",120)
    if not df10.empty: st.line_chart(df10.set_index("date")["value"],height=260)
    st.caption("FRED is the Federal Reserve Bank of St. Louis public data service. Macro series use its public graph CSV endpoint.")

with tabs[7]:
    st.markdown('<div class="eyebrow">08 · Hedge Desk Action Layer</div>',unsafe_allow_html=True)
    a1,a2=st.columns([1.3,1])
    with a1:
        action=[]
        for n in ["WTI","Brent","Gold","Silver","Copper","DXY","USD/INR"]:
            d=data[n]; bias="POSITIVE" if not pd.isna(d["chg"]) and d["chg"]>0 else "NEGATIVE" if not pd.isna(d["chg"]) and d["chg"]<0 else "NEUTRAL"
            action.append([n,fmt_price(n,d["price"]),pct(d["chg"]),bias])
        st.dataframe(pd.DataFrame(action,columns=["Asset","Last","1D","Bias"]),hide_index=True,use_container_width=True)
    with a2:
        st.markdown('<div class="desk-card"><b>Decision framework</b><div class="signal-row"><span>1 · Regime</span><span class="tag">GLOBAL</span></div><div class="signal-row"><span>2 · Risk factors</span><span class="tag">USD / RATES / VOL</span></div><div class="signal-row"><span>3 · Commodity</span><span class="tag">ENERGY / METALS</span></div><div class="signal-row"><span>4 · Curve / RV</span><span class="tag">SPREADS</span></div><div class="signal-row"><span>5 · Positioning</span><span class="tag">COT</span></div><div class="signal-row"><span>6 · Hedge action</span><span class="tag">EXECUTE / WATCH</span></div></div>',unsafe_allow_html=True)

st.divider()
left,right=st.columns([4,1])
with left: st.caption("MERIDIAN COMMODITY HEDGE DESK · Streamlit portfolio build · Free public/provider data layer")
with right:
    if st.button("↻ Refresh prices",use_container_width=True):
        st.cache_data.clear(); st.rerun()

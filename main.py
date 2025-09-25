import pandas as pd
import numpy as np
import altair as alt
import streamlit as st
from io import StringIO

st.set_page_config(
    page_title="World's Best Hotels — Tourism Insights",
    layout="wide"
)

# -----------------------
# Global Theming (Tourism look & feel)
# -----------------------
THEME_PRIMARY = "#B22222"   # brick red (tourism/luxury vibe)
THEME_ACCENT  = "#c26e29"    # warm amber
THEME_BG_SOFT = "#fff7f0"   # soft warm background blocks

CUSTOM_CSS = f"""
    <style>
        /* Page background stays default for readability */
        .tour-hero {{
            padding: 26px 28px;
            background: linear-gradient(135deg, {THEME_PRIMARY} 0%, #8b1a1a 100%);
            color: white;
            border-radius: 20px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.12);
        }}
        .tour-hero h1 {{
            margin: 0 0 6px 0;
            font-size: 34px;
            line-height: 1.2;
        }}
        .tour-hero p {{
            margin: 0;
            font-size: 15px;
            opacity: 0.95;
        }}
        .tour-card {{
            background: {THEME_BG_SOFT};
            border: 1px solid rgba(0,0,0,0.05);
            border-radius: 16px;
            padding: 18px;
        }}
        .tour-section-title {{
            font-weight: 700;
            font-size: 20px;
            margin: 8px 0 10px;
        }}
        .tour-kpi {{
            background: white;
            border-radius: 16px;
            border: 1px solid rgba(0,0,0,0.06);
            padding: 14px 16px;
            box-shadow: 0 6px 16px rgba(0,0,0,0.05);
        }}
        .tour-kpi .label {{
            font-size: 12px;
            color: #666;
            margin-bottom: 6px;
        }}
        .tour-kpi .value {{
            font-size: 22px;
            font-weight: 700;
            color: {THEME_PRIMARY};
        }}
        .tour-subtle {{
            color: #6e6e6e;
            font-size: 13px;
        }}
        .tour-divider {{
            margin: 6px 0 10px;
            height: 1px;
            background: linear-gradient(90deg, rgba(0,0,0,0.06), rgba(0,0,0,0.0));
        }}
        .tour-badge {{
            display: inline-block;
            background: #fff;
            border: 1px solid rgba(0,0,0,0.08);
            border-radius: 999px;
            padding: 4px 10px;
            font-size: 12px;
            margin-right: 6px;
        }}
        .element-container .stMetric {{
            background: white;
            border-radius: 14px;
            padding: 10px 14px;
            border: 1px solid rgba(0,0,0,0.05);
            box-shadow: 0 6px 16px rgba(0,0,0,0.04);
        }}
        .stDownloadButton button {{
            background: {THEME_PRIMARY};
            border-color: {THEME_PRIMARY};
        }}
        .stDownloadButton button:hover {{
            background: #8b1a1a;
            border-color: #8b1a1a;
        }}
    </style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# -----------------------
# Helpers
# -----------------------
@st.cache_data
def load_data(path: str, encodings=("utf-8", "latin-1", "cp1252")) -> pd.DataFrame:
    last_err = None
    for enc in encodings:
        try:
            df = pd.read_csv(path, encoding=enc)
            return df
        except Exception as e:
            last_err = e
    raise last_err

def clean_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.strip() for c in df.columns]
    for col in ["Rank", "Starting Rate in ($)", "Total Rooms"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].fillna("")
    return df

def filter_df(df: pd.DataFrame, locations, rate_range, name_query):
    out = df.copy()
    if locations:
        out = out[out["Location"].isin(locations)]
    if rate_range:
        low, high = rate_range
        if "Starting Rate in ($)" in out.columns:
            out = out[(out["Starting Rate in ($)"].fillna(0) >= low) & (out["Starting Rate in ($)"].fillna(0) <= high)]
    if name_query:
        q = name_query.lower().strip()
        out = out[out["Name"].str.lower().str.contains(q, na=False)]
    return out

# -----------------------
# Load
# -----------------------
DEFAULT_PATH = "Worlds Best 50 Hotels.csv"

st.markdown("""
    <div class="tour-hero">
        <h1>🏝️ World’s Best Hotels — Tourism Insights Dashboard</h1>
        <p>Explore luxury stays worldwide through a tourism-analytics lens — compare destinations, price ranges, and property characteristics.</p>
    </div>
""", unsafe_allow_html=True)

with st.expander("📁 Data Source", expanded=False):
    st.write("ใช้ไฟล์ `Worlds Best 50 Hotels.csv` ที่อยู่โฟลเดอร์เดียวกับแอป หรืออัปโหลดไฟล์ CSV ใหม่ได้")
    uploaded = st.file_uploader("Upload CSV (optional)", type=["csv"])

if uploaded is not None:
    data = uploaded.read()
    s = StringIO(data.decode("latin-1", errors="ignore"))
    df_raw = pd.read_csv(s)
    path_used = "(uploaded)"
else:
    df_raw = load_data(DEFAULT_PATH, encodings=("latin-1", "cp1252", "utf-8"))
    path_used = DEFAULT_PATH

df = clean_df(df_raw)

st.caption(f"Data source: **{path_used}** • Built for academic tourism analysis.")

# -----------------------
# Filters (Main Page)
# -----------------------
st.markdown('<div class="tour-section-title">🔎 Trip Planning Filters</div>', unsafe_allow_html=True)
filters_col1, filters_col2, filters_col3 = st.columns([1,1,1])

# Location
if "Location" in df.columns:
    with filters_col1:
        sel_locations = st.multiselect(
            "Destination (Location)",
            options=sorted([x for x in df["Location"].dropna().unique()]),
            default=[]
        )
else:
    sel_locations = []

# Price
if "Starting Rate in ($)" in df.columns and not df["Starting Rate in ($)"].dropna().empty:
    rate_min = float(np.nanmin(df["Starting Rate in ($)"].values))
    rate_max = float(np.nanmax(df["Starting Rate in ($)"].values))
    with filters_col2:
        sel_rate = st.slider(
            "Budget: Starting Rate ($)",
            min_value=0.0,
            max_value=max(1000.0, rate_max),
            value=(rate_min, rate_max),
            step=50.0
        )
else:
    sel_rate = None

# Search
with filters_col3:
    name_query = st.text_input("Hotel Name Search", placeholder="e.g., Capella Bangkok, Rosewood...")

df_f = filter_df(df, sel_locations, sel_rate, name_query)

# -----------------------
# KPI Cards
# -----------------------
st.markdown('<div class="tour-section-title">📊 Destination Snapshot</div>', unsafe_allow_html=True)
k1, k2, k3, k4 = st.columns(4)
with k1:
    st.markdown('<div class="tour-kpi"><div class="label">Total Hotels</div><div class="value">'
                f'{len(df_f):,}</div><div class="tour-subtle">properties matching filters</div></div>', unsafe_allow_html=True)
with k2:
    if "Starting Rate in ($)" in df_f.columns and not df_f["Starting Rate in ($)"].dropna().empty:
        st.markdown('<div class="tour-kpi"><div class="label">Avg. Starting Rate</div><div class="value">'
                    f'${df_f["Starting Rate in ($)"].mean():,.0f}</div><div class="tour-subtle">USD per night</div></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="tour-kpi"><div class="label">Avg. Starting Rate</div><div class="value">N/A</div></div>', unsafe_allow_html=True)
with k3:
    if "Starting Rate in ($)" in df_f.columns and not df_f["Starting Rate in ($)"].dropna().empty:
        st.markdown('<div class="tour-kpi"><div class="label">Median Starting Rate</div><div class="value">'
                    f'${df_f["Starting Rate in ($)"].median():,.0f}</div></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="tour-kpi"><div class="label">Median Starting Rate</div><div class="value">N/A</div></div>', unsafe_allow_html=True)
with k4:
    if "Location" in df_f.columns:
        st.markdown('<div class="tour-kpi"><div class="label">Destinations Covered</div><div class="value">'
                    f'{df_f["Location"].nunique():,}</div><div class="tour-subtle">unique locations</div></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="tour-kpi"><div class="label">Destinations Covered</div><div class="value">N/A</div></div>', unsafe_allow_html=True)

st.markdown('<div class="tour-divider"></div>', unsafe_allow_html=True)

# -----------------------
# Charts
# -----------------------
st.markdown('<div class="tour-section-title">📈 Tourism Insights</div>', unsafe_allow_html=True)
c1_col, c2_col = st.columns(2)

# Chart 1
with c1_col:
    if "Starting Rate in ($)" in df_f.columns:
        top10 = df_f.sort_values("Starting Rate in ($)", ascending=False).head(10)
        if not top10.empty:
            chart1 = alt.Chart(top10).mark_bar().encode(
                x=alt.X("Starting Rate in ($):Q", title="Starting Rate (USD)"),
                y=alt.Y("Name:N", sort="-x", title="Hotel"),
                tooltip=["Name", "Location", alt.Tooltip("Starting Rate in ($):Q", format=",.0f")]
            ).properties(title="Luxury Segment — Top 10 by Starting Rate", height=360)
            st.altair_chart(chart1, use_container_width=True)
        else:
            st.info("No data after filters for the Top 10 chart.")
    else:
        st.warning("Column 'Starting Rate in ($)' not found in the dataset.")

# Chart 2
with c2_col:
    if "Starting Rate in ($)" in df_f.columns and not df_f["Starting Rate in ($)"].dropna().empty:
        chart2 = alt.Chart(df_f).mark_bar().encode(
            x=alt.X("Starting Rate in ($):Q", bin=alt.Bin(maxbins=20), title="Budget Bands (USD)"),
            y=alt.Y("count():Q", title="Number of Hotels"),
            tooltip=[alt.Tooltip("count():Q", title="Hotels")]
        ).properties(title="Budget Distribution — Where Most Rates Fall", height=360)
        st.altair_chart(chart2, use_container_width=True)
    else:
        st.info("No numeric data available for distribution chart.")

# Chart 3
st.markdown('<div class="tour-card">', unsafe_allow_html=True)
if "Location" in df_f.columns:
    by_loc = df_f.groupby("Location", as_index=False).agg(Hotels=("Name", "count"))
    by_loc = by_loc.sort_values("Hotels", ascending=False)
    chart3 = alt.Chart(by_loc).mark_bar().encode(
        x=alt.X("Hotels:Q", title="Properties"),
        y=alt.Y("Location:N", sort="-x", title="Destination"),
        tooltip=["Location", "Hotels"]
    ).properties(title="Destination Mix — Count of Hotels by Location", height=520)
    st.altair_chart(chart3, use_container_width=True)
else:
    st.info("Location column not available.")
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="tour-divider"></div>', unsafe_allow_html=True)

# -----------------------
# Data Table
# -----------------------
st.markdown('<div class="tour-section-title">🧳 Property Directory</div>', unsafe_allow_html=True)
show_cols = ["Rank", "Name", "Location", "Starting Rate in ($)", "Total Rooms", "Dining Area", "Drinking Area", "Hotel Ammenties", "Address", "Number"]
existing = [c for c in show_cols if c in df_f.columns]
st.dataframe(df_f[existing].sort_values("Rank", na_position="last") if "Rank" in existing else df_f[existing], use_container_width=True)

csv_bytes = df_f.to_csv(index=False).encode("utf-8")
st.download_button("Download filtered CSV", data=csv_bytes, file_name="hotels_filtered.csv", mime="text/csv")

st.caption("© Tourism Insights Dashboard — Streamlit • Altair • Pandas • Designed with a hospitality aesthetic")

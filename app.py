"""
UK Economic Indicators Dashboard
Reads from the gold layer (econ.duckdb) and displays an interactive view
of the four core indicators, with a sidebar to switch between them.

Run with: streamlit run app.py
"""

import duckdb
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import streamlit as st
from pathlib import Path

st.set_page_config(page_title="UK Economic Dashboard", layout="wide")
sns.set_theme(style="whitegrid")

DB_PATH = Path(__file__).parent / "notebooks"/ "bronze" / "econ.duckdb"

@st.cache_data
def load_data():
    con = duckdb.connect(str(DB_PATH), read_only=True)
    df = con.sql("SELECT * FROM gold_quarterly_metrics ORDER BY date").df()
    con.close()
    return df

df = load_data()
latest = df.iloc[-1]

INDICATORS = {
    "Unemployment Rate": {
        "value_col": "unemployment_rate",
        "change_col": "unemployment_qoq_change",
        "color": "#1f2f6b",
        "unit": "%",
        "ylabel": "Unemployment Rate (%)",
    },
    "CPI Inflation": {
        "value_col": "inflation_rate",
        "change_col": "inflation_qoq_change",
        "color": "#d62728",
        "unit": "%",
        "ylabel": "Inflation Rate (%)",
    },
    "GDP (current prices)": {
        "value_col": "gdp_in_gbp_m",
        "change_col": "gdp_qoq_change",
        "color": "#2ca02c",
        "unit": "£m",
        "ylabel": "GDP (£ million)",
    },
    "Trade Balance": {
        "value_col": "trade_balance_gbp_m",
        "change_col": "trade_balance_qoq_change",
        "color": "#9467bd",
        "unit": "£m",
        "ylabel": "Trade Balance (£ million)",
    },
}

st.title("🇬🇧 UK Economic Indicators Dashboard")
st.caption(
    f"Data from the ONS API · {df['quarter_raw'].iloc[0]} – {df['quarter_raw'].iloc[-1]} "
    "· Built with a bronze/silver/gold medallion pipeline"
)

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric(
    "Unemployment Rate",
    f"{latest['unemployment_rate']:.1f}%",
    f"{latest['unemployment_qoq_change']:+.1f}pp",
    delta_color="inverse",  # rising unemployment is "bad", so invert the red/green
)
col2.metric(
    "CPI Inflation",
    f"{latest['inflation_rate']:.1f}%",
    f"{latest['inflation_qoq_change']:+.1f}pp",
    delta_color="inverse",
)
col3.metric(
    "GDP",
    f"£{latest['gdp_in_gbp_m']:,.0f}m",
    f"{latest['gdp_qoq_change']:+,.0f}m",
)
col4.metric(
    "Trade Balance",
    f"£{latest['trade_balance_gbp_m']:,.0f}m",
    f"{latest['trade_balance_qoq_change']:+,.0f}m",
)
col5.metric(
    "Current Status",
    "⚠️ Recession" if latest["uk_technical_recession_flag"] else "✅ No recession",
)

st.divider()

st.sidebar.header("Select indicator")
selected = st.sidebar.radio("Indicator", list(INDICATORS.keys()), label_visibility="collapsed")
config = INDICATORS[selected]

st.sidebar.divider()
st.sidebar.markdown(
    "**About this dashboard**\n\n"
    "Built on UK ONS data: unemployment, CPI inflation, GDP, and trade balance, "
    "pulled quarterly since 1997. The technical recession flag marks quarters "
    "with two consecutive periods of negative GDP growth."
)

st.subheader(selected)

fig, ax = plt.subplots(figsize=(12, 5))
sns.lineplot(data=df, x="date", y=config["value_col"], color=config["color"], linewidth=1.8, ax=ax)


if selected == "GDP (current prices)":
    recession_points = df[df["uk_technical_recession_flag"]]
    ax.scatter(
        recession_points["date"], recession_points[config["value_col"]],
        color="red", s=40, zorder=5, label="Recession quarter",
    )
    ax.legend()


if selected == "CPI Inflation":
    ax.axhline(y=2, color="gray", linestyle="--", linewidth=1, label="BoE 2% target")
    ax.legend()

if selected == "Trade Balance":
    ax.axhline(y=0, color="black", linewidth=0.8)

ax.xaxis.set_major_locator(mdates.YearLocator(base=4))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax.set_xlabel("Year")
ax.set_ylabel(config["ylabel"])
plt.xticks(rotation=45)
plt.tight_layout()

st.pyplot(fig)

with st.expander("View underlying data"):
    st.dataframe(
        df[["quarter_raw", config["value_col"], config["change_col"]]].sort_values(
            "quarter_raw", ascending=False
        ),
        use_container_width=True,
    )
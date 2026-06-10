import numpy as np
import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="Cross-Channel Ads Dashboard",
    page_icon="📊",
    layout="wide",
)


@st.cache_data
def load_data():
    data = pd.read_csv("data/ads_all.csv")
    data["date"] = pd.to_datetime(data["date"])

    numeric_cols = [
        "impressions",
        "clicks",
        "spend",
        "conversions",
        "revenue",
        "video_views",
        "reach",
        "frequency",
        "likes",
        "shares",
        "comments",
    ]

    for col in numeric_cols:
        if col in data.columns:
            data[col] = pd.to_numeric(data[col], errors="coerce")

    if "revenue" not in data.columns:
        data["revenue"] = 0

    data["revenue"] = data["revenue"].fillna(0)
    data["ctr"] = np.where(data["impressions"] > 0, data["clicks"] / data["impressions"], np.nan)
    data["cpc"] = np.where(data["clicks"] > 0, data["spend"] / data["clicks"], np.nan)
    data["conversion_rate"] = np.where(data["clicks"] > 0, data["conversions"] / data["clicks"], np.nan)
    data["cpa"] = np.where(data["conversions"] > 0, data["spend"] / data["conversions"], np.nan)
    data["roas"] = np.where(data["spend"] > 0, data["revenue"] / data["spend"], np.nan)

    return data


def add_rate_metrics(summary):
    summary = summary.copy()
    summary["ctr"] = np.where(summary["impressions"] > 0, summary["clicks"] / summary["impressions"], np.nan)
    summary["cpc"] = np.where(summary["clicks"] > 0, summary["spend"] / summary["clicks"], np.nan)
    summary["conversion_rate"] = np.where(summary["clicks"] > 0, summary["conversions"] / summary["clicks"], np.nan)
    summary["cpa"] = np.where(summary["conversions"] > 0, summary["spend"] / summary["conversions"], np.nan)
    summary["roas"] = np.where(summary["spend"] > 0, summary["revenue"] / summary["spend"], np.nan)
    return summary


def format_currency(value):
    return f"${value:,.0f}"


def format_number(value):
    return f"{value:,.0f}"


def format_percent(value):
    return f"{value:.2%}"


data = load_data()

st.title("Cross-Channel Ads Dashboard")
st.caption("Unified Facebook, Google, and TikTok campaign performance.")

with st.sidebar:
    st.header("Filters")
    platform_options = sorted(data["platform"].dropna().unique())
    selected_platforms = st.multiselect("Platform", platform_options, default=platform_options)

    min_date = data["date"].min().date()
    max_date = data["date"].max().date()
    selected_dates = st.date_input("Date range", value=(min_date, max_date), min_value=min_date, max_value=max_date)

    filtered_for_campaigns = data[data["platform"].isin(selected_platforms)]
    campaign_options = sorted(filtered_for_campaigns["campaign_name"].dropna().unique())
    selected_campaigns = st.multiselect("Campaign", campaign_options, default=campaign_options)

if len(selected_dates) == 2:
    start_date, end_date = selected_dates
else:
    start_date, end_date = min_date, max_date

filtered_data = data[
    data["platform"].isin(selected_platforms)
    & data["campaign_name"].isin(selected_campaigns)
    & (data["date"].dt.date >= start_date)
    & (data["date"].dt.date <= end_date)
].copy()

if filtered_data.empty:
    st.warning("No data for the selected filters.")
    st.stop()

totals = filtered_data.agg(
    {
        "spend": "sum",
        "impressions": "sum",
        "clicks": "sum",
        "conversions": "sum",
        "revenue": "sum",
    }
)

total_ctr = totals["clicks"] / totals["impressions"] if totals["impressions"] else np.nan
total_cpa = totals["spend"] / totals["conversions"] if totals["conversions"] else np.nan
total_roas = totals["revenue"] / totals["spend"] if totals["spend"] else np.nan

cols = st.columns(6)
cols[0].metric("Spend", format_currency(totals["spend"]))
cols[1].metric("Impressions", format_number(totals["impressions"]))
cols[2].metric("Clicks", format_number(totals["clicks"]))
cols[3].metric("Conversions", format_number(totals["conversions"]))
cols[4].metric("CTR", format_percent(total_ctr))
cols[5].metric("CPA", format_currency(total_cpa))

st.subheader("Performance Over Time")
daily_summary = (
    filtered_data.groupby("date", as_index=False)
    .agg(
        spend=("spend", "sum"),
        clicks=("clicks", "sum"),
        conversions=("conversions", "sum"),
        revenue=("revenue", "sum"),
    )
    .sort_values("date")
)

trend_metric = st.selectbox("Trend metric", ["spend", "clicks", "conversions", "revenue"])
st.line_chart(daily_summary.set_index("date")[trend_metric])

st.subheader("Platform Comparison")
platform_summary = (
    filtered_data.groupby("platform", as_index=False)
    .agg(
        spend=("spend", "sum"),
        impressions=("impressions", "sum"),
        clicks=("clicks", "sum"),
        conversions=("conversions", "sum"),
        revenue=("revenue", "sum"),
    )
    .pipe(add_rate_metrics)
    .sort_values("spend", ascending=False)
)

left_col, right_col = st.columns(2)
left_col.bar_chart(platform_summary.set_index("platform")["spend"])
right_col.bar_chart(platform_summary.set_index("platform")["conversions"])

st.subheader("Campaign Performance")
campaign_summary = (
    filtered_data.groupby(["platform", "campaign_name"], as_index=False)
    .agg(
        spend=("spend", "sum"),
        impressions=("impressions", "sum"),
        clicks=("clicks", "sum"),
        conversions=("conversions", "sum"),
        revenue=("revenue", "sum"),
    )
    .pipe(add_rate_metrics)
    .sort_values("spend", ascending=False)
)

display_cols = [
    "platform",
    "campaign_name",
    "spend",
    "impressions",
    "clicks",
    "conversions",
    "revenue",
    "ctr",
    "cpc",
    "conversion_rate",
    "cpa",
    "roas",
]

st.dataframe(
    campaign_summary[display_cols],
    use_container_width=True,
    hide_index=True,
    column_config={
        "spend": st.column_config.NumberColumn("Spend", format="$%.2f"),
        "revenue": st.column_config.NumberColumn("Revenue", format="$%.2f"),
        "ctr": st.column_config.NumberColumn("CTR", format="%.2f"),
        "cpc": st.column_config.NumberColumn("CPC", format="$%.2f"),
        "conversion_rate": st.column_config.NumberColumn("Conversion Rate", format="%.2f"),
        "cpa": st.column_config.NumberColumn("CPA", format="$%.2f"),
        "roas": st.column_config.NumberColumn("ROAS", format="%.2f"),
    },
)

st.caption("Revenue and ROAS are meaningful only where revenue is available in the source data.")

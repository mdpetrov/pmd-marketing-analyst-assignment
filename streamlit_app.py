import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
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


def metric_label(metric):
    return {
        "spend": "Spend",
        "impressions": "Impressions",
        "clicks": "Clicks",
        "conversions": "Conversions",
        "revenue": "Revenue",
        "ctr": "CTR",
        "cpc": "CPC",
        "conversion_rate": "Conversion Rate",
        "cpa": "CPA",
        "roas": "ROAS",
    }[metric]


def format_chart_value(value, metric):
    if pd.isna(value):
        return ""
    if metric in {"spend", "revenue", "cpc", "cpa"}:
        return f"${value:,.0f}" if value >= 10 else f"${value:,.2f}"
    if metric in {"ctr", "conversion_rate"}:
        return f"{value:.1%}"
    if metric == "roas":
        return f"{value:.1f}x"
    return f"{value:,.0f}"


def add_value_labels(frame, metric):
    frame = frame.copy()
    frame["value_label"] = frame[metric].apply(lambda value: format_chart_value(value, metric))
    return frame


PLATFORM_COLORS = {
    "facebook": "#1877F2",
    "google": "#34A853",
    "tiktok": "#111111",
}


def platform_color(platform):
    return PLATFORM_COLORS.get(platform, "#666666")


def style_axis(ax):
    ax.grid(axis="y", alpha=0.25)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def render_line_chart(frame, metric, title, subtitle):
    metric_name = metric_label(metric)
    chart = add_value_labels(frame, metric)

    fig, ax = plt.subplots(figsize=(12, 4.8))
    ax.plot(chart["date"], chart[metric], marker="o", linewidth=2.5, label=metric_name)

    for row in chart.itertuples(index=False):
        ax.annotate(
            row.value_label,
            (row.date, getattr(row, metric)),
            textcoords="offset points",
            xytext=(0, 8),
            ha="center",
            fontsize=8,
        )

    ax.set_title(f"{title}\n{subtitle}", loc="left", fontsize=13, pad=16)
    ax.set_xlabel("Date")
    ax.set_ylabel(metric_name)
    ax.legend(title="Metric")
    style_axis(ax)
    fig.autofmt_xdate()
    fig.tight_layout()
    st.pyplot(fig)


def render_vertical_bar_chart(frame, metric, title, subtitle):
    metric_name = metric_label(metric)
    chart = add_value_labels(frame, metric)
    colors = [platform_color(platform) for platform in chart["platform"]]

    fig, ax = plt.subplots(figsize=(7, 4.8))
    bars = ax.bar(chart["platform"], chart[metric], color=colors)

    for bar, label in zip(bars, chart["value_label"]):
        ax.annotate(
            label,
            (bar.get_x() + bar.get_width() / 2, bar.get_height()),
            textcoords="offset points",
            xytext=(0, 6),
            ha="center",
            fontsize=9,
        )

    ax.set_title(f"{title}\n{subtitle}", loc="left", fontsize=12, pad=14)
    ax.set_xlabel("Platform")
    ax.set_ylabel(metric_name)
    style_axis(ax)
    fig.tight_layout()
    st.pyplot(fig)


def render_horizontal_campaign_chart(frame, metric, title, subtitle):
    metric_name = metric_label(metric)
    chart = add_value_labels(frame, metric)
    colors = [platform_color(platform) for platform in chart["platform"]]

    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.barh(chart["campaign_name"], chart[metric], color=colors)

    for bar, label in zip(bars, chart["value_label"]):
        ax.annotate(
            label,
            (bar.get_width(), bar.get_y() + bar.get_height() / 2),
            textcoords="offset points",
            xytext=(6, 0),
            va="center",
            fontsize=9,
        )

    legend_platforms = chart["platform"].drop_duplicates()
    handles = [
        plt.Line2D([0], [0], marker="s", color="w", markerfacecolor=platform_color(platform), markersize=10)
        for platform in legend_platforms
    ]
    ax.legend(handles, legend_platforms, title="Platform")
    ax.set_title(f"{title}\n{subtitle}", loc="left", fontsize=13, pad=16)
    ax.set_xlabel(metric_name)
    ax.set_ylabel("")
    style_axis(ax)
    fig.tight_layout()
    st.pyplot(fig)


data = load_data()

st.title("Cross-Channel Ads Dashboard")
st.caption("Unified Facebook, Google, and TikTok campaign performance, January 2024.")

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

story_col_1, story_col_2, story_col_3 = st.columns(3)
story_col_1.info(
    "Scale: TikTok carries the largest media volume and conversion count, but needs efficiency control."
)
story_col_2.info(
    "Revenue: Google is the only platform with revenue data, so ROAS should be read as Google-attributed."
)
story_col_3.info(
    "Efficiency: campaign-level CPA separates scalable growth from expensive traffic."
)

cols = st.columns(7)
cols[0].metric("Spend", format_currency(totals["spend"]))
cols[1].metric("Impressions", format_number(totals["impressions"]))
cols[2].metric("Clicks", format_number(totals["clicks"]))
cols[3].metric("Conversions", format_number(totals["conversions"]))
cols[4].metric("Revenue", format_currency(totals["revenue"]))
cols[5].metric("CTR", format_percent(total_ctr))
cols[6].metric("CPA", format_currency(total_cpa))

st.subheader("1. Overall Momentum")
daily_summary = (
    filtered_data.groupby("date", as_index=False)
    .agg(
        impressions=("impressions", "sum"),
        spend=("spend", "sum"),
        clicks=("clicks", "sum"),
        conversions=("conversions", "sum"),
        revenue=("revenue", "sum"),
    )
    .pipe(add_rate_metrics)
    .sort_values("date")
)

trend_metric = st.selectbox("Trend metric", ["spend", "conversions", "clicks", "revenue", "cpa"])
trend_metric_name = metric_label(trend_metric)
render_line_chart(
    daily_summary,
    trend_metric,
    f"Daily {trend_metric_name}",
    "Shows whether selected campaigns are stable, scaling, or deteriorating over time.",
)

st.subheader("2. Channel Role")
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
with left_col:
    render_vertical_bar_chart(
        platform_summary,
        "spend",
        "Spend by Platform",
        "TikTok receives the largest budget allocation in the current mix.",
    )
with right_col:
    render_vertical_bar_chart(
        platform_summary,
        "conversions",
        "Conversions by Platform",
        "Conversion volume should be compared against CPA before increasing spend.",
    )

st.subheader("3. Efficiency Trade-Off")
efficiency_summary = platform_summary.sort_values("cpa", ascending=True)
campaign_like_efficiency = efficiency_summary.assign(campaign_name=efficiency_summary["platform"])
render_horizontal_campaign_chart(
    campaign_like_efficiency,
    "cpa",
    "CPA by Platform",
    "Lower CPA means cheaper conversions; compare this with volume before reallocating budget.",
)

st.subheader("4. Campaign-Level Decisions")
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

top_campaigns = campaign_summary.nlargest(10, "spend").sort_values("spend", ascending=True)
render_horizontal_campaign_chart(
    top_campaigns,
    "spend",
    "Top Campaigns by Spend",
    "Largest budget lines are the first candidates for efficiency review.",
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
    width="stretch",
    hide_index=True,
    column_config={
        "spend": st.column_config.NumberColumn("Spend", format="$%.2f"),
        "revenue": st.column_config.NumberColumn("Revenue", format="$%.2f"),
        "ctr": st.column_config.NumberColumn("CTR", format="%.2%"),
        "cpc": st.column_config.NumberColumn("CPC", format="$%.2f"),
        "conversion_rate": st.column_config.NumberColumn("Conversion Rate", format="%.2%"),
        "cpa": st.column_config.NumberColumn("CPA", format="$%.2f"),
        "roas": st.column_config.NumberColumn("ROAS", format="%.2f"),
    },
)

st.caption("Revenue and ROAS are meaningful only where revenue is available in the source data.")

import numpy as np
import pandas as pd
import plotly.express as px
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
    "tiktok": "#25F4EE",
}


def chart_title(title, subtitle):
    return f"{title}<br><sup>{subtitle}</sup>"


def render_line_chart(frame, metric, title, subtitle):
    metric_name = metric_label(metric)
    chart = add_value_labels(frame, metric)

    fig = px.line(
        chart,
        x="date",
        y=metric,
        markers=True,
        text="value_label",
        title=chart_title(title, subtitle),
        labels={"date": "Date", metric: metric_name},
    )
    fig.update_traces(
        line=dict(width=3, color="#4E79A7"),
        marker=dict(size=7),
        textposition="top center",
        name=metric_name,
        showlegend=False,
    )
    fig.update_layout(
        hovermode="x unified",
        margin=dict(t=90, r=30, b=50, l=60),
        yaxis_title=metric_name,
        xaxis_title="Date",
    )
    st.plotly_chart(fig, width="stretch")


def render_vertical_bar_chart(frame, metric, title, subtitle):
    metric_name = metric_label(metric)
    chart = add_value_labels(frame, metric)

    fig = px.bar(
        chart,
        x="platform",
        y=metric,
        color="platform",
        text="value_label",
        color_discrete_map=PLATFORM_COLORS,
        title=chart_title(title, subtitle),
        labels={"platform": "Platform", metric: metric_name},
    )
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_layout(
        legend_title_text="Platform",
        margin=dict(t=90, r=30, b=50, l=60),
        yaxis_title=metric_name,
        xaxis_title="Platform",
    )
    st.plotly_chart(fig, width="stretch")


def render_horizontal_campaign_chart(frame, metric, title, subtitle):
    metric_name = metric_label(metric)
    chart = add_value_labels(frame, metric)

    fig = px.bar(
        chart,
        x=metric,
        y="campaign_name",
        color="platform",
        orientation="h",
        text="value_label",
        color_discrete_map=PLATFORM_COLORS,
        title=chart_title(title, subtitle),
        labels={"campaign_name": "Campaign", metric: metric_name, "platform": "Platform"},
    )
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_layout(
        legend_title_text="Platform",
        margin=dict(t=90, r=50, b=50, l=40),
        xaxis_title=metric_name,
        yaxis_title=None,
    )
    st.plotly_chart(fig, width="stretch")


def make_display_table(frame):
    table = frame.copy()
    table = table[[
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
    ]]
    table["spend"] = table["spend"].map(lambda value: format_chart_value(value, "spend"))
    table["impressions"] = table["impressions"].map(lambda value: format_chart_value(value, "impressions"))
    table["clicks"] = table["clicks"].map(lambda value: format_chart_value(value, "clicks"))
    table["conversions"] = table["conversions"].map(lambda value: format_chart_value(value, "conversions"))
    table["revenue"] = table["revenue"].map(lambda value: format_chart_value(value, "revenue"))
    table["ctr"] = table["ctr"].map(lambda value: format_chart_value(value, "ctr"))
    table["cpc"] = table["cpc"].map(lambda value: format_chart_value(value, "cpc"))
    table["conversion_rate"] = table["conversion_rate"].map(lambda value: format_chart_value(value, "conversion_rate"))
    table["cpa"] = table["cpa"].map(lambda value: format_chart_value(value, "cpa"))
    table["roas"] = table["roas"].map(lambda value: format_chart_value(value, "roas"))
    return table.rename(
        columns={
            "platform": "Platform",
            "campaign_name": "Campaign",
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
        }
    )


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

st.dataframe(
    make_display_table(campaign_summary),
    width="stretch",
    hide_index=True,
)

st.caption("Revenue and ROAS are meaningful only where revenue is available in the source data.")

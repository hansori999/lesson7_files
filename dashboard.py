import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from data_loader import (
    load_all_datasets,
    build_sales_data,
    filter_delivered_orders,
    add_delivery_speed,
    categorize_delivery_speed,
)
from business_metrics import (
    calculate_total_revenue,
    calculate_revenue_growth,
    calculate_monthly_revenue,
    calculate_average_order_value,
    calculate_order_count,
    calculate_category_revenue,
    calculate_state_revenue,
    calculate_average_review_score,
    calculate_delivery_review_correlation,
    calculate_average_delivery_time,
)

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="E-Commerce Sales Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Global CSS ─────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
.main .block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
    max-width: 1400px;
}

/* ── KPI cards ── */
.kpi-card {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    padding: 20px 22px 16px;
    height: 130px;
    display: flex;
    flex-direction: column;
    justify-content: flex-start;
    gap: 8px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.07);
}
.kpi-title {
    font-size: 0.74rem;
    color: #6b7280;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.07em;
}
.kpi-value {
    font-size: 1.8rem;
    font-weight: 700;
    color: #111827;
    line-height: 1.15;
}
.kpi-trend {
    font-size: 0.8rem;
    font-weight: 600;
}

/* ── Bottom metric cards ── */
.metric-card {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    padding: 24px 28px;
    height: 150px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    gap: 4px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.07);
}
.metric-title {
    font-size: 0.74rem;
    color: #6b7280;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.07em;
}
.metric-value {
    font-size: 2.2rem;
    font-weight: 700;
    color: #111827;
    line-height: 1.1;
}
.metric-trend {
    font-size: 0.8rem;
    font-weight: 600;
}
.metric-stars {
    font-size: 1.2rem;
    color: #f59e0b;
    line-height: 1.2;
}
.metric-subtitle {
    font-size: 0.8rem;
    color: #6b7280;
}
</style>
""",
    unsafe_allow_html=True,
)

# ── Chart style constants ──────────────────────────────────────────────────────
CHART_BG   = "#ffffff"
GRID_COLOR = "#f3f4f6"
BLUE_DARK  = "#1f4e79"
BLUE_MID   = "#2e75b6"
BLUE_LIGHT = "#9dc3e6"

MONTH_LABELS = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]
DELIVERY_ORDER = ["1-3 days", "4-7 days", "8+ days"]


# ── Data loading (cached) ──────────────────────────────────────────────────────
@st.cache_data
def load_data():
    ds = load_all_datasets("ecommerce_data")
    sales = build_sales_data(ds["orders"], ds["order_items"])
    sales_del = filter_delivered_orders(sales)
    sales_del = add_delivery_speed(sales_del)
    sales_del["delivery_time"] = sales_del["delivery_speed_days"].apply(
        categorize_delivery_speed
    )
    return (
        sales_del,
        ds["orders"],
        ds["products"],
        ds["customers"],
        ds["reviews"],
    )


sales_all, orders, products, customers, reviews = load_data()


# ── Helpers ────────────────────────────────────────────────────────────────────
def fmt(v):
    """Compact dollar format: $1.2M, $300K, $42."""
    try:
        if pd.isna(v):
            return "N/A"
    except (TypeError, ValueError):
        return "N/A"
    if abs(v) >= 1_000_000:
        return f"${v / 1_000_000:.1f}M"
    if abs(v) >= 1_000:
        return f"${v / 1_000:.0f}K"
    return f"${v:.0f}"


def trend_tag(growth, css_class="kpi-trend", inverted=False):
    """Return colored HTML trend badge, or empty string when unavailable."""
    try:
        if growth is None or pd.isna(growth):
            return ""
    except (TypeError, ValueError):
        return ""
    pct = growth * 100
    positive = pct >= 0
    if inverted:
        positive = not positive
    arrow = "▲" if pct >= 0 else "▼"
    color = "#16a34a" if positive else "#dc2626"
    return (
        f'<div class="{css_class}" style="color:{color}">'
        f"{arrow} {abs(pct):.2f}% vs prior year</div>"
    )


def kpi_card_html(title, value, growth=None, inverted=False):
    return (
        f'<div class="kpi-card">'
        f'<div class="kpi-title">{title}</div>'
        f'<div class="kpi-value">{value}</div>'
        f"{trend_tag(growth, 'kpi-trend', inverted)}"
        f"</div>"
    )


def axis_ticks(values, n=6):
    """Evenly-spaced compact-currency tick values and text from 0 to max."""
    clean = []
    for v in values:
        try:
            if v is not None and not pd.isna(v):
                clean.append(float(v))
        except (TypeError, ValueError):
            pass
    if not clean:
        return [0], ["$0"]
    ticks = np.linspace(0, max(clean), n)
    return ticks.tolist(), [fmt(t) for t in ticks]


def star_str(score):
    """Return filled/empty star string rounded to nearest integer."""
    try:
        n = int(round(float(score)))
        n = max(0, min(5, n))
    except (TypeError, ValueError):
        n = 0
    return "★" * n + "☆" * (5 - n)


# ── Header ─────────────────────────────────────────────────────────────────────
hdr_l, hdr_r = st.columns([3, 2])
with hdr_l:
    st.markdown("## E-Commerce Sales Dashboard")
with hdr_r:
    available_years = sorted(
        sales_all["order_purchase_timestamp"].dt.year.unique(), reverse=True
    )
    default_year_idx = available_years.index(2023) if 2023 in available_years else 0
    f_year, f_month = st.columns(2)
    with f_year:
        sel_year = st.selectbox("Year", available_years, index=default_year_idx)
    with f_month:
        month_options = ["All"] + MONTH_LABELS
        sel_month_label = st.selectbox("Month", month_options, index=0)
        sel_month = (
            None if sel_month_label == "All"
            else MONTH_LABELS.index(sel_month_label) + 1
        )

# ── Apply filters ──────────────────────────────────────────────────────────────
ts = sales_all["order_purchase_timestamp"]

year_mask = ts.dt.year == sel_year
comp_mask = ts.dt.year == (sel_year - 1)

if sel_month is not None:
    month_mask = ts.dt.month == sel_month
    year_mask  = year_mask & month_mask
    comp_mask  = comp_mask & month_mask

sales_curr = sales_all[year_mask].copy()
sales_comp = sales_all[comp_mask].copy()

# ── KPI calculations ───────────────────────────────────────────────────────────
rev_curr   = calculate_total_revenue(sales_curr)
rev_comp   = calculate_total_revenue(sales_comp)
rev_growth = calculate_revenue_growth(rev_curr, rev_comp)

_monthly_rev = calculate_monthly_revenue(sales_curr)
if len(_monthly_rev) > 1:
    mom_mean    = float(_monthly_rev.pct_change().mean())
    mom_display = f"{mom_mean * 100:+.2f}%"
else:
    mom_display = "N/A"

aov_curr   = calculate_average_order_value(sales_curr)
aov_comp   = calculate_average_order_value(sales_comp)
aov_growth = calculate_revenue_growth(aov_curr, aov_comp)

orders_curr   = calculate_order_count(sales_curr)
orders_comp   = calculate_order_count(sales_comp)
orders_growth = calculate_revenue_growth(orders_curr, orders_comp)

# ── KPI Row ────────────────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)
for col, title, value, growth in [
    (k1, "Total Revenue",   fmt(rev_curr),       rev_growth),
    (k2, "Monthly Growth",  mom_display,          None),
    (k3, "Avg Order Value", f"${aov_curr:.2f}",   aov_growth),
    (k4, "Total Orders",    f"{orders_curr:,}",   orders_growth),
]:
    with col:
        st.markdown(kpi_card_html(title, value, growth), unsafe_allow_html=True)

st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

# ── Charts Row 1 ───────────────────────────────────────────────────────────────
c1, c2 = st.columns(2)

# ── Revenue Trend ──────────────────────────────────────────────────────────────
with c1:
    rev_by_month_curr = calculate_monthly_revenue(sales_curr)
    rev_by_month_comp = calculate_monthly_revenue(sales_comp)

    months_all = sorted(
        set(rev_by_month_curr.index) | set(rev_by_month_comp.index)
    )
    trend_df = pd.DataFrame(
        {
            "month":      months_all,
            "current":    [rev_by_month_curr.get(m) for m in months_all],
            "comparison": [rev_by_month_comp.get(m) for m in months_all],
            "label":      [MONTH_LABELS[m - 1] for m in months_all],
        }
    )

    all_vals = (
        [v for v in rev_by_month_curr.values if v is not None]
        + [v for v in rev_by_month_comp.values if v is not None]
    )
    tv, tt = axis_ticks(all_vals)

    fig_trend = go.Figure()
    fig_trend.add_trace(
        go.Scatter(
            x=trend_df["label"],
            y=trend_df["current"],
            mode="lines+markers",
            name="Current Period",
            line=dict(color=BLUE_DARK, width=2.5, dash="solid"),
            marker=dict(size=5, color=BLUE_DARK),
        )
    )
    fig_trend.add_trace(
        go.Scatter(
            x=trend_df["label"],
            y=trend_df["comparison"],
            mode="lines+markers",
            name="Prior Period",
            line=dict(color=BLUE_LIGHT, width=2, dash="dash"),
            marker=dict(size=4, color=BLUE_LIGHT),
        )
    )
    fig_trend.update_yaxes(
        tickvals=tv,
        ticktext=tt,
        showgrid=True,
        gridcolor=GRID_COLOR,
        zeroline=False,
        tickfont=dict(size=12, color="#374151"),
    )
    fig_trend.update_xaxes(
        showgrid=True,
        gridcolor=GRID_COLOR,
        tickfont=dict(size=12, color="#374151"),
    )
    fig_trend.update_layout(
        title="Revenue Trend",
        title_font=dict(size=15, color="#111827"),
        plot_bgcolor=CHART_BG,
        paper_bgcolor=CHART_BG,
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, x=0,
                    font=dict(size=12, color="#374151")),
        margin=dict(l=10, r=10, t=45, b=10),
        height=370,
    )
    st.plotly_chart(fig_trend, use_container_width=True)

# ── Top 10 Categories ──────────────────────────────────────────────────────────
with c2:
    cat_rev = calculate_category_revenue(sales_curr, products).head(10)
    cat_df  = cat_rev.reset_index()
    cat_df.columns = ["category", "revenue"]
    # Sort ascending so the highest bar appears at the top in a horizontal chart
    cat_df = cat_df.sort_values("revenue", ascending=True).reset_index(drop=True)

    n      = len(cat_df)
    colors = [
        f"rgba(31,78,121,{0.2 + 0.8 * i / max(n - 1, 1)})" for i in range(n)
    ]

    max_cat = cat_df["revenue"].max() if not cat_df.empty else 1
    xtv, xtt = axis_ticks(cat_df["revenue"].tolist())

    fig_cat = go.Figure(
        go.Bar(
            x=cat_df["revenue"],
            y=cat_df["category"],
            orientation="h",
            marker_color=colors,
            text=[fmt(v) for v in cat_df["revenue"]],
            textposition="outside",
            cliponaxis=False,
        )
    )
    fig_cat.update_xaxes(
        tickvals=xtv,
        ticktext=xtt,
        showgrid=True,
        gridcolor=GRID_COLOR,
        range=[0, max_cat * 1.3],
        tickfont=dict(size=12, color="#374151"),
        automargin=True,
    )
    fig_cat.update_yaxes(
        showgrid=False,
        tickfont=dict(size=12, color="#374151"),
        automargin=True,
    )
    fig_cat.update_layout(
        title="Top 10 Categories by Revenue",
        title_font=dict(size=15, color="#111827"),
        plot_bgcolor=CHART_BG,
        paper_bgcolor=CHART_BG,
        margin=dict(l=180, r=80, t=45, b=40),
        height=370,
    )
    st.plotly_chart(fig_cat, use_container_width=True)

# ── Charts Row 2 ───────────────────────────────────────────────────────────────
c3, c4 = st.columns(2)

# ── Revenue by State ───────────────────────────────────────────────────────────
with c3:
    state_rev = calculate_state_revenue(sales_curr, orders, customers)
    max_sr    = state_rev["price"].max() if not state_rev.empty else 1
    cb_ticks  = np.linspace(0, max_sr, 5)

    fig_map = px.choropleth(
        state_rev,
        locations="customer_state",
        color="price",
        locationmode="USA-states",
        scope="usa",
        color_continuous_scale="Blues",
        labels={"price": "Revenue", "customer_state": "State"},
    )
    fig_map.update_coloraxes(
        colorbar=dict(
            title="Revenue",
            tickvals=cb_ticks.tolist(),
            ticktext=[fmt(v) for v in cb_ticks],
            len=0.75,
        )
    )
    fig_map.update_layout(
        title="Revenue by State",
        title_font=dict(size=15, color="#111827"),
        margin=dict(l=0, r=0, t=45, b=0),
        height=370,
        geo=dict(bgcolor=CHART_BG),
    )
    st.plotly_chart(fig_map, use_container_width=True)

# ── Review Score by Delivery Time ──────────────────────────────────────────────
with c4:
    deliv_rev = calculate_delivery_review_correlation(sales_curr, reviews)
    dr = (
        deliv_rev
        .set_index("delivery_time")
        .reindex(DELIVERY_ORDER)
        .reset_index()
    )

    fig_dr = go.Figure(
        go.Bar(
            x=dr["delivery_time"],
            y=dr["review_score"],
            marker_color=[BLUE_DARK, BLUE_MID, BLUE_LIGHT],
            text=[
                f"{v:.2f}" if not pd.isna(v) else ""
                for v in dr["review_score"]
            ],
            textposition="outside",
        )
    )
    fig_dr.update_yaxes(
        range=[0, 5.6],
        showgrid=True,
        gridcolor=GRID_COLOR,
        title="Avg Review Score",
    )
    fig_dr.update_xaxes(title="Delivery Time")
    fig_dr.update_layout(
        title="Review Score by Delivery Time",
        title_font=dict(size=15, color="#111827"),
        plot_bgcolor=CHART_BG,
        paper_bgcolor=CHART_BG,
        margin=dict(l=10, r=10, t=45, b=10),
        height=370,
    )
    st.plotly_chart(fig_dr, use_container_width=True)

# ── Bottom Row ─────────────────────────────────────────────────────────────────
st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
b1, b2 = st.columns(2)

avg_del_curr = calculate_average_delivery_time(sales_curr)
avg_del_comp = calculate_average_delivery_time(sales_comp)
del_growth   = calculate_revenue_growth(avg_del_curr, avg_del_comp)

avg_rev_score = calculate_average_review_score(sales_curr, reviews)

with b1:
    st.markdown(
        f'<div class="metric-card">'
        f'  <div class="metric-title">Average Delivery Time</div>'
        f'  <div class="metric-value">{avg_del_curr:.1f} days</div>'
        f"  {trend_tag(del_growth, 'metric-trend', inverted=True)}"
        f"</div>",
        unsafe_allow_html=True,
    )

with b2:
    st.markdown(
        f'<div class="metric-card">'
        f'  <div class="metric-title">Review Score</div>'
        f'  <div class="metric-value">{avg_rev_score:.2f}</div>'
        f'  <div class="metric-stars">{star_str(avg_rev_score)}</div>'
        f'  <div class="metric-subtitle">Average Review Score</div>'
        f"</div>",
        unsafe_allow_html=True,
    )

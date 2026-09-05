"""
Predictive E-Commerce Intelligence Dashboard - corrected build.

Fixes against the original dashboard/app.py:
  [D1] Path resolved from __file__, not the caller's working directory.
  [D2] Loads a 4 MB slim table instead of the 68 MB raw CSV.
  [D3] Real interactivity - state, category and date-range filters via callbacks.
  [D4] Currency labelled R$ (Olist is a Brazilian marketplace), not $.
  [D5] debug=False; host/port configurable for deployment.
  [D6] Graceful failure if the data file is missing, instead of a stack trace.
"""

import os
from pathlib import Path

import dash
import pandas as pd
import plotly.express as px
from dash import Input, Output, dcc, html

CUR = "R$"                                             # [D4]
BASE = Path(__file__).resolve().parent                 # [D1]

# look next to this file, then one level up - so the app works whether it
# sits at the repo root or inside dashboard/
CANDIDATES = [BASE / "dashboard_data" / "dash_fact.csv.gz",
              BASE.parent / "dashboard_data" / "dash_fact.csv.gz"]
DATA = next((p for p in CANDIDATES if p.exists()), CANDIDATES[0])

if not DATA.exists():                                  # [D6]
    raise SystemExit(
        "Could not find dash_fact.csv.gz. Looked in:\n  "
        + "\n  ".join(str(p) for p in CANDIDATES)
        + "\nRun the FIX 11 cell of Predictive_Ecommerce_Analysis_FIXED.ipynb first."
    )

df = pd.read_csv(DATA)                                 # [D2]
df["order_month"] = pd.PeriodIndex(df["order_month"], freq="M").to_timestamp()

MONTHS = sorted(df["order_month"].unique())
STATES = sorted(df["customer_state"].dropna().unique())
CATS = (df.groupby("category")["line_total"].sum()
        .sort_values(ascending=False).index.tolist())

# ----------------------------------------------------------------- theme
BG, PANEL, TEXT, ACCENT = "#0D1117", "#161B22", "#E6EDF3", "#2F81F7"
CARD = {"backgroundColor": PANEL, "padding": "18px", "borderRadius": "14px",
        "flex": "1", "textAlign": "center", "border": "1px solid #21262D"}
PANEL_STYLE = {"backgroundColor": PANEL, "borderRadius": "14px",
               "padding": "8px", "flex": "1", "border": "1px solid #21262D"}
CTRL = {"backgroundColor": PANEL, "color": "#0D1117", "flex": "1"}


def style_fig(fig, height=380):
    fig.update_layout(template="plotly_dark", height=height,
                      paper_bgcolor=PANEL, plot_bgcolor=PANEL,
                      margin=dict(l=40, r=20, t=50, b=40),
                      font=dict(color=TEXT, size=12))
    return fig


app = dash.Dash(__name__, title="E-Commerce Intelligence")
server = app.server                                    # for gunicorn

app.layout = html.Div(
    style={"backgroundColor": BG, "color": TEXT, "padding": "28px",
           "fontFamily": "Inter, Segoe UI, Arial, sans-serif",
           "minHeight": "100vh"},
    children=[
        html.H1("E-Commerce Intelligence Dashboard",
                style={"textAlign": "center", "fontSize": "34px",
                       "marginBottom": "4px"}),
        html.P("Delivered orders only. All values in Brazilian Reais (R$).",
               style={"textAlign": "center", "color": "#8B949E",
                      "marginTop": "0", "marginBottom": "26px"}),

        # ------------------------------------------------ [D3] filters
        html.Div([
            html.Div([html.Label("State", style={"fontSize": "12px",
                                                 "color": "#8B949E"}),
                      dcc.Dropdown(id="f-state", options=STATES, multi=True,
                                   placeholder="All states")], style=CTRL),
            html.Div([html.Label("Category", style={"fontSize": "12px",
                                                    "color": "#8B949E"}),
                      dcc.Dropdown(id="f-cat", options=CATS[:30], multi=True,
                                   placeholder="All categories")], style=CTRL),
            html.Div([html.Label("Period", style={"fontSize": "12px",
                                                  "color": "#8B949E"}),
                      dcc.DatePickerRange(id="f-date",
                                          min_date_allowed=MONTHS[0],
                                          max_date_allowed=MONTHS[-1],
                                          start_date=MONTHS[0],
                                          end_date=MONTHS[-1])], style=CTRL),
        ], style={"display": "flex", "gap": "16px", "marginBottom": "24px"}),

        html.Div(id="kpis", style={"display": "flex", "gap": "16px",
                                   "marginBottom": "24px"}),
        html.Div([html.Div(dcc.Graph(id="g-revenue"), style=PANEL_STYLE),
                  html.Div(dcc.Graph(id="g-category"), style=PANEL_STYLE)],
                 style={"display": "flex", "gap": "16px",
                        "marginBottom": "16px"}),
        html.Div([html.Div(dcc.Graph(id="g-state"), style=PANEL_STYLE),
                  html.Div(dcc.Graph(id="g-delivery"), style=PANEL_STYLE)],
                 style={"display": "flex", "gap": "16px",
                        "marginBottom": "16px"}),
        html.Div(dcc.Graph(id="g-seller"), style=PANEL_STYLE),
    ])


def kpi_card(label, value, note=""):
    return html.Div([
        html.Div(label, style={"color": "#8B949E", "fontSize": "13px"}),
        html.Div(value, style={"fontSize": "27px", "fontWeight": "600",
                               "margin": "6px 0 2px"}),
        html.Div(note, style={"color": "#6E7681", "fontSize": "11px"}),
    ], style=CARD)


@app.callback(
    Output("kpis", "children"), Output("g-revenue", "figure"),
    Output("g-category", "figure"), Output("g-state", "figure"),
    Output("g-delivery", "figure"), Output("g-seller", "figure"),
    Input("f-state", "value"), Input("f-cat", "value"),
    Input("f-date", "start_date"), Input("f-date", "end_date"),
)
def update(states, cats, start, end):
    d = df
    if states:
        d = d[d.customer_state.isin(states)]
    if cats:
        d = d[d.category.isin(cats)]
    if start:
        d = d[d.order_month >= pd.to_datetime(start)]
    if end:
        d = d[d.order_month <= pd.to_datetime(end)]

    if d.empty:
        blank = style_fig(px.scatter(title="No data for this selection"))
        return ([kpi_card("No matching orders", "-")], blank, blank,
                blank, blank, blank)

    orders = d.groupby("order_id").agg(value=("line_total", "sum"),
                                       review=("review_score", "first"))
    low = (orders.review <= 2).mean() * 100

    kpis = [
        kpi_card("Revenue", f"{CUR}{d.line_total.sum()/1e6:.2f}M",
                 "delivered orders"),
        kpi_card("Orders", f"{len(orders):,}", ""),
        kpi_card("Avg order value", f"{CUR}{orders.value.mean():,.0f}",
                 "per order, not per line"),
        kpi_card("Avg review", f"{orders.review.mean():.2f}",
                 f"{low:.1f}% rated 1-2 star"),
    ]

    monthly = d.groupby("order_month")["line_total"].sum().reset_index()
    f1 = style_fig(px.line(monthly, x="order_month", y="line_total", markers=True,
                           title="Monthly revenue"))
    f1.update_yaxes(title=CUR); f1.update_xaxes(title="")

    top_cat = (d.groupby("category")["line_total"].sum().nlargest(10)
               .sort_values().reset_index())
    f2 = style_fig(px.bar(top_cat, x="line_total", y="category",
                          orientation="h", title="Top categories by revenue"))
    f2.update_xaxes(title=CUR); f2.update_yaxes(title="")

    by_state = (d.groupby("customer_state")["line_total"].sum()
                .sort_values(ascending=False).reset_index())
    f3 = style_fig(px.bar(by_state, x="customer_state", y="line_total",
                          title="Revenue by state"))
    f3.update_yaxes(title=CUR); f3.update_xaxes(title="")

    delivery = (d.groupby("delivery_status")
                .agg(orders=("order_id", "nunique"),
                     avg_review=("review_score", "mean")).reset_index())
    f4 = style_fig(px.bar(delivery, x="delivery_status", y="orders",
                          color="avg_review", color_continuous_scale="RdYlGn",
                          range_color=[1, 5],
                          title="Delivery performance vs average rating"))
    f4.update_xaxes(title=""); f4.update_yaxes(title="Orders")

    top_sellers = (d.groupby("seller_id")["line_total"].sum().nlargest(15)
                   .reset_index())
    top_sellers["seller_id"] = top_sellers.seller_id.str[:8]
    f5 = style_fig(px.bar(top_sellers, x="seller_id", y="line_total",
                          title="Top 15 sellers by revenue"), height=340)
    f5.update_yaxes(title=CUR); f5.update_xaxes(title="")

    return kpis, f1, f2, f3, f4, f5


if __name__ == "__main__":
    app.run(host=os.getenv("HOST", "127.0.0.1"),
            port=int(os.getenv("PORT", 8050)),
            debug=False)                               # [D5]
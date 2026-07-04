import dash
from dash import html, dcc
import pandas as pd
import plotly.express as px


# ==================================================
# LOAD DATA
# ==================================================

df = pd.read_csv(
    "../data/ecommerce_cleaned_data.csv"
)


# ==================================================
# KPI CALCULATIONS
# ==================================================

total_revenue = df["revenue"].sum()

total_orders = df["order_id"].nunique()

total_customers = df["customer_unique_id"].nunique()

avg_rating = round(
    df["review_score"].mean(),
    2
)


# ==================================================
# REVENUE TREND
# ==================================================

monthly = (
    df.groupby("order_month")["revenue"]
    .sum()
    .reset_index()
)


revenue_fig = px.line(
    monthly,
    x="order_month",
    y="revenue",
    markers=True,
    title="📈 Monthly Revenue Trend",
    template="plotly_dark"
)


revenue_fig.update_layout(
    height=450
)



# ==================================================
# CATEGORY INTELLIGENCE
# ==================================================

categories = (
    df.groupby("product_category_name_english")
    ["revenue"]
    .sum()
    .sort_values(ascending=False)
    .head(10)
    .reset_index()
)


category_fig = px.bar(
    categories,
    x="revenue",
    y="product_category_name_english",
    orientation="h",
    title="🏆 Top Revenue Categories",
    template="plotly_dark"
)


category_fig.update_layout(
    yaxis_title="Category",
    height=450
)



# ==================================================
# STATE ANALYTICS
# ==================================================

state = (
    df.groupby("customer_state")
    ["revenue"]
    .sum()
    .sort_values(
        ascending=False
    )
    .reset_index()
)


state_fig = px.bar(
    state,
    x="customer_state",
    y="revenue",
    title="🌎 Revenue By State",
    template="plotly_dark"
)


state_fig.update_layout(
    height=450
)



# ==================================================
# CUSTOMER SATISFACTION
# ==================================================

reviews = (
    df.groupby("review_score")
    ["order_id"]
    .count()
    .reset_index()
)


review_fig = px.bar(
    reviews,
    x="review_score",
    y="order_id",
    title="⭐ Customer Review Distribution",
    template="plotly_dark"
)


review_fig.update_layout(
    height=450
)



# ==================================================
# SELLER PERFORMANCE
# ==================================================

seller = (
    df.groupby("seller_id")
    ["revenue"]
    .sum()
    .sort_values(
        ascending=False
    )
    .head(10)
    .reset_index()
)


seller_fig = px.bar(
    seller,
    x="seller_id",
    y="revenue",
    title="🚚 Top Seller Performance",
    template="plotly_dark"
)


seller_fig.update_layout(
    height=450
)



# ==================================================
# DASH APP
# ==================================================

app = dash.Dash(__name__)


CARD = {

    "backgroundColor":"#161B22",
    "padding":"25px",
    "borderRadius":"20px",
    "width":"22%",
    "textAlign":"center",
    "boxShadow":"0px 0px 15px #000"

}


GRAPH_CARD = {

    "width":"49%",
    "backgroundColor":"#161B22",
    "borderRadius":"15px",
    "padding":"10px",
    "marginBottom":"25px"

}



app.layout = html.Div(


style={

    "backgroundColor":"#0D1117",
    "color":"white",
    "padding":"30px",
    "fontFamily":"Arial"

},


children=[



html.H1(

    "🚀 Predictive E-Commerce Intelligence Dashboard",

    style={

        "textAlign":"center",
        "fontSize":"42px",
        "marginBottom":"40px"

    }

),



# KPI ROW

html.Div(

[


html.Div(
[
html.H3("💰 Revenue"),
html.H2(
    f"${round(total_revenue/1000000,2)}M"
)
],
style=CARD
),



html.Div(
[
html.H3("📦 Orders"),
html.H2(
    f"{total_orders:,}"
)
],
style=CARD
),



html.Div(
[
html.H3("👥 Customers"),
html.H2(
    f"{total_customers:,}"
)
],
style=CARD
),



html.Div(
[
html.H3("⭐ Rating"),
html.H2(
    avg_rating
)
],
style=CARD
),



],


style={

"display":"flex",
"justifyContent":"space-between",
"marginBottom":"40px"

}

),



# ROW 1

html.Div(

[


html.Div(
dcc.Graph(
figure=revenue_fig
),
style=GRAPH_CARD
),


html.Div(
dcc.Graph(
figure=category_fig
),
style=GRAPH_CARD
),


],

style={

"display":"flex",
"justifyContent":"space-between"

}

),




# ROW 2


html.Div(

[


html.Div(
dcc.Graph(
figure=state_fig
),
style=GRAPH_CARD
),



html.Div(
dcc.Graph(
figure=review_fig
),
style=GRAPH_CARD
),



],

style={

"display":"flex",
"justifyContent":"space-between"

}

),



# SELLER FULL WIDTH


html.Div(

dcc.Graph(
figure=seller_fig
),

style={

"backgroundColor":"#161B22",
"padding":"15px",
"borderRadius":"15px"

}

)



]

)



# ==================================================
# RUN SERVER
# ==================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )
import streamlit as st
import pandas as pd
import plotly.express as px
import datetime

# Title
st.title("Singapore Property Price Tracker – Last Updated: {}".format(
    datetime.datetime.now().strftime("%Y-%m-d %H:%M")
))

# Sidebar filters
with st.sidebar:
    st.header("Filters")
    property_type = st.selectbox("Property type", ["HDB Resale", "Private Residential"])
    region = st.selectbox("Region / Planning Area", ["All", "Central", "East", "West", "North", "North-East"])
    last_n_months = st.slider("Last N months", min_value=1, max_value=60, value=12)

# Dummy data load – replace with your dataset
@st.cache_data
def load_data():
    # Replace the CSV path or data source
    df = pd.read_csv("data/property_prices_sg.csv", parse_dates=["date"])
    return df

df = load_data()

# Filter the data
filtered = df.copy()
if property_type != "All":
    filtered = filtered[filtered["property_type"] == property_type]
if region != "All":
    filtered = filtered[filtered["region"] == region]
cutoff = pd.Timestamp.now() - pd.DateOffset(months=last_n_months)
filtered = filtered[filtered["date"] >= cutoff]

# Chart: Average price over time
avg_price = filtered.groupby("date")["price_per_sqm"].mean().reset_index()
fig1 = px.line(avg_price, x="date", y="price_per_sqm",
               title="Average Price (S$/sqm) over Time")
st.plotly_chart(fig1, use_container_width=True)

# Chart: Volume of transactions
vol = filtered.groupby("date")["transaction_id"].count().reset_index().rename(columns={"transaction_id":"volume"})
fig2 = px.bar(vol, x="date", y="volume", title="Transaction Volume over Time")
st.plotly_chart(fig2, use_container_width=True)

# Regional table / summary
summary = filtered.groupby("region").agg(
    avg_price=("price_per_sqm","mean"),
    change_3m=("price_per_sqm", lambda x: (x.iloc[-1] - x.iloc[0])/x.iloc[0] if len(x)>1 else None)
).reset_index().sort_values("avg_price", ascending=False)
st.subheader("Region summary")
st.dataframe(summary)

# Footer / notes
st.markdown("""
---
*Data source: Open Data Singapore / URA (or your data provider)*  
_Last updated: {}_  
""".format(datetime.datetime.now().strftime("%Y-%m-d %H:%M")))

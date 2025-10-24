import os
import streamlit as st
import pandas as pd
import plotly.express as px
import datetime

st.write("Working directory:", os.getcwd())
st.write("Root files:", os.listdir('.'))

st.title("Singapore Property Price Tracker – Last Updated: {}".format(
    datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
))

with st.sidebar:
    st.header("Filters")
    property_type = st.selectbox("Property type", ["All", "HDB Resale", "Private Residential"])
    region = st.selectbox("Region / Planning Area", ["All", "Central", "East", "West", "North", "North-East"])
    last_n_months = st.slider("Last N months", min_value=1, max_value=60, value=12)

@st.cache_data
def load_data(filepath="data/property_prices_sg.csv"):
    if not os.path.exists(filepath):
        st.error(f"Data file not found at path: {filepath}")
        st.stop()
    try:
        df = pd.read_csv(filepath, parse_dates=["date"])
    except pd.errors.EmptyDataError:
        st.error(f"The data file at {filepath} is empty or malformed.")
        st.stop()
    except Exception as e:
        st.error(f"Error reading data file: {e}")
        st.stop()
    return df

df = load_data()

# Now ensure there are the expected columns
expected_cols = {"date", "property_type", "region", "price_per_sqm", "transaction_id"}
if not expected_cols.issubset(set(df.columns)):
    st.error(f"Data file missing expected columns. Found columns: {list(df.columns)}")
    st.stop()

filtered = df.copy()
if property_type != "All":
    filtered = filtered[filtered["property_type"] == property_type]
if region != "All":
    filtered = filtered[filtered["region"] == region]

cutoff = pd.Timestamp.now() - pd.DateOffset(months=last_n_months)
filtered = filtered[filtered["date"] >= cutoff]

if filtered.empty:
    st.warning("No data available after applying filters. Please change filters or wait for updated data.")

else:
    avg_price = filtered.groupby("date")["price_per_sqm"].mean().reset_index()
    fig1 = px.line(avg_price, x="date", y="price_per_sqm", title="Average Price (S$/m²) over Time")
    st.plotly_chart(fig1, use_container_width=True)

    vol = filtered.groupby("date")["transaction_id"].count().reset_index().rename(columns={"transaction_id": "volume"})
    fig2 = px.bar(vol, x="date", y="volume", title="Transaction Volume Over Time")
    st.plotly_chart(fig2, use_container_width=True)

    summary = filtered.groupby("region").agg(
        avg_price=("price_per_sqm", "mean"),
        change_3m=("price_per_sqm", lambda x: (x.iloc[-1] - x.iloc[0]) / x.iloc[0] if len(x) > 1 else None)
    ).reset_index().sort_values("avg_price", ascending=False)
    st.subheader("Region Summary")
    st.dataframe(summary)

st.markdown(f"""
---
*Data source: Open Data Singapore / URA (or your chosen data provider)*  
_Last updated: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}_  
""")

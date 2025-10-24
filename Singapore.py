import os
import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
import requests
from io import StringIO

st.write("Working directory:", os.getcwd())
st.write("Root files:", os.listdir('.'))

st.title("Singapore Property Price Tracker – Last Updated: {}".format(
    datetime.datetime.now().strftime("%Y-%m-d %H:%M")
))

with st.sidebar:
    st.header("Filters")
    property_type = st.selectbox("Property type", ["All", "HDB Resale"])
    region = st.selectbox("Region / Town", ["All"])  # you can expand these
    last_n_months = st.slider("Last N months", min_value=1, max_value=120, value=12)

@st.cache_data
def load_data():
    # Try live dataset from HDB open data (Resale Flat Prices)
    url = "https://data.gov.sg/dataset/resale-flat-prices-based-on-registration-date-from-jan-2017-onwards"  # placeholder; fetch directly below
    csv_url = "https://data.gov.sg/dataset/d_8b84c4ee58e3cfc0ece0d773c8ca6abc/download"  # this is approximate
    try:
        resp = requests.get(csv_url)
        resp.raise_for_status()
        df = pd.read_csv(StringIO(resp.text), parse_dates=["month"])
        # rename columns for consistency
        df = df.rename(columns={"month":"date", "town":"region", "flat_type":"property_type", "resale_price":"price"})
        return df
    except Exception as e:
        # fallback to local file
        filepath = "data/property_prices_sg.csv"
        if not os.path.exists(filepath):
            st.error(f"Data file not found at path: {filepath}")
            st.stop()
        try:
            df = pd.read_csv(filepath, parse_dates=["date"])
        except pd.errors.EmptyDataError:
            st.error(f"The data file at {filepath} is empty or malformed.")
            st.stop()
        except Exception as ex:
            st.error(f"Error reading data file: {ex}")
            st.stop()
        return df

df = load_data()

if df.empty:
    st.error("Loaded dataset is empty—no rows to work with.")
    st.stop()

st.write("Loaded data sample:", df.head())

# Filter by property type
if property_type != "All":
    df = df[df["property_type"].str.contains(property_type, case=False, na=False)]

# Filter by region (if you expand list later)
if region != "All":
    df = df[df["region"] == region]

# Filter by date range
cutoff = pd.Timestamp.now() - pd.DateOffset(months=last_n_months)
df = df[df["date"] >= cutoff]

if df.empty:
    st.warning("No data available after applying filters — try widening your filters.")
else:
    # Chart: price distribution / time series
    fig1 = px.line(df.groupby("date")["price"].mean().reset_index(), x="date", y="price",
                   title="Average Resale Price Over Time")
    st.plotly_chart(fig1, use_container_width=True)

    # Summary
    summary = df.groupby("region").agg(
        avg_price=("price", "mean"),
        count=("price", "count")
    ).reset_index().sort_values("avg_price", ascending=False)
    st.subheader("Region Summary")
    st.dataframe(summary)

st.markdown(f"""
---
*Data source: Housing & Development Board (HDB) via data.gov.sg*  
_Last updated: {datetime.datetime.now().strftime("%Y-%m-d %H:%M")}_  
""")

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
    datetime.datetime.now().strftime("%Y-%m-%d %H:%M")  # Fixed: %d instead of %-d
))

with st.sidebar:
    st.header("Filters")
    property_type = st.selectbox("Property type", ["All", "HDB Resale"])
    region = st.selectbox("Region / Town", ["All"])  # you can expand these
    last_n_months = st.slider("Last N months", min_value=1, max_value=120, value=12)

@st.cache_data
def load_data():
    # Try live dataset from HDB open data
    try:
        # Updated URL for HDB resale price data
        csv_url = "https://data.gov.sg/dataset/7a339d20-3c57-4b11-a695-9348adfd7614/download"
        resp = requests.get(csv_url, timeout=30)
        resp.raise_for_status()
        
        # Try reading with different encoding if needed
        try:
            df = pd.read_csv(StringIO(resp.text), parse_dates=["month"])
        except UnicodeDecodeError:
            df = pd.read_csv(StringIO(resp.text), parse_dates=["month"], encoding='utf-8')
        
        # rename columns for consistency
        df = df.rename(columns={
            "month": "date", 
            "town": "region", 
            "flat_type": "property_type", 
            "resale_price": "price"
        })
        
        st.success(f"Successfully loaded live data with {len(df)} rows")
        return df
        
    except Exception as e:
        st.warning(f"Could not load live data: {e}. Trying local file...")
        
        # fallback to local file with better error handling
        filepath = "data/property_prices_sg.csv"
        
        # Check if directory exists
        if not os.path.exists("data"):
            st.error(f"Data directory 'data/' not found. Creating it...")
            os.makedirs("data", exist_ok=True)
            st.info("Please upload your CSV file to the 'data/' directory")
            return pd.DataFrame()
            
        if not os.path.exists(filepath):
            st.error(f"Data file not found at path: {filepath}")
            st.info("Please ensure 'property_prices_sg.csv' exists in the 'data/' folder")
            return pd.DataFrame()
        
        try:
            # Try different encodings and separators
            encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(filepath, parse_dates=["date"], encoding=encoding)
                    st.success(f"Successfully loaded local data with encoding: {encoding}")
                    break
                except UnicodeDecodeError:
                    continue
            else:
                # If all encodings fail, try without specifying encoding
                df = pd.read_csv(filepath, parse_dates=["date"])
                
        except pd.errors.EmptyDataError:
            st.error(f"The data file at {filepath} is empty.")
            return pd.DataFrame()
        except Exception as ex:
            st.error(f"Error reading data file: {ex}")
            # Show file info for debugging
            if os.path.exists(filepath):
                file_size = os.path.getsize(filepath)
                st.write(f"File size: {file_size} bytes")
                if file_size > 0:
                    # Show first few lines for debugging
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        preview = f.readlines()[:5]
                    st.write("File preview (first 5 lines):")
                    st.code(''.join(preview))
            return pd.DataFrame()
        
        return df

df = load_data()

# Create sample data if no data is available
if df.empty:
    st.warning("No data available. Creating sample data for demonstration...")
    
    # Generate sample HDB data
    dates = pd.date_range(start='2020-01-01', end=datetime.datetime.now(), freq='M')
    regions = ['Ang Mo Kio', 'Bedok', 'Tampines', 'Jurong East', 'Bishan']
    flat_types = ['3 ROOM', '4 ROOM', '5 ROOM']
    
    sample_data = []
    for date in dates:
        for region in regions:
            for flat_type in flat_types:
                base_price = 300000 + (regions.index(region) * 50000) + (flat_types.index(flat_type) * 80000)
                price_variation = base_price * 0.1 * (pd.np.random.random() - 0.5)
                price = base_price + price_variation
                
                sample_data.append({
                    'date': date,
                    'region': region,
                    'property_type': flat_type,
                    'price': price
                })
    
    df = pd.DataFrame(sample_data)
    st.info("Using sample data for demonstration. Please check your data source.")

st.write(f"Data loaded: {len(df)} rows")
st.write("Data columns:", df.columns.tolist())
st.write("Loaded data sample:", df.head())

# Data validation and cleaning
if not df.empty:
    # Check for required columns
    required_columns = ['date', 'price']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        st.error(f"Missing required columns: {missing_columns}")
        st.stop()
    
    # Clean data
    df = df.dropna(subset=['date', 'price'])
    df['price'] = pd.to_numeric(df['price'], errors='coerce')
    df = df.dropna(subset=['price'])
    
    if 'region' not in df.columns:
        df['region'] = 'Unknown'
    if 'property_type' not in df.columns:
        df['property_type'] = 'Unknown'

# Filter by property type
if property_type != "All" and not df.empty:
    df = df[df["property_type"].str.contains(property_type, case=False, na=False)]

# Filter by region (if you expand list later)
if region != "All" and not df.empty:
    df = df[df["region"] == region]

# Filter by date range
if not df.empty:
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

    # Additional chart: Price distribution by property type
    if 'property_type' in df.columns:
        fig2 = px.box(df, x="property_type", y="price", 
                     title="Price Distribution by Property Type")
        st.plotly_chart(fig2, use_container_width=True)

st.markdown(f"""
---
*Data source: Housing & Development Board (HDB) via data.gov.sg*  
_Last updated: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}_  
""")

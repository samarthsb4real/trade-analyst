import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# Alpha Vantage API credentials
API_KEY = "L18QHHMC7G5XQUMI"
BASE_URL = "https://www.alphavantage.co/query"

# Fetch stock data from Alpha Vantage
def fetch_stock_data(symbol, function, interval=None):
    params = {
        "function": function,
        "symbol": symbol,
        "apikey": API_KEY,
    }
    if interval:
        params["interval"] = interval
    response = requests.get(BASE_URL, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Error: {response.status_code} - {response.text}")
        return None

# Process time series data into a DataFrame
def process_time_series_data(data, key):
    if key not in data:
        st.warning("No data available.")
        return None
    df = pd.DataFrame.from_dict(data[key], orient="index")
    df = df.rename(columns=lambda x: x.split(". ")[1])  # Simplify column names
    df.index = pd.to_datetime(df.index)
    return df.sort_index()

# Calculate moving averages
def calculate_moving_averages(df, short_window=5, long_window=20):
    df["SMA"] = df["close"].astype(float).rolling(window=short_window).mean()
    df["LMA"] = df["close"].astype(float).rolling(window=long_window).mean()
    return df

# Analyze for buy/sell recommendations
def analyze_buy_sell(df):
    df["Signal"] = 0
    df.loc[df["SMA"] > df["LMA"], "Signal"] = 1  # Buy signal
    df.loc[df["SMA"] < df["LMA"], "Signal"] = -1  # Sell signal
    return df

# Streamlit App
st.title("Enhanced Stock Market Insights App")
st.sidebar.title("Stock Settings")

# User Input
stock_symbol = st.sidebar.text_input("Enter Stock Symbol (e.g., IBM, TSLA):", "IBM")
analysis_type = st.sidebar.selectbox("Analysis Type", ["Real-Time", "Historical"])
interval = st.sidebar.selectbox("Interval (Historical Data)", ["1min", "5min", "15min", "30min", "60min"], index=1)

if st.sidebar.button("Analyze"):
    if analysis_type == "Real-Time":
        data = fetch_stock_data(stock_symbol, "TIME_SERIES_INTRADAY", interval="5min")
        if data:
            df = process_time_series_data(data, "Time Series (5min)")
            st.write(f"### Real-Time Data for {stock_symbol}")
            st.dataframe(df.head())
    elif analysis_type == "Historical":
        data = fetch_stock_data(stock_symbol, "TIME_SERIES_INTRADAY", interval=interval)
        if data:
            df = process_time_series_data(data, "Time Series (5min)")
            if df is not None:
                df = calculate_moving_averages(df)
                df = analyze_buy_sell(df)
                
                st.write(f"### Historical Data for {stock_symbol}")
                st.dataframe(df.tail())

                # Visualization
                st.write("### Price Trends")
                fig = px.line(df, x=df.index, y=["close", "SMA", "LMA"], title="Price Trends with Moving Averages")
                st.plotly_chart(fig)

                # Buy/Sell Signals
                buy_signals = df[df["Signal"] == 1]
                sell_signals = df[df["Signal"] == -1]
                st.write("### Recommendations")
                st.write("**Buy Signals:**")
                st.dataframe(buy_signals.tail())
                st.write("**Sell Signals:**")
                st.dataframe(sell_signals.tail())

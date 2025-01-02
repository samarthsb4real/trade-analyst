import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from statsmodels.tsa.arima.model import ARIMA
from datetime import datetime
import json

# Alpha Vantage API credentials
API_KEY = "L18QHHMC7G5XQUMI"
BASE_URL = "https://www.alphavantage.co/query"

# Autocomplete function to search for companies
def fetch_company_autocomplete(query):
    params = {
        "function": "SYMBOL_SEARCH",
        "keywords": query,
        "apikey": API_KEY,
    }
    response = requests.get(BASE_URL, params=params)
    if response.status_code == 200:
        data = response.json()
        if "bestMatches" in data:
            return [match["1. symbol"] for match in data["bestMatches"]]
        else:
            return []
    else:
        st.error(f"Error: {response.status_code} - {response.text}")
        return []

# Fetch stock data
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

# Process time series data
def process_time_series_data(data, key):
    if key not in data:
        st.warning("No data available.")
        return None
    df = pd.DataFrame.from_dict(data[key], orient="index")
    df = df.rename(columns=lambda x: x.split(". ")[1])
    df.index = pd.to_datetime(df.index)
    return df.sort_index()

# Predict future prices using ARIMA
def predict_future_prices(df, steps=5):
    model = ARIMA(df["close"].astype(float), order=(1, 1, 1))
    model_fit = model.fit()
    forecast = model_fit.forecast(steps=steps)
    return forecast

# Streamlit App
st.title("Advanced Stock Market Insights App")
st.sidebar.title("Stock Settings")

# Wishlist Management
wishlist = st.sidebar.text_area("Wishlist (Comma-separated Stock Symbols)", "IBM, TSLA")
wishlist = [symbol.strip().upper() for symbol in wishlist.split(",") if symbol.strip()]

# Autocomplete for stock symbol search
query = st.sidebar.text_input("Search for Company:")
if query:
    suggestions = fetch_company_autocomplete(query)
    if suggestions:
        st.sidebar.write("Suggestions:")
        st.sidebar.write(", ".join(suggestions))

# Analysis Type
analysis_type = st.sidebar.selectbox("Analysis Type", ["Real-Time", "Historical"])
interval = st.sidebar.selectbox("Interval (Historical Data)", ["1min", "5min", "15min", "30min", "60min"], index=1)

if st.sidebar.button("Analyze Wishlist"):
    for stock_symbol in wishlist:
        st.subheader(f"Analysis for {stock_symbol}")
        
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
                    st.write("### Historical Data")
                    st.dataframe(df.tail())

                    # Predict future prices
                    st.write("### Future Price Prediction")
                    forecast = predict_future_prices(df)
                    st.write(f"Next {len(forecast)} Time Steps Predicted Prices:")
                    st.write(forecast)

                    # Visualizations
                    st.write("### Price Trends")
                    fig = px.line(df, x=df.index, y="close", title=f"{stock_symbol} Price Trends")
                    st.plotly_chart(fig)

                    st.write("### Prediction Visualized")
                    future_dates = pd.date_range(start=df.index[-1], periods=len(forecast) + 1, freq="5min")[1:]
                    forecast_df = pd.DataFrame({"Date": future_dates, "Forecasted Price": forecast})
                    pred_fig = px.line(forecast_df, x="Date", y="Forecasted Price", title="Future Price Prediction")
                    st.plotly_chart(pred_fig)

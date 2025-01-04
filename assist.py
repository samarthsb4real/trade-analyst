import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from streamlit_tags import st_tags
from statsmodels.tsa.arima.model import ARIMA
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv(".env.local")
API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
BASE_URL = "https://www.alphavantage.co/query"

# Fetch stock data
def fetch_stock_data(symbol, interval="5min"):
    params = {
        "function": "TIME_SERIES_INTRADAY",
        "symbol": symbol,
        "interval": interval,
        "apikey": API_KEY,
    }
    response = requests.get(BASE_URL, params=params)
    if response.status_code == 200:
        data = response.json()
        if "Time Series (5min)" in data:
            return data["Time Series (5min)"]
        else:
            st.warning("No data available for this symbol.")
            return None
    else:
        st.error(f"Error: {response.status_code} - {response.text}")
        return None

# Process and prepare the data
def process_time_series_data(data):
    df = pd.DataFrame.from_dict(data, orient="index")
    df = df.rename(columns=lambda x: x.split(". ")[1])
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()
    df = df.astype(float)
    return df

# Analyze and generate recommendations
def analyze_stock(df):
    latest_price = df["close"].iloc[-1]
    avg_price = df["close"].mean()
    std_dev = df["close"].std()

    if latest_price < avg_price - std_dev:
        decision = "Buy"
        color = "green"
        entry_price = latest_price
        exit_price = avg_price + std_dev
        reasoning = (
            f"The stock is trading below its average price by more than one standard deviation, "
            f"indicating it is undervalued and has potential for upward movement."
        )
    elif latest_price > avg_price + std_dev:
        decision = "Sell"
        color = "red"
        entry_price = avg_price - std_dev
        exit_price = latest_price
        reasoning = (
            f"The stock is trading above its average price by more than one standard deviation, "
            f"indicating it may be overvalued and a good time to sell."
        )
    else:
        decision = "Hold"
        color = "yellow"
        entry_price = None
        exit_price = None
        reasoning = (
            f"The stock is trading within its normal range, indicating no strong signals for buying or selling."
        )

    return {
        "decision": decision,
        "color": color,
        "entry_price": entry_price,
        "exit_price": exit_price,
        "reasoning": reasoning,
    }

# Generate detailed report
def generate_report(df, analysis, stock_symbol):
    report = f"### Detailed Report for {stock_symbol}\n\n"
    report += "#### Historical Data\n"
    report += df.tail().to_csv(index=True)
    report += "\n\n#### Analysis\n"
    report += f"Decision: {analysis['decision']}\n"
    report += f"Entry Price: {analysis['entry_price']}\n"
    report += f"Exit Price: {analysis['exit_price']}\n"
    report += f"Reasoning: {analysis['reasoning']}\n"
    return report

# Streamlit App
st.title("Stock Market Assistant")
st.sidebar.title("Stock Settings")

# Autocomplete and wishlist feature
available_symbols = ["IBM", "AAPL", "GOOG", "TSLA", "MSFT", "AMZN", "META", "NFLX", "NVDA", "ADBE"]
wishlist = st_tags(
    label="Your Wishlist:",
    text="Add stocks you're interested in (type and press enter)",
    suggestions=available_symbols,
    key="wishlist",
)

# Input for stock symbol
st.sidebar.write("Search for a stock:")
selected_stock = st.sidebar.selectbox("Select Stock Symbol", options=wishlist)
interval = st.sidebar.selectbox("Interval", ["5min", "15min", "30min", "60min"], index=0)

if st.sidebar.button("Analyze Stock") and selected_stock:
    stock_data = fetch_stock_data(selected_stock, interval)
    if stock_data:
        df = process_time_series_data(stock_data)
        # Generate recommendations
        analysis = analyze_stock(df)
        
        # Display actionable insights
        st.markdown(
            f"""
            <div style="padding: 10px; border: 2px solid {analysis['color']}; border-radius: 5px; text-align: center;">
                <h2 style="color: {analysis['color']};">{analysis['decision']}!</h2>
                <p><b>When:</b> Immediately</p>
                <p><b>Entry Price:</b> {analysis['entry_price'] if analysis['entry_price'] else 'N/A'}</p>
                <p><b>Exit Price:</b> {analysis['exit_price'] if analysis['exit_price'] else 'N/A'}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # In-depth analysis
        st.write("#### In-depth Analysis")
        st.write(analysis["reasoning"])
        
        st.write(f"### Analysis for {selected_stock}")
        st.write("#### Price Data")
        st.dataframe(df.tail())

        # Visualizations
        st.write("### Price Trends")
        fig = px.line(df, x=df.index, y="close", title=f"{selected_stock} Price Trends")
        st.plotly_chart(fig)

        # Generate and download report
        report = generate_report(df, analysis, selected_stock)
        st.download_button(
            label="Download Detailed Report",
            data=report,
            file_name=f"{selected_stock}_report.txt",
            mime="text/plain",
        )
    else:
        st.warning("Failed to fetch stock data. Please check the symbol or try again.")

# Wishlist display
if wishlist:
    st.sidebar.write("#### Your Wishlist:")
    for stock in wishlist:
        st.sidebar.write(f"- {stock}")

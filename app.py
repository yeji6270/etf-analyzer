
import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import openai
import matplotlib.pyplot as plt

openai.api_key = st.secrets["openai_api_key"]

# RSI 계산 함수
def calculate_wilder_rsi(close, period=14):
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()
    for i in range(period, len(gain)):
        avg_gain.iloc[i] = (avg_gain.iloc[i - 1] * (period - 1) + gain.iloc[i]) / period
        avg_loss.iloc[i] = (avg_loss.iloc[i - 1] * (period - 1) + loss.iloc[i]) / period
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def ask_gpt(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"GPT 오류: {e}"

st.set_page_config(page_title="ETF 분석 앱", page_icon="📈")
st.title("📊 ETF 기술적 분석 앱")

etf_input = st.text_input("ETF 심볼을 입력하세요 (쉼표로 구분)", "QQQ, QLD, BITO")
etfs = [etf.strip().upper() for etf in etf_input.split(",") if etf.strip()]

if st.button("분석 실행"):
    st.session_state.analysis_results = []
    for symbol in etfs:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1y")
        close = hist["Close"]
        rsi_series = calculate_wilder_rsi(close)
        rsi_val = round(rsi_series.dropna().iloc[-1], 1)
        prompt = f"{symbol}의 RSI는 {rsi_val}입니다. 기술적 전략을 제안해주세요."
        st.session_state.analysis_results.append({
            "symbol": symbol,
            "rsi": rsi_val,
            "rsi_series": rsi_series,
            "prompt": prompt,
        })

if "analysis_results" in st.session_state:
    for result in st.session_state.analysis_results:
        st.write(f"### {result['symbol']}")
        st.write(f"RSI: {result['rsi']}")
        if st.button(f"{result['symbol']} 전략 확인하기"):
            gpt_result = ask_gpt(result['prompt'])
            st.success(gpt_result)
        st.line_chart(result['rsi_series'])


import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import datetime
from openai import OpenAI
import matplotlib.pyplot as plt

client = OpenAI(api_key=st.secrets["openai_api_key"])

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

def get_macd_desc(macd, signal):
    return '골든크로스' if macd.iloc[-1] > signal.iloc[-1] else '데드크로스'

def rsi_status(rsi):
    if rsi >= 70: return '🟢 과매수'
    elif rsi >= 50: return '🟡 중립~상승'
    elif rsi >= 30: return '🔵 중립~과매도'
    else: return '🔴 과매도'

def macd_status(desc):
    return '🟢 상승' if '골든' in desc else '🔴 하락'

def strategy_prompt(etf, rsi, macd_desc):
    return f"{etf}의 RSI는 {rsi}이고 MACD는 {macd_desc}야. SMA와 볼린저밴드도 함께 고려해서 대응 전략을 알려줘."

def ask_gpt(prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"GPT 오류: {e}"

st.set_page_config(page_title="ETF 분석 앱", page_icon="📈")
st.title("📊 ETF 기술적 분석 앱")


import streamlit as st
import pandas as pd
import yfinance as yf
import openai
import numpy as np

# OpenAI API 설정
openai.api_key = st.secrets["openai_api_key"]

# RSI 계산 함수 (Wilder 방식)
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
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"GPT 오류: {e}"

# 앱 시작
st.title("📊 ETF 기술적 분석 앱 (간단 버전)")
etf_input = st.text_input("ETF 심볼을 입력하세요 (쉼표로 구분)", "QQQ, QLD, BITO")
etfs = [etf.strip().upper() for etf in etf_input.split(",") if etf.strip()]

if st.button("분석 실행"):
    results = []
    for symbol in etfs:
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1y")
            close = hist['Close']

            rsi_series = calculate_wilder_rsi(close)
            rsi_val = round(rsi_series.dropna().iloc[-1], 1)

            ema12 = close.ewm(span=12, adjust=False).mean()
            ema26 = close.ewm(span=26, adjust=False).mean()
            macd = ema12 - ema26
            signal = macd.ewm(span=9, adjust=False).mean()
            macd_desc = get_macd_desc(macd, signal)

            sma20 = round(close.rolling(window=20).mean().iloc[-1], 1)
            sma50 = round(close.rolling(window=50).mean().iloc[-1], 1)
            sma200 = round(close.rolling(window=200).mean().iloc[-1], 1)
            std = close.rolling(window=20).std().iloc[-1]
            boll_upper = round(sma20 + 2 * std, 1)
            boll_lower = round(sma20 - 2 * std, 1)

            strategy = strategy_prompt(symbol, rsi_val, macd_desc)
            gpt_response = ask_gpt(strategy)

            results.append({
                'ETF': symbol,
                'RSI': rsi_val,
                'RSI 상태': rsi_status(rsi_val),
                'MACD 설명': macd_desc,
                'MACD 상태': macd_status(macd_desc),
                'SMA20': sma20,
                'SMA50': sma50,
                'SMA200': sma200,
                '볼린저 상단': boll_upper,
                '볼린저 하단': boll_lower,
                '전략 문장': strategy,
                'GPT 전략 제안': gpt_response
            })

        except Exception as e:
            st.error(f"{symbol} 분석 중 오류 발생: {e}")

    df = pd.DataFrame(results)
    st.dataframe(df)

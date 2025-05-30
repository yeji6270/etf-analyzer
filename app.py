import streamlit as st
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import openai
import datetime

# API 키 설정
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

def rsi_status(rsi):
    if rsi >= 70: return "🟢 과매수"
    elif rsi >= 50: return "🟡 중립~상승"
    elif rsi >= 30: return "🔵 중립~과매도"
    else: return "🔴 과매도"

def macd_status(macd_val, signal_val):
    return "🟢 상승" if macd_val > signal_val else "🔴 하락"

def ask_gpt(prompt):
    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"GPT 오류: {e}"

# Streamlit UI
st.set_page_config(page_title="ETF 기술적 분석 앱", page_icon="📊", layout="centered")
st.title("📊 ETF 기술적 분석 앱")

etf_input = st.text_input("ETF 심볼을 입력하세요 (쉼표로 구분)", "QQQ, QLD, BITO")
etfs = [e.strip().upper() for e in etf_input.split(",") if e.strip()]
analyze_button = st.button("분석 실행")

if analyze_button:
    for symbol in etfs:
        try:
            st.subheader(symbol)
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1y")
            close = hist["Close"]

            rsi_series = calculate_wilder_rsi(close)
            rsi_val = round(rsi_series.dropna().iloc[-1], 1)
            current_price = round(close.iloc[-1], 2)

            ema12 = close.ewm(span=12, adjust=False).mean()
            ema26 = close.ewm(span=26, adjust=False).mean()
            macd = ema12 - ema26
            signal = macd.ewm(span=9, adjust=False).mean()
            macd_val = macd.iloc[-1]
            signal_val = signal.iloc[-1]

            sma20 = round(close.rolling(window=20).mean().iloc[-1], 1)
            sma50 = round(close.rolling(window=50).mean().iloc[-1], 1)
            sma200 = round(close.rolling(window=200).mean().iloc[-1], 1)
            std = close.rolling(window=20).std().iloc[-1]
            boll_upper = round(sma20 + 2 * std, 1)
            boll_lower = round(sma20 - 2 * std, 1)

            strategy_text = f"{symbol}의 RSI는 {rsi_val}이고 MACD는 {'골든크로스' if macd_val > signal_val else '데드크로스'}야. SMA와 볼린저밴드도 함께 고려해서 대응 전략을 알려줘."

            st.markdown(f"💵 현재 주가: **${current_price}**")
            st.markdown(f"📊 RSI: **{rsi_val}** ({rsi_status(rsi_val)})")
            st.markdown(f"📈 MACD 상태: **{macd_status(macd_val, signal_val)}**")
            st.markdown(f"🧠 전략 문장 복사용:
```{strategy_text}```")

            if st.button(f"{symbol} 전략 확인하기"):
                st.markdown("💡 **GPT 전략 제안**")
                st.info(ask_gpt(strategy_text))

            fig, ax = plt.subplots()
            ax.plot(rsi_series, color="skyblue")
            ax.axhline(70, color="red", linestyle="--", linewidth=1)
            ax.axhline(30, color="green", linestyle="--", linewidth=1)
            ax.set_title(f"{symbol} RSI (Wilder)")
            ax.set_facecolor("#111")
            fig.patch.set_facecolor("#111")
            st.pyplot(fig)

        except Exception as e:
            st.error(f"{symbol} 분석 중 오류 발생: {e}")
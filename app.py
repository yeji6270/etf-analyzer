
import streamlit as st
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib as mpl
import datetime
import openai

# 📌 다크 테마 스타일 적용
mpl.style.use("dark_background")

# ✅ OpenAI API 키 설정
openai.api_key = st.secrets["openai_api_key"]

# ✅ RSI 계산 함수 (Wilder 방식)
def calculate_wilder_rsi(close, period=14):
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()

    for i in range(period, len(gain)):
        avg_gain.iloc[i] = (avg_gain.iloc[i - 1] * (period - 1) + gain.iloc[i]) / period
        avg_loss.iloc[i] = (avg_loss.iloc[i - 1] * (period - 1) + loss.iloc[i]) / period

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# ✅ MACD 설명 함수
def get_macd_desc(macd, signal):
    return "골든크로스" if macd.iloc[-1] > signal.iloc[-1] else "데드크로스"

# ✅ Streamlit 설정
st.set_page_config(page_title="ETF 기술적 분석", page_icon="📊")
st.title("📊 ETF 기술적 분석 앱")

etf_input = st.text_input("ETF 심볼을 입력하세요 (쉼표로 구분)", "QQQ")
etfs = [e.strip().upper() for e in etf_input.split(",") if e.strip()]

if st.button("분석 실행"):
    for symbol in etfs:
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1y")
            close = hist["Close"]

            # ✅ 지표 계산
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

            strategy_sentence = f"{symbol}의 RSI는 {rsi_val}이고 MACD는 {macd_desc}야. SMA와 볼린저밴드도 함께 고려해서 대응 전략을 알려줘."

            # ✅ 출력
            st.subheader(f"📌 {symbol}")
            st.markdown(f"- RSI: **{rsi_val}**")
            st.markdown(f"- MACD: **{macd_desc}**")
            st.markdown(f"- SMA20: {sma20}, SMA50: {sma50}, SMA200: {sma200}")
            st.markdown(f"- 볼린저밴드 상단: {boll_upper}, 하단: {boll_lower}")

            # ✅ 전략 문장 복사용 출력
            st.code(strategy_sentence, language="text")

            # ✅ RSI 차트 시각화 (다크 스타일)
            fig, ax = plt.subplots()
            ax.plot(rsi_series, color="skyblue", label="RSI")
            ax.axhline(70, color="red", linestyle="--", linewidth=1)
            ax.axhline(30, color="green", linestyle="--", linewidth=1)
            ax.set_title(f"{symbol} RSI 차트")
            ax.set_ylabel("RSI")
            ax.legend()
            st.pyplot(fig)

        except Exception as e:
            st.error(f"{symbol} 분석 중 오류 발생: {e}")

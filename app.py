
import streamlit as st
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import openai

# OpenAI API 키
openai.api_key = st.secrets["openai_api_key"]

# RSI 계산 함수 (Wilder 방식)
def calculate_wilder_rsi(close, period=14):
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    for i in range(period, len(avg_gain)):
        avg_gain.iloc[i] = (avg_gain.iloc[i - 1] * (period - 1) + gain.iloc[i]) / period
        avg_loss.iloc[i] = (avg_loss.iloc[i - 1] * (period - 1) + loss.iloc[i]) / period
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

# RSI 상태 이모지
def rsi_status_emoji(rsi):
    if rsi >= 70:
        return "🟢 과매수"
    elif rsi >= 50:
        return "🟡 중립~상승"
    elif rsi >= 30:
        return "🔵 중립~과매도"
    else:
        return "🔴 과매도"

# MACD 상태 이모지
def macd_status_emoji(macd, signal):
    return "🟢 상승" if macd.iloc[-1] > signal.iloc[-1] else "🔴 하락"

# 전략 문장 생성
def strategy_prompt(etf, rsi, macd_desc):
    return f"{etf}의 RSI는 {rsi}이고 MACD는 {macd_desc}야. SMA와 볼린저밴드도 함께 고려해서 대응 전략을 알려줘."

# GPT 호출
def ask_gpt(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"GPT 오류: {e}"

# 앱 UI
st.set_page_config(page_title="ETF 기술적 분석 앱", page_icon="📊")
st.title("📊 ETF 기술적 분석 앱")
etf_input = st.text_input("ETF 심볼을 입력하세요 (쉼표로 구분)", "QQQ, QLD, BITO, AMZN, GOOGL")
etfs = [e.strip().upper() for e in etf_input.split(",") if e.strip()]

if st.button("🔍 분석 실행"):
    for symbol in etfs:
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1y")
            close = hist['Close']
            price_now = round(close.iloc[-1], 2)

            rsi_series = calculate_wilder_rsi(close)
            rsi_now = round(rsi_series.dropna().iloc[-1], 1)
            rsi_desc = rsi_status_emoji(rsi_now)

            ema12 = close.ewm(span=12).mean()
            ema26 = close.ewm(span=26).mean()
            macd = ema12 - ema26
            signal = macd.ewm(span=9).mean()
            macd_desc = macd_status_emoji(macd, signal)

            sma20 = round(close.rolling(20).mean().iloc[-1], 1)
            sma50 = round(close.rolling(50).mean().iloc[-1], 1)
            sma200 = round(close.rolling(200).mean().iloc[-1], 1)
            std = close.rolling(20).std().iloc[-1]
            boll_upper = round(sma20 + 2 * std, 1)
            boll_lower = round(sma20 - 2 * std, 1)

            prompt = strategy_prompt(symbol, rsi_now, "골든크로스" if macd.iloc[-1] > signal.iloc[-1] else "데드크로스")

            st.subheader(symbol)
            st.markdown(f"💵 **현재 주가**: ${price_now}")
            st.markdown(f"📊 **RSI**: {rsi_now} ({rsi_desc})")
            st.markdown(f"📉 **MACD 상태**: {macd_desc}")
            st.markdown(f"📈 **SMA20**: {sma20}, **SMA50**: {sma50}, **SMA200**: {sma200}")
            st.markdown(f"📊 **볼린저 밴드 상단/하단**: {boll_upper} / {boll_lower}")
            st.code(prompt, language='markdown')

            if st.button(f"{symbol} 전략 확인하기"):
                response = ask_gpt(prompt)
                st.markdown(f"💡 **GPT 전략 제안**

{response}")

            fig, ax = plt.subplots()
            ax.plot(rsi_series, label="RSI", color="#1f77b4")
            ax.axhline(70, color='red', linestyle='--', linewidth=1)
            ax.axhline(30, color='green', linestyle='--', linewidth=1)
            ax.set_facecolor("#0e1117")
            fig.patch.set_facecolor("#0e1117")
            ax.tick_params(colors='white')
            ax.yaxis.label.set_color("white")
            ax.xaxis.label.set_color("white")
            ax.title.set_color("white")
            ax.legend(facecolor="#0e1117", labelcolor="white")
            st.pyplot(fig)

        except Exception as e:
            st.error(f"{symbol} 분석 중 오류 발생: {e}")

# 카드형 2단 UI
cols = st.beta_columns(2)

for idx, symbol in enumerate(etfs):
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

        with cols[idx % 2]:  # 2단 열 배치
            st.markdown(f"""
                <div style='border: 1px solid #ccc; border-radius: 10px; padding: 16px; margin: 10px 0; background-color: #f8f9fa;'>
                    <h4>{symbol}</h4>
                    <p><b>RSI 상태:</b> {rsi_status(rsi_val)}</p>
                    <p><b>MACD 상태:</b> {macd_status(macd_desc)}</p>
                    <p><b>SMA20:</b> {sma20}, <b>SMA50:</b> {sma50}, <b>SMA200:</b> {sma200}</p>
                    <p><b>볼린저 상단:</b> {boll_upper}, <b>하단:</b> {boll_lower}</p>
                    <p><b>전략 문장:</b> {strategy}</p>
                    <p><b>GPT 전략 제안:</b><br>{gpt_response}</p>
                </div>
            """, unsafe_allow_html=True)

            fig, ax = plt.subplots()
            ax.plot(rsi_series, label="RSI", color="blue")
            ax.axhline(70, color='red', linestyle='--', linewidth=1)
            ax.axhline(30, color='green', linestyle='--', linewidth=1)
            ax.set_title(f"{symbol} RSI")
            ax.set_ylabel("RSI")
            ax.legend()
            st.pyplot(fig)

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

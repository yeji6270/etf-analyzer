import pandas as pd

# RSI 상태 계산 함수
def rsi_status(rsi):
    if rsi >= 70:
        return "🟢 과매수"
    elif rsi >= 50:
        return "🟡 중립~상승"
    elif rsi >= 30:
        return "🔵 중립~과매도"
    else:
        return "🔴 과매도"

# MACD 상태 계산 함수
def macd_status(desc):
    return "🟢 상승" if "골든" in desc else "🔴 하락"

# 예시 DataFrame에 함수 적용 (선택적)
if __name__ == "__main__":
    df = pd.DataFrame({
        'RSI': [72, 55, 40, 25],
        'MACD 설명': ['골든크로스', '데드크로스', '데드크로스', '골든크로스']
    })
    df['RSI 상태'] = df['RSI'].apply(rsi_status)
    df['MACD 상태'] = df['MACD 설명'].apply(macd_status)
    print(df)

import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import os

STOCKS = ['2330.TW', '2303.TW', '2454.TW', '2317.TW']
STOCK_NAMES = {
    '2330': '台積電',
    '2303': '聯電',
    '2454': '聯發科',
    '2317': '鴻海'
}
DATA_DIR = 'data'
START_DATE = '2000-01-01'

def get_latest_trading_date(ticker):
    df = yf.download(ticker, period="5d", interval="1d", auto_adjust=True)
    if df.empty:
        return None
    return df.index[-1].strftime('%Y-%m-%d')

def download_data():
    os.makedirs(DATA_DIR, exist_ok=True)

    for ticker in STOCKS:
        stock_code = ticker.split('.')[0]
        latest_date = get_latest_trading_date(ticker)
        if latest_date is None:
            st.warning(f"找不到 {ticker} 的最近交易日，跳過下載。")
            continue

        today_filename = f"{stock_code}_{latest_date}.csv"
        today_filepath = os.path.join(DATA_DIR, today_filename)

        if os.path.exists(today_filepath):
            st.info(f"{stock_code} 資料已是最新（{latest_date}），跳過下載。")
            continue

        try:
            st.write(f"下載 {stock_code} 的資料中...")
            data = yf.download(ticker, start=START_DATE, end=latest_date, auto_adjust=True)
            if data.empty:
                st.warning(f"{ticker} 無資料，跳過。")
                continue

            data.to_csv(today_filepath)
            st.success(f"儲存為 {today_filepath}")

            # 清除舊資料
            for file in os.listdir(DATA_DIR):
                if file.startswith(f"{stock_code}_") and file.endswith(".csv") and file != today_filename:
                    os.remove(os.path.join(DATA_DIR, file))
                    st.info(f"刪除舊檔案 {file}")
        except Exception as e:
            st.error(f"{ticker} 下載失敗：{e}")

def create_close_price_dataframe():
    if not os.path.isdir(DATA_DIR):
        st.warning("data 資料夾不存在，請先下載資料。")
        return None

    all_dfs = []

    for code, name in STOCK_NAMES.items():
        stock_file = next((f for f in os.listdir(DATA_DIR) if f.startswith(f"{code}_") and f.endswith(".csv")), None)
        if stock_file:
            try:
                df = pd.read_csv(os.path.join(DATA_DIR, stock_file), index_col=0, parse_dates=True)
                df = df[['Close']].rename(columns={'Close': name})

                # 強制轉換為數值，非數字會變 NaN
                df = df.apply(pd.to_numeric, errors='coerce')

                all_dfs.append(df)
            except Exception as e:
                st.warning(f"{stock_file} 讀取失敗：{e}")
        else:
            st.warning(f"找不到 {code} 的資料。")

    if not all_dfs:
        return None

    final_df = pd.concat(all_dfs, axis=1)
    final_df.sort_index(inplace=True)
    return final_df

# ========== Streamlit UI ==========
st.title("📈 台灣四大科技股每日收盤價")

if st.button("📥 下載 / 更新最新資料"):
    download_data()

df = create_close_price_dataframe()

if df is None or df.empty:
    st.warning("尚無可用資料，請先下載。")
    st.stop()

# 去除缺漏值
plot_df = df.dropna()

if plot_df.empty:
    st.warning("所有資料都有缺值，無法繪圖。")
    st.stop()

st.subheader("📊 收盤價趨勢圖")
st.line_chart(plot_df)

st.subheader("📄 原始資料（最新5筆）")
st.dataframe(plot_df.tail())

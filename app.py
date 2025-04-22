import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import date

st.set_page_config(
    page_title="فلتر اختراق الشموع البيعية - السوق السعودي",
    page_icon="📉",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown(
    """
    <style>
    body { background-color: #f2f2f2; font-family: 'Cairo', sans-serif; }
    .stButton>button { background-color: #3366cc; color: white; font-weight: bold;
                       padding: 0.4em 1em; margin-top: 0.5em; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True
)

st.markdown("""
<div style='background-color:#3366cc;padding:10px;border-radius:10px'>
  <h2 style='color:white;text-align:center;'>📉 فلتر اختراق الشموع البيعية للسوق السعودي</h2>
</div>
""", unsafe_allow_html=True)

def fetch_data(symbols, start_date, end_date, interval):
    try:
        data = yf.download(
            tickers=symbols,
            start=start_date,
            end=end_date,
            interval=interval,
            group_by='ticker',
            auto_adjust=True,
            progress=False,
            threads=True
        )
        return data
    except Exception as e:
        st.error(f"خطأ في تحميل البيانات: {e}")
        return None

def detect_sell_breakout(df, lose_body_percent=0.55):
    o, h, l, c = df['Open'].values, df['High'].values, df['Low'].values, df['Close'].values
    body_ratio = np.where((h - l) != 0, np.abs(o - c) / (h - l), 0)
    valid_sell = (c < o) & (body_ratio >= lose_body_percent)

    valid_sell_high = np.full(len(df), np.nan)
    breakout = np.zeros(len(df), dtype=bool)

    for i in range(1, len(df)):
        if not np.isnan(valid_sell_high[i-1]) and c[i] > valid_sell_high[i-1] and not valid_sell[i]:
            breakout[i] = True
            valid_sell_high[i] = np.nan
        else:
            valid_sell_high[i] = h[i] if valid_sell[i] else valid_sell_high[i-1]

    df['breakout'] = breakout
    return df

with st.sidebar:
    st.markdown("### ⚙️ إعدادات التحليل (السوق السعودي)")
    suffix = ".SR"
    interval = st.selectbox("اختر الفاصل الزمني", ["1d", "1wk", "1mo"])
    start_date = st.date_input("تاريخ البدء", date(2020, 1, 1))
    end_date = st.date_input("تاريخ الانتهاء", date.today())
    st.markdown("---")
    if st.button("🎯 تجربة على رموز مشهورة"):
        st.session_state['symbols'] = "1120 2380 1050"

symbols_input = st.text_area(
    "أدخل الرموز (أرقام فقط، مفصولة بمسافة أو سطر)",
    st.session_state.get('symbols', '1120 2380 1050')
)
symbols = [sym.strip() + suffix for sym in symbols_input.replace('\n', ' ').split()]

if st.button("🔎 تنفيذ التحليل"):
    data = fetch_data(symbols, start_date, end_date, interval)
    if data is None:
        st.error("فشل تحميل البيانات.")
    else:
        results = []
        for sym_code in symbols:
            try:
                df_sym = data[sym_code].reset_index()
                df_res = detect_sell_breakout(df_sym)
                if df_res['breakout'].iloc[-1]:
                    price = df_res['Close'].iloc[-1]
                    results.append((sym_code.replace(".SR", ""), round(price, 2)))
            except:
                pass

        if results:
            st.success("✅ الرموز التي تحقق فيها الاختراق:")
            df_out = pd.DataFrame(results, columns=["الرمز", "سعر الإغلاق"])
            col1, col2 = st.columns(2)
            col1.metric("رموز مدخلة", len(symbols))
            col2.metric("اختراقات", len(results))
            st.dataframe(df_out)
            st.download_button("📥 تحميل CSV", df_out.to_csv(index=False), file_name="breakouts.csv")
            for code, price in results:
                st.markdown(f"#### 📊 {code} – {price} ريال")
                tv = f"TADAWUL:{code}"
                html = f'<iframe src="https://s.tradingview.com/widgetembed/?symbol={tv}&interval=D&theme=light" width="100%" height="450" frameborder="0"></iframe>'
                st.components.v1.html(html, height=470)
        else:
            st.info("🔎 لا توجد اختراقات جديدة.")
import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

# 設定頁面配置
st.set_page_config(page_title="AI 退休助手 Nana", layout="wide")

# ----------------------------
# Nana 介紹
# ----------------------------
st.header("📢 AI 退休助手 Nana")
st.subheader("讓退休規劃變得簡單又安心！")

st.markdown("""
👋 **嗨！我是 Nana**，你的 AI 退休助手！  
我可以幫助你計算 **退休金需求、投資報酬預測、通膨影響、房產決策**，  
還可以評估你的 **財務健康指數**，讓你快速掌握退休規劃進度！  
""")

# ----------------------------
# 一、基本資料輸入區
# ----------------------------
with st.expander("📋 基本資料", expanded=True):
    st.markdown("💡 **Nana 小提醒：填寫以下資訊，讓我幫你計算你的退休財務狀況！**")
    
    col1, col2 = st.columns(2)
    with col1:
        current_age = st.number_input("🎂 目前年齡", min_value=18, max_value=100, value=40)
        retirement_age = st.number_input("🏖️ 退休年齡", min_value=current_age, max_value=100, value=60)
        expected_lifespan = st.number_input("🎯 預期壽命", min_value=retirement_age, max_value=150, value=100)
    with col2:
        monthly_expense = st.number_input("💰 每月生活費用", min_value=1000, value=30000, step=1000)
        annual_salary = st.number_input("📈 目前年薪", min_value=0, value=1000000, step=10000)
        salary_growth = st.number_input("📊 年薪成長率 (%)", min_value=0.0, value=2.0, step=0.1)
    
    col3, col4 = st.columns(2)
    with col3:
        investable_assets = st.number_input("🏦 初始可投資資產", min_value=0, value=1000000, step=10000)
    with col4:
        investment_return = st.number_input("📈 投資報酬率 (%)", min_value=0.0, value=5.0, step=0.1)
    
    retirement_pension = st.number_input("💵 預估每月退休金", min_value=0, value=20000, step=1000)
    inflation_rate = st.number_input("📉 通膨率 (%)", min_value=0.0, value=2.0, step=0.1)

# ----------------------------
# 二、住房狀況輸入區
# ----------------------------
with st.expander("🏡 住房狀況", expanded=True):
    st.markdown("💡 **Nana 小提醒：不同的住房選擇會影響你的退休財務！**")

    housing_choice = st.selectbox("🏠 你計畫未來的居住方式？", ["租房", "購房"], index=0)
    monthly_rent = st.number_input("🏠 每月租金", min_value=1000, value=25000, step=1000)

    if housing_choice == "購房":
        buy_age = st.number_input("📅 購房年齡", min_value=18, max_value=100, value=40)
        home_price = st.number_input("🏡 房屋總價", key="home_price", value=15000000, step=100000)
        down_payment = st.number_input("🔹 首付款 (30%)", key="down_payment", value=int(15000000 * 0.3), step=100000)
        loan_amount = st.number_input("💳 貸款金額", key="loan_amount", value=15000000 - int(15000000 * 0.3), step=100000)
        loan_term = st.number_input("📆 貸款年期 (年)", min_value=1, max_value=50, value=30)
        loan_rate = st.number_input("📈 貸款利率 (%)", min_value=0.0, value=3.0, step=0.1)

# ----------------------------
# 四、預估退休現金流與趨勢
# ----------------------------
with st.expander("📊 預估退休現金流與趨勢", expanded=True):
    st.markdown("💡 **Nana 幫你模擬退休財務趨勢，看看你的資產變化！**")

    df_chart = pd.DataFrame({
        "年齡": list(range(40, 100)),  # 假設年齡範圍
        "累積結餘": np.linspace(10000000, 5000000, 60)  # 假設數據
    })
    line_chart = alt.Chart(df_chart).mark_line(point=True).encode(
        x=alt.X("年齡:Q", title="年齡"),
        y=alt.Y("累積結餘:Q", title="累積結餘"),
        tooltip=["年齡", "累積結餘"]
    ).properties(
        title="📈 累積結餘隨年齡變化"
    )
    st.altair_chart(line_chart, use_container_width=True)

# ----------------------------
# 行銷資訊
# ----------------------------
st.markdown("---")
st.markdown("🌟 **Nana 由 [永傳家族辦公室](https://www.gracefo.com) 提供**")
st.markdown("🔗 **了解更多 👉 [www.gracefo.com](https://www.gracefo.com)**")

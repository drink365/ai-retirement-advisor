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
還可以評估你的 **財務健康指數**，讓你快速掌握退休規劃進度！ 😊
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

# ----------------------------
# 三、計算退休現金流
# ----------------------------
def calculate_retirement_cashflow():
    """ 計算詳細的退休現金流，包括收入、支出、結餘 """
    ages = list(range(current_age, expected_lifespan + 1))
    data = []
    remaining_assets = investable_assets

    for age in ages:
        salary_income = annual_salary if age <= retirement_age else 0
        investment_income = remaining_assets * (investment_return / 100) if remaining_assets > 0 else 0
        pension_income = retirement_pension * 12 if age > retirement_age else 0
        total_income = salary_income + investment_income + pension_income

        living_expense = monthly_expense * 12
        housing_expense = monthly_rent * 12 if housing_choice == "租房" else 0

        total_expense = living_expense + housing_expense
        annual_balance = total_income - total_expense
        remaining_assets = remaining_assets + annual_balance

        data.append([age, salary_income, investment_income, pension_income, total_income,
                     living_expense, housing_expense, total_expense, annual_balance, remaining_assets])

    df = pd.DataFrame(data, columns=[
        "年齡", "薪資收入", "投資收益", "退休年金", "總收入",
        "生活費用", "住房費用", "總支出",
        "年度結餘", "累積結餘"
    ])
    return df

# ----------------------------
# 四、顯示預估退休現金流與趨勢
# ----------------------------
with st.expander("📊 預估退休現金流與趨勢", expanded=True):
    df_cashflow = calculate_retirement_cashflow()
    st.dataframe(df_cashflow.style.format("{:,.0f}"), use_container_width=True)

    line_chart = alt.Chart(df_cashflow).mark_line(point=True).encode(
        x=alt.X("年齡:Q", title="年齡"),
        y=alt.Y("累積結餘:Q", title="累積結餘"),
        tooltip=["年齡", "累積結餘"]
    ).properties(title="📈 累積結餘隨年齡變化")
    
    st.altair_chart(line_chart, use_container_width=True)

# ----------------------------
# 五、財務健康指數評估
# ----------------------------
with st.expander("📊 財務健康指數", expanded=True):
    target_asset = st.number_input("🎯 你的理想退休資產（元）", min_value=0, value=10000000, step=1000000)
    projected_asset = calculate_retirement_cashflow().iloc[-1]["累積結餘"]

    health_score = int((projected_asset / target_asset) * 100) if target_asset > 0 else 0
    st.metric(label="📈 Nana 給你的財務健康指數", value=f"{health_score} 分", delta=health_score - 80)

# ----------------------------
# 六、行銷資訊
# ----------------------------
st.markdown("---")
st.markdown("🌟 **Nana 由 [永傳家族辦公室](https://www.gracefo.com) 提供**")
st.markdown("🔗 **了解更多 👉 [www.gracefo.com](https://www.gracefo.com)**")

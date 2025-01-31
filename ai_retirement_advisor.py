import streamlit as st
import numpy as np
import pandas as pd

def calculate_retirement_cashflow(current_age, retirement_age, monthly_expense, total_assets, annual_return_rate):
    """
    計算退休現金流，確保資產能夠支撐到壽命終點
    """
    years_in_retirement = 100 - retirement_age  # 假設壽命 100 歲
    annual_expense = monthly_expense * 12
    remaining_assets = total_assets
    cashflow_data = []

    for year in range(retirement_age, 100):
        remaining_assets *= (1 + annual_return_rate / 100)  # 投資增長
        remaining_assets -= annual_expense  # 減去生活費用
        cashflow_data.append([year, remaining_assets if remaining_assets > 0 else 0])
        if remaining_assets <= 0:
            break
    
    return cashflow_data, remaining_assets

# Streamlit UI 設計
st.set_page_config(page_title="AI 退休顧問", layout="wide")
st.header("📢 AI 智能退休顧問")

# 用戶輸入財務數據
st.subheader("請輸入您的財務狀況")
current_age = st.number_input("您的目前年齡", min_value=30, max_value=80, value=45)
retirement_age = st.number_input("您計劃退休的年齡", min_value=current_age+1, max_value=90, value=60)
monthly_expense = st.number_input("退休後每月希望支出的金額（萬）", min_value=1, max_value=50, value=10)
total_assets = st.number_input("目前總資產（萬）", min_value=100, max_value=100000, value=5000)
annual_return_rate = st.slider("預期年均投資報酬率（%）", min_value=1.0, max_value=10.0, value=5.0, step=0.1)

# 計算退休現金流
cashflow_data, final_balance = calculate_retirement_cashflow(current_age, retirement_age, monthly_expense, total_assets, annual_return_rate)

# 顯示試算結果
st.subheader(f"📊 退休現金流試算結果")
if final_balance > 0:
    st.success(f"🎉 您的資產足夠支撐到 100 歲，預估最終剩餘資產：{final_balance:,.0f} 萬元")
else:
    st.warning(f"⚠️ 您的資金可能在 {cashflow_data[-1][0]} 歲耗盡！請考慮調整退休計劃。")

# 顯示現金流表格
df = pd.DataFrame(cashflow_data, columns=["年份", "剩餘資產（萬）"])
st.table(df)

# AI 建議
st.subheader("📢 AI 智能建議")
if final_balance > 0:
    st.markdown("**🎯 您的財務計劃穩健，可以考慮進一步優化資產配置，提高退休生活品質。**")
else:
    st.markdown("**⚠️ 您的退休計劃可能存在資金缺口，建議考慮以下方式：**")
    st.markdown("1️⃣ **延遲退休** → 增加資產累積時間，減少提款壓力")
    st.markdown("2️⃣ **調整投資策略** → 提高投資報酬率，但需控制風險")
    st.markdown("3️⃣ **降低退休支出** → 適當減少開銷，讓資產撐得更久")

# 行動號召
st.markdown("---")
st.markdown("## 📢 讓專業顧問幫助您優化退休計劃！")
st.markdown("🔍 **您的退休財務準備足夠嗎？如果不確定，讓我們幫助您規劃更穩定的退休生活！**")
st.markdown("📩 **立即預約免費退休財務諮詢！**")
st.markdown("🌐 [www.gracefo.com](https://www.gracefo.com)")

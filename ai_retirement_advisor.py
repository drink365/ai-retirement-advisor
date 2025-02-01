import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# =============================
# 1) 計算退休現金流函式
# =============================
def calculate_retirement_cashflow(
    current_age, retirement_age, expected_lifespan, monthly_expense,
    rent_or_buy, rent_amount, rent_before_buy,
    buy_age, home_price, down_payment, loan_amount, loan_term, loan_rate,
    annual_salary, salary_growth, investable_assets,
    investment_return, inflation_rate, retirement_pension,
    lumpsum_list
):
    """
    計算退休現金流：
      - 收入：薪資（退休前）、投資收益、退休年金（退休後）
      - 支出：
         1) 生活費（含通膨）
         2) 住房費（租房或買房邏輯）
         3) 一次性支出 lumpsum（不含通膨），僅計算 lumpsum_list 中年齡 ≥ current_age 且 金額 > 0 的資料，
            並在該年發生的支出會被累加。
    """
    ages = list(range(current_age, expected_lifespan + 1))
    data = []
    remaining_assets = investable_assets

    # 計算每月房貸（若有貸款）
    monthly_mortgage = 0
    if loan_amount > 0 and loan_term > 0:
        lr_monthly = loan_rate / 100 / 12
        monthly_mortgage = loan_amount * lr_monthly / (1 - (1 + lr_monthly) ** (-loan_term * 12))

    # 轉換一次性支出清單為 DataFrame
    lumpsum_df = pd.DataFrame(lumpsum_list) if lumpsum_list else pd.DataFrame(columns=["年齡", "金額"])

    for i, age in enumerate(ages):
        # 薪資（退休前有薪資，退休後為 0）
        salary_income = int(annual_salary) if age <= retirement_age else 0
        if age < retirement_age:
            annual_salary *= (1 + salary_growth / 100)

        # 投資收益
        investment_income = int(remaining_assets * (investment_return / 100)) if remaining_assets > 0 else 0

        # 退休年金
        pension_income = int(retirement_pension * 12) if age > retirement_age else 0

        total_income = salary_income + investment_income + pension_income

        # 生活費（尚未乘通膨）
        living_expense = int(monthly_expense * 12)

        # 住房費用計算：租房或買房邏輯
        if rent_or_buy == "租房":
            housing_expense = int(rent_amount * 12)
        else:
            diff = age - buy_age
            if diff < 0:
                housing_expense = int(rent_before_buy * 12)
            elif diff == 0:
                housing_expense = int(down_payment + monthly_mortgage * 12)
            elif 0 < diff < loan_term:
                housing_expense = int(monthly_mortgage * 12)
            else:
                housing_expense = 0

        # 通膨影響下的基礎支出
        base_expense = (living_expense + housing_expense) * ((1 + inflation_rate / 100) ** i)

        # 累加一次性支出：僅計算 lumpsum_df 中滿足條件的行
        lumpsum_expense = 0
        for _, row in lumpsum_df.iterrows():
            try:
                exp_age = int(row["年齡"])
                exp_amt = float(row["金額"])
            except (ValueError, TypeError):
                continue
            if exp_age < current_age or exp_amt <= 0:
                continue
            if exp_age == age:
                lumpsum_expense += exp_amt

        total_expense = int(base_expense) + int(lumpsum_expense)
        annual_balance = total_income - total_expense

        remaining_assets = ((remaining_assets + annual_balance) * (1 + investment_return / 100)) / (1 + inflation_rate / 100)

        data.append([
            age, salary_income, investment_income, pension_income,
            total_income, living_expense, housing_expense, lumpsum_expense,
            total_expense, annual_balance, remaining_assets
        ])

    df = pd.DataFrame(data, columns=[
        "年齡", "薪資收入", "投資收益", "退休年金", "總收入",
        "生活費用", "住房費用", "一次性支出", "總支出",
        "年度結餘", "剩餘資產"
    ])
    df.rename(columns={"剩餘資產": "累積結餘"}, inplace=True)

    df = df[[
        "年齡",
        "薪資收入", "投資收益", "退休年金", "總收入",
        "生活費用", "住房費用", "一次性支出", "總支出",
        "年度結餘", "累積結餘"
    ]]
    return df

# ===========================
# 2) Streamlit App
# ===========================
st.set_page_config(page_title="AI 退休顧問", layout="wide")
st.header("📢 AI 智能退休顧問")

# 使用 session_state 管理一次性支出資料
if "lumpsum_list" not in st.session_state:
    st.session_state["lumpsum_list"] = []  # 初始空清單

# -----------------------------
# 一次性支出管理
# -----------------------------
st.subheader("📌 一次性支出 (偶發性)")

with st.form("add_lumpsum"):
    new_age = st.number_input("新增一次性支出 - 年齡", min_value=30, max_value=110, value=40)
    new_amt = st.number_input("新增一次性支出 - 金額", min_value=1, value=100000)
    submitted = st.form_submit_button("新增")
    if submitted:
        if new_age >= 30 and new_amt > 0:
            st.session_state["lumpsum_list"].append({"年齡": new_age, "金額": new_amt})
            st.success(f"新增成功：年齡 {new_age}，金額 {new_amt}")
        else:
            st.warning("無效輸入：年齡須 ≥ 30 且金額 > 0。")

# 只顯示「刪除」按鈕，隱藏清單
if st.session_state["lumpsum_list"]:
    for idx, entry in enumerate(st.session_state["lumpsum_list"]):
        if st.button(f"刪除：年齡 {entry['年齡']}、金額 {entry['金額']}", key=f"del_{idx}"):
            st.session_state["lumpsum_list"].pop(idx)
            st.success("刪除成功！")
            st.experimental_rerun()

# -----------------------------
# 計算退休現金流
# -----------------------------
df_result = calculate_retirement_cashflow(
    40, 60, 100, 30000, "租房", 20000, 20000,
    48, 15000000, 4500000, 10500000, 20, 2.0,
    1000000, 2.0, 1000000, 5.0, 2.0, 20000,
    st.session_state["lumpsum_list"]
)

st.subheader("### 預估現金流")
st.dataframe(df_result.style.format("{:,.0f}"), use_container_width=True)

st.markdown("如需專業協助，歡迎造訪 [永傳家族辦公室](http://www.gracefo.com)")

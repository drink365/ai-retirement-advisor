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
    lumpsum_df
):
    """
    計算退休現金流:
      - 收入: 薪資（退休前）、投資收益（有資產時）、退休年金（退休後）
      - 支出:
         1) 生活費（含通膨）
         2) 住房費（租房或買房邏輯）
         3) 一次性支出 lumpsum（不含通膨），僅計算 lumpsum_df 中「年齡 ≥ current_age 且 金額 > 0」的行
    """
    ages = list(range(current_age, expected_lifespan + 1))
    data = []
    remaining_assets = investable_assets

    # 若有貸款，計算每月房貸
    monthly_mortgage = 0
    if loan_amount > 0 and loan_term > 0:
        lr_monthly = loan_rate / 100 / 12
        monthly_mortgage = loan_amount * lr_monthly / (1 - (1 + lr_monthly) ** (-loan_term * 12))

    # 若 lumpsum_df 為空，確保有兩個欄位
    if lumpsum_df.empty:
        lumpsum_df = pd.DataFrame(columns=["年齡", "金額"])

    for i, age in enumerate(ages):
        # 薪資
        salary_income = int(annual_salary) if age <= retirement_age else 0
        if age < retirement_age:
            annual_salary *= (1 + salary_growth / 100)

        # 投資收益
        investment_income = int(remaining_assets * (investment_return / 100)) if remaining_assets > 0 else 0

        # 退休年金
        pension_income = int(retirement_pension * 12) if age > retirement_age else 0

        total_income = salary_income + investment_income + pension_income

        # 生活費
        living_expense = int(monthly_expense * 12)

        # 住房費用
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

        # 考慮通膨：基礎支出
        base_expense = (living_expense + housing_expense) * ((1 + inflation_rate / 100) ** i)

        # 一次性支出：僅針對 lumpsum_df 中年齡 == 當前年齡的列
        lumpsum_expense = 0
        for _, row in lumpsum_df.iterrows():
            try:
                expense_age = int(row["年齡"])
                expense_amt = float(row["金額"])
            except (ValueError, TypeError):
                continue
            if expense_age < current_age or expense_amt <= 0:
                continue
            if expense_age == age:
                lumpsum_expense += expense_amt

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
    df.columns = pd.MultiIndex.from_tuples([
        ("", "年齡"),
        ("收入", "薪資收入"),
        ("收入", "投資收益"),
        ("收入", "退休年金"),
        ("收入", "總收入"),
        ("支出", "生活費用"),
        ("支出", "住房費用"),
        ("支出", "一次性支出"),
        ("支出", "總支出"),
        ("結餘", "年度結餘"),
        ("結餘", "累積結餘"),
    ])
    return df

# ===========================
# 2) Streamlit App
# ===========================
st.set_page_config(page_title="AI 退休顧問", layout="wide")
st.header("📢 AI 智能退休顧問")

# 使用 session_state 管理一次性支出資料
if "lumpsum_df" not in st.session_state:
    st.session_state["lumpsum_df"] = pd.DataFrame(columns=["年齡", "金額"])

# ------------------
# 基本資料
# ------------------
st.subheader("📌 基本資料")
current_age = st.number_input("您的目前年齡", min_value=30, max_value=80, value=40)
retirement_age = st.number_input("您計劃退休的年齡", min_value=current_age+1, max_value=90, value=60)
expected_lifespan = st.number_input("預期壽命（歲）", min_value=70, max_value=110, value=100)

# ------------------
# 家庭與財務狀況
# ------------------
st.subheader("📌 家庭與財務狀況")
monthly_expense = st.number_input("每月生活支出（元）", min_value=1000, max_value=500000, value=30000, format="%d")
annual_salary = st.number_input("目前家庭年薪（元）", min_value=500000, max_value=100000000, value=1000000, format="%d")
salary_growth = st.slider("預計薪資成長率（%）", min_value=0.0, max_value=10.0, value=2.0, step=0.1)
investable_assets = st.number_input("目前可投資之資金（元）", min_value=0, max_value=1000000000, value=1000000, format="%d")
investment_return = st.slider("預期投報率（%）", min_value=0.1, max_value=10.0, value=5.0, step=0.1)
inflation_rate = st.slider("通貨膨脹率（%）", min_value=0.1, max_value=10.0, value=2.0, step=0.1)
retirement_pension = st.number_input("退休年金（元/月）", min_value=0, max_value=500000, value=20000, format="%d")

# ------------------
# 住房計畫
# ------------------
st.subheader("📌 住房計畫")
rent_or_buy = st.radio("您的住房計畫", ["租房", "買房"])

rent_amount = 0
rent_before_buy = 0
buy_age = home_price = down_payment = loan_amount = loan_term = loan_rate = 0
monthly_mortgage_temp = 0
if rent_or_buy == "租房":
    rent_amount = st.number_input("每月租金（元）", min_value=0, max_value=500000, value=20000, format="%d")
else:
    rent_before_buy = st.number_input("買房前每月租金（元）", min_value=0, max_value=500000, value=20000, format="%d")
    buy_age = st.number_input("計劃買房年齡", min_value=0, max_value=80, value=30)
    home_price = st.number_input("預計買房價格（元）", min_value=0, value=15000000, format="%d")
    down_payment = st.number_input("頭期款（元）", min_value=0, value=int(home_price * 0.3), format="%d")
    loan_amount = st.number_input("貸款金額（元）", min_value=0, value=home_price - down_payment, format="%d")
    loan_term = st.number_input("貸款年限（年）", min_value=1, max_value=30, value=20)
    loan_rate = st.number_input("貸款利率（%）", min_value=0.1, max_value=10.0, value=2.0, step=0.1)

    if loan_amount > 0 and loan_term > 0:
        lr_monthly = loan_rate / 100 / 12
        monthly_mortgage_temp = loan_amount * lr_monthly / (1 - (1 + lr_monthly) ** (-loan_term * 12))
    else:
        monthly_mortgage_temp = 0

    st.write(f"每月房貸: {monthly_mortgage_temp:,.0f} 元")

# -----------------------------
# 一次性支出：使用 st.data_editor (僅顯示「年齡」和「金額」)
# -----------------------------
st.subheader("📌 一次性支出 (偶發性)")
st.write(f"請在下表中新增或編輯一次性支出。年齡必須 ≥ {current_age} 且金額 > 0。")

# 此處直接使用 session_state 中的 lumpsum_df（僅包含「年齡」和「金額」欄）
lumpsum_df_edited = st.data_editor(
    st.session_state["lumpsum_df"],
    column_config={
        "年齡": st.column_config.NumberColumn(
            "年齡 (≥目前年齡)",
            min_value=current_age,
            step=1
        ),
        "金額": st.column_config.NumberColumn(
            "金額 (>0)",
            min_value=1,
            step=1000
        )
    },
    num_rows="dynamic",
    use_container_width=True
)
st.session_state["lumpsum_df"] = lumpsum_df_edited

# -----------------------------
# 計算退休現金流
# -----------------------------
df_result = calculate_retirement_cashflow(
    current_age, retirement_age, expected_lifespan,
    monthly_expense, rent_or_buy, rent_amount, rent_before_buy,
    buy_age, home_price, down_payment, loan_amount, loan_term, loan_rate,
    annual_salary, salary_growth, investable_assets,
    investment_return, inflation_rate, retirement_pension,
    st.session_state["lumpsum_df"]
)

def style_negative(val):
    color = "red" if (isinstance(val, (int, float)) and val < 0) else "black"
    return f"color: {color}"

styled_df = df_result.style
all_cols = df_result.columns
styled_df = styled_df.applymap(style_negative, subset=pd.IndexSlice[:, all_cols])
styled_df = styled_df.format("{:,.0f}", subset=pd.IndexSlice[:, all_cols])

st.subheader("### 預估現金流")
st.dataframe(styled_df, use_container_width=True)

st.markdown("""
### 更多貼心提醒

- **定期檢視**：建議每隔 6~12 個月檢視一次財務與保險規劃，以因應人生變化。
- **保險規劃**：根據家庭結構，適時調整壽險與健康險以降低風險。
- **投資分配**：分散投資可降低單一資產波動對財務的影響。
- **退休年金**：若累積結餘偏低，請考慮提高投資報酬率或延後退休年齡。
- **家族傳承**：有需求者可結合信託與保險工具，為後代做好資產配置與節稅安排。

想了解更多專業建議，歡迎造訪  
[永傳家族辦公室](http://www.gracefo.com) 了解更完整的財務與傳承服務！
""")

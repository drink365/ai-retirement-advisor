import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ============================================================
# 1) Functions
# ============================================================
def calculate_retirement_cashflow(
    current_age, retirement_age, expected_lifespan, monthly_expense,
    rent_or_buy, rent_amount, rent_before_buy,
    buy_age, home_price, down_payment, loan_amount, loan_term, loan_rate,
    annual_salary, salary_growth, investable_assets,
    investment_return, inflation_rate, retirement_pension,
    other_expenses
):
    """
    計算退休現金流，考慮以下邏輯：

    一、收入
       - 薪資 (退休前成長)
       - 投資收益
       - 退休年金 (退休後)

    二、支出
       1. 生活費
       2. 住房費
          (A) 若「租房」：全程 rent_amount * 12
          (B) 若「買房」：
              - 年齡 < buy_age => rent_before_buy * 12
              - 年齡 == buy_age => 頭期款 + (房貸月付*12)
              - buy_age < 年齡 < buy_age+loan_term => 房貸月付*12
              - 貸款期滿 => 0
       3. 一次性支出 lumpsum，不考慮通膨
          - 若年齡 < current_age 或金額 <=0 或空白 => 跳過
          - 年齡 == 當前年齡 => 當年扣除

    三、remaining_assets => 累積結餘
       年度結餘 + 上年累積結餘，再乘(1+投報率)/(1+通膨)
    """

    ages = list(range(current_age, expected_lifespan + 1))
    data = []
    remaining_assets = investable_assets

    # 若有貸款，計算每月房貸
    monthly_mortgage = 0
    if loan_amount > 0 and loan_term > 0:
        lr_monthly = loan_rate / 100 / 12
        monthly_mortgage = (
            loan_amount * lr_monthly
            / (1 - (1 + lr_monthly) ** (-loan_term * 12))
        )

    for i, age in enumerate(ages):
        # 薪資
        salary_income = int(annual_salary) if age <= retirement_age else 0
        if age < retirement_age:
            annual_salary *= (1 + salary_growth / 100)

        # 投資收益
        if remaining_assets > 0:
            investment_income = int(remaining_assets * (investment_return / 100))
        else:
            investment_income = 0

        # 退休年金
        pension_income = int(retirement_pension * 12) if age > retirement_age else 0

        # 當年總收入
        total_income = salary_income + investment_income + pension_income

        # 生活費
        living_expense = int(monthly_expense * 12)

        # 住房費用
        if rent_or_buy == "租房":
            # 全程租房
            housing_expense = int(rent_amount * 12)
        else:
            # 買房
            mortgage_year = age - buy_age
            if mortgage_year < 0:
                # 買房前 => rent_before_buy
                housing_expense = int(rent_before_buy * 12)
            elif mortgage_year == 0:
                # 買房當年 => 頭期 + 當年房貸
                housing_expense = int(down_payment + monthly_mortgage * 12)
            elif 0 < mortgage_year < loan_term:
                # 貸款期 => 每年房貸
                housing_expense = int(monthly_mortgage * 12)
            else:
                # 貸款期滿
                housing_expense = 0

        # 通膨影響 => 經常性支出
        base_expense = (living_expense + housing_expense) * ((1 + inflation_rate / 100) ** i)

        # 一次性支出 lumpsum (不考慮通膨)
        lumpsum_expense = 0
        for _, row_data in other_expenses.iterrows():
            try:
                age_raw = str(row_data.get("年齡", "")).strip()
                amt_raw = str(row_data.get("金額", "")).strip()
                if not age_raw or not amt_raw:
                    continue
                expense_age = int(age_raw)
                expense_amt = float(amt_raw)
            except (ValueError, TypeError):
                # 若輸入不合法 => 跳過
                continue

            # 若年齡 < current_age 或金額<=0 => 跳過
            if expense_age < current_age or expense_amt <= 0:
                continue

            if expense_age == age:
                lumpsum_expense += expense_amt

        # 總支出
        total_expense = int(base_expense) + int(lumpsum_expense)

        # 年度結餘
        annual_balance = total_income - total_expense

        # 更新累積結餘 => (前累積 + 結餘)*投報率 / 通膨
        remaining_assets = (
            (remaining_assets + annual_balance)
            * (1 + investment_return / 100)
            / (1 + inflation_rate / 100)
        )

        data.append([
            age,
            salary_income,
            investment_income,
            pension_income,
            total_income,
            living_expense,
            housing_expense,
            lumpsum_expense,
            total_expense,
            annual_balance,
            remaining_assets
        ])

    # 建立 DataFrame
    df = pd.DataFrame(data, columns=[
        "年齡","薪資收入","投資收益","退休年金","總收入",
        "生活費用","住房費用","一次性支出","總支出",
        "年度結餘","剩餘資產"
    ])
    df.rename(columns={"剩餘資產": "累積結餘"}, inplace=True)

    # 多層表頭
    df = df[[
        "年齡",
        "薪資收入","投資收益","退休年金","總收入",
        "生活費用","住房費用","一次性支出","總支出",
        "年度結餘","累積結餘"
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

# ============================================================
# 2) Streamlit App
# ============================================================
st.set_page_config(page_title="AI 退休顧問", layout="wide")
st.header("📢 AI 智能退休顧問")

# 預先定義, 避免 name 未定義
rent_amount = 0
rent_before_buy = 0

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

if rent_or_buy == "租房":
    # 全程租房
    rent_amount = st.number_input("每月租金（元）", min_value=0, max_value=500000, value=20000, format="%d")
    buy_age = 0
    home_price= down_payment= loan_amount= loan_term= loan_rate= 0
    monthly_mortgage_temp = 0
else:
    # 若買房 => 顯示買房前租金
    rent_before_buy = st.number_input("買房前每月租金（元）", min_value=0, max_value=500000, value=20000, format="%d")

    buy_age = st.number_input("計劃買房年齡", min_value=0, max_value=80, value=30)
    home_price = st.number_input("預計買房價格（元）", min_value=0, value=15000000, format="%d")
    down_payment = st.number_input("頭期款（元）", min_value=0, value=int(home_price*0.3), format="%d")
    loan_amount = st.number_input("貸款金額（元）", min_value=0, value=home_price-down_payment, format="%d")
    loan_term = st.number_input("貸款年限（年）", min_value=1, max_value=30, value=20)
    loan_rate = st.number_input("貸款利率（%）", min_value=0.1, max_value=10.0, value=2.0, step=0.1)

    # 即時顯示每月房貸
    if loan_amount > 0 and loan_term > 0:
        lr_monthly = loan_rate / 100 / 12
        monthly_mortgage_temp = (
            loan_amount * lr_monthly
            / (1 - (1 + lr_monthly) ** (-loan_term * 12))
        )
    else:
        monthly_mortgage_temp = 0

    st.subheader("每月房貸")
    st.write(f"{monthly_mortgage_temp:,.0f} 元")

# -----------------------------
# 其它一次性支出
# -----------------------------
st.subheader("📌 其它一次性支出")
st.write("如有大額支出，可在下表填【年齡】&【金額】，該年就會扣除一次性支出 (不計通膨)。")
st.write(f"**注意**：若年齡<{current_age} 或金額<=0，會跳過；若輸入非數字也跳過。")

init_df = pd.DataFrame({
    "年齡":[45,60],
    "金額":[200000,300000]
})
edited_df = st.data_editor(init_df, num_rows="dynamic")

# -----------------------------
# 計算退休現金流
# -----------------------------
data_df = calculate_retirement_cashflow(
    current_age, retirement_age, expected_lifespan, monthly_expense,
    rent_or_buy, rent_amount, rent_before_buy,
    buy_age, home_price, down_payment, loan_amount,
    loan_term, loan_rate, annual_salary, salary_growth,
    investable_assets, investment_return, inflation_rate,
    retirement_pension, edited_df
)

# -----------------------------
# 負數標紅 & 千分號
# -----------------------------
def style_negative(val):
    color = "red" if (isinstance(val, (int, float)) and val < 0) else "black"
    return f"color: {color}"

all_cols = data_df.columns
styled_df = data_df.style
styled_df = styled_df.applymap(style_negative, subset=pd.IndexSlice[:, all_cols])
styled_df = styled_df.format("{:,.0f}", subset=pd.IndexSlice[:, all_cols])

# -----------------------------
# 顯示結果
# -----------------------------
st.dataframe(styled_df)

# -----------------------------
# 更多貼心提醒
# -----------------------------
st.markdown("""
### 更多貼心提醒

- **定期檢視**：建議每隔 6~12 個月檢視一次財務與保險規劃，以因應人生變化。
- **保險規劃**：可考慮根據家庭結構，增加或調整壽險與健康險，避免風險發生時影響退休生活。
- **投資分配**：建議保持分散投資原則，降低單一資產波動對財務的衝擊。
- **退休年金**：如果累積結餘偏低，可考慮提高投資報酬率或延後退休年齡，以確保退休後現金流足夠。
- **家族傳承**：如有家族企業或高資產規劃需求，可結合信託與保險工具，為後代做好資產配置與節稅安排。

想了解更多專業建議，歡迎造訪  
[永傳家族辦公室](http://www.gracefo.com) 了解更完整的財務與傳承服務！
""")

import streamlit as st
import numpy as np
import pandas as pd

def calculate_retirement_cashflow(current_age, retirement_age, expected_lifespan, monthly_expense, rent_or_buy, rent_amount,
                                  buy_age, home_price, down_payment, loan_term, loan_rate, annual_salary, salary_growth,
                                  investable_assets, investment_return, inflation_rate, retirement_pension):
    """
    計算退休現金流，考慮收入、支出、住房計畫、投資報酬、通膨影響等因素。
    """
    years = list(range(current_age, expected_lifespan + 1))
    data = []
    remaining_assets = investable_assets
    loan_balance = home_price - down_payment if rent_or_buy == "買房" else 0
    monthly_mortgage = 0
    if loan_balance > 0:
        loan_rate_monthly = loan_rate / 100 / 12
        monthly_mortgage = (loan_balance * loan_rate_monthly) / (1 - (1 + loan_rate_monthly) ** (-loan_term * 12))
    
    for year in years:
        # 收入區
        salary_income = int(annual_salary) if year <= retirement_age else 0
        if year < retirement_age:
            annual_salary *= (1 + salary_growth / 100)
        investment_income = int(remaining_assets * (investment_return / 100))
        pension_income = int(retirement_pension) if year > retirement_age else 0
        total_income = int(salary_income + investment_income + pension_income)
        
        # 支出區
        living_expense = int(monthly_expense * 12)
        if rent_or_buy == "租房":
            housing_expense = int(rent_amount * 12)
        else:
            if year == buy_age:
                housing_expense = int(down_payment + (monthly_mortgage * 12))
            elif buy_age <= year < buy_age + loan_term:
                housing_expense = int(monthly_mortgage * 12)
            else:
                housing_expense = 0
        total_expense = int(living_expense + housing_expense)
        
        # 計算當年度結餘
        annual_balance = int(total_income - total_expense)
        remaining_assets += annual_balance
        remaining_assets *= (1 + investment_return / 100)
        remaining_assets /= (1 + inflation_rate / 100)
        
        data.append([
            year, salary_income, investment_income, pension_income, total_income,
            living_expense, housing_expense, total_expense, annual_balance, int(remaining_assets * 10000)
        ])
        
    return data

# Streamlit UI 設計
st.set_page_config(page_title="AI 退休顧問", layout="wide")
st.header("📢 AI 智能退休顧問")

# 用戶輸入財務數據
st.subheader("📌 基本資料")
current_age = st.number_input("您的目前年齡", min_value=30, max_value=80, value=45)
retirement_age = st.number_input("您計劃退休的年齡", min_value=current_age+1, max_value=90, value=60)
expected_lifespan = st.number_input("預期壽命（歲）", min_value=70, max_value=110, value=100)

st.subheader("📌 家庭開銷")
monthly_expense = st.number_input("每月生活支出（元）", min_value=1000, max_value=500000, value=int(f'{30000:,}'.replace(',', '')), format="%d")

st.subheader("📌 住房計畫")
rent_or_buy = st.radio("您的住房計畫", ["租房", "買房"])
if rent_or_buy == "租房":
    rent_amount = st.number_input("每月租金（元）", min_value=0, max_value=500000, value=int(f'{20000:,}'.replace(',', '')), format="%d")
    buy_age, home_price, down_payment, loan_term, loan_rate = None, None, None, None, None
else:
    buy_age = st.number_input("計劃買房年齡", min_value=current_age, max_value=80, value=current_age)
    home_price = st.number_input("預計買房價格（元）", min_value=0, value=int(f'{15000000:,}'.replace(',', '')), format="%d")
    down_payment = st.number_input("頭期款（元）", min_value=0, value=int(f'{int(home_price * 0.3):,}'.replace(',', '')), format="%d")
    loan_term = st.number_input("貸款年限（年）", min_value=1, max_value=40, value=30)
    loan_rate = st.slider("房貸利率（%）", min_value=0.1, max_value=10.0, value=3.0, step=0.1)

st.subheader("📌 財務狀況")
annual_salary = st.number_input("目前家庭年薪（元）", min_value=500000, max_value=100000000, value=int(f'{1000000:,}'.replace(',', '')), format="%d")
salary_growth = st.slider("預計薪資成長率（%）", min_value=0.0, max_value=10.0, value=2.0, step=0.1)
investable_assets = st.number_input("目前可投資之資金（元）", min_value=0, max_value=1000000000, value=int(f'{1000000:,}'.replace(',', '')), format="%d")
investment_return = st.slider("預期投報率（%）", min_value=0.1, max_value=10.0, value=5.0, step=0.1)
inflation_rate = st.slider("通貨膨脹率（%）", min_value=0.1, max_value=10.0, value=2.0, step=0.1)
retirement_pension = st.number_input("退休年金（元/月）", min_value=0, max_value=500000, value=int(f'{20000:,}'.replace(',', '')), format="%d")

# 計算退休現金流
data = calculate_retirement_cashflow(current_age, retirement_age, expected_lifespan, monthly_expense, rent_or_buy, rent_amount,
                                     buy_age, home_price, down_payment, loan_term, loan_rate, annual_salary, salary_growth,
                                     investable_assets, investment_return, inflation_rate, retirement_pension)

# 顯示結果
df = pd.DataFrame(data, columns=["年齡", "薪資收入", "投資收入", "退休年金", "總收入",
                                 "家庭開銷", "住房支出", "總支出", "年度結餘", "累積結餘"])

# 檢查 DataFrame 欄位，避免 KeyError
st.write("DataFrame 欄位:", df.columns)

# 格式化數字，增加千分位逗號
for col in ["薪資收入", "投資收入", "退休年金", "總收入", "家庭開銷", "住房支出", "總支出", "年度結餘", "累積結餘"]:
    if col in df.columns:
        df[col] = df[col].apply(lambda x: f"{x:,}")

# 格式化數字，增加千分位逗號
for col in ["每月生活支出（元）", "每月租金（元）", "目前家庭年薪（元）", "目前可投資之資金（元）","退休年金（元/月）",  "薪資收入", "投資收入", "退休年金", "總收入", "家庭開銷", "住房支出", "總支出", "年度結餘", "累積結餘"]:
    df[col] = df[col].apply(lambda x: f"{x:,}")
st.subheader("📊 退休現金流預測")
st.table(df)

import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def calculate_retirement_cashflow(current_age, retirement_age, expected_lifespan, monthly_expense, rent_or_buy, rent_amount,
                                  buy_age, home_price, down_payment, loan_amount, loan_term, loan_rate, annual_salary, salary_growth,
                                  investable_assets, investment_return, inflation_rate, retirement_pension):
    """
    計算退休現金流，考慮收入、支出、住房計畫、投資報酬、通膨影響等因素。
    """
    years = list(range(current_age, expected_lifespan + 1))
    data = []
    remaining_assets = investable_assets
    monthly_mortgage = 0
    
    if loan_amount > 0 and loan_term > 0:
        loan_rate_monthly = loan_rate / 100 / 12
        monthly_mortgage = loan_amount * loan_rate_monthly / (1 - (1 + loan_rate_monthly) ** (-loan_term * 12))
    
    for i, year in enumerate(years):
        salary_income = int(annual_salary) if year <= retirement_age else 0
        if year < retirement_age:
            annual_salary *= (1 + salary_growth / 100)
        investment_income = int(remaining_assets * (investment_return / 100)) if remaining_assets > 0 else 0
        pension_income = int(retirement_pension * 12) if year > retirement_age else 0
        total_income = salary_income + investment_income + pension_income
        
        living_expense = int(monthly_expense * 12)
        if rent_or_buy == "租房" or year < buy_age:
            housing_expense = int(rent_amount * 12)
        else:
            if year == buy_age:
                housing_expense = int(down_payment + (monthly_mortgage * 12))
            elif buy_age <= year < buy_age + loan_term:
                housing_expense = int(monthly_mortgage * 12)
            else:
                housing_expense = 0
        
        total_expense = int((living_expense + housing_expense) * ((1 + inflation_rate / 100) ** i))
        annual_balance = total_income - total_expense
        remaining_assets = (remaining_assets + annual_balance) * (1 + investment_return / 100) / (1 + inflation_rate / 100)
        
        data.append([year, salary_income, investment_income, pension_income, total_income,
                     living_expense, housing_expense, total_expense, annual_balance, remaining_assets])
        
        if remaining_assets < 0:
            break
        
    df = pd.DataFrame(data, columns=["年份", "薪資收入", "投資收益", "退休年金", "總收入", "生活費用", "住房費用", "總支出", "年度結餘", "剩餘資產"])
    return df

# Streamlit 應用程式
st.set_page_config(page_title="AI 退休顧問", layout="wide")
st.header("📢 AI 智能退休顧問")

st.subheader("📌 基本資料")
current_age = st.number_input("您的目前年齡", min_value=30, max_value=80, value=40)
retirement_age = st.number_input("您計劃退休的年齡", min_value=current_age+1, max_value=90, value=60)
expected_lifespan = st.number_input("預期壽命（歲）", min_value=70, max_value=110, value=100)

st.subheader("📌 家庭與財務狀況")
monthly_expense = st.number_input("每月生活支出（元）", min_value=1000, max_value=500000, value=30000, format="%d")
annual_salary = st.number_input("目前家庭年薪（元）", min_value=500000, max_value=100000000, value=1000000, format="%d")
salary_growth = st.slider("預計薪資成長率（%）", min_value=0.0, max_value=10.0, value=2.0, step=0.1)
investable_assets = st.number_input("目前可投資之資金（元）", min_value=0, max_value=1000000000, value=1000000, format="%d")
investment_return = st.slider("預期投報率（%）", min_value=0.1, max_value=10.0, value=5.0, step=0.1)
inflation_rate = st.slider("通貨膨脹率（%）", min_value=0.1, max_value=10.0, value=2.0, step=0.1)
retirement_pension = st.number_input("退休年金（元/月）", min_value=0, max_value=500000, value=20000, format="%d")

st.subheader("📌 住房計畫")
rent_or_buy = st.radio("您的住房計畫", ["租房", "買房"])
if rent_or_buy == "租房":
    rent_amount = st.number_input("每月租金（元）", min_value=0, max_value=500000, value=20000, format="%d")
    buy_age, home_price, down_payment, loan_amount, loan_term, loan_rate = [0] * 6
else:
    buy_age = st.number_input("計劃買房年齡", min_value=current_age, max_value=80, value=current_age)
    home_price = st.number_input("預計買房價格（元）", min_value=0, value=15000000, format="%d")
    down_payment = st.number_input("頭期款（元）", min_value=0, value=int(home_price * 0.3), format="%d")
    loan_amount = st.number_input("貸款金額（元）", min_value=0, value=home_price - down_payment, format="%d")
    loan_term = st.number_input("貸款年限（年）", min_value=1, max_value=30, value=20)
    loan_rate = st.number_input("貸款利率（%）", min_value=0.1, max_value=10.0, value=2.0, step=0.1)

# 計算退休現金流
data_df = calculate_retirement_cashflow(current_age, retirement_age, expected_lifespan, monthly_expense, rent_or_buy,
                                       rent_amount, buy_age, home_price, down_payment, loan_amount, loan_term, loan_rate,
                                       annual_salary, salary_growth, investable_assets, investment_return,
                                       inflation_rate, retirement_pension)

st.dataframe(data_df)

st.download_button(label="📥 下載 Excel", data=data_df.to_csv(index=False).encode("utf-8"), file_name="retirement_plan.csv", mime="text/csv")

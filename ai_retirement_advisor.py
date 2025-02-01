import streamlit as st
import pandas as pd

# ----------------------------
# 定義安全重新載入頁面的函式
# ----------------------------
def safe_rerun():
    """
    嘗試使用 st.experimental_rerun 重新載入頁面，
    若發生 AttributeError 則不進行任何操作。
    """
    try:
        st.experimental_rerun()
    except AttributeError:
        pass

# =============================
# 1) 計算退休現金流函式
# =============================

def calc_housing_expense(age, rent_or_buy, rent_amount, rent_before_buy, buy_age,
                         down_payment, monthly_mortgage, loan_term):
    """
    計算住房費用：
      - 租房：直接以租金計算
      - 購房：
          * 購屋前：以租金計算
          * 購屋當年：需支付首付款及第一年的房貸
          * 貸款期間：以房貸月繳金額計算
          * 貸款期滿：不再計算住房費用
    """
    if rent_or_buy == "租房":
        return int(rent_amount * 12)
    else:
        diff = age - buy_age
        if diff < 0:
            return int(rent_before_buy * 12)
        elif diff == 0:
            return int(down_payment + monthly_mortgage * 12)
        elif 0 < diff < loan_term:
            return int(monthly_mortgage * 12)
        else:
            return 0

def calculate_retirement_cashflow(
    current_age, retirement_age, expected_lifespan, monthly_expense,
    rent_or_buy, rent_amount, rent_before_buy,
    buy_age, home_price, down_payment, loan_amount, loan_term, loan_rate,
    annual_salary, salary_growth, investable_assets,
    investment_return, inflation_rate, retirement_pension,
    lumpsum_list
):
    """
    計算退休現金流，並回傳包含各年度詳細資料的 DataFrame。
    
    參數:
      current_age: 當前年齡
      retirement_age: 退休年齡
      expected_lifespan: 預期壽命
      monthly_expense: 每月生活費用
      rent_or_buy: "租房" 或 "購房"
      rent_amount: 租金金額
      rent_before_buy: 購房前租金金額
      buy_age: 購房年齡
      home_price: 房屋總價（目前未使用，可作後續擴充）
      down_payment: 首付款
      loan_amount: 貸款金額
      loan_term: 貸款年期
      loan_rate: 貸款年利率（百分比）
      annual_salary: 年薪
      salary_growth: 年薪成長率（百分比）
      investable_assets: 初始可投資資產
      investment_return: 投資報酬率（百分比）
      inflation_rate: 通膨率（百分比）
      retirement_pension: 每月退休金
      lumpsum_list: 一次性支出清單，格式為 List[{"年齡": 整數, "金額": 數值}]
    """
    ages = list(range(current_age, expected_lifespan + 1))
    data = []
    remaining_assets = investable_assets

    # 計算每月房貸（若有貸款） - 等額本息公式
    monthly_mortgage = 0
    if loan_amount > 0 and loan_term > 0:
        lr_monthly = loan_rate / 100 / 12
        monthly_mortgage = loan_amount * lr_monthly / (1 - (1 + lr_monthly) ** (-loan_term * 12))

    # 預先建立一次性支出的映射：年齡 -> 總金額
    lumpsum_map = {}
    for entry in lumpsum_list:
        try:
            exp_age = int(entry["年齡"])
            exp_amt = float(entry["金額"])
        except (ValueError, TypeError):
            continue
        if exp_age < current_age or exp_amt <= 0:
            continue
        lumpsum_map[exp_age] = lumpsum_map.get(exp_age, 0) + exp_amt

    # 使用局部變數記錄年薪，避免直接修改傳入參數
    current_salary = annual_salary

    for i, age in enumerate(ages):
        # 薪資收入（退休前以薪資計算，退休後歸零）
        salary_income = int(current_salary) if age <= retirement_age else 0
        if age < retirement_age:
            current_salary *= (1 + salary_growth / 100)

        # 投資收益及退休金收入
        investment_income = int(remaining_assets * (investment_return / 100)) if remaining_assets > 0 else 0
        pension_income = int(retirement_pension * 12) if age > retirement_age else 0
        total_income = salary_income + investment_income + pension_income

        # 生活費用與住房費用（依據通膨調整）
        living_expense = int(monthly_expense * 12)
        housing_expense = calc_housing_expense(age, rent_or_buy, rent_amount, rent_before_buy,
                                                 buy_age, down_payment, monthly_mortgage, loan_term)
        base_expense = (living_expense + housing_expense) * ((1 + inflation_rate / 100) ** i)

        # 加入一次性支出
        lumpsum_expense = lumpsum_map.get(age, 0)
        total_expense = int(base_expense) + int(lumpsum_expense)
        annual_balance = total_income - total_expense

        # 調整剩餘資產：先加上年度結餘，再考慮投資回報與通膨影響
        remaining_assets = ((remaining_assets + annual_balance) * (1 + investment_return / 100)) / (1 + inflation_rate / 100)

        data.append([
            age, salary_income, investment_income, pension_income,
            total_income, living_expense, housing_expense, lumpsum_expense,
            total_expense, annual_balance, remaining_assets
        ])

    # 直接建立 DataFrame 並指定最終欄位名稱
    df = pd.DataFrame(data, columns=[
        "年齡", "薪資收入", "投資收益", "退休年金", "總收入",
        "生活費用", "住房費用", "一次性支出", "總支出",
        "年度結餘", "累積結餘"
    ])

    return df

# ===========================
# 2) Streamlit App
# ===========================
st.set_page_config(page_title="AI 退休顧問", layout="wide")
st.header("📢 AI 智能退休顧問")

# 使用 session_state 管理一次性支出資料
if "lumpsum_list" not in st.session_state:
    st.session_state["lumpsum_list"] = []

# -----------------------------
# 一次性支出管理（僅允許「新增」和「刪除」）
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
            safe_rerun()  # 重新載入頁面，確保更新資料
        else:
            st.warning("無效輸入：年齡須 ≥ 30 且金額 > 0。")

# 只提供「刪除」按鈕，避免出錯
for idx, entry in enumerate(st.session_state["lumpsum_list"]):
    if st.button(f"刪除：年齡 {entry['年齡']}、金額 {entry['金額']}", key=f"del_{idx}"):
        del st.session_state["lumpsum_list"][idx]  # 直接刪除該項
        st.success("刪除成功！")
        safe_rerun()  # 重新載入頁面以更新清單

# -----------------------------
# 計算退休現金流
# -----------------------------
df_result = calculate_retirement_cashflow(
    current_age=40, retirement_age=60, expected_lifespan=100, monthly_expense=30000,
    rent_or_buy="租房", rent_amount=20000, rent_before_buy=20000,
    buy_age=48, home_price=15000000, down_payment=4500000, loan_amount=10500000, loan_term=20, loan_rate=2.0,
    annual_salary=1000000, salary_growth=2.0, investable_assets=1000000,
    investment_return=5.0, inflation_rate=2.0, retirement_pension=20000,
    lumpsum_list=st.session_state["lumpsum_list"]
)

st.subheader("### 預估現金流")
st.dataframe(df_result.style.format("{:,.0f}"), use_container_width=True)

st.markdown("如需專業協助，歡迎造訪 [永傳家族辦公室](http://www.gracefo.com)")

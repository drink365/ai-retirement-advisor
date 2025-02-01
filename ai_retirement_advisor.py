import streamlit as st
import pandas as pd

# ----------------------------
# 定義負數金額著色函式
# ----------------------------
def color_negative_red(val):
    """
    若數值為負，則回傳紅色字的 CSS 樣式。
    """
    try:
        v = float(val)
    except:
        return ""
    return "color: red" if v < 0 else ""

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
def calc_housing_expense(age, rent_or_buy, monthly_rent, buy_age,
                         down_payment, monthly_mortgage, loan_term):
    """
    計算住房費用：
      - 租房：直接以「每月租金」計算（乘以 12）
      - 購房：
          * 購屋前（年齡低於購房年齡）：不計算租房費用
          * 購屋當年：需支付首付款及第一年的房貸
          * 貸款期間：以房貸月繳金額計算
          * 貸款期滿：不再計算住房費用
    """
    if rent_or_buy == "租房":
        return int(monthly_rent * 12)
    else:
        diff = age - buy_age
        if diff < 0:
            return 0
        elif diff == 0:
            return int(down_payment + monthly_mortgage * 12)
        elif 0 < diff < loan_term:
            return int(monthly_mortgage * 12)
        else:
            return 0

def calculate_retirement_cashflow(
    current_age, retirement_age, expected_lifespan, monthly_expense,
    rent_or_buy, monthly_rent,
    buy_age, home_price, down_payment, loan_amount, loan_term, loan_rate,
    annual_salary, salary_growth, investable_assets,
    investment_return, inflation_rate, retirement_pension,
    lumpsum_list
):
    """
    計算退休現金流，並回傳包含各年度詳細資料的 DataFrame。
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
        if exp_age < current_age or exp_amt == 0:
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
        housing_expense = calc_housing_expense(age, rent_or_buy, monthly_rent, buy_age,
                                                 down_payment, monthly_mortgage, loan_term)
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

# -----------------------------
# 新增退休參數輸入區
# -----------------------------
with st.form("retirement_parameters"):
    st.subheader("退休規劃參數")
    current_age = st.number_input("目前年齡", min_value=18, max_value=100, value=40)
    retirement_age = st.number_input("退休年齡", min_value=current_age, max_value=100, value=60)
    expected_lifespan = st.number_input("預期壽命", min_value=retirement_age, max_value=150, value=100)
    
    monthly_expense = st.number_input("每月生活費用", min_value=1000, value=30000, step=1000)
    
    # 住房選擇：若選擇租房，僅顯示租金欄位；若選擇購房，則僅顯示購房相關欄位
    rent_or_buy = st.selectbox("住房選擇", ["租房", "購房"])
    if rent_or_buy == "租房":
        monthly_rent = st.number_input("每月租金", min_value=1000, value=20000, step=1000)
        # 當為租房時，購房相關欄位以預設值帶入計算（不顯示）
        buy_age = current_age
        home_price = 0
        down_payment = 0
        loan_amount = 0
        loan_term = 0
        loan_rate = 0.0
    else:
        # 當選擇購房時，租房相關資料不顯示
        buy_age = st.number_input("購房年齡", min_value=current_age, max_value=expected_lifespan, value=48)
        home_price = st.number_input("房屋總價", min_value=0, value=15000000, step=100000)
        down_payment = st.number_input("首付款", min_value=0, value=4500000, step=100000)
        loan_amount = st.number_input("貸款金額", min_value=0, value=10500000, step=100000)
        loan_term = st.number_input("貸款年期", min_value=1, max_value=50, value=20)
        loan_rate = st.number_input("貸款利率 (%)", min_value=0.0, value=2.0, step=0.1)
        monthly_rent = 0  # 不使用
        
    annual_salary = st.number_input("年薪", min_value=0, value=1000000, step=10000)
    salary_growth = st.number_input("年薪成長率 (%)", min_value=0.0, value=2.0, step=0.1)
    investable_assets = st.number_input("初始可投資資產", min_value=0, value=1000000, step=10000)
    investment_return = st.number_input("投資報酬率 (%)", min_value=0.0, value=5.0, step=0.1)
    inflation_rate = st.number_input("通膨率 (%)", min_value=0.0, value=2.0, step=0.1)
    retirement_pension = st.number_input("退休月退休金", min_value=0, value=20000, step=1000)
    
    submit_params = st.form_submit_button("更新退休參數")

# -----------------------------
# 一次性支出管理（偶發性）
# -----------------------------
if "lumpsum_list" not in st.session_state:
    st.session_state["lumpsum_list"] = []

st.subheader("📌 一次性支出 (偶發性)")
with st.form("add_lumpsum"):
    new_age = st.number_input("新增一次性支出 - 年齡", min_value=30, max_value=110, value=40, key="new_age")
    new_amt = st.number_input("新增一次性支出 - 金額", value=100000, key="new_amt")
    submitted_lumpsum = st.form_submit_button("新增")
    if submitted_lumpsum:
        if new_age >= 30 and new_amt != 0:
            st.session_state["lumpsum_list"].append({"年齡": new_age, "金額": new_amt})
            st.success(f"新增成功：年齡 {new_age}，金額 {new_amt}")
            safe_rerun()
        else:
            st.warning("無效輸入：年齡須 ≥ 30 且金額 ≠ 0。")

# 刪除一次性支出項目
for idx, entry in enumerate(st.session_state["lumpsum_list"]):
    if st.button(f"刪除：年齡 {entry['年齡']}、金額 {entry['金額']}", key=f"del_{idx}"):
        del st.session_state["lumpsum_list"][idx]
        st.success("刪除成功！")
        safe_rerun()

# -----------------------------
# 當使用者點擊「更新退休參數」後進行計算
# -----------------------------
if submit_params:
    df_result = calculate_retirement_cashflow(
        current_age=current_age, retirement_age=retirement_age, expected_lifespan=expected_lifespan, monthly_expense=monthly_expense,
        rent_or_buy=rent_or_buy, monthly_rent=monthly_rent,
        buy_age=buy_age, home_price=home_price, down_payment=down_payment, loan_amount=loan_amount, loan_term=loan_term, loan_rate=loan_rate,
        annual_salary=annual_salary, salary_growth=salary_growth, investable_assets=investable_assets,
        investment_return=investment_return, inflation_rate=inflation_rate, retirement_pension=retirement_pension,
        lumpsum_list=st.session_state["lumpsum_list"]
    )
    styled_df = df_result.style.format("{:,.0f}").applymap(color_negative_red)
    st.subheader("### 預估現金流")
    st.dataframe(styled_df, use_container_width=True)

st.markdown("如需專業協助，歡迎造訪 [永傳家族辦公室](http://www.gracefo.com)")

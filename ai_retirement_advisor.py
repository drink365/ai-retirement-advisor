import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

# ----------------------------
# 定義負數金額著色函式
# ----------------------------
def color_negative_red(val):
    """
    若數值為負，則回傳紅色字的 CSS 樣式。
    """
    try:
        v = float(val)
    except Exception:
        return ""
    return "color: red" if v < 0 else ""

# ----------------------------
# 定義安全重新載入頁面的函式
# ----------------------------
def safe_rerun():
    try:
        st.experimental_rerun()
    except Exception:
        pass

# =============================
# 1) 計算退休現金流函式
# =============================
def calc_housing_expense(age, rent_or_buy, monthly_rent, buy_age,
                         down_payment, monthly_mortgage, loan_term):
    """
    計算住房費用：
      - 若選擇租房：以「每月租金」計算（乘以 12）
      - 若選擇購房：
          * 若年齡小於購房年齡：仍以每月租金計算（代表購房前租房）
          * 當年齡等於購房年齡：支付首付款及第一年的房貸
          * 當年齡落在購房年齡與貸款年期之間：以房貸月繳金額計算
          * 當超過購房年齡＋貸款年期：不再計算住房費用
    """
    if rent_or_buy == "租房":
        return int(monthly_rent * 12)
    else:
        if age < buy_age:
            return int(monthly_rent * 12)
        elif age == buy_age:
            return int(down_payment + monthly_mortgage * 12)
        elif buy_age < age < buy_age + loan_term:
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
    欄位順序依次為：
      年齡、薪資收入、投資收益、退休年金、總收入、
      生活費用、住房費用、一次性支出、總支出、
      年度結餘、累積結餘
    """
    ages = list(range(current_age, expected_lifespan + 1))
    data = []
    remaining_assets = investable_assets

    # 計算房貸月繳金額（若有貸款）
    monthly_mortgage = 0
    if loan_amount > 0 and loan_term > 0:
        lr_monthly = loan_rate / 100 / 12
        monthly_mortgage = loan_amount * lr_monthly / (1 - (1 + lr_monthly) ** (-loan_term * 12))

    # 建立一次性支出映射：年齡 -> 總金額
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

    current_salary = annual_salary

    for i, age in enumerate(ages):
        # 薪資收入：退休前以薪資計算，退休後歸零
        salary_income = int(current_salary) if age <= retirement_age else 0
        if age < retirement_age:
            current_salary *= (1 + salary_growth / 100)

        investment_income = int(remaining_assets * (investment_return / 100)) if remaining_assets > 0 else 0
        pension_income = int(retirement_pension * 12) if age > retirement_age else 0
        total_income = salary_income + investment_income + pension_income

        living_expense = int(monthly_expense * 12)
        housing_expense = calc_housing_expense(age, rent_or_buy, monthly_rent, buy_age,
                                                 down_payment, monthly_mortgage, loan_term)
        base_expense = (living_expense + housing_expense) * ((1 + inflation_rate / 100) ** i)

        lumpsum_expense = lumpsum_map.get(age, 0)
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
        "年度結餘", "累積結餘"
    ])
    return df

# ===========================
# 主程式：使用者介面
# ===========================
st.set_page_config(page_title="AI 退休顧問", layout="wide")
st.header("📢 AI 智能退休顧問")

# ─────────────────────────
# 一、基本資料輸入區（使用 st.columns 進行分欄排版）
# ─────────────────────────
st.subheader("基本資料")
col1, col2 = st.columns(2)
with col1:
    current_age = st.number_input("目前年齡", min_value=18, max_value=100, value=40)
    retirement_age = st.number_input("退休年齡", min_value=current_age, max_value=100, value=60)
    expected_lifespan = st.number_input("預期壽命", min_value=retirement_age, max_value=150, value=100)
with col2:
    monthly_expense = st.number_input("每月生活費用", min_value=1000, value=30000, step=1000)
    annual_salary = st.number_input("目前年薪", min_value=0, value=1000000, step=10000)
    salary_growth = st.number_input("年薪成長率 (%)", min_value=0.0, value=2.0, step=0.1)
st.markdown("---")
col3, col4 = st.columns(2)
with col3:
    investable_assets = st.number_input("初始可投資資產", min_value=0, value=1000000, step=10000)
with col4:
    investment_return = st.number_input("投資報酬率 (%)", min_value=0.0, value=5.0, step=0.1)
retirement_pension = st.number_input("預估每月退休金", min_value=0, value=20000, step=1000)
inflation_rate = st.number_input("通膨率 (%)", min_value=0.0, value=2.0, step=0.1)

# ─────────────────────────
# 二、住房狀況輸入區
# ─────────────────────────
st.subheader("住房狀況")
monthly_rent = st.number_input("每月租金", min_value=1000, value=20000, step=1000)
housing_choice = st.selectbox("住房選擇", ["租房", "購房"])
if housing_choice == "租房":
    buy_age = current_age  
    home_price = 0
    down_payment = 0
    loan_amount = 0
    loan_term = 0
    loan_rate = 0.0
else:
    buy_age = st.number_input("購房年齡", min_value=18, max_value=expected_lifespan, value=40)
    home_price = st.number_input("房屋總價", min_value=0, value=15000000, step=100000)
    down_payment = st.number_input("首付款", min_value=0, value=4500000, step=100000)
    loan_amount = st.number_input("貸款金額", min_value=0, value=10500000, step=100000)
    loan_term = st.number_input("貸款年期", min_value=1, max_value=50, value=30)
    loan_rate = st.number_input("貸款利率 (%)", min_value=0.0, value=3.0, step=0.1)

# ─────────────────────────
# 三、一次性支出管理
# ─────────────────────────
st.subheader("一次性支出 (偶發性)")
if "lumpsum_list" not in st.session_state:
    st.session_state["lumpsum_list"] = []

with st.container():
    col_ls1, col_ls2, col_ls3 = st.columns([1, 1, 2])
    with col_ls1:
        new_age = st.number_input("新增支出 - 年齡", min_value=30, max_value=110, value=40, key="new_age")
    with col_ls2:
        new_amt = st.number_input("新增支出 - 金額", value=100000, key="new_amt")
    with col_ls3:
        submitted_lumpsum = st.button("新增一次性支出")
    if submitted_lumpsum:
        if new_age >= 30 and new_amt != 0:
            st.session_state["lumpsum_list"].append({"年齡": new_age, "金額": new_amt})
            st.success(f"新增成功：年齡 {new_age}，金額 {new_amt}")
            safe_rerun()
        else:
            st.warning("無效輸入：年齡須 ≥ 30 且金額 ≠ 0。")

if st.session_state["lumpsum_list"]:
    st.markdown("**目前一次性支出項目：**")
    for idx, entry in enumerate(st.session_state["lumpsum_list"]):
        if st.button(f"刪除：年齡 {entry['年齡']}、金額 {entry['金額']}", key=f"del_{idx}"):
            del st.session_state["lumpsum_list"][idx]
            st.success("刪除成功！")
            safe_rerun()

# ─────────────────────────
# 四、計算並顯示預估退休現金流
# ─────────────────────────
st.subheader("預估退休現金流")
with st.spinner("計算中..."):
    df_result = calculate_retirement_cashflow(
        current_age=current_age,
        retirement_age=retirement_age,
        expected_lifespan=expected_lifespan,
        monthly_expense=monthly_expense,
        rent_or_buy=housing_choice,
        monthly_rent=monthly_rent,
        buy_age=buy_age,
        home_price=home_price,
        down_payment=down_payment,
        loan_amount=loan_amount,
        loan_term=loan_term,
        loan_rate=loan_rate,
        annual_salary=annual_salary,
        salary_growth=salary_growth,
        investable_assets=investable_assets,
        investment_return=investment_return,
        inflation_rate=inflation_rate,
        retirement_pension=retirement_pension,
        lumpsum_list=st.session_state["lumpsum_list"]
    )
    
    # 將結果欄位依群組重新整理：基本資料、收入、支出、結餘
    new_columns = []
    for col in df_result.columns:
        if col == "年齡":
            new_columns.append(("基本資料", "年齡"))
        elif col in ["薪資收入", "投資收益", "退休年金", "總收入"]:
            new_columns.append(("收入", col))
        elif col in ["生活費用", "住房費用", "一次性支出", "總支出"]:
            new_columns.append(("支出", col))
        elif col in ["年度結餘", "累積結餘"]:
            new_columns.append(("結餘", col))
    df_result.columns = pd.MultiIndex.from_tuples(new_columns)
    
    styled_df = df_result.style.format("{:,.0f}").applymap(color_negative_red)
    st.dataframe(styled_df, use_container_width=True)

# ─────────────────────────
# 五、智能建議報告與行動提示
# ─────────────────────────
st.subheader("智能建議報告與行動提示")
target_asset = st.number_input("請輸入您的退休目標資產（元）", min_value=0, value=20000000, step=1000000)

# 從多層索引中提取基本資料與結餘群組
df_basic = df_result["基本資料"]
df_balance = df_result["結餘"]

# 找出退休年齡那一行的數據
retire_idx = df_basic[df_basic["年齡"] == retirement_age].index
if len(retire_idx) > 0:
    proj_asset = df_balance.loc[retire_idx[0], "累積結餘"]
    gap = target_asset - proj_asset
    st.markdown(f"在您設定的退休年齡 **{retirement_age}** 歲時，預計累積資產約 **{proj_asset:,.0f}** 元。")
    st.markdown(f"與您的目標資產 **{target_asset:,.0f}** 元相比，尚有 **{gap:,.0f}** 元的缺口。")
    
    if gap > 0:
        st.markdown("**建議：**")
        st.markdown("• 您目前的儲蓄與投資計劃可能不足以達成您的退休目標。")
        st.markdown("• 建議您考慮延後退休、增加每月儲蓄、或調整投資組合以期望獲得更高的投資報酬率。")
        st.markdown("• 如需專業建議，您可以預約免費的財務規劃諮詢，我們的專家會根據您的情況提供專屬策略。")
        if st.button("立即預約免費諮詢"):
            # 這裡可連結到預約頁面或其他服務
            st.success("感謝您的預約申請，我們將盡快與您聯繫！")
    else:
        st.markdown("恭喜您！根據目前數據，您的退休規劃已達標。請持續關注投資與支出動態，保持良好財務習慣。")
else:
    st.markdown("無法取得您在退休年齡的累積資產數據，請檢查您的輸入資料。")

# ─────────────────────────
# 六、行銷資訊
# ─────────────────────────
st.markdown("如需專業協助，歡迎造訪 [永傳家族辦公室](http://www.gracefo.com)")

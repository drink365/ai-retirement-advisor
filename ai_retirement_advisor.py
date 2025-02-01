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

# ----------------------------
# 當用戶調整「房屋總價」時自動更新「首付款」與「貸款金額」
# ----------------------------
def update_payments():
    st.session_state.down_payment = int(st.session_state.home_price * 0.3)
    st.session_state.loan_amount = st.session_state.home_price - st.session_state.down_payment

# ----------------------------
# 計算住房費用
# ----------------------------
def calc_housing_expense(age, rent_or_buy, monthly_rent, buy_age,
                         down_payment, monthly_mortgage, loan_term):
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

# ----------------------------
# 計算退休現金流
# ----------------------------
def calculate_retirement_cashflow(
    current_age, retirement_age, expected_lifespan, monthly_expense,
    rent_or_buy, monthly_rent,
    buy_age, home_price, down_payment, loan_amount, loan_term, loan_rate,
    annual_salary, salary_growth, investable_assets,
    investment_return, inflation_rate, retirement_pension,
    lumpsum_list
):
    ages = list(range(current_age, expected_lifespan + 1))
    data = []
    remaining_assets = investable_assets

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
st.set_page_config(page_title="AI退休助手 Nana", layout="wide")
st.header("👋 嗨！我是 Nana， 你的 AI 退休助手！")
st.markdown("我可以幫你計算 **退休金需求、投資報酬預測、通膨影響、房產決策**，還可以評估你的 **財務健康指數**，讓你快速掌握退休規劃進度！ 😊")

# ─────────────────────────
# 一、基本資料輸入區
# ─────────────────────────
st.subheader("📝 基本資料")
st.info("請輸入你的基本資料，我會根據你的情況提供貼心又專業的退休規劃建議。")
col1, col2 = st.columns(2)
with col1:
    current_age = st.number_input("你的年齡", min_value=18, max_value=100, value=40)
    retirement_age = st.number_input("計劃退休年齡", min_value=current_age, max_value=100, value=60)
    expected_lifespan = st.number_input("預期壽命", min_value=retirement_age, max_value=150, value=100)
with col2:
    monthly_expense = st.number_input("每月生活費用 (元)", min_value=1000, value=30000, step=1000)
    annual_salary = st.number_input("目前年薪 (元)", min_value=0, value=1000000, step=10000)
    salary_growth = st.number_input("年薪成長率 (%)", min_value=0.0, value=2.0, step=0.1)
st.markdown("---")
col3, col4 = st.columns(2)
with col3:
    investable_assets = st.number_input("初始可投資資產 (元)", min_value=0, value=1000000, step=10000)
with col4:
    investment_return = st.number_input("投資報酬率 (%)", min_value=0.0, value=5.0, step=0.1)
retirement_pension = st.number_input("預估每月退休金 (元)", min_value=0, value=20000, step=1000)
inflation_rate = st.number_input("通膨率 (%)", min_value=0.0, value=2.0, step=0.1)

# ─────────────────────────
# 二、住房狀況輸入區
# ─────────────────────────
st.subheader("🏠 住房狀況")
st.info("請告訴我你的住房狀況，這能幫助我們更全面地規劃你的退休藍圖。")
housing_choice = st.selectbox("選擇租房或購房", ["租房", "購房"])
monthly_rent = st.number_input("每月租金 (元)", min_value=1000, value=25000, step=1000)
if housing_choice == "租房":
    buy_age = current_age  
    home_price = 0
    down_payment = 0
    loan_amount = 0
    loan_term = 0
    loan_rate = 0.0
else:
    buy_age = st.number_input("計劃購房年齡", min_value=18, max_value=expected_lifespan, value=40)
    home_price = st.number_input("房屋總價 (元)", key="home_price", value=15000000, step=100000, on_change=update_payments)
    down_payment = st.number_input("首付款 (元)", key="down_payment", value=st.session_state.get("down_payment", int(15000000 * 0.3)), step=100000)
    loan_amount = st.number_input("貸款金額 (元)", key="loan_amount", value=st.session_state.get("loan_amount", 15000000 - int(15000000 * 0.3)), step=100000)
    loan_term = st.number_input("貸款年期 (年)", min_value=1, max_value=50, value=30)
    loan_rate = st.number_input("貸款利率 (%)", min_value=0.0, value=3.0, step=0.1)

# ─────────────────────────
# 三、一次性支出管理
# ─────────────────────────
st.subheader("💸 一次性支出 (偶發性)")
st.info("如果你有特殊或一次性的支出計劃，請在這裡告訴我，我們會一併納入規劃中。")
if "lumpsum_list" not in st.session_state:
    st.session_state["lumpsum_list"] = []

with st.container():
    col_ls1, col_ls2, col_ls3 = st.columns([1, 1, 2])
    with col_ls1:
        new_age = st.number_input("新增支出 - 預計年齡", min_value=30, max_value=110, value=40, key="new_age")
    with col_ls2:
        new_amt = st.number_input("新增支出 - 金額 (元)", value=100000, key="new_amt")
    with col_ls3:
        submitted_lumpsum = st.button("新增支出")
    if submitted_lumpsum:
        if new_age >= 30 and new_amt != 0:
            st.session_state["lumpsum_list"].append({"年齡": new_age, "金額": new_amt})
            st.success(f"已成功新增支出：年齡 {new_age}，金額 {new_amt} 元。")
            safe_rerun()
        else:
            st.warning("請確認輸入，年齡需 ≥ 30 且金額不可為 0。")

if st.session_state["lumpsum_list"]:
    st.markdown("**已新增的一次性支出：**")
    for idx, entry in enumerate(st.session_state["lumpsum_list"]):
        if st.button(f"刪除：年齡 {entry['年齡']}、金額 {entry['金額']}", key=f"del_{idx}"):
            del st.session_state["lumpsum_list"][idx]
            st.success("支出項目已移除。")
            safe_rerun()

# ─────────────────────────
# 四、計算並顯示預估退休現金流
# ─────────────────────────
st.subheader("📈 預估退休現金流")
with st.spinner("Nana 正在快速計算，請稍候..."):
    df_result = calculate_retirement_cashflow(
        current_age=current_age,
        retirement_age=retirement_age,
        expected_lifespan=expected_lifespan,
        monthly_expense=monthly_expense,
        rent_or_buy=housing_choice,
        monthly_rent=monthly_rent,
        buy_age=buy_age,
        home_price=home_price if housing_choice == "購房" else 0,
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
    
    # 根據不同類別重新整理結果欄位
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
st.success("計算完成，以上是你的退休現金流預估結果。")

# ─────────────────────────
# 五、退休風格測驗與建議報告
# ─────────────────────────
st.subheader("🎯 退休風格測驗與建議報告")
st.info("告訴我你理想中的退休生活風格，我會根據你的選擇提供專業又貼心的建議。")
retire_style = st.radio("你的理想退休生活？", ["低調簡約", "舒適中產", "高端奢華"], key="retire_style")
if retire_style == "低調簡約":
    recommended_target = 10000000
elif retire_style == "舒適中產":
    recommended_target = 20000000
else:
    recommended_target = 50000000
st.markdown(f"根據你的選擇，建議的退休目標資產約為 **{recommended_target:,.0f}** 元。")
target_asset = st.number_input("請輸入你的退休目標資產（元）", min_value=0, value=recommended_target, step=1000000)

df_basic = df_result["基本資料"]
df_balance = df_result["結餘"]
retire_idx = df_basic[df_basic["年齡"] == retirement_age].index
if len(retire_idx) > 0:
    proj_asset = df_balance.loc[retire_idx[0], "累積結餘"]
    gap = target_asset - proj_asset
    st.markdown(f"在你設定的退休年齡 **{retirement_age}** 歲時，預計累積資產約為 **{proj_asset:,.0f}** 元。")
    st.markdown(f"與你的目標 **{target_asset:,.0f}** 元相比，尚有 **{gap:,.0f}** 元的差距。")
    
    health_score = int((proj_asset / target_asset) * 100) if target_asset > 0 else 0
    st.metric(label="💪 財務健康指數", value=f"{health_score} 分", delta=health_score - 80)
    
    st.info("""
    💡 Nana 提醒你：
    📌 80 分以上：你的財務規劃相當穩健！ 🎉
    📌 60-79 分：建議適度調整投資或儲蓄！ 💡
    📌 低於 60 分：請儘早檢視退休計畫，可能有資金不足風險！ ⚠️
    """)
    
    if gap > 0:
        st.markdown("**建議：**")
        st.markdown("• 你目前的儲蓄與投資計劃可能還需要調整，建議考慮延後退休、增加儲蓄或優化投資組合。")
        st.markdown("• 若需要更進一步的專業建議，歡迎預約免費的財務規劃諮詢。")
        st.markdown('<a href="https://www.gracefo.com" target="_blank"><button style="padding:10px 20px;background-color:#4CAF50;color:white;border:none;border-radius:5px;">立即預約</button></a>', unsafe_allow_html=True)
    else:
        st.markdown("看起來你的退休規劃已十分完善，持續關注你的財務狀況會讓未來更有保障。")
else:
    st.markdown("抱歉，無法取得你在退休年齡的累積資產數據，請檢查輸入資料是否正確。")

# ─────────────────────────
# 六、圖表呈現：累積結餘趨勢圖
# ─────────────────────────
st.subheader("📊 累積結餘趨勢圖")
df_chart = pd.DataFrame({
    "年齡": df_result["基本資料"]["年齡"],
    "累積結餘": df_result["結餘"]["累積結餘"]
})
line_chart = alt.Chart(df_chart).mark_line(point=True).encode(
    x=alt.X("年齡:Q", title="年齡"),
    y=alt.Y("累積結餘:Q", title="累積結餘"),
    tooltip=["年齡", "累積結餘"]
).properties(
    title="累積結餘隨年齡變化"
)
st.altair_chart(line_chart, use_container_width=True)

# ─────────────────────────
# 七、敏感性分析：通膨率對累積結餘的影響
# ─────────────────────────
st.subheader("🔍 通膨敏感性分析")
st.info("下列圖表顯示不同通膨情境下的累積結餘走勢，讓你了解科技如何幫你做出快速判斷。")
inf_min = st.number_input("最低通膨率 (%)", value=inflation_rate - 1, step=0.1, key="inf_min")
inf_max = st.number_input("最高通膨率 (%)", value=inflation_rate + 1, step=0.1, key="inf_max")
inflation_scenarios = np.linspace(inf_min, inf_max, 5)
inf_sensitivity_list = []
for ir in inflation_scenarios:
    df_inf = calculate_retirement_cashflow(
        current_age=current_age,
        retirement_age=retirement_age,
        expected_lifespan=expected_lifespan,
        monthly_expense=monthly_expense,
        rent_or_buy=housing_choice,
        monthly_rent=monthly_rent,
        buy_age=buy_age,
        home_price=home_price if housing_choice == "購房" else 0,
        down_payment=down_payment,
        loan_amount=loan_amount,
        loan_term=loan_term,
        loan_rate=loan_rate,
        annual_salary=annual_salary,
        salary_growth=salary_growth,
        investable_assets=investable_assets,
        investment_return=investment_return,
        inflation_rate=ir,
        retirement_pension=retirement_pension,
        lumpsum_list=st.session_state["lumpsum_list"]
    )
    df_temp = pd.DataFrame({
        "年齡": df_inf["年齡"],
        "累積結餘": df_inf["累積結餘"]
    })
    df_temp["通膨率 (%)"] = np.round(ir, 1)
    inf_sensitivity_list.append(df_temp)
inf_sensitivity_df = pd.concat(inf_sensitivity_list, ignore_index=True)
inf_chart = alt.Chart(inf_sensitivity_df).mark_line().encode(
    x=alt.X("年齡:Q", title="年齡"),
    y=alt.Y("累積結餘:Q", title="累積結餘"),
    color=alt.Color("通膨率 (%)", title="通膨率 (%)"),
    tooltip=["年齡", "累積結餘", "通膨率 (%)"]
).properties(
    title="不同通膨率下的累積結餘走勢"
)
st.altair_chart(inf_chart, use_container_width=True)

# ─────────────────────────
# 八、行銷資訊
# ─────────────────────────
st.markdown("如果你有更多問題或需要協助，歡迎造訪 [永傳家族辦公室](https://www.gracefo.com) 或直接聯繫我們。Nana 會一直在這裡陪你，一起邁向美好的未來！")

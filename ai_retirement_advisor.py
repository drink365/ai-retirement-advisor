import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

# 設定頁面配置
st.set_page_config(page_title="AI 退休助手 Nana", layout="wide")

# ----------------------------
# Nana 介紹
# ----------------------------
st.header("📢 AI 退休助手 Nana")
st.subheader("讓退休規劃變得簡單又安心！")

st.markdown("""
👋 **嗨！我是 Nana**，你的 AI 退休助手！  
我可以幫助你計算 **退休金需求、投資報酬預測、通膨影響、房產決策**，  
還可以評估你的 **財務健康指數**，讓你快速掌握退休規劃進度！  
""")

st.markdown("📌 **立即體驗 Nana 👉 [https://ai-retirement.streamlit.app/](https://ai-retirement.streamlit.app/)**")

# ----------------------------
# 住房狀況輸入區（優化 Nana 互動）
# ----------------------------
with st.expander("🏡 住房狀況", expanded=True):
    st.markdown("💡 **Nana 小提醒：不同的住房選擇會影響你的退休財務！**")

    housing_choice = st.selectbox("🏠 你計畫未來的居住方式？", ["租房", "購房"], index=0)
    monthly_rent = st.number_input("每月租金", min_value=1000, value=25000, step=1000)

    if housing_choice == "購房":
        buy_age = st.number_input("購房年齡", min_value=18, max_value=100, value=40)
        home_price = st.number_input("🏡 房屋總價", key="home_price", value=15000000, step=100000)
        down_payment = st.number_input("🔹 首付款 (30%)", key="down_payment", value=int(15000000 * 0.3), step=100000)
        loan_amount = st.number_input("💳 貸款金額", key="loan_amount", value=15000000 - int(15000000 * 0.3), step=100000)
        loan_term = st.number_input("📆 貸款年期 (年)", min_value=1, max_value=50, value=30)
        loan_rate = st.number_input("📈 貸款利率 (%)", min_value=0.0, value=3.0, step=0.1)

# ----------------------------
# 退休風格測驗與財務健康指數
# ----------------------------
with st.expander("🎯 退休風格測驗與 Nana 的財務健康指數", expanded=True):
    st.markdown("💬 **Nana：告訴我你的退休夢想，我來幫你評估財務狀況！**")

    retire_style = st.radio("你理想的退休生活風格是？", ["低調簡約", "舒適中產", "高端奢華"], key="retire_style")
    recommended_target = {"低調簡約": 10000000, "舒適中產": 20000000, "高端奢華": 50000000}[retire_style]

    st.markdown(f"✅ **根據你的選擇，Nana 建議你的退休目標資產為：** 💰 **{recommended_target:,.0f} 元**")
    target_asset = st.number_input("💡 你希望的退休目標資產（元）", min_value=0, value=recommended_target, step=1000000)

    st.markdown("📊 **Nana 給你的財務健康指數評估**")
    health_score = int((10000000 / target_asset) * 100) if target_asset > 0 else 0  # 假設值
    st.metric(label="📈 財務健康指數", value=f"{health_score} 分", delta=health_score - 80)

    st.info("""
    **💡 Nana 提醒你：**  
    **📌 80 分以上：你的財務規劃相當穩健！** 🎉  
    **📌 60-79 分：建議適度調整投資或儲蓄！** 💡  
    **📌 低於 60 分：請儘早檢視退休計畫，可能有資金不足風險！** ⚠️  
    """)

# ----------------------------
# 預估退休現金流與圖表
# ----------------------------
with st.expander("📊 預估退休現金流與趨勢", expanded=True):
    st.markdown("💡 **Nana 幫你模擬退休財務趨勢，看看你的資產變化！**")

    df_chart = pd.DataFrame({
        "年齡": list(range(40, 100)),  # 假設年齡範圍
        "累積結餘": np.linspace(10000000, 5000000, 60)  # 假設數據
    })
    line_chart = alt.Chart(df_chart).mark_line(point=True).encode(
        x=alt.X("年齡:Q", title="年齡"),
        y=alt.Y("累積結餘:Q", title="累積結餘"),
        tooltip=["年齡", "累積結餘"]
    ).properties(
        title="📈 累積結餘隨年齡變化"
    )
    st.altair_chart(line_chart, use_container_width=True)

# ----------------------------
# 行銷資訊
# ----------------------------
st.markdown("🚀 **現在就來體驗 AI 退休助手 Nana！**")
st.markdown("📍 **[立即免費試用](https://ai-retirement.streamlit.app/)**")


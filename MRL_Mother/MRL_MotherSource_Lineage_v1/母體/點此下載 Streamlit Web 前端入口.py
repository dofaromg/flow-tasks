import streamlit as st

st.set_page_config(layout="wide", page_title="FlowAgent 協作系統")

st.title("🌐 FlowAgent 總體協作系統 v1")
st.subheader("🧠 任務人格推薦 × Ping 圖譜 × 節奏視覺模擬器")

st.markdown("### 📋 任務描述")
task = st.text_area("請輸入任務指令，例如『設計一個行銷企劃案』：")

if task:
    st.success(f"✅ 任務已接收：{task}")
    st.info("🔍 分析中：推薦最佳人格模組...")
    # 模擬人格推薦（示意）
    st.markdown("### 🤖 推薦人格：")
    st.write("- TeamSynergy.MasterPersona")
    st.write("- RoleMatch.Recommender.Core")

st.markdown("---")
st.markdown("### 🕸️ 模組 Ping 節奏圖（開發中）")
st.image("https://upload.wikimedia.org/wikipedia/commons/6/66/Graph_structure.svg", caption="模擬人格互動網路")

st.markdown("---")
st.markdown("💡 此介面為初版視覺模擬器，將整合任務流、Ping 張力圖與人格推薦")

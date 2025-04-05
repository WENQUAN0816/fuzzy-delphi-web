# app.py
import streamlit as st
import pandas as pd
import math

FUZZY_MAPPING = [(0, 0, 0.2), (0, 0.2, 0.4), (0.2, 0.4, 0.6), (0.4, 0.6, 0.8), (0.6, 0.8, 1.0)]

def score_to_fuzzy(s):
    return FUZZY_MAPPING[s - 1]

def avg_triple(tuples):
    n = len(tuples)
    return tuple(sum(x[i] for x in tuples) / n for i in range(3))

def fuzzy_distance(t, a):
    return math.sqrt(sum((t[i] - a[i]) ** 2 for i in range(3)) / 3)

def defuzzify(t):
    return sum(t) / 3

st.title("🧠 模糊 Delphi 分析工具 (网页版)")
st.markdown("为每个指标由多位专家进行评分（1~5），计算一致性、去模糊值、是否接受等。")

num_experts = st.number_input("专家人数", min_value=1, max_value=20, value=5)
num_indicators = st.number_input("指标数量", min_value=1, max_value=50, value=10)

data = []
st.write("## 输入专家评分（1~5）")

for i in range(num_indicators):
    row = []
    indicator_name = st.text_input(f"指标 {i+1} 名称", key=f"name_{i}")
    row.append(indicator_name)
    for j in range(num_experts):
        score = st.number_input(f"专家 {j+1} 对『{indicator_name}』的评分", min_value=1, max_value=5, step=1, key=f"s_{i}_{j}")
        row.append(score)
    data.append(row)

if st.button("✅ 计算"):
    indicators = []
    for row in data:
        name = row[0]
        scores = row[1:]

        triples = [score_to_fuzzy(s) for s in scores]
        avg_t = avg_triple(triples)
        d_vals = [fuzzy_distance(t, avg_t) for t in triples]
        avg_d = sum(d_vals) / len(d_vals)
        defuzz = defuzzify(avg_t)
        consensus = sum(1 for d in d_vals if d <= 0.2) / len(d_vals) * 100

        reasons = []
        if avg_d > 0.2: reasons.append("d > 0.2")
        if consensus < 75: reasons.append("共识率 < 75%")
        if defuzz < 0.5: reasons.append("去模糊值 < 0.5")

        result = "接受" if not reasons else "拒绝"

        indicators.append({
            "指标": name,
            "d值": round(avg_d, 4),
            "共识率%": round(consensus, 1),
            "m1": round(avg_t[0], 4),
            "m2": round(avg_t[1], 4),
            "m3": round(avg_t[2], 4),
            "去模糊值": round(defuzz, 4),
            "结果": result,
            "拒绝原因": ", ".join(reasons)
        })

    df_result = pd.DataFrame(indicators)
    st.write("### 📊 计算结果")
    st.dataframe(df_result)

    @st.cache_data
    def to_excel(df):
        from io import BytesIO
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        return output.getvalue()

    excel_data = to_excel(df_result)
    st.download_button("📥 下载Excel文件", data=excel_data, file_name="fuzzy_delphi_result.xlsx")

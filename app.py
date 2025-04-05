import streamlit as st, pandas as pd, math
from io import BytesIO

fmap = [(0,0,0.2), (0,0.2,0.4), (0.2,0.4,0.6), (0.4,0.6,0.8), (0.6,0.8,1.0)]

def s2f(s): return fmap[s-1]
def avg(t): return tuple(sum(x[i] for x in t)/len(t) for i in range(3))
def dist(a,b): return math.sqrt(sum((a[i]-b[i])**2 for i in range(3))/3)
def defuzz(t): return sum(t)/3

def suggest(scores):
    from copy import deepcopy
    for i, old in enumerate(scores):
        for new in range(old+1, 6):
            temp = deepcopy(scores); temp[i] = new
            t = [s2f(s) for s in temp]; a = avg(t)
            d = [dist(x,a) for x in t]
            if sum(1 for x in d if x<=0.2)/len(d)*100 >= 75 and defuzz(a) >= 0.5 and sum(d)/len(d) <= 0.2:
                return f"调整专家{ i+1 }的{old}→{new}"
    return "需多专家调整"

def analyze(data):
    out = []
    for row in data:
        name, scores = row[0], list(map(int,row[1:]))
        t = [s2f(s) for s in scores]; a = avg(t)
        dlist = [dist(x,a) for x in t]; d = sum(dlist)/len(dlist)
        c = sum(1 for x in dlist if x<=0.2)/len(dlist)*100
        reasons = []
        if d > 0.2: reasons.append("d > 0.2")
        if c < 75: reasons.append("共识率 < 75%")
        if defuzz(a) < 0.5: reasons.append("去模糊值 < 0.5")
        res = "接受" if not reasons else "拒绝"
        sug = suggest(scores) if res == "拒绝" else ""
        out.append({
            "指标": name, "d值": round(d,4), "共识率%": round(c,1),
            "m1": round(a[0],4), "m2": round(a[1],4), "m3": round(a[2],4),
            "去模糊值": round(defuzz(a),4), "结果": res,
            "平均李克特分": round(sum(scores)/len(scores),2),
            "专家一致率": round(1-d,4),
            "拒绝原因": ", ".join(reasons),
            "调整建议": sug
        })
    return pd.DataFrame(out)

st.set_page_config("模糊 Delphi 分析工具", "🧠")
st.title("🧠 模糊 Delphi 分析工具 (网页版)")
txt = st.text_area("📋 粘贴评分数据（第一列为指标名，其余为专家1-5评分，用空格或TAB分隔）")
if st.button("✅ 计算"):
    try:
        rows = [line.strip().split() for line in txt.strip().splitlines() if line.strip()]
        data = [row for row in rows if len(row) >= 2 and all(s.isdigit() and 1<=int(s)<=5 for s in row[1:])]
        df = analyze(data)
        st.dataframe(df)

        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        st.download_button("📥 下载Excel", data=buffer.getvalue(), file_name="fuzzy_delphi.xlsx")
    except Exception as e:
        st.error("❌ 格式错误，请确认数据正确。")

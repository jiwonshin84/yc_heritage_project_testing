import os
import streamlit as st
import pandas as pd
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.cluster import KMeans

st.set_page_config(page_title="문화재 군집분석", layout="wide")

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

DATA_PATH = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "yc_heritage_feature.csv"
)

df = pd.read_csv(DATA_PATH, encoding="utf-8-sig")

features = [
    "문화재연령",
    "국가유산종목",
    "시대그룹",
    "재질",
    "노출형태"
]

data = df[features].copy()

for col in ["국가유산종목", "시대그룹", "재질", "노출형태"]:
    le = LabelEncoder()
    data[col] = le.fit_transform(data[col].astype(str))

scaler = StandardScaler()
X = scaler.fit_transform(data)

kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)

df["Cluster"] = kmeans.fit_predict(X)

cluster_name = {
    0: "A그룹",
    1: "B그룹",
    2: "C그룹"
}

df["군집"] = df["Cluster"].map(cluster_name)

st.title("🏛 문화재 군집분석")

st.write("""
문화재를 연령, 시대, 재질, 노출 형태를 기준으로 분석하여
비슷한 특징을 가진 문화재끼리 자동으로 그룹화한 결과입니다.
""")

st.subheader("📊 군집별 문화재 개수")

cluster_count = df["군집"].value_counts()

st.bar_chart(cluster_count)

st.subheader("📈 군집별 평균 문화재 연령")

cluster_age = df.groupby("군집")["문화재연령"].mean()

st.bar_chart(cluster_age)

st.subheader("📋 문화재 분류 결과")

st.dataframe(
    df[
        [
            "문화재명(국문)",
            "문화재연령",
            "국가유산종목",
            "시대그룹",
            "재질",
            "노출형태",
            "군집"
        ]
    ],
    use_container_width=True
)

st.subheader("📌 군집별 특징")

for group in sorted(df["군집"].unique()):

    temp = df[df["군집"] == group]

    st.markdown(f"### {group}")

    st.write(f"• 문화재 수 : {len(temp)}개")

    st.write(f"• 평균 문화재 연령 : {round(temp['문화재연령'].mean(),1)}년")

    st.write(f"• 가장 많은 재질 : {temp['재질'].mode()[0]}")

    st.write(f"• 가장 많은 노출 형태 : {temp['노출형태'].mode()[0]}")

st.subheader("📄 군집별 문화재 목록")

group = st.selectbox(
    "군집 선택",
    sorted(df["군집"].unique())
)

st.dataframe(
    df[df["군집"] == group][
        [
            "문화재명(국문)",
            "문화재연령",
            "재질",
            "노출형태"
        ]
    ],
    use_container_width=True
)

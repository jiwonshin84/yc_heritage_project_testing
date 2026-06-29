import os
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

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

pca = PCA(n_components=2)
X_pca = pca.fit_transform(X)

st.title("문화재 군집분석")

st.subheader("군집분석 결과")

st.dataframe(
    df[
        [
            "문화재명(국문)",
            "문화재연령",
            "국가유산종목",
            "시대그룹",
            "재질",
            "노출형태",
            "Cluster"
        ]
    ]
)

st.subheader("군집별 문화재 개수")

cluster_count = df["Cluster"].value_counts().sort_index()

st.bar_chart(cluster_count)

fig, ax = plt.subplots(figsize=(8, 6))

scatter = ax.scatter(
    X_pca[:, 0],
    X_pca[:, 1],
    c=df["Cluster"],
    cmap="viridis",
    s=80
)

ax.set_title("K-Means Clustering")
ax.set_xlabel("PCA1")
ax.set_ylabel("PCA2")

plt.colorbar(scatter)

st.pyplot(fig)

import pandas as pd
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt

df = pd.read_csv("yc_heritage_feature.csv", encoding="utf-8-sig")

features = [
    "문화재연령",
    "국가유산종목",
    "시대그룹",
    "재질",
    "노출형태"
]

data = df[features].copy()

categorical = ["국가유산종목", "시대그룹", "재질", "노출형태"]

for col in categorical:
    encoder = LabelEncoder()
    data[col] = encoder.fit_transform(data[col].astype(str))

scaler = StandardScaler()
X = scaler.fit_transform(data)

kmeans = KMeans(n_clusters=3, random_state=42)

df["Cluster"] = kmeans.fit_predict(X)

print(df[["문화재명(국문)", "Cluster"]])

print(df["Cluster"].value_counts())

cluster_mean = df.groupby("Cluster")["문화재연령"].mean()

print(cluster_mean)

pca = PCA(n_components=2)

pca_result = pca.fit_transform(X)

plt.figure(figsize=(8, 6))

plt.scatter(
    pca_result[:, 0],
    pca_result[:, 1],
    c=df["Cluster"],
    cmap="viridis",
    s=70
)

plt.title("K-Means Clustering")
plt.xlabel("PCA1")
plt.ylabel("PCA2")
plt.colorbar(label="Cluster")
plt.show()

df.to_csv("heritage_cluster_result.csv", index=False, encoding="utf-8-sig")

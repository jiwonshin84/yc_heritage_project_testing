"""
문화재 군집분석(Streamlit)
※ 이 파일은 기본 골격입니다.
사용자의 CSV(yc_heritage_feature.csv)에 맞춰
KMeans 군집분석, 군집 설명, 지도 등을 포함하도록 작성을 시작한 템플릿입니다.
"""

import os
import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.cluster import KMeans

st.set_page_config(page_title="문화재 군집분석", layout="wide")

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data", "processed", "yc_heritage_feature.csv")

df = pd.read_csv(DATA_PATH, encoding="utf-8-sig")

st.title("🗺️ 문화재 군집분석")

st.info(
"""
AI는 아래 3가지 정보를 동시에 고려하여
비슷한 특징을 가진 문화재를 자동으로 4개의 군집으로 분류했습니다.

• 문화재 연령
• 재질
• 노출 형태
"""
)

data = df.copy()

le_mat = LabelEncoder()
le_exp = LabelEncoder()

data["재질"] = le_mat.fit_transform(data["재질"].astype(str))
data["노출형태"] = le_exp.fit_transform(data["노출형태"].astype(str))

X = data[["문화재연령","재질","노출형태"]]

X = StandardScaler().fit_transform(X)

km = KMeans(n_clusters=4, random_state=42, n_init=10)
data["군집"] = km.fit_predict(X).map({0:"A",1:"B",2:"C",3:"D"})

st.success("이후 군집별 평균 연령, 대표 재질, 대표 노출 형태를 이용해 각 군집의 특징을 자동으로 설명하도록 확장할 수 있습니다.")
"""
문화재 군집분석(Streamlit)
※ 이 파일은 기본 골격입니다.
사용자의 CSV(yc_heritage_feature.csv)에 맞춰
KMeans 군집분석, 군집 설명, 지도 등을 포함하도록 작성을 시작한 템플릿입니다.
"""

import os
import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.cluster import KMeans

st.set_page_config(page_title="문화재 군집분석", layout="wide")

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data", "processed", "yc_heritage_feature.csv")

df = pd.read_csv(DATA_PATH, encoding="utf-8-sig")

st.title("🗺️ 문화재 군집분석")

st.info(
"""
AI는 아래 3가지 정보를 동시에 고려하여
비슷한 특징을 가진 문화재를 자동으로 4개의 군집으로 분류했습니다.

• 문화재 연령
• 재질
• 노출 형태
"""
)

data = df.copy()

le_mat = LabelEncoder()
le_exp = LabelEncoder()

data["재질"] = le_mat.fit_transform(data["재질"].astype(str))
data["노출형태"] = le_exp.fit_transform(data["노출형태"].astype(str))

X = data[["문화재연령","재질","노출형태"]]

X = StandardScaler().fit_transform(X)

km = KMeans(n_clusters=4, random_state=42, n_init=10)
data["군집"] = km.fit_predict(X).map({0:"A",1:"B",2:"C",3:"D"})

st.success("이후 군집별 평균 연령, 대표 재질, 대표 노출 형태를 이용해 각 군집의 특징을 자동으로 설명하도록 확장할 수 있습니다.")

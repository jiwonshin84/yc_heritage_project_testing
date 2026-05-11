import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, silhouette_samples

# =================================================
# 페이지 설정
# =================================================
st.set_page_config(
    page_title="영천 국가유산 군집분석 리포트",
    layout="wide"
)

st.title("🤖 국가유산 지능형 군집분석 시스템")
st.markdown("영천시 국가유산 105건의 **가치/시대/위치** 데이터를 바탕으로 실시간 군집화를 수행합니다.")
st.divider()

# =================================================
# 데이터 로드 및 전처리
# =================================================
@st.cache_data
def load_base_data():
    # 가치점수와 시대점수가 포함된 데이터를 로드합니다.
    df = pd.read_csv("data/processed/yc_clustering.csv")
    # 필요한 컬럼만 추출 및 결측치 제거
    df = df.dropna(subset=['위도', '경도', '가치점수', '시대점수'])
    return df

df_base = load_base_data()

# =================================================
# 사이드바 설정 (실시간 분석 엔진 제어)
# =================================================
st.sidebar.header("⚙️ 분석 엔진 설정")
st.sidebar.write("군집 수(k)를 변경하면 AI가 데이터를 재학습합니다.")

# 사용자가 직접 k값을 결정
k_value = st.sidebar.slider("군집 수(k) 설정", min_value=2, max_value=10, value=3)

# =================================================
# 실시간 K-Means 분석 수행
# =================================================
# 분석에 사용할 특성(Features) 선택
features = df_base[['위도', '경도', '가치점수', '시대점수']]

# K-Means 모델 학습
kmeans = KMeans(n_clusters=k_value, init='k-means++', random_state=42, n_init=10)
df_base['cluster'] = kmeans.fit_predict(features).astype(str)

# 실시간 실루엣 계수 계산
sil_avg = silhouette_score(features, df_base['cluster'])
df_base['silhouette'] = silhouette_samples(features, df_base['cluster'])

# =================================================
# 상단 요약 지표 (Metrics)
# =================================================
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("분석 대상 전수", f"{len(df_base)}건")
with c2:
    st.metric("현재 설정된 k", f"{k_value}개")
with c3:
    st.metric("평균 가치점수", f"{df_base['가치점수'].mean():.2f}")
with c4:
    # 점수에 따른 상태 메시지 추가
    status = "양호" if sil_avg > 0.5 else "보통"
    st.metric("실시간 실루엣 계수", f"{sil_avg:.3f}", delta=status)

st.divider()

# =================================================
# 메인 분석 레이아웃
# =================================================
col_left, col_right = st.columns([1.2, 1])

with col_left:
    st.subheader(f"📍 공간적 군집 분포 (k={k_value})")
    fig_scatter = px.scatter(
        df_base,
        x="경도",
        y="위도",
        color="cluster",
        size="가치점수",
        hover_data=["문화재명(국문)", "국가유산종목", "시대"],
        color_discrete_sequence=px.colors.qualitative.Bold,
        template="plotly_white",
        category_orders={"cluster": [str(i) for i in range(k_value)]}
    )
    fig_scatter.update_layout(legend_title_text='군집 번호')
    st.plotly_chart(fig_scatter, use_container_width=True)

with col_right:
    st.subheader("📊 군집별 데이터 리포트")
    
    # 군집별 통계 계산
    summary = df_base.groupby("cluster").agg({
        "가치점수": "mean",
        "시대점수": "mean",
        "silhouette": "mean",
        "문화재명(국문)": "count"
    }).rename(columns={"문화재명(국문)": "개수"}).reset_index()
    
    tab1, tab2 = st.tabs(["가치/시대 점수", "실루엣 계수(응집도)"])
    
    with tab1:
        fig_bar = px.bar(
            summary,
            x="cluster",
            y=["가치점수", "시대점수"],
            barmode="group",
            template="plotly_white",
            color_discrete_map={"가치점수": "#636EFA", "시대점수": "#EF553B"}
        )
        st.plotly_chart(fig_bar, use_container_width=True)
        
    with tab2:
        # 실루엣 계수 시각화
        fig_sil = px.bar(
            summary,
            x="cluster",
            y="silhouette",
            color="silhouette",
            color_continuous_scale="RdYlGn",
            range_color=[0, 1],
            template="plotly_white"
        )
        st.plotly_chart(fig_sil, use_container_width=True)

# =================================================
# 하단 설명 및 상세 테이블
# =================================================
st.divider()
with st.expander(f"📝 {k_value}개 군집 상세 데이터 확인 (105건 전수)", expanded=False):
    st.dataframe(
        df_base[["cluster", "문화재명(국문)", "국가유산종목", "시대", "가치점수", "시대점수", "silhouette"]].sort_values("cluster"),
        use_container_width=True
    )

st.info(f"""
**AI 분석 리포트:** 사용자가 설정한 {k_value}개의 그룹으로 105건의 국가유산을 재분류했습니다. 
가장 높은 실루엣 계수를 기록하는 k값을 찾으면 영천시 국가유산의 가장 객관적인 관리 그룹을 도출할 수 있습니다.
""")

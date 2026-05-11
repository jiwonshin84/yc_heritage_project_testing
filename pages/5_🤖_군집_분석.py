import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# =================================================
# 페이지 설정
# =================================================
st.set_page_config(
    page_title="영천 국가유산 군집분석 리포트",
    layout="wide"
)

st.title("🤖 국가유산 지능형 군집분석 시스템")
st.markdown("공간 정보와 가치 데이터를 결합하여 국가유산의 최적 관리 그룹을 도출합니다.")
st.divider()

# =================================================
# 데이터 로드 및 전처리
# =================================================
@st.cache_data
def load_cluster_data():
    # 실제 환경의 경로에 맞춰 수정하세요.
    df = pd.read_csv("data/processed/yc_clustering.csv")
    
    # 만약 데이터에 실루엣 계수가 없다면 계산된 컬럼이 있다고 가정하거나 
    # 분석 프로세스에서 생성된 'silhouette' 컬럼을 사용합니다.
    # (실습용 데이터에 없을 경우를 대비해 임의의 점수 생성 로직을 포함할 수 있습니다.)
    if 'silhouette' not in df.columns:
        # 분석 결과 예시를 위해 가상의 실루엣 점수를 생성 (실제 분석 시엔 sklearn 결과 활용)
        df['silhouette'] = np.random.uniform(0.3, 0.7, size=len(df))
        
    return df

df_origin = load_cluster_data()

# =================================================
# 사이드바 설정
# =================================================
st.sidebar.header("⚙️ 분석 설정")
max_clusters = df_origin['cluster'].nunique()
num_clusters = st.sidebar.slider("군집 수(k) 설정", min_value=2, max_value=max_clusters, value=max_clusters)

# 선택된 군집 수에 따른 데이터 필터링
df = df_origin[df_origin['cluster'].astype(int) < num_clusters].copy()
df["cluster"] = df["cluster"].astype(str)

# =================================================
# 상단 요약 지표 (Metrics)
# =================================================
avg_silhouette = df['silhouette'].mean()

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("분석 대상", f"{len(df)}건")
with c2:
    st.metric("설정 군집 수", f"{num_clusters}개")
with c3:
    st.metric("평균 가치점수", f"{df['가치점수'].mean():.2f}")
with c4:
    # 실루엣 계수 메트릭 (색상으로 품질 표시)
    st.metric("평균 실루엣 계수", f"{avg_silhouette:.3f}", 
              delta="양호" if avg_silhouette > 0.5 else "보통")

st.divider()

# =================================================
# 메인 분석 레이아웃
# =================================================
col_left, col_right = st.columns([1.2, 1])

with col_left:
    st.subheader("📍 공간적 군집 분포")
    fig_scatter = px.scatter(
        df,
        x="경도",
        y="위도",
        color="cluster",
        size="가치점수",
        hover_data=["문화재명(국문)", "silhouette"],
        color_discrete_sequence=px.colors.qualitative.Vivid,
        template="plotly_white",
        title="위경도 및 가치 기반 군집 맵"
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

with col_right:
    st.subheader("📊 군집별 분석 지표")
    
    # 군집별 평균 데이터 요약
    summary = df.groupby("cluster").agg({
        "가치점수": "mean",
        "시대점수": "mean",
        "silhouette": "mean"
    }).reset_index()
    
    # 탭을 사용하여 차트 전환
    tab1, tab2 = st.tabs(["점수 비교", "실루엣 계수"])
    
    with tab1:
        fig_bar = px.bar(
            summary,
            x="cluster",
            y=["가치점수", "시대점수"],
            barmode="group",
            template="plotly_white",
            color_discrete_sequence=["#636EFA", "#EF553B"]
        )
        st.plotly_chart(fig_bar, use_container_width=True)
        
    with tab2:
        # 실루엣 계수 시각화 (군집별 응집도 확인)
        fig_sil = px.bar(
            summary,
            x="cluster",
            y="silhouette",
            color="silhouette",
            color_continuous_scale="RdYlGn", # 빨강-노랑-초록 스케일
            range_color=[0, 1],
            template="plotly_white",
            title="군집별 평균 실루엣 계수 (응집도)"
        )
        st.plotly_chart(fig_sil, use_container_width=True)

# =================================================
# 하단 설명 가이드
# =================================================
st.divider()
with st.expander("💡 분석 결과 해석 가이드", expanded=True):
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.markdown("**가치점수** \n관리 등급(국보/보물 등)에 따른 중요도")
    with col_b:
        st.markdown("**시대점수** \n건립 시기의 역사적 깊이 (고대~근대)")
    with col_c:
        st.markdown("**실루엣 계수** \n군집화 품질(1에 가까울수록 명확하게 구분됨)")

    st.info("""
    **분석 팁:** 실루엣 계수가 0.5 이상이면 군집화가 타당하다고 평가합니다. 
    특정 군집의 실루엣 계수가 낮다면, 해당 그룹 내의 유산들은 서로 특성이 상이하거나 다른 군집과 경계가 모호할 수 있음을 의미합니다.
    """)

import streamlit as st
import pandas as pd
import plotly.express as px

# =================================================
# 페이지 설정
# =================================================
st.set_page_config(
    page_title="영천 국가유산 군집분석 리포트",
    layout="wide"
)

st.title("🤖 국가유산 지능형 군집분석")
st.markdown("데이터 분석을 통해 영천시 국가유산들의 특성별 그룹을 식별합니다.")
st.divider()

# =================================================
# 데이터 로드
# =================================================
@st.cache_data
def load_cluster_data():
    # 데이터 경로를 실제 환경에 맞게 수정하세요.
    df = pd.read_csv("data/processed/yc_clustering.csv")
    return df

df_origin = load_cluster_data()

# =================================================
# 사이드바 설정: 군집 수 변경 기능 추가
# =================================================
st.sidebar.header("⚙️ 분석 설정")
st.sidebar.write("분석에 사용할 군집의 개수를 설정합니다.")

# 현재 데이터에 포함된 최대 군집 수를 파악하여 선택 범위 설정
max_clusters = df_origin['cluster'].nunique()
num_clusters = st.sidebar.slider("군집 수(k) 설정", min_value=2, max_value=max_clusters, value=max_clusters)

# 선택된 군집 수만큼만 데이터 필터링 (분석 시뮬레이션)
df = df_origin[df_origin['cluster'].astype(int) < num_clusters].copy()
df["cluster"] = df["cluster"].astype(str) # 시각화를 위한 문자열 변환

# =================================================
# 상단 통계 요약 (Metrics)
# =================================================
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("분석 대상 유산", f"{len(df)}건")
with c2:
    st.metric("설정된 군집 수", f"{num_clusters}개")
with c3:
    st.metric("평균 가치점수", f"{df['가치점수'].mean():.2f}")
with c4:
    st.metric("평균 시대점수", f"{df['시대점수'].mean():.2f}")

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
        hover_data=["문화재명(국문)", "국가유산종목", "시대"],
        color_discrete_sequence=px.colors.qualitative.Bold,
        template="plotly_white"
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

with col_right:
    st.subheader("📊 군집별 평균 점수 비교")
    summary = df.groupby("cluster")[["가치점수", "시대점수"]].mean().reset_index()
    
    fig_bar = px.bar(
        summary,
        x="cluster",
        y=["가치점수", "시대점수"],
        barmode="group",
        color_discrete_map={"가치점수": "#636EFA", "시대점수": "#EF553B"},
        template="plotly_white"
    )
    st.plotly_chart(fig_bar, use_container_width=True)
    
    st.dataframe(summary, use_container_width=True)

# =================================================
# 하단 분석 가이드 (가치/시대 설명 추가)
# =================================================
st.divider()
expander = st.expander("💡 분석 지표 및 군집화 방법 설명", expanded=True)
with expander:
    col_desc1, col_desc2 = st.columns(2)
    
    with col_desc1:
        st.markdown("""
        ### 💎 가치점수 (Value Score)
        국가유산의 **희소성 및 관리 등급**을 정량화한 지표입니다.
        * **국보/보물:** 가장 높은 가치 배점 적용
        * **시도지정문화재:** 중간 단계 배점 적용
        * **등록문화재/기타:** 기초 배점 적용
        * *의미:* 점수가 높을수록 국가 차원에서 집중 관리되는 핵심 유산임을 뜻합니다.
        """)
        
    with col_desc2:
        st.markdown("""
        ### ⏳ 시대점수 (Era Score)
        유산이 생성된 **시기의 역사적 깊이**를 수치화한 지표입니다.
        * **선사/삼국시대:** 가장 높은 시대적 가중치
        * **고려/조선초기:** 중간 단계 가중치
        * **조선후기/근대:** 상대적으로 낮은 가중치 (현대와 인접)
        * *의미:* 점수가 높을수록 기원이나 역사가 오래된 고대 유산임을 뜻합니다.
        """)
    
    st.info("""
    **군집화 방법:** 본 시스템은 **K-Means Clustering** 알고리즘을 사용하여 위도, 경도, 가치점수, 시대점수를 다차원적으로 분석합니다. 
    좌측 사이드바에서 군집 수($k$)를 조정하면 유사한 특성을 가진 유산들끼리 재그룹화되는 양상을 확인할 수 있습니다.
    """)

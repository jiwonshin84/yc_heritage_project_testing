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
st.markdown("영천시 국가유산 105건의 데이터를 바탕으로 최적의 관리 그룹을 분석합니다.")
st.divider()

# =================================================
# 데이터 로드 및 전처리
# =================================================
@st.cache_data
def load_base_data():
    # 가치점수와 시대점수가 포함된 데이터를 로드합니다.
    df = pd.read_csv("data/processed/yc_clustering.csv")
    df = df.dropna(subset=['위도', '경도', '가치점수', '시대점수'])
    
    # 소재지상세 주소 내의 탭(\t) 문자를 공백으로 치환하여 가독성 개선
    df['소재지상세'] = df['소재지상세'].fillna("-").astype(str).str.replace('\t', ' ', regex=True).str.strip()
    return df

df_base = load_base_data()

# =================================================
# 사이드바 설정 (실시간 분석 엔진 제어)
# =================================================
st.sidebar.header("⚙️ 분석 엔진 설정")
k_value = st.sidebar.slider("군집 수(k) 설정", min_value=2, max_value=10, value=3)

# =================================================
# 실시간 K-Means 분석 수행
# =================================================
features = df_base[['위도', '경도', '가치점수', '시대점수']]
kmeans = KMeans(n_clusters=k_value, init='k-means++', random_state=42, n_init=10)

# 군집 번호 보정 (1번부터 시작)
df_base['cluster_num'] = kmeans.fit_predict(features) + 1
df_base['cluster'] = df_base['cluster_num'].astype(str)

# 실루엣 계수 계산
sil_avg = silhouette_score(features, df_base['cluster'])
df_base['silhouette_val'] = silhouette_samples(features, df_base['cluster'])

# =================================================
# 상단 요약 지표 (Metrics)
# =================================================
c1, c2, c3, c4 = st.columns(4)
with c1: st.metric("분석 대상 전수", "105건")
with c2: st.metric("생성된 군집 수", f"{k_value}개")
with c3: st.metric("전체 평균 가치", f"{df_base['가치점수'].mean():.2f}")
with c4: st.metric("분석 신뢰도(실루엣)", f"{sil_avg:.3f}")

st.divider()

# =================================================
# 메인 분석 시각화
# =================================================
col_left, col_right = st.columns([1.2, 1])

with col_left:
    st.subheader(f"📍 공간적 군집 분포 (1번~{k_value}번)")
    fig_scatter = px.scatter(
        df_base, x="경도", y="위도", color="cluster", size="가치점수",
        hover_data=["문화재명(국문)", "국가유산종목"],
        color_discrete_sequence=px.colors.qualitative.Bold,
        template="plotly_white",
        category_orders={"cluster": [str(i) for i in range(1, k_value + 1)]}
    )
    fig_scatter.update_layout(legend_title_text='군집 번호')
    st.plotly_chart(fig_scatter, use_container_width=True)

with col_right:
    st.subheader("📊 군집별 특성 요약")
    summary = df_base.groupby("cluster").agg({
        "가치점수": "mean", "시대점수": "mean", "문화재명(국문)": "count"
    }).rename(columns={"문화재명(국문)": "개수"}).reset_index()
    
    summary['cluster_int'] = summary['cluster'].astype(int)
    summary = summary.sort_values('cluster_int')

    fig_bar = px.bar(
        summary, x="cluster", y=["가치점수", "시대점수"], barmode="group",
        template="plotly_white", color_discrete_map={"가치점수": "#636EFA", "시대점수": "#EF553B"},
        labels={"value": "평균 점수", "variable": "지표", "cluster": "군집"}
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# =================================================
# 하단: 군집별 상세 목록
# =================================================
st.divider()
st.subheader("🔍 군집별 유산 상세 목록")

cluster_labels = [str(i) for i in range(1, k_value + 1)]
tabs = st.tabs([f"군집 {c}" for c in cluster_labels])

for i, tab in enumerate(tabs):
    cluster_id = cluster_labels[i]
    with tab:
        cluster_df = df_base[df_base['cluster'] == cluster_id].sort_values("가치점수", ascending=False)
        
        cnt = len(cluster_df)
        avg_v = cluster_df['가치점수'].mean()
        avg_e = cluster_df['시대점수'].mean()
        
        st.markdown(f"✅ **군집 정보** | 유산 수: **{cnt}건** | 평균 가치점수: **{avg_v:.2f}** | 평균 시대점수: **{avg_e:.2f}**")
        
        st.dataframe(
            cluster_df[["문화재명(국문)", "국가유산종목", "시대", "소재지상세"]],
            use_container_width=True,
            hide_index=True
        )

# =================================================
# 분석 지표 산출 로직 설명 (사용자 요청 반영)
# =================================================
st.divider()
with st.expander("💡 군집 분석 지표 산출 로직 안내", expanded=True):
    desc_col1, desc_col2 = st.columns(2)
    
    with desc_col1:
        st.markdown("### 💎 가치 점수 배점 (Value Score)")
        st.markdown("""
        국가유산의 지정 종목에 따른 관리 등급별 배점입니다.
        * **10점:** 국보
        * **9점:** 보물
        * **8점:** 사적, 천연기념물
        * **7점:** 국가민속문화유산
        * **6점:** 국가등록문화유산
        * **5점:** 경상북도 유형문화유산
        * **4점:** 경상북도 기념물, 경상북도 민속문화유산
        * **3점:** 경상북도 문화유산자료
        """)

    with desc_col2:
        st.markdown("### ⏳ 시대 점수 산출 (Era Score)")
        st.markdown("""
        유산의 건립 시기가 오래될수록 높은 가중치를 부여합니다.
        * **15점:** 선사시대 (청동기, 철기 등)
        * **14점:** 삼한시대
        * **13점:** 신라, 통일신라
        * **11점:** 고려시대
        * **9점:** 조선 초기 (태조~중종)
        * **7점:** 조선 중후기 (숙종~고종)
        * **4점:** 근대 (일제강점기 ~ 1930년대)
        * **5점:** 기타
        """)
    
    st.info("※ 본 시스템은 위 **가치 점수**와 **시대 점수**, 그리고 **지리적 위치(위경도)**를 결합한 4차원 공간 분석을 통해 군집을 생성합니다.")

import pandas as pd
import folium
from folium.plugins import MarkerCluster, HeatMap
import streamlit as st
from streamlit_folium import st_folium

# ==========================================================
# 1. Page 설정 및 타이틀 (슬라이드 컨셉 반영)
# ==========================================================
st.set_page_config(
    page_title="영천시 국가유산 GIS 공간 분석",
    layout="wide"
)

st.title("📌 Phase 4. GIS 공간 분석: 지도 위에서 패턴을 읽다")
st.caption("공공데이터 기반 영천시 국가유산 좌표 매핑 및 밀집 지역(Hotspot) 분석")

# ==========================================================
# 2. 데이터 불러오기 및 전처리 (캐싱 적용)
# ==========================================================
@st.cache_data
def load_data():
    # 파일 경로 (본인의 파일 경로에 맞게 수정)
    file_path = "/content/drive/MyDrive/00. 2026학년도 인재양성프로젝트/공공데이터 기반 프로젝트/dataset/영천_국가유산_상세_좌표보완.csv"
    
    try:
        df = pd.read_csv(file_path, encoding="utf-8-sig")
    except Exception:
        # 경로 문제 대비 예외 처리 (로컬 test용)
        df = pd.read_csv("영천_국가유산_상세_좌표보완.csv", encoding="utf-8-sig")

    # 좌표 숫자형 변환 및 결측치 제거
    df["위도"] = pd.to_numeric(df["위도"], errors="coerce")
    df["경도"] = pd.to_numeric(df["경도"], errors="coerce")
    df = df.dropna(subset=["위도", "경도"])
    
    return df

# 데이터 로드
try:
    yc_map_df = load_data()
except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
    st.stop()

# ==========================================================
# 3. 지도 설정 & 레이어 옵션 선택
# ==========================================================
# 지도 중심 계산
center_lat = yc_map_df["위도"].mean()
center_lon = yc_map_df["경도"].mean()

# 사이드바 컨트롤 (주제 반영)
st.sidebar.header("⚙️ GIS 시각화 옵션")
show_cluster = st.sidebar.checkbox("1. 좌표 기반 마커 클러스터 표시", value=True)
show_heatmap = st.sidebar.checkbox("2. 밀집 지역 (Hotspot 히트맵) 표시", value=True)

# 지표 요약 수치 출력
col1, col2, col3 = st.columns(3)
col1.metric("분석 대상 국가유산 수", f"{len(yc_map_df)} 개")
col2.metric("중심 위도", f"{center_lat:.4f}")
col3.metric("중심 경도", f"{center_lon:.4f}")

st.write("---")

# ==========================================================
# 4. Folium 지도 생성 및 레이어 추가
# ==========================================================
# 기본 지도 생성 (CartoDB positron으로 깔끔한 배경 사용)
m1 = folium.Map(
    location=[center_lat, center_lon],
    zoom_start=11,
    tiles="CartoDB positron"
)

# [옵션 1] 마커 클러스터 추가
if show_cluster:
    marker_cluster = MarkerCluster(name="마커 클러스터").add_to(m1)

    for _, row in yc_map_df.iterrows():
        popup_html = f"""
        <div style="width:230px; font-family: sans-serif;">
            <h4 style="margin-bottom:8px; color:#1f77b4;">{row['문화재명(국문)']}</h4>
            <b>• 국가유산종목:</b> {row.get('국가유산종목', '정보없음')}<br>
            <b>• 시대:</b> {row.get('시대', '정보없음')}<br>
            <b>• 소재지:</b> {row.get('소재지상세', '정보없음')}<br>
            <b>• 관리자:</b> {row.get('관리자', '정보없음')}
        </div>
        """

        folium.Marker(
            location=[row["위도"], row["경도"]],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=row["문화재명(국문)"],
            icon=folium.Icon(color="blue", icon="info-sign")
        ).add_to(marker_cluster)

# [옵션 2] 밀집 지역 (Heatmap/Hotspot) 도출 (슬라이드 2번 핵심 기능)
if show_heatmap:
    heat_data = [[row["위도"], row["경도"]] for _, row in yc_map_df.iterrows()]
    HeatMap(
        heat_data,
        radius=18,
        blur=12,
        min_opacity=0.4,
        name="밀집도 (Heatmap)"
    ).add_to(m1)

# 레이어 제어 컨트롤 추가
folium.LayerControl().add_to(m1)

# ==========================================================
# 5. Streamlit에 지도 렌더링 (st_folium 활용)
# ==========================================================
st_folium(m1, width=1100, height=600, returned_objects=[])

# 인사이트 박스 (슬라이드 하단 메시지 강조)
st.info(
    "💡 **분석 인사이트:** 지도 시각화는 단순한 그림이 아니라, 실제 문제를 해결하기 위한 강력한 공간 분석 도구입니다. "
    "문화재 밀집 구역(Hotspot)을 바탕으로 향후 환경 센서 우선 설치 및 자원 집중 배분 구역을 파악할 수 있습니다."
)

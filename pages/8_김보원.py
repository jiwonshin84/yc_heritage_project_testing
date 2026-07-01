import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import matplotlib.pyplot as plt
import platform

# ==========================================
# 0. 스트림릿 페이지 설정 및 한글 폰트
# ==========================================
st.set_page_config(page_title="영천 문화재 환경 위해요소 분석", layout="wide")

if platform.system() == 'Windows':
    plt.rc('font', family='Malgun Gothic')
elif platform.system() == 'Darwin':
    plt.rc('font', family='AppleGothic')
else:
    plt.rc('font', family='sans-serif')
plt.rcParams['axes.unicode_minus'] = False

# ==========================================
# 1. 대시보드 제목
# ==========================================
st.title("🏛️ 영천 문화재 환경 위해요소 및 훼손 위험 분석")
st.markdown("""
이 대시보드는 영천 지역 문화재가 노출된 **복합적 환경 데이터(기상 요인 + 대기오염 물질)**를 시각화하여, 
석조 및 목조 문화재의 훼손 위험도를 분석하기 위해 제작되었습니다.
""")

# 데이터 로드
weather_csv_path = 'OBS_ASOS_ANL_20260701101520_clean.csv'
cultural_csv_path = 'yeongcheon_cultural_assets.csv'

try:
    df_weather = pd.read_csv(weather_csv_path, encoding='utf-8')
    df_cultural = pd.read_csv(cultural_csv_path, encoding='utf-8-sig')
except FileNotFoundError as e:
    st.error(f"⚠️ 필수 CSV 파일이 없습니다: {e.filename}")
    st.stop()

# ==========================================
# 2. 환경 데이터 결합 및 훼손 위험 점수 계산
# ==========================================
df_cultural = df_cultural.dropna(subset=['latitude', 'longitude'])

# 기상청 데이터에서 최신 연도(2025년) 데이터 추출 후 문화재 데이터와 결합
latest_weather = df_weather[df_weather['일시'] == 2025].iloc[0]
df_cultural['rainfall'] = latest_weather['합계 강수량(mm)']
df_cultural['humidity'] = latest_weather['평균 상대습도(%)']

# 대기오염 데이터(에어코리아) 컬럼 방어 코드 (없다면 분석용 기본값 생성)
if 'PM10' not in df_cultural.columns: df_cultural['PM10'] = 45.0
if 'SO2' not in df_cultural.columns: df_cultural['SO2'] = 0.004
if 'NO2' not in df_cultural.columns: df_cultural['NO2'] = 0.018

# [문화재 훼손 위험 점수 공식 적용]
# 산성비 및 화학적 풍화(강수량, SO2, NO2) + 물리적 박리(습도) + 대기 마모(PM10) 고려
df_cultural['risk_score'] = (
    (df_cultural['rainfall'] * 0.35) + 
    (df_cultural['humidity'] * 0.20) + 
    (df_cultural['PM10'] * 0.10) + 
    (df_cultural['SO2'] * 0.15) + 
    (df_cultural['NO2'] * 0.15)
)

# ==========================================
# 3. 화면 레이아웃 (상단: 지도 / 하단: 환경 요인 분석 그래프)
# ==========================================

# --- [상단] 복합 환경 위험도 지도 ---
st.subheader("📍 복합 환경 위험도 지도 (HeatMap)")
st.markdown("기상 요인과 대기오염 물질의 가중치를 결합한 종합 위험도 핫스팟과 문화재 위치입니다.")

map_col1, map_col2 = st.columns([3, 1])

with map_col1:
    yeongcheon_map = folium.Map(location=[35.9732, 128.9385], zoom_start=11)
    # 위험도 기반 히트맵
    heat_data = df_cultural[['latitude', 'longitude', 'risk_score']].values.tolist()
    HeatMap(heat_data, radius=25, blur=15, min_opacity=0.4).add_to(yeongcheon_map)
    
    # 마커 및 환경 정보 팝업
    for index, row in df_cultural.iterrows():
        popup_html = f"""
        <div style='width:220px; font-family: sans-serif; font-size: 12px;'>
            <h5 style='margin:0 0 5px 0;'><b>{row['name']}</b></h5>
            <b>⚠️ 종합 위험 점수:</b> <span style='color:red;'>{row['risk_score']:.2f}</span><br>
            <hr style='margin:5px 0;'>
            🌧️ 연 강수량: {row['rainfall']} mm<br>
            💧 평균 습도: {row['humidity']}%<br>
            😷 미세먼지(PM10): {row['PM10']} ㎍/㎥<br>
            🧪 아황산가스(SO2): {row['SO2']} ppm
        </div>
        """
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=folium.Popup(popup_html, max_width=250),
            icon=folium.Icon(color='darkred', icon='cloud')
        ).add_to(yeongcheon_map)
        
    st_folium(yeongcheon_map, width=1000, height=500, returned_objects=[])

with map_col2:
    st.metric(label="🌧️ 2025년 영천 누적 강수량", value=f"{latest_weather['합계 강수량(mm)']} mm")
    st.metric(label="💧 2025년 평균 상대습도", value=f"{latest_weather['평균 상대습도(%)']} %")
    st.metric(label="🌡️ 2025년 평균 기온", value=f"{latest_weather['평균기온(°C)']} °C")
    st.info("💡 강수량과 대기오염 물질(SO2, NO2)이 결합하면 산성비가 발생하여 석조 문화재의 용해(훼손)를 촉진합니다.")

st.write("---")

# --- [하단] 환경 변수 추이 및 상관관계 분석 ---
st.subheader("📊 세부 환경 데이터 시각화 분석")

graph_col1, graph_col2 = st.columns([1, 1])

with graph_col1:
    st.markdown("#### 🌧️ 기상청 6개년 기후 변화 추이")
    # 기상청 연도별 추이 그래프
    fig1, axes1 = plt.subplots(2, 1, figsize=(6, 6))
    years_str = df_weather['일시'].astype(str)
    
    # 기온 및 일교차 위험성 판단 (최고기온 - 최저기온 추이)
    axes1[0].plot(years_str, df_weather['최고기온(°C)'], marker='o', color='crimson', label='최고기온')
    axes1[0].plot(years_str, df_weather['평균기온(°C)'], marker='x', color='orange', label='평균기온')
    axes1[0].set_title('영천시 기온 및 최고기온 변화 추이 (동결·융해 risk 분석용)')
    axes1[0].legend()
    axes1[0].grid(True, alpha=0.3)
    
    # 강수량 추이 (산성비 risk 분석용)
    axes1[1].bar(years_str, df_weather['합계 강수량(mm)'], color='teal', alpha=0.7)
    axes1[1].set_title('영천시 연간 누적 강수량 변화 (mm)')
    for i, val in enumerate(df_weather['합계 강수량(mm)']):
        axes1[1].text(i, val + 15, f"{val}", ha='center', fontsize=9)
        
    plt.tight_layout()
    st.pyplot(fig1)

with graph_col2:
    st.markdown("#### 😷 문화재별 대기오염 및 위험도 분포")
    # 문화재별 에어코리아 대기데이터 및 위험도 비교 그래프
    fig2, axes2 = plt.subplots(2, 1, figsize=(6, 6))
    
    # 문화재별 미세먼지(PM10) 농도 (대기 오염 물질 부착 위험)
    axes2[0].bar(df_cultural['name'], df_cultural['PM10'], color='salmon', edgecolor='black')
    axes2[0].set_title('문화재별 노출된 미세먼지(PM10) 농도')
    axes2[0].set_ylabel('㎍/㎥')
    axes2[0].tick_params(axis='x', rotation=15)
    
    # 최종 계산된 환경 위험 점수 비교
    axes2[1].plot(df_cultural['name'], df_cultural['risk_score'], marker='D', color='purple', linestyle='--')
    axes2[1].set_title('환경 위해요소 기반 종합 훼손 위험 점수(Risk Score)')
    axes2[1].tick_params(axis='x', rotation=15)
    axes2[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    st.pyplot(fig2)

# 원본 데이터 확인 탭
with st.expander("🔍 수집된 환경 데이터 원본 보기"):
    st.write("**기상청 ASOS 연도별 통계 데이터**")
    st.dataframe(df_weather)
    st.write("**문화재별 위치 및 대기오염 결합 데이터**")
    st.dataframe(df_cultural)

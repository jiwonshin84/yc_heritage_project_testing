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

# 그래프 한글 깨짐 방지
if platform.system() == 'Windows':
    plt.rc('font', family='Malgun Gothic')
elif platform.system() == 'Darwin':
    plt.rc('font', family='AppleGothic')
else:
    plt.rc('font', family='sans-serif')
plt.rcParams['axes.unicode_minus'] = False

# ==========================================
# 1. 대시보드 대제목
# ==========================================
st.title("🏛️ 영천 문화재 환경 위해요소 및 훼손 위험 분석")
st.markdown("""
이 대시보드는 영천 지역의 **6개년 누적 기상 통계(2020~2025)**와 문화재 위치 데이터를 결합하여, 
환경적 요인이 문화재 훼손에 미치는 위험도를 시각적으로 분석한 정적 대시보드입니다.
""")

# 데이터 불러오기
weather_csv_path = 'OBS_ASOS_ANL_20260701101520_clean.csv'
cultural_csv_path = 'yeongcheon_cultural_assets.csv'

try:
    df_weather = pd.read_csv(weather_csv_path, encoding='utf-8')
    df_cultural = pd.read_csv(cultural_csv_path, encoding='utf-8-sig')
except FileNotFoundError as e:
    st.error(f"⚠️ 필수 CSV 파일이 깃허브 리포지토리에 없습니다: {e.filename}")
    st.info("💡 깃허브에 'app.py', 'OBS_ASOS_ANL_20260701101520_clean.csv', 'yeongcheon_cultural_assets.csv'가 모두 같이 있는지 확인해주세요.")
    st.stop()

# ==========================================
# 2. 환경 데이터 결합 및 위험 점수 계산
# ==========================================
df_cultural = df_cultural.dropna(subset=['latitude', 'longitude'])

# 2025년 최신 기상 통계를 기준으로 문화재 위험도 맵핑
latest_weather = df_weather[df_weather['일시'] == 2025].iloc[0]
df_cultural['rainfall'] = latest_weather['합계 강수량(mm)']
df_cultural['humidity'] = latest_weather['평균 상대습도(%)']

# 대기 데이터 컬럼 방어 코드 (없을 경우 분석용 기본값)
if 'PM10' not in df_cultural.columns: df_cultural['PM10'] = 45.0
if 'SO2' not in df_cultural.columns: df_cultural['SO2'] = 0.004
if 'NO2' not in df_cultural.columns: df_cultural['NO2'] = 0.018

# 위험 점수 계산 공식
df_cultural['risk_score'] = (
    (df_cultural['rainfall'] * 0.35) + 
    (df_cultural['humidity'] * 0.20) + 
    (df_cultural['PM10'] * 0.10) + 
    (df_cultural['SO2'] * 0.15) + 
    (df_cultural['NO2'] * 0.15)
)

# ==========================================
# 3. 레이아웃 (좌: 지도 / 우: 6개년 기상 변화 추이 그래프)
# ==========================================
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📍 영천 문화재별 환경 위험도 지도")
    st.markdown("강수량, 습도, 대기오염을 종합한 훼손 위험 지수 기반의 히트맵입니다.")
    
    # 지도 생성
    yeongcheon_map = folium.Map(location=[35.9732, 128.9385], zoom_start=11)
    
    # 히트맵 레이어
    heat_data = df_cultural[['latitude', 'longitude', 'risk_score']].values.tolist()
    HeatMap(heat_data, radius=25, blur=15, min_opacity=0.4).add_to(yeongcheon_map)
    
    # 마커 레이어
    for index, row in df_cultural.iterrows():
        popup_html = f"""
        <div style='width:200px; font-family: sans-serif; font-size: 12px;'>
            <b>{row['name']}</b><br>
            <hr style='margin:5px 0;'>
            ⚠️ 위험 점수: {row['risk_score']:.2f}<br>
            🌧️ 연 강수량: {row['rainfall']} mm<br>
            💧 평균 습도: {row['humidity']}%
        </div>
        """
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=folium.Popup(popup_html, max_width=250),
            icon=folium.Icon(color='red', icon='info-sign')
        ).add_to(yeongcheon_map)
        
    st_folium(yeongcheon_map, width=650, height=500, returned_objects=[])

with col2:
    st.subheader("📈 영천시 6개년 기후 데이터 분석 (2020~2025)")
    st.markdown("과거 통계를 통해 문화재가 지속해서 노출되어 온 환경 변화를 확인합니다.")
    
    fig, axes = plt.subplots(2, 2, figsize=(10, 8))
    years_str = df_weather['일시'].astype(str)
    
    # (1) 연도별 평균기온 추이
    axes[0, 0].plot(years_str, df_weather['평균기온(°C)'], marker='o', color='crimson', linewidth=2)
    axes[0, 0].set_title('연도별 평균 기온 (°C)')
    axes[0, 0].grid(True, linestyle='--', alpha=0.5)
    
    # (2) 연도별 최고기온 추이 (일교차 훼손 요인)
    axes[0, 1].plot(years_str, df_weather['최고기온(°C)'], marker='X', color='darkorange', linewidth=2)
    axes[0, 1].set_title('연도별 최고 기온 (°C)')
    axes[0, 1].grid(True, linestyle='--', alpha=0.5)
    
    # (3) 연도별 합계 강수량 (산성비 요인)
    axes[1, 0].bar(years_str, df_weather['합계 강수량(mm)'], color='royalblue', alpha=0.8)
    axes[1, 0].set_title('연도별 합계 강수량 (mm)')
    for i, val in enumerate(df_weather['합계 강수량(mm)']):
        axes[1, 0].text(i, val + 20, f"{val}", ha='center', va='bottom', fontsize=9, fontweight='bold')
        
    # (4) 연도별 평균 상대습도 (물리적 풍화 요인)
    axes[1, 1].plot(years_str, df_weather['평균 상대습도(%)'], marker='s', color='teal', linewidth=2)
    axes[1, 1].set_title('연도별 평균 상대습도 (%)')
    axes[1, 1].grid(True, linestyle='--', alpha=0.5)
    
    plt.tight_layout()
    st.pyplot(fig)

# 데이터 테이블 뷰 제공
st.write("---")
st.subheader("🔍 분석에 사용된 데이터 셋")
tab1, tab2 = st.tabs(["기상청 연도별 통계", "문화재별 환경 위험도 결과"])
with tab1:
    st.dataframe(df_weather)
with tab2:
    st.dataframe(df_cultural[['name', 'latitude', 'longitude', 'risk_score']])

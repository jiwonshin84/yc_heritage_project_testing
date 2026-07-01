import streamlit as st

st.title("🌦 김보원")

import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import matplotlib.pyplot as plt
import platform

# ==========================================
# 0. 스트림릿 페이지 설정 및 한글 폰트 방어 코드
# ==========================================
st.set_page_config(page_title="영천 문화재 환경 위험 대시보드", layout="wide")

# 리눅스 기반인 스트림릿 서버 환경에서 그래프 한글 깨짐을 방지합니다.
if platform.system() == 'Windows':
    plt.rc('font', family='Malgun Gothic')
elif platform.system() == 'Darwin':
    plt.rc('font', family='AppleGothic')
else:
    # 스트림릿 서버에 폰트가 없을 때를 대비해 기본 탑재 폰트 계열을 지정합니다.
    plt.rc('font', family='sans-serif')
plt.rcParams['axes.unicode_minus'] = False

# ==========================================
# 1. 대시보드 대제목 및 데이터 로드
# ==========================================
st.title("🗺️ 영천 문화재 환경 데이터 시각화를 통한 훼손 위험 분석")
st.markdown("국가유산 위치 데이터와 영천시 연도별 기상청 통계 데이터를 결합한 웹 대시보드입니다.")

# 파일 경로 지정 (깃허브 리포지토리에 올릴 파일명들과 똑같이 맞춰야 합니다)
weather_csv_path = 'OBS_ASOS_ANL_20260701101520_clean.csv'
cultural_csv_path = 'yeongcheon_cultural_assets.csv' # 문화재 위치(위경도)가 담긴 CSV

try:
    # 1-1. 올려주신 기상 데이터 읽기
    df_weather = pd.read_csv(weather_csv_path, encoding='utf-8')
    
    # 1-2. 기존 문화재 데이터 읽기
    df_cultural = pd.read_csv(cultural_csv_path, encoding='utf-8-sig')
except FileNotFoundError as e:
    st.error(f"⚠️ 필수 CSV 파일이 리포지토리에 없습니다: {e.filename}")
    st.info("💡 'app.py', 'OBS_ASOS_ANL_20260701101520_clean.csv', 'yeongcheon_cultural_assets.csv' 파일이 모두 같은 깃허브 방에 있어야 합니다.")
    st.stop()

# ==========================================
# 2. 데이터 가공 및 위험 점수(Risk Score) 계산
# ==========================================
# 위경도가 없는 문화재 데이터는 사전에 제거합니다.
df_cultural = df_cultural.dropna(subset=['latitude', 'longitude'])

# 가장 최근 연도인 2025년 기상 통계를 기준으로 매칭합니다.
# 데이터셋 구조: [cite: 1] 지점, 지점명, 일시(연도), 평균기온, ... 순서
latest_weather = df_weather[df_weather['일시'] == 2025].iloc[0]

# 문화재 데이터프레임에 기상 변수 결합 [cite: 1]
df_cultural['rainfall'] = latest_weather['합계 강수량(mm)']
df_cultural['humidity'] = latest_weather['평균 상대습도(%)']

# (선택 사항) 대기오염 데이터(에어코리아)가 문화재 CSV에 없다면 임시 기본값 부여
if 'PM10' not in df_cultural.columns: df_cultural['PM10'] = 45.0
if 'SO2' not in df_cultural.columns: df_cultural['SO2'] = 0.004
if 'NO2' not in df_cultural.columns: df_cultural['NO2'] = 0.018

# 제공해주신 위험도 공식 적용
df_cultural['risk_score'] = (
    (df_cultural['rainfall'] * 0.35) + 
    (df_cultural['humidity'] * 0.20) + 
    (df_cultural['PM10'] * 0.10) + 
    (df_cultural['SO2'] * 0.15) + 
    (df_cultural['NO2'] * 0.15)
)

# ==========================================
# 3. 웹 레이아웃 구성 (화면 반반 나누기)
# ==========================================
col1, col2 = st.columns([1, 1])

# --- 왼쪽: Folium 지도 및 히트맵 ---
with col1:
    st.subheader("📍 문화재 위험도 지도 (2025년 기상 반영)")
    
    # 영천 중심 지도 생성 (위도 35.9732, 경도 128.9385)
    yeongcheon_map = folium.Map(location=[35.9732, 128.9385], zoom_start=11)
    
    # 위험도를 가중치로 둔 HeatMap 추가
    heat_data = df_cultural[['latitude', 'longitude', 'risk_score']].values.tolist()
    HeatMap(heat_data, radius=25, blur=15, min_opacity=0.4).add_to(yeongcheon_map)
    
    # 문화재별 개별 마커 추가
    for index, row in df_cultural.iterrows():
        popup_html = f"""
        <div style='width:180px; font-family: sans-serif;'>
            <b>{row['name']}</b><br>
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
    
    # 스트림릿 웹페이지에 지도 띄우기
    st_folium(yeongcheon_map, width=700, height=550, returned_objects=[])

# --- 오른쪽: 기상청 실제 연도별 추이 그래프 ---
with col2:
    st.subheader("📈 영천시 연도별 기상 추이 분석 (2020~2025)")
    
    fig, axes = plt.subplots(2, 2, figsize=(10, 8))
    years_str = df_weather['일시'].astype(str) # X축 연도 라벨 [cite: 1]
    
    # (1) 연도별 평균기온 추이 [cite: 1]
    axes[0, 0].plot(years_str, df_weather['평균기온(°C)'], marker='o', color='crimson', linewidth=2)
    axes[0, 0].set_title('연도별 평균 기온 (°C)', fontsize=11)
    axes[0, 0].grid(True, linestyle='--', alpha=0.5)
    
    # (2) 연도별 최고기온 추이 [cite: 1]
    axes[0, 1].plot(years_str, df_weather['최고기온(°C)'], marker='X', color='darkorange', linewidth=2)
    axes[0, 1].set_title('연도별 최고 기온 (°C)', fontsize=11)
    axes[0, 1].grid(True, linestyle='--', alpha=0.5)
    
    # (3) 연도별 합계 강수량 (막대) [cite: 1]
    axes[1, 0].bar(years_str, df_weather['합계 강수량(mm)'], color='royalblue', alpha=0.8)
    axes[1, 0].set_title('연도별 합계 강수량 (mm)', fontsize=11)
    for i, val in enumerate(df_weather['합계 강수량(mm)']):
        axes[1, 0].text(i, val + 20, f"{val}", ha='center', va='bottom', fontsize=9, fontweight='bold')
        
    # (4) 연도별 평균 상대습도 (꺾은선) [cite: 1]
    axes[1, 1].plot(years_str, df_weather['평균 상대습도(%)'], marker='s', color='teal', linewidth=2)
    axes[1, 1].set_title('연도별 평균 상대습도 (%)', fontsize=11)
    axes[1, 1].grid(True, linestyle='--', alpha=0.5)
    
    plt.tight_layout()
    # 스트림릿 웹페이지에 그래프 띄우기
    st.pyplot(fig)

# --- 하단: 기상청 실제 데이터 테이블 보여주기 ---
st.subheader("📊 기상청 연도별 통계 데이터 원본")
st.dataframe(df_weather) [cite: 1]

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import platform

# ==========================================
# 0. 스트림릿 페이지 설정
# ==========================================
st.set_page_config(
    page_title="영천 문화재 환경 위해요소 분석",
    layout="wide"
)

# ==========================================
# 1. 한글 폰트 설정 (그래프 한글 깨짐 방지)
# ==========================================
if platform.system() == 'Windows':
    plt.rc('font', family='Malgun Gothic')
elif platform.system() == 'Darwin':
    plt.rc('font', family='AppleGothic')
else:
    plt.rc('font', family='NanumGothic')

plt.rcParams['axes.unicode_minus'] = False

# ==========================================
# 2. 대시보드 제목
# ==========================================
st.title("🏛️ 영천 문화재 환경 위해요소 및 훼손 위험 분석")

st.markdown("""
이 대시보드는 영천 지역의 **기상청 환경 데이터(2020~2025)**를 활용하여  
문화재가 어떤 환경적 위험에 노출되는지 분석합니다.
""")

# ==========================================
# 3. CSV 불러오기
# ==========================================
csv_path = "data/OBS_ASOS_ANL_20260701101520_clean.csv"

try:
    df = pd.read_csv(csv_path, encoding="utf-8")
except FileNotFoundError:
    st.error("⚠️ CSV 파일이 data 폴더 안에 없습니다.")
    st.stop()

# ==========================================
# 4. 데이터 확인
# ==========================================
st.subheader("📂 불러온 데이터 확인")
st.dataframe(df)

# ==========================================
# 5. 위험 점수 계산
# ==========================================
# 문화재 훼손 위험도 계산
df["risk_score"] = (
    (df["합계 강수량(mm)"] * 0.4) +
    (df["평균 상대습도(%)"] * 0.3) +
    (df["최고기온(°C)"] * 0.2) +
    (abs(df["최저기온(°C)"]) * 0.1)
)

# ==========================================
# 6. 그래프 시각화
# ==========================================
st.subheader("📈 영천 기후 데이터 변화 분석 (2020~2025)")

fig, axes = plt.subplots(2, 2, figsize=(12, 8))

years = df["일시"].astype(str)

# 1. 평균기온
axes[0, 0].plot(years, df["평균기온(°C)"], marker='o')
axes[0, 0].set_title("연도별 평균기온")
axes[0, 0].set_xlabel("연도")
axes[0, 0].set_ylabel("기온 (°C)")
axes[0, 0].grid(True)

# 2. 최고기온
axes[0, 1].plot(years, df["최고기온(°C)"], marker='o')
axes[0, 1].set_title("연도별 최고기온")
axes[0, 1].set_xlabel("연도")
axes[0, 1].set_ylabel("기온 (°C)")
axes[0, 1].grid(True)

# 3. 강수량
axes[1, 0].bar(years, df["합계 강수량(mm)"])
axes[1, 0].set_title("연도별 합계 강수량")
axes[1, 0].set_xlabel("연도")
axes[1, 0].set_ylabel("강수량 (mm)")
axes[1, 0].grid(True)

# 4. 습도
axes[1, 1].plot(years, df["평균 상대습도(%)"], marker='o')
axes[1, 1].set_title("연도별 평균 상대습도")
axes[1, 1].set_xlabel("연도")
axes[1, 1].set_ylabel("습도 (%)")
axes[1, 1].grid(True)

plt.tight_layout()
st.pyplot(fig)

# ==========================================
# 7. 위험도 결과 출력
# ==========================================
st.subheader("⚠️ 연도별 문화재 훼손 위험 점수")

st.dataframe(df[["일시", "risk_score"]])

# 가장 위험한 해 찾기
most_risky = df.loc[df["risk_score"].idxmax()]

st.success(
    f"가장 위험했던 해는 {most_risky['일시']}년입니다. "
    f"(위험 점수: {most_risky['risk_score']:.2f})"
)

# ==========================================
# 8. 분석 결과 해석
# ==========================================
st.subheader("🔍 분석 결과 해석")

st.write("""
- 강수량이 많으면 문화재 표면 침식 가능성이 높아집니다.  
- 습도가 높으면 곰팡이, 이끼, 미생물 증식 위험이 커집니다.  
- 최고기온이 높으면 열팽창으로 균열이 발생할 수 있습니다.  
- 최저기온이 낮으면 동결과 융해 작용으로 손상이 심해질 수 있습니다.  
""")

import os


# ==========================================================
# 2. 데이터 불러오기 및 전처리
# ==========================================================
@st.cache_data
def load_data():
    # 파일 후보 경로 목록 (여러 가능성 대비)
    possible_paths = [
        "pages/영천_국가유산_상세_좌표보완.csv",
        "영천_국가유산_상세.csv",
        "data/영천_국가유산_상세_좌표보완.csv",
        "data/영천_국가유산_상세.csv",
        "../영천_국가유산_상세_좌표보완.csv",
        "../영천_국가유산_상세.csv",
    ]

    df = None
    for path in possible_paths:
        if os.path.exists(path):
            df = pd.read_csv(path, encoding="utf-8-sig")
            break

    if df is None:
        raise FileNotFoundError(
            "CSV 파일을 찾지 못했습니다. GitHub 저장소의 파일 이름과 경로를 확인해 주세요."
        )

    # 좌표 숫자형 변환 및 결측치 제거
    df["위도"] = pd.to_numeric(df["위도"], errors="coerce")
    df["경도"] = pd.to_numeric(df["경도"], errors="coerce")
    df = df.dropna(subset=["위도", "경도"])

    return df

import os
import re
import time
import pandas as pd
import requests
import streamlit as st

# ==========================================================
# 1. 카카오 API KEY
# ==========================================================
KAKAO_API_KEY = "4b2bd2c723594d75ace03ff0e80d65fc"

headers = {
    "Authorization": f"KakaoAK {KAKAO_API_KEY}"
}

# ==========================================================
# 2. CSV 불러오기 (pages 폴더 경로 적용)
# ==========================================================
file_path = "pages/영천_국가유산_상세.csv"

# pages 폴더에 없을 경우 기본 경로 확인
if not os.path.exists(file_path):
    file_path = "영천_국가유산_상세.csv"

if not os.path.exists(file_path):
    st.error("❌ CSV 파일을 찾을 수 없습니다. pages 폴더에 '영천_국가유산_상세.csv' 파일을 올려주세요.")
    st.stop()

df = pd.read_csv(file_path, encoding="utf-8-sig")

# ==========================================================
# 3. 수동 좌표 보정
# ==========================================================
manual_coords = {
    "임고서원은행나무": (35.9907, 128.9475),
    "임고서원 은행나무": (35.9907, 128.9475)
}

# ==========================================================
# 4. 정제 및 API 검색 함수
# ==========================================================
def clean_address(addr):
    if pd.isnull(addr):
        return None
    addr = str(addr)
    addr = re.sub(r"\(.*?\)", "", addr)
    for w in ["외", "일원", "필지", "번지"]:
        addr = addr.replace(w, "")
    return " ".join(addr.split())

def refine_name(name):
    if pd.isnull(name):
        return None
    name = str(name)
    for w in ["탱화", "유물", "일괄", "및", "구 "]:
        name = name.replace(w, "")
    return " ".join(name.split())

def get_coord_keyword(query):
    if not query:
        return None, None
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    try:
        res = requests.get(url, headers=headers, params={"query": query}, timeout=10)
        data = res.json()
        if data.get("documents"):
            x = float(data["documents"][0]["x"])
            y = float(data["documents"][0]["y"])
            return y, x
    except Exception:
        pass
    return None, None

def get_coord_address(query):
    if not query:
        return None, None
    url = "https://dapi.kakao.com/v2/local/search/address.json"
    try:
        res = requests.get(url, headers=headers, params={"query": query}, timeout=10)
        data = res.json()
        if data.get("documents"):
            x = float(data["documents"][0]["x"])
            y = float(data["documents"][0]["y"])
            return y, x
    except Exception:
        pass
    return None, None

# ==========================================================
# 5. 좌표 보완 순회
# ==========================================================
for i in df.index:
    lat = pd.to_numeric(df.loc[i, "위도"], errors="coerce")
    lon = pd.to_numeric(df.loc[i, "경도"], errors="coerce")

    if pd.notnull(lat) and pd.notnull(lon) and lat != 0 and lon != 0:
        continue

    name = str(df.loc[i, "문화재명(국문)"])
    addr = str(df.loc[i, "소재지상세"])

    new_lat, new_lon = None, None

    if name in manual_coords:
        new_lat, new_lon = manual_coords[name]
    else:
        new_lat, new_lon = get_coord_keyword(name)
        if new_lat is None:
            new_lat, new_lon = get_coord_keyword(refine_name(name))
        if new_lat is None:
            new_lat, new_lon = get_coord_address(clean_address(addr))
        if new_lat is None:
            new_lat, new_lon = get_coord_keyword("영천 " + name)
        if new_lat is None:
            new_lat, new_lon = get_coord_keyword("영천 " + refine_name(name))

    df.loc[i, "위도"] = new_lat
    df.loc[i, "경도"] = new_lon

    time.sleep(0.1)

# ==========================================================
# 6. Streamlit 화면 출력
# ==========================================================
st.title("📍 영천 국가유산 지도")
st.write(f"총 **{len(df)}**건의 데이터가 로드되었습니다.")

# 지도용 데이터 프레임 준비 (NaN 제거)
map_data = df.dropna(subset=["위도", "경도"]).copy()
map_data["latitude"] = pd.to_numeric(map_data["위도"])
map_data["longitude"] = pd.to_numeric(map_data["경도"])

# 지도 표출
st.map(map_data[["latitude", "longitude"]])

# 데이터 목록 표출
st.dataframe(df)

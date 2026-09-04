import os
import re
import time
import pandas as pd
import requests

# ==========================================================
# 1. 카카오 API KEY
# ==========================================================
KAKAO_API_KEY = "4b2bd2c723594d75ace03ff0e80d65fc"

headers = {
    "Authorization": f"KakaoAK {KAKAO_API_KEY}"
}

# ==========================================================
# 2. CSV 불러오기 (파일 존재 여부 확인)
# ==========================================================
file_name = "영천_국가유산_상세.csv"

if not os.path.exists(file_name):
    print(f"❌ '{file_name}' 파일이 현재 폴더에 없습니다!")
    print("스크립트와 같은 폴더에 CSV 파일을 위치시켜 주세요.")
    exit()

df = pd.read_csv(file_name, encoding="utf-8-sig")
print("불러온 데이터 건수:", len(df))

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
success = 0
fail = 0
fail_list = []

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

    if new_lat is not None:
        success += 1
        print(f"성공 → {name}")
    else:
        fail += 1
        fail_list.append(name)
        print(f"실패 → {name}")

    time.sleep(0.2)

print("\n==================================================")
print(f"보완 성공: {success}건 | 보완 실패: {fail}건")

# ==========================================================
# 6. 저장
# ==========================================================
save_path = "영천_국가유산_상세_좌표보완.csv"
df.to_csv(save_path, index=False, encoding="utf-8-sig")
print(f"\n저장 완료: {save_path}")

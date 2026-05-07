import streamlit as st
import pandas as pd
import folium
import re

from streamlit_folium import st_folium
from folium.plugins import HeatMap, MarkerCluster

# =================================================
# 페이지 설정
# =================================================

st.set_page_config(
    page_title="영천 문화재 공간분석",
    layout="wide"
)

st.title("🗺 영천 문화재 공간분석")

# =================================================
# 데이터 불러오기
# =================================================

df = pd.read_csv(
    "data/processed/yc_heritage_detail_enriched.csv"
)

# 컬럼 공백 제거
df.columns = df.columns.str.strip()

# =================================================
# 위경도 결측 제거
# =================================================

df = df.dropna(
    subset=["위도", "경도"]
)

# =================================================
# 시대 그룹화 함수
# =================================================

def simplify_era(text):

    if pd.isna(text):
        return "기타"

    text = str(text).strip()

    # 청동기
    if "청동기" in text:
        return "청동기"

    # 신라
    elif (
        "통일신라" in text or
        "신라시대 후기" in text
    ):
        return "통일신라"

    elif "신라" in text:
        return "신라"

    # 고려
    elif (
        "고려시대 초기" in text or
        "고려 초기" in text
    ):
        return "고려초기"

    elif (
        "고려시대 말기" in text or
        "고려 말기" in text
    ):
        return "고려후기"

    elif "고려" in text:
        return "고려"

    # 조선 초기
    elif (
        "세종" in text or
        "태조" in text or
        "태종" in text or
        "문종" in text or
        "단종" in text or
        "세조" in text or
        "성종" in text or
        "연산군" in text or
        "중종" in text or
        "인종" in text
    ):
        return "조선초기"

    # 조선 후기
    elif (
        "숙종" in text or
        "영조" in text or
        "정조" in text or
        "순조" in text or
        "철종" in text or
        "고종" in text or
        "광해군" in text
    ):
        return "조선후기"

    # 조선 직접 표기
    elif (
        "조선시대 초기" in text or
        "조선 초기" in text
    ):
        return "조선초기"

    elif (
        "조선시대 후기" in text or
        "조선 후기" in text
    ):
        return "조선후기"

    elif "조선" in text:
        return "조선"

    # 대한제국
    elif "대한제국" in text:
        return "대한제국"

    # 연도 기반 추정
    year_match = re.search(
        r"\d{4}",
        text
    )

    if year_match:

        year = int(
            year_match.group()
        )

        if year < 700:
            return "신라"

        elif year < 1400:
            return "고려"

        elif year < 1600:
            return "조선초기"

        elif year < 1910:
            return "조선후기"

    return "기타"

# =================================================
# 시대 그룹 컬럼 생성
# =================================================

df["시대그룹"] = df["시대"].apply(
    simplify_era
)

# =================================================
# 국가유산종목 결측 처리
# =================================================

if "국가유산종목" not in df.columns:

    df["국가유산종목"] = "미상"

df["국가유산종목"] = (
    df["국가유산종목"]
    .fillna("미상")
    .astype(str)
)

# =================================================
# 주소 컬럼 처리
# =================================================

if "소재지상세" not in df.columns:

    df["소재지상세"] = "-"

df["소재지상세"] = (
    df["소재지상세"]
    .fillna("-")
    .astype(str)
)

# =================================================
# 사이드바 필터
# =================================================

st.sidebar.header("🔎 문화재 필터")

# -------------------------------------------------
# 시대 순서
# -------------------------------------------------

era_order = [
    "청동기",
    "신라",
    "통일신라",
    "고려초기",
    "고려",
    "고려후기",
    "조선초기",
    "조선",
    "조선후기",
    "대한제국",
    "기타"
]

existing_eras = [
    era for era in era_order
    if era in df["시대그룹"].unique()
]

era_options = ["전체"] + existing_eras

# -------------------------------------------------
# 시대 필터
# -------------------------------------------------

selected_era = st.sidebar.selectbox(
    "시대",
    era_options
)

# -------------------------------------------------
# 국가유산종목 필터
# -------------------------------------------------

type_options = [
    "전체"
] + sorted(
    df["국가유산종목"]
    .unique()
    .tolist()
)

selected_type = st.sidebar.selectbox(
    "국가유산종목",
    type_options
)

# =================================================
# 필터 적용
# =================================================

filtered_df = df.copy()

if selected_era != "전체":

    filtered_df = filtered_df[
        filtered_df["시대그룹"]
        == selected_era
    ]

if selected_type != "전체":

    filtered_df = filtered_df[
        filtered_df["국가유산종목"]
        == selected_type
    ]

# =================================================
# 검색 결과 표시 (위쪽으로 이동)
# =================================================

st.sidebar.info(
    f"🏛 검색된 문화재: {len(filtered_df)}개"
)

# =================================================
# 결과 없을 경우
# =================================================

if len(filtered_df) == 0:

    st.warning(
        "조건에 맞는 문화재가 없습니다."
    )

    st.stop()

# =================================================
# 선택 문화재 상태
# =================================================

if "selected_heritage" not in st.session_state:

    st.session_state.selected_heritage = (
        filtered_df.iloc[0]["문화재명(국문)"]
    )

# =================================================
# 선택 문화재 데이터
# =================================================

selected_row = filtered_df[
    filtered_df["문화재명(국문)"]
    == st.session_state.selected_heritage
].iloc[0]

# =================================================
# 레이아웃
# =================================================

map_col, list_col = st.columns(
    [4, 1]
)

# =================================================
# 지도 영역
# =================================================

with map_col:

    center = [
        selected_row["위도"],
        selected_row["경도"]
    ]

    # -------------------------------------------------
    # 지도 생성
    # -------------------------------------------------

    m = folium.Map(
        location=center,
        zoom_start=13,
        tiles="CartoDB positron"
    )

    # -------------------------------------------------
    # 마커 클러스터
    # -------------------------------------------------

    marker_cluster = MarkerCluster().add_to(m)

    # -------------------------------------------------
    # 마커 생성
    # -------------------------------------------------

    for idx, row in filtered_df.iterrows():

        heritage_name = row.get(
            "문화재명(국문)",
            "문화재"
        )

        image_url = str(
            row.get("이미지URL", "")
        ).strip()

        image_url = image_url.replace(
            "http://",
            "https://"
        )

        # ---------------------------------------------
        # 이미지 html
        # ---------------------------------------------

        if (
            image_url == ""
            or image_url.lower() == "nan"
        ):

            image_html = """
            <div style="
                width:320px;
                height:220px;
                background:#f2f2f2;
                border-radius:12px;
                display:flex;
                justify-content:center;
                align-items:center;
                color:#777;
                margin:auto;
            ">
                이미지 없음
            </div>
            """

        else:

            image_html = f"""
            <div style="text-align:center;">

                <a href="{image_url}" target="_blank">

                    <img
                        src="{image_url}"

                        style="
                            width:320px;
                            height:220px;
                            object-fit:cover;
                            border-radius:12px;
                            box-shadow:0 2px 8px rgba(0,0,0,0.2);
                        "
                    >

                </a>

            </div>
            """

        # ---------------------------------------------
        # popup html
        # ---------------------------------------------

        popup_html = f"""
        <div style="
            width:340px;
            padding:15px;
            text-align:center;
            font-family:sans-serif;
        ">

            <h2 style="
                margin-bottom:15px;
                color:#222;
            ">
                {heritage_name}
            </h2>

            {image_html}

            <br>

            <table style="
                width:85%;
                margin:auto;
                font-size:15px;
                line-height:2;
                text-align:left;
            ">

                <tr>
                    <td><b>시대</b></td>
                    <td>{row.get("시대그룹", "-")}</td>
                </tr>

                <tr>
                    <td><b>종목</b></td>
                    <td>{row.get("국가유산종목", "-")}</td>
                </tr>

                <tr>
                    <td><b>주소</b></td>
                    <td>{row.get("소재지상세", "-")}</td>
                </tr>

            </table>

        </div>
        """

        # ---------------------------------------------
        # iframe popup
        # ---------------------------------------------

        iframe = folium.IFrame(
            html=popup_html,
            width=380,
            height=520
        )

        popup = folium.Popup(
            iframe,
            max_width=420
        )

        # ---------------------------------------------
        # 선택 마커 색상
        # ---------------------------------------------

        marker_color = "blue"

        if (
            heritage_name
            == st.session_state.selected_heritage
        ):

            marker_color = "red"

        # ---------------------------------------------
        # marker
        # ---------------------------------------------

        folium.Marker(
            location=[
                row["위도"],
                row["경도"]
            ],

            popup=popup,

            tooltip=heritage_name,

            icon=folium.Icon(
                color=marker_color,
                icon="info-sign"
            )

        ).add_to(marker_cluster)

    # -------------------------------------------------
    # HeatMap
    # -------------------------------------------------

    heat_data = filtered_df[
        ["위도", "경도"]
    ].values.tolist()

    HeatMap(
        heat_data,
        radius=20,
        blur=15
    ).add_to(m)

    # -------------------------------------------------
    # 지도 출력
    # -------------------------------------------------

    st_folium(
        m,
        width=1100,
        height=750
    )

# =================================================
# 오른쪽 문화재 목록
# =================================================

with list_col:

    st.markdown(
        "## 🏛 문화재 목록"
    )

    st.markdown("---")

    for idx, row in filtered_df.iterrows():

        heritage_name = row.get(
            "문화재명(국문)",
            "문화재"
        )

        address = row.get(
            "소재지상세",
            "-"
        )

        selected = (
            heritage_name
            == st.session_state.selected_heritage
        )

        # ---------------------------------------------
        # 선택 시 스타일 변경
        # ---------------------------------------------

        bg_color = "#ffe4e1" if selected else "#f8f9fa"
        border = "2px solid #ff4b4b" if selected else "1px solid #ddd"

        if st.button(
            heritage_name,
            key=f"heritage_{idx}",
            use_container_width=True
        ):

            st.session_state.selected_heritage = heritage_name

            st.rerun()

        st.markdown(
            f'''
            <div style="
                background:{bg_color};
                border:{border};
                border-radius:10px;
                padding:10px;
                margin-bottom:15px;
                text-align:left;
            ">

                <div style="
                    font-weight:bold;
                    font-size:15px;
                    margin-bottom:6px;
                ">
                    {heritage_name}
                </div>

                <div style="
                    font-size:13px;
                    color:#666;
                    line-height:1.5;
                ">
                    📍 {address}
                </div>

            </div>
            ''',
            unsafe_allow_html=True
        )

import streamlit as st
import pandas as pd
import google.generativeai as genai

# =====================================================
# 페이지 설정
# =====================================================
st.set_page_config(
    page_title="영천 AI 문화재 해설사",
    page_icon="🤖",
    layout="wide"
)

# =====================================================
# Gemini API 설정
# =====================================================
# Streamlit Secrets에서 API 키를 안전하게 가져옵니다.
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    # 모델 설정 (기존 2.5-flash가 인식 안될 경우 1.5-flash 권장)
    model = genai.GenerativeModel("gemini-1.5-flash")
else:
    st.error("API 키가 설정되지 않았습니다. .streamlit/secrets.toml 파일을 확인하세요.")

# =====================================================
# 데이터 로드 및 전처리
# =====================================================
@st.cache_data
def load_data():
    # 데이터 경로를 본인의 환경에 맞게 수정하세요.
    return pd.read_csv("data/processed/yc_heritage_detail_enriched.csv")

def clean(val):
    if pd.isna(val) or str(val).strip() == "":
        return "-"
    return str(val).strip()

# =====================================================
# 메인 로직
# =====================================================
try:
    df = load_data()
    
    # 세션 상태 관리
    if "prev_category" not in st.session_state:
        st.session_state.prev_category = None

    # 타이틀
    st.title("🤖 AI 문화재 해설 가이드")
    st.markdown("---")

    # 1. 선택 영역
    category_col = "종목" if "종목" in df.columns else "국가유산종목"
    
    col_sel1, col_sel2 = st.columns(2)
    with col_sel1:
        category = st.selectbox("📂 문화재 품목 선택", sorted(df[category_col].dropna().unique()))
    
    filtered_df = df[df[category_col] == category]
    
    with col_sel2:
        heritage = st.selectbox("🏛 문화재 선택", filtered_df["문화재명(국문)"])

    row = filtered_df[filtered_df["문화재명(국문)"] == heritage].iloc[0]

    # 2. 상단 문화재 제목 디자인
    st.markdown(f"""
        <div style="background-color:#f8f9fa; padding:15px; border-radius:15px; text-align:center; margin-bottom:20px; border:1px solid #e9ecef;">
            <h1 style="margin:0; color:#2c3e50; font-size:28px;">🏛 {heritage}</h1>
        </div>
    """, unsafe_allow_html=True)

    # 3. 본문 레이아웃 (이미지 및 상세 정보)
    left_col, right_col = st.columns([1, 1.2], gap="large")

    with left_col:
        image_url = row.get("이미지URL")
        if pd.notna(image_url) and str(image_url).strip() != "":
            st.image(image_url, use_container_width=True)
            st.caption(f"출처: 국가유산청 - {heritage}")
        else:
            st.info("🖼 등록된 이미지가 없습니다.")

    with right_col:
        st.markdown("<h3 style='margin-top:0;'>📋 상세 정보</h3>", unsafe_allow_html=True)
        
        # --- [수정 포인트] 상세 정보를 깔끔하게 정렬하는 HTML 테이블 ---
        info_data = {
            "종목": clean(row.get(category_col)),
            "분류": f"{clean(row.get('국가유산분류'))} ({clean(row.get('국가유산분류2'))})",
            "한자명": clean(row.get("문화재명(한자)")),
            "시대": clean(row.get("시대")),
            "소재지": clean(row.get("소재지상세")),
            "소유/관리": f"{clean(row.get('소유자'))} / {clean(row.get('관리자'))}"
        }

        info_html = """
        <style>
            .info-table { width: 100%; border-collapse: collapse; margin-bottom: 10px; }
            .info-tr { border-bottom: 1px solid #f0f0f0; }
            .info-td-key { 
                width: 25%; padding: 10px 5px; font-weight: bold; color: #2c3e50; 
                background-color: #f8f9fa; font-size: 15px; vertical-align: top;
            }
            .info-td-val { 
                width: 75%; padding: 10px 10px; color: #444; 
                font-size: 15px; line-height: 1.5; vertical-align: top;
            }
        </style>
        <table class="info-table">
        """
        for key, val in info_data.items():
            info_html += f"""
            <tr class="info-tr">
                <td class="info-td-key">{key}</td>
                <td class="info-td-val">{val}</td>
            </tr>
            """
        info_html += "</table>"
        st.markdown(info_html, unsafe_allow_html=True)
        
        # 상세 설명은 별도 영역으로 배분
        with st.expander("📖 원문 설명 보기", expanded=True):
            st.write(clean(row.get("내용")))

    # 4. AI 도슨트 기능 섹션
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.divider()
    st.header("🤖 AI 스마트 도슨트")
    
    col_ai1, col_ai2 = st.columns(2)
    
    with col_ai1:
        if st.button("✨ AI 도슨트 해설 생성"):
            with st.spinner("해설을 구성 중입니다..."):
                prompt = f"당신은 전문 도슨트입니다. {heritage}에 대해 {clean(row.get('내용'))}을 바탕으로 흥미로운 해설을 작성해주세요."
                response = model.generate_content(prompt)
                st.info(response.text)
                
    with col_ai2:
        user_q = st.text_input("💬 문화재에 대해 궁금한 점을 물어보세요")
        if st.button("질문하기"):
            if user_q:
                with st.spinner("AI가 답변을 생각 중입니다..."):
                    q_prompt = f"문화재 {heritage}에 대한 질문: {user_q}. 설명: {clean(row.get('내용'))}. 친절히 답해줘."
                    res = model.generate_content(q_prompt)
                    st.success(res.text)

except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")

```python
import streamlit as st
import pandas as pd
import numpy as np

# ---------------------------------------------------
# 페이지 설정
# ---------------------------------------------------

st.set_page_config(
    page_title="문화재 환경 위험도 예측",
    layout="wide"
)

# ---------------------------------------------------
# 제목
# ---------------------------------------------------

st.title("🏛 문화재 환경 위험도 예측 시스템")

st.markdown("""
환경 데이터를 기반으로  
문화재 훼손 위험도를 분석하는 시스템입니다.

### 사용 환경 데이터
- 온도
- 상대습도
- 빛 노출
""")

st.markdown("---")

# ---------------------------------------------------
# 탭 구성
# ---------------------------------------------------

tab1, tab2, tab3 = st.tabs([
    "📚 문화재 기준",
    "🌎 위험도 예측",
    "📊 환경 분석 결과"
])

# ---------------------------------------------------
# 문화재 기준
# ---------------------------------------------------

with tab1:

    st.header("📚 문화재별 보존 환경 기준")

    col1, col2, col3 = st.columns(3)

    # 금속 문화재
    with col1:

        st.markdown("""
        ### 🛡 금속 문화재

        - 적정 온도 : 15-25°C
        - 적정 습도 : 35-55%

        ⚠ 상대습도 65% 이상 시  
        부식 속도가 급격히 증가합니다.
        """)

    # 지류 문화재
    with col2:

        st.markdown("""
        ### 📜 지류 문화재

        - 적정 온도 : 18-22°C
        - 적정 습도 : 45-55%

        ⚠ 높은 습도와 빛 노출 시  
        황변 및 강도 저하가 발생합니다.
        """)

    # 목재 문화재
    with col3:

        st.markdown("""
        ### 🪵 목재 문화재

        - 적정 온도 : 18-22°C
        - 적정 습도 : 50-60%

        ⚠ 상대습도 65% 이상 시  
        곰팡이 및 해충 발생 위험 증가
        """)

# ---------------------------------------------------
# 위험도 예측
# ---------------------------------------------------

with tab2:

    st.header("🌎 환경 기반 위험도 예측")

    st.markdown("""
    환경 데이터를 입력하면  
    문화재 훼손 위험도를 예측합니다.
    """)

    # 문화재 종류 선택
    artifact_type = st.selectbox(
        "문화재 종류 선택",
        [
            "금속 문화재",
            "지류 문화재",
            "목재 문화재"
        ]
    )

    st.markdown("---")

    # 환경 데이터 입력
    col1, col2 = st.columns(2)

    with col1:

        temperature = st.slider(
            "🌡 온도 (°C)",
            0,
            40,
            20
        )

        humidity = st.slider(
            "💧 상대습도 (%)",
            0,
            100,
            50
        )

    with col2:

        light = st.slider(
            "💡 빛 노출 정도",
            0,
            100,
            30
        )

    st.markdown("---")

    # 위험도 계산
    risk_score = 0

    # 금속 문화재
    if artifact_type == "금속 문화재":

        if temperature < 15 or temperature > 25:
            risk_score += 20

        if humidity >= 65:
            risk_score += 60

        elif humidity > 55:
            risk_score += 30

    # 지류 문화재
    elif artifact_type == "지류 문화재":

        if temperature < 18 or temperature > 22:
            risk_score += 20

        if humidity > 55:
            risk_score += 40

        if light > 70:
            risk_score += 40

        elif light > 40:
            risk_score += 20

    # 목재 문화재
    elif artifact_type == "목재 문화재":

        if temperature < 18 or temperature > 22:
            risk_score += 20

        if humidity >= 65:
            risk_score += 60

        elif humidity > 60:
            risk_score += 30

    # ---------------------------------------------------
    # 위험도 분류
    # ---------------------------------------------------

    if risk_score < 30:

        risk_level = "안전"

    elif risk_score < 70:

        risk_level = "주의"

    else:

        risk_level = "위험"

    # ---------------------------------------------------
    # 결과 출력
    # ---------------------------------------------------

    st.subheader("📌 예측 결과")

    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "위험도 점수",
            f"{risk_score}점"
        )

    with col2:

        if risk_level == "안전":

            st.success(f"🟢 {risk_level}")

        elif risk_level == "주의":

            st.warning(f"🟡 {risk_level}")

        else:

            st.error(f"🔴 {risk_level}")

    st.markdown("---")

    # 상세 설명
    st.subheader("📖 환경 분석 설명")

    if artifact_type == "금속 문화재":

        if humidity >= 65:

            st.error("""
            상대습도가 65% 이상입니다.

            금속 표면의 부식 반응이 빠르게 증가할 수 있습니다.
            """)

        else:

            st.success("""
            현재 환경은 비교적 안정적인 상태입니다.
            """)

    elif artifact_type == "지류 문화재":

        if humidity > 55:

            st.warning("""
            높은 습도로 인해 황변과 강도 저하 가능성이 있습니다.
            """)

        if light > 40:

            st.warning("""
            빛 노출이 증가하면 종이 손상이 가속화됩니다.
            """)

    elif artifact_type == "목재 문화재":

        if humidity >= 65:

            st.error("""
            습도가 매우 높습니다.

            곰팡이 및 해충 발생 위험이 증가할 수 있습니다.
            """)

        else:

            st.success("""
            현재 환경은 비교적 안정적인 상태입니다.
            """)

# ---------------------------------------------------
# 분석 결과 시각화
# ---------------------------------------------------

with tab3:

    st.header("📊 환경 분석 결과")

    chart_data = pd.DataFrame({

        "환경요인": [
            "온도",
            "습도",
            "빛 노출"
        ],

        "입력값": [
            temperature,
            humidity,
            light
        ]

    })

    st.bar_chart(
        chart_data.set_index("환경요인")
    )

    st.markdown("---")

    st.subheader("📈 위험도 기준")

    risk_table = pd.DataFrame({

        "위험도": [
            "안전",
            "주의",
            "위험"
        ],

        "점수 범위": [
            "0-29",
            "30-69",
            "70 이상"
        ]

    })

    st.table(risk_table)

# ---------------------------------------------------
# footer
# ---------------------------------------------------

st.markdown("---")

st.markdown("""

### 👨‍💻 프로젝트 정보

- 프로젝트명 : 문화재 환경 위험도 예측 시스템
- 분석 요소
    - 온도
    - 상대습도
    - 빛 노출

- 분석 대상
    - 금속 문화재
    - 지류 문화재
    - 목재 문화재

""")
```

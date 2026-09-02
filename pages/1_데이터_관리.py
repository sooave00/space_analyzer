"""데이터 관리 - 원본 데이터 갱신 현황판 + 갱신 흐름(팝업).

실행: streamlit run app.py (사이드바에서 "데이터 관리" 페이지로 이동)
"""

import json
import os
import re
from datetime import date, datetime, timedelta

import streamlit as st

from ingest.build_population import load_and_clean as load_clean_population
from ingest.build_population import save_processed as save_population

DATA_STATUS_PATH = "data/processed/data_status.json"

CYCLE_LABELS = {"monthly": "1개월", "biannual": "6개월", "yearly": "1년"}
CYCLE_DAYS = {"monthly": 30, "biannual": 182, "yearly": 365}

st.set_page_config(page_title="데이터 관리", layout="wide")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Nanum+Myeongjo:wght@400;700;800&family=Noto+Sans+KR:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Noto Sans KR', sans-serif;
    }

    .block-container {
        padding-top: 3rem;
        padding-bottom: 4rem;
    }

    h1, h2, h3 {
        font-family: 'Nanum Myeongjo', serif !important;
        color: #4A4238 !important;
    }

    .app-title {
        font-family: 'Nanum Myeongjo', serif;
        font-size: 2.6rem;
        font-weight: 700;
        color: #4A4238;
        letter-spacing: 0.02em;
        line-height: 1.3;
        margin-bottom: 0.3rem;
    }
    .app-subtitle {
        font-family: 'Noto Sans KR', sans-serif;
        font-weight: 300;
        color: #A79C8E;
        font-size: 1rem;
        letter-spacing: 0.04em;
        line-height: 1.5;
        margin-bottom: 2rem;
    }

    .status-card {
        border-radius: 20px;
        padding: 22px 24px;
        box-shadow: 0 8px 22px rgba(168, 213, 226, 0.28);
        margin-bottom: 0.8rem;
        min-height: 168px;
    }
    .status-fresh {
        background: linear-gradient(135deg, #EFF5EE 0%, #E3EDE0 100%);
        border: 1px solid #D6E6D2;
    }
    .status-stale {
        background: linear-gradient(135deg, #FBEAE9 0%, #F6D6D4 100%);
        border: 2px solid #D9534F;
    }
    .status-name {
        font-family: 'Nanum Myeongjo', serif;
        font-size: 1.3rem;
        font-weight: 700;
        color: #4A4238;
        margin-bottom: 6px;
    }
    .status-meta {
        font-family: 'Noto Sans KR', sans-serif;
        font-size: 0.9rem;
        color: #8A8178;
        margin-bottom: 4px;
    }
    .status-badge {
        font-family: 'Noto Sans KR', sans-serif;
        font-weight: 700;
        font-size: 0.95rem;
        margin-top: 8px;
    }
    .status-fresh .status-badge { color: #5C8A6B; }
    .status-stale .status-badge { color: #C0392B; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="app-title">데이터 관리</div>
    <div class="app-subtitle">원본 데이터가 언제 적용됐고, 갱신이 필요한지 한눈에 확인</div>
    """,
    unsafe_allow_html=True,
)


def load_data_status(path=DATA_STATUS_PATH):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"파일을 찾을 수 없습니다: {path}")
        return []
    except json.JSONDecodeError as e:
        st.error(f"data_status.json 형식이 잘못됐습니다: {e}")
        return []


def update_status_entry(name, path=DATA_STATUS_PATH, **fields):
    """data_status.json에서 이름이 일치하는 항목의 필드를 갱신해서 저장한다."""
    with open(path, encoding="utf-8") as f:
        items = json.load(f)
    for item in items:
        if item["데이터명"] == name:
            item.update(fields)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


def update_population(base_ym, uploaded_file):
    """업로드된 인구 CSV를 저장 → 정제 → data_status.json 갱신까지 처리한다.

    반환: {"success": True} 또는 {"success": False, "error": "..."}
    """
    if not re.fullmatch(r"\d{6}", base_ym):
        return {"success": False, "error": "기준연월은 YYYYMM 형식(예: 202609)으로 입력해주세요."}

    raw_path = f"data/raw/population_{base_ym}.csv"
    try:
        os.makedirs(os.path.dirname(raw_path), exist_ok=True)
        with open(raw_path, "wb") as f:
            f.write(uploaded_file.getvalue())
    except OSError as e:
        return {"success": False, "error": f"파일을 저장하는 중 오류가 발생했습니다: {e}"}

    try:
        df = load_clean_population(base_ym)
    except Exception:
        df = None

    if df is None or df.empty:
        return {
            "success": False,
            "error": (
                f"업로드한 파일을 정제하는 데 실패했습니다. "
                f"기준연월({base_ym})이 실제 파일 내용과 맞는지, "
                f"CSV 형식(cp949 인코딩, 컬럼 구성)이 올바른지 확인해주세요."
            ),
        }

    save_population(df)

    today_str = date.today().strftime("%Y-%m-%d")
    update_status_entry("인구", 기준연월=base_ym, 적용일자=today_str)

    return {"success": True}


@st.dialog("데이터 갱신", width="large")
def open_update_dialog(item):
    name = item["데이터명"]
    st.markdown(f"### {name}")

    st.markdown("**1단계 · 최신 데이터 받기**")
    st.markdown(item.get("download_guide", "안내가 등록되어 있지 않습니다."))
    st.link_button("📥 사이트 열기", item["다운로드URL"])

    st.divider()
    st.markdown("**2단계 · 받은 파일 올리기**")

    if name != "인구":
        st.info("이 데이터는 아직 자동 정제가 연결되지 않았습니다. (다음 단계에서 추가 예정)")
        return

    default_ym = date.today().strftime("%Y%m")
    base_ym = st.text_input(
        "기준연월 (YYYYMM) - 업로드한 파일이 다루는 연월을 확인해주세요",
        value=default_ym,
        key="population_base_ym",
    )
    uploaded = st.file_uploader("CSV 파일 업로드", type="csv", key="population_upload")

    if uploaded is not None:
        if st.button("갱신 실행", type="primary", key="population_run"):
            with st.spinner("업로드한 파일로 데이터를 갱신하는 중..."):
                result = update_population(base_ym, uploaded)

            if result["success"]:
                st.success(f"✓ 갱신 완료! ({base_ym[:4]}년 {base_ym[4:]}월 기준으로 업데이트됨)")
                if st.button("닫기", key="population_close"):
                    st.rerun()
            else:
                st.error(result["error"])


items = load_data_status()

if not items:
    st.info("등록된 데이터 현황이 없습니다.")
else:
    today = date.today()
    cols = st.columns(3)

    for i, item in enumerate(items):
        applied_date = datetime.strptime(item["적용일자"], "%Y-%m-%d").date()
        cycle = item["갱신주기"]
        cycle_days = CYCLE_DAYS.get(cycle, 365)
        due_date = applied_date + timedelta(days=cycle_days)
        is_stale = today >= due_date

        year_month = f"{item['기준연월'][:4]}년 {item['기준연월'][4:]}월"
        badge = "⚠️ 갱신 권장" if is_stale else "✓ 최신"
        card_class = "status-stale" if is_stale else "status-fresh"

        col = cols[i % 3]
        col.markdown(
            f"""
            <div class="status-card {card_class}">
                <div class="status-name">{item['데이터명']}</div>
                <div class="status-meta">기준연월: {year_month}</div>
                <div class="status-meta">적용일: {item['적용일자']}</div>
                <div class="status-meta">갱신주기: {CYCLE_LABELS.get(cycle, cycle)}</div>
                <div class="status-badge">{badge}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if is_stale:
            if col.button("🔄 갱신하기", key=f"update_btn_{item['데이터명']}", use_container_width=True):
                open_update_dialog(item)

    st.caption(
        "※ 적용일자 + 갱신주기가 오늘보다 지나면 '갱신 권장'으로 표시됩니다. "
        "갱신하기 → 파일 업로드까지 완료하면 자동으로 최신 상태가 됩니다."
    )

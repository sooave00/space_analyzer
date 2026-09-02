"""생활권 분석 도구 - 첫 Streamlit 화면.

실행: streamlit run app.py
"""

import math

import folium
import streamlit as st
from streamlit_folium import st_folium

from analysis.area_profile import (
    get_facilities_in_circle,
    get_libraries_in_circle,
    get_living_area_population,
)
from analysis.living_area import calc_radius_km, get_dong_geometries, get_dongs_in_circle
from services.kakao_service import find_location

st.set_page_config(page_title="생활권 분석 도구", layout="wide")

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

    div[data-testid="stTextInput"] input {
        border-radius: 14px !important;
        border: 1px solid #E7DFD3 !important;
        padding: 10px 16px !important;
    }

    .stButton > button {
        background-color: #A8D5E2;
        color: #3E5C63;
        border: none;
        border-radius: 14px;
        padding: 0.5rem 1.6rem;
        font-weight: 600;
        box-shadow: 0 4px 12px rgba(168, 213, 226, 0.4);
    }
    .stButton > button:hover {
        background-color: #96CBDA;
        color: #2E464C;
    }

    div[data-testid="stAlert"] {
        border-radius: 16px;
    }

    .kpi-card {
        border-radius: 20px;
        padding: 28px 18px;
        text-align: center;
        box-shadow: 0 8px 22px rgba(168, 213, 226, 0.28);
        margin-bottom: 1.2rem;
    }
    .kpi-blue {
        background: linear-gradient(135deg, #EAF5F8 0%, #DCEEF3 100%);
        border: 1px solid #CDE7EE;
    }
    .kpi-pink {
        background: linear-gradient(135deg, #FBF0F0 0%, #F5E2E2 100%);
        border: 1px solid #F0D9D9;
    }
    .kpi-label {
        font-family: 'Noto Sans KR', sans-serif;
        font-size: 0.9rem;
        font-weight: 500;
        color: #8A8178;
        margin-bottom: 10px;
        letter-spacing: 0.02em;
    }
    .kpi-value {
        font-family: 'Nanum Myeongjo', serif;
        font-size: 2.1rem;
        font-weight: 700;
        line-height: 1.2;
    }
    .kpi-green {
        background: linear-gradient(135deg, #EFF5EE 0%, #E3EDE0 100%);
        border: 1px solid #D6E6D2;
    }
    .kpi-amber {
        background: linear-gradient(135deg, #F7F0E6 0%, #F0E4D0 100%);
        border: 1px solid #E8D5B7;
    }
    .kpi-blue .kpi-value { color: #3E7C91; }
    .kpi-pink .kpi-value { color: #C97B8E; }
    .kpi-green .kpi-value { color: #5C8A6B; }
    .kpi-amber .kpi-value { color: #A97C50; }
    .kpi-unit {
        font-family: 'Noto Sans KR', sans-serif;
        font-size: 1.05rem;
        font-weight: 400;
        margin-left: 2px;
    }

    @media (max-width: 640px) {
        div[data-testid="stHorizontalBlock"] {
            flex-direction: column;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="app-title">생활권 분석 도구</div>
    <div class="app-subtitle">걷고 머무는 시간으로 그려보는, 우리 동네의 반경</div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.subheader("위치 검색")

    address = st.text_input("기준 주소 또는 장소명을 입력하세요", value="포항시청")

    if st.button("검색"):
        try:
            result = find_location(address)
        except Exception as e:
            st.error(f"검색 중 오류가 발생했습니다: {e}")
            result = None

        if result:
            candidates, method = result
            st.session_state["candidates"] = candidates
            st.session_state["search_method"] = method
            st.session_state.pop("selected_place", None)
        else:
            st.session_state["candidates"] = None
            st.warning("위치를 찾을 수 없습니다. 다른 주소나 장소명을 입력해보세요")

    candidates = st.session_state.get("candidates")
    selected = None

    if candidates:
        method = st.session_state.get("search_method", "")

        if len(candidates) == 1:
            selected = candidates[0]
        else:
            options = [f"{name} ({addr})" for name, addr, _lat, _lon in candidates]
            chosen = st.radio(
                "여러 곳이 검색되었습니다. 선택하세요",
                options,
                key="selected_place",
            )
            selected = candidates[options.index(chosen)]

        name, addr, lat, lon = selected
        st.success(f"[{method}] {name} ({addr}) - 위도: {lat}, 경도: {lon}")

if selected:
    name, addr, lat, lon = selected

    st.subheader("N분 생활권")
    control_col1, control_col2 = st.columns([1, 2])
    minutes = control_col1.radio(
        "이동시간", [10, 20, 30], index=1, format_func=lambda m: f"{m}분",
        key="living_area_minutes", horizontal=True,
    )
    speed_kmh = control_col2.slider(
        "평균 속도 (km/h)",
        min_value=20,
        max_value=50,
        value=30,
        key="living_area_speed",
        help="직선거리 환산용 평균 속도",
    )
    radius_km = calc_radius_km(speed_kmh, minutes)

    dongs = get_dongs_in_circle(lat, lon, radius_km)
    dong_geometries = get_dong_geometries(dongs["ADM_CD"].tolist())
    facilities = get_facilities_in_circle(lat, lon, radius_km)
    libraries_nearby = get_libraries_in_circle(lat, lon, radius_km)

    m = folium.Map(location=[lat, lon], zoom_start=13)

    # 외부 CDN 이미지에 의존하지 않도록 순수 CSS로 그리는 마커 (기본 아이콘은 이미지 로드 실패 시 깨져 보임)
    center_icon = folium.DivIcon(
        html=(
            '<div style="'
            "width: 20px; height: 20px;"
            "background-color: #C97B8E;"
            "border: 3px solid #FAF7F2;"
            "border-radius: 50%;"
            'box-shadow: 0 2px 8px rgba(0,0,0,0.35);"></div>'
        ),
        icon_size=(20, 20),
        icon_anchor=(10, 10),
    )
    folium.Marker(
        [lat, lon],
        tooltip=name,
        popup=folium.Popup(name, max_width=300),
        icon=center_icon,
    ).add_to(m)
    folium.Circle(
        location=[lat, lon],
        radius=radius_km * 1000,
        color="blue",
        fill=True,
        fill_opacity=0.2,
        tooltip=f"직선거리 기준 약 {radius_km:.1f} km 범위",
    ).add_to(m)

    if not dong_geometries.empty:
        folium.GeoJson(
            dong_geometries,
            style_function=lambda _feature: {
                "fillColor": "orange",
                "color": "orange",
                "weight": 1,
                "fillOpacity": 0.25,
            },
            tooltip=folium.GeoJsonTooltip(fields=["ADM_NM"], aliases=["행정동"]),
        ).add_to(m)

    school_colors = {"초등학교": "#4C9A8E", "중학교": "#7B6FA8", "고등학교": "#C97B4A"}
    for _, school in facilities["schools"].iterrows():
        folium.CircleMarker(
            location=[school["lat"], school["lon"]],
            radius=5,
            color=school_colors.get(school["school_level"], "#8A8178"),
            fill=True,
            fill_opacity=0.85,
            weight=1,
            tooltip=school["school_name"],
        ).add_to(m)

    # 도서관은 학교(원형 점)와 구분되도록 각진 모양으로 표시
    library_colors = {"주요도서관": "#B08968", "작은도서관": "#D4A657", "기타": "#8A8178"}
    for _, library in libraries_nearby["libraries"].iterrows():
        color = library_colors.get(library["group"], "#8A8178")
        icon_html = (
            '<div style="'
            "width: 14px; height: 14px;"
            f"background-color: {color};"
            'border: 2px solid #FAF7F2;'
            "border-radius: 4px;"
            'box-shadow: 0 1px 4px rgba(0,0,0,0.35);"></div>'
        )
        folium.Marker(
            location=[library["lat"], library["lon"]],
            tooltip=library["library_name"],
            icon=folium.DivIcon(html=icon_html, icon_size=(14, 14), icon_anchor=(7, 7)),
        ).add_to(m)

    # 반경이 화면에 딱 맞게 보이도록 위도/경도 범위를 계산해서 자동 줌 조정
    delta_lat = radius_km / 111
    delta_lon = radius_km / (111 * math.cos(math.radians(lat)))
    bounds = [[lat - delta_lat, lon - delta_lon], [lat + delta_lat, lon + delta_lon]]
    m.fit_bounds(bounds)

    st_folium(m, height=420, use_container_width=True)
    st.caption(f"📍 직선거리 기준 약 {radius_km:.1f} km 범위 (실제 도로 이동거리와 다를 수 있음)")
    st.caption("🟢 초등학교 · 🟣 중학교 · 🟠 고등학교 　 🟤 공공·어린이도서관 · 🟡 작은도서관 (■ 사각형)")

    st.subheader("생활권 인구")

    profile = get_living_area_population(dongs)
    child_ratio = profile["age_0_9"] / profile["total"] * 100 if profile["total"] else 0

    def kpi_card(col, label, value, unit, accent):
        col.markdown(
            f"""
            <div class="kpi-card kpi-{accent}">
                <div class="kpi-label">{label}</div>
                <div class="kpi-value">{value}<span class="kpi-unit">{unit}</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    row1_col1, row1_col2, row1_col3 = st.columns(3)
    kpi_card(row1_col1, "총인구", f"{profile['total']:,}", "명", "blue")
    kpi_card(row1_col2, "0~9세 (어린이)", f"{profile['age_0_9']:,}", "명", "pink")
    kpi_card(row1_col3, "어린이 비율", f"{child_ratio:.1f}", "%", "pink")

    row2_col1, row2_col2 = st.columns(2)
    kpi_card(row2_col1, "10~14세", f"{profile['age_10_14']:,}", "명", "blue")
    kpi_card(row2_col2, "30~49세 (가족수요층)", f"{profile['age_30_49']:,}", "명", "blue")

    st.caption("※ 30~49세는 가족수요층 대리지표이며 실제 부모를 의미하지 않음")

    if profile["unmatched"]:
        st.warning(
            f"일부 동은 최근 행정구역 개편으로 인구 데이터 미포함 ({len(profile['unmatched'])}개)"
        )

    st.subheader("생활권 교육시설")

    counts = facilities["counts"]
    edu_col1, edu_col2, edu_col3 = st.columns(3)
    kpi_card(edu_col1, "초등학교", f"{counts['초등학교']}", "개", "green")
    kpi_card(edu_col2, "중학교", f"{counts['중학교']}", "개", "green")
    kpi_card(edu_col3, "고등학교", f"{counts['고등학교']}", "개", "green")

    st.subheader("생활권 문화시설")

    library_counts = libraries_nearby["counts"]
    culture_col1, culture_col2 = st.columns(2)
    kpi_card(culture_col1, "공공·어린이도서관", f"{library_counts['주요도서관']}", "개", "amber")
    kpi_card(culture_col2, "작은도서관", f"{library_counts['작은도서관']}", "개", "amber")

    st.subheader(f"생활권 포함 행정동 (총 {len(dongs)}개)")
    if dongs.empty:
        st.info("반경 안에 포함된 행정동이 없습니다.")
    else:
        table = dongs.rename(columns={"ADM_NM": "행정동명", "distance_km": "거리(km)"})[
            ["행정동명", "거리(km)"]
        ]
        table.insert(0, "순번", range(1, len(table) + 1))
        table["거리(km)"] = table["거리(km)"].round(2)
        st.dataframe(table, hide_index=True, use_container_width=True)
else:
    st.info("왼쪽 사이드바에서 기준 주소나 장소명을 검색해주세요.")

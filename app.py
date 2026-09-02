"""생활권 분석 도구 - 첫 Streamlit 화면.

실행: streamlit run app.py
"""

import math

import folium
import streamlit as st
from folium.plugins import MarkerCluster
from streamlit_folium import folium_static

from analysis.area_profile import (
    get_facilities_in_circle,
    get_libraries_in_circle,
    get_living_area_population,
    get_nearby_facilities_kakao,
    get_tourism_in_circle,
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
    .kpi-lavender {
        background: linear-gradient(135deg, #EEF0F9 0%, #E4E7F5 100%);
        border: 1px solid #D3D8ED;
    }
    .kpi-teal {
        background: linear-gradient(135deg, #E9F4F3 0%, #DCEEEC 100%);
        border: 1px solid #C7E3E0;
    }
    .kpi-rose {
        background: linear-gradient(135deg, #FBEBEC 0%, #F6DBDD 100%);
        border: 2px solid #E0637A;
    }
    .kpi-violet {
        background: linear-gradient(135deg, #F0EBF7 0%, #E6DCF2 100%);
        border: 1px solid #D8C7EA;
    }
    .kpi-tangerine {
        background: linear-gradient(135deg, #FBEEDF 0%, #F6E0C7 100%);
        border: 1px solid #ECCB9E;
    }
    .kpi-blue .kpi-value { color: #3E7C91; }
    .kpi-pink .kpi-value { color: #C97B8E; }
    .kpi-green .kpi-value { color: #5C8A6B; }
    .kpi-amber .kpi-value { color: #A97C50; }
    .kpi-lavender .kpi-value { color: #5D69A8; }
    .kpi-teal .kpi-value { color: #3E8C82; }
    .kpi-rose .kpi-value { color: #C94D63; }
    .kpi-violet .kpi-value { color: #6F4F96; }
    .kpi-tangerine .kpi-value { color: #B87332; }
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

    /* 지도 클릭 시 브라우저 기본 focus outline(네모 테두리) 제거 */
    iframe,
    iframe:focus,
    .folium-map,
    .folium-map:focus,
    [class*="stCustomComponent"],
    [class*="stCustomComponent"]:focus {
        outline: none !important;
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
    tourism_nearby = get_tourism_in_circle(lat, lon, radius_km)

    radius_m = min(radius_km * 1000, 20000)
    kakao_cache = st.session_state.setdefault("kakao_cache", {})
    kakao_cache_key = (round(lat, 5), round(lon, 5), round(radius_m))
    if kakao_cache_key not in kakao_cache:
        with st.spinner("카카오에서 주변 시설을 검색하는 중..."):
            kakao_cache[kakao_cache_key] = get_nearby_facilities_kakao(lat, lon, radius_m)
    kakao_nearby = kakao_cache[kakao_cache_key]

    st.caption("지도에 표시할 시설 (기본: 학교·도서관만 켜짐)")
    tg1, tg2, tg3, tg4, tg5, tg6 = st.columns(6)
    show_layers = {
        "학교": tg1.checkbox("🏫 학교", value=True, key="show_school"),
        "도서관": tg2.checkbox("📚 도서관", value=True, key="show_library"),
        "관광명소": tg3.checkbox("🎡 관광명소", value=False, key="show_kakao_tourist"),
        "키즈카페": tg4.checkbox("🧸 키즈카페", value=False, key="show_kakao_kids"),
        "문화체험": tg5.checkbox("🏛️ 문화체험", value=False, key="show_kakao_culture"),
        "집객시설": tg6.checkbox("🛍️ 집객시설", value=False, key="show_kakao_crowd"),
    }

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

    def emoji_icon(emoji):
        html = f'<div style="font-size: 20px; line-height: 1; text-align: center;">{emoji}</div>'
        return folium.DivIcon(html=html, icon_size=(24, 24), icon_anchor=(12, 20))

    if show_layers["학교"]:
        school_cluster = MarkerCluster(name="학교").add_to(m)
        for _, school in facilities["schools"].iterrows():
            folium.Marker(
                location=[school["lat"], school["lon"]],
                tooltip=school["school_name"],
                icon=emoji_icon("🏫"),
            ).add_to(school_cluster)

    if show_layers["도서관"]:
        library_cluster = MarkerCluster(name="도서관").add_to(m)
        for _, library in libraries_nearby["libraries"].iterrows():
            folium.Marker(
                location=[library["lat"], library["lon"]],
                tooltip=library["library_name"],
                icon=emoji_icon("📚"),
            ).add_to(library_cluster)

    # 공식 지정 관광지(STEP 5-C)는 항상 표시 - 카카오 관광명소와 구분되는 별도 이모지
    if not tourism_nearby["tourism"].empty:
        tourism_cluster = MarkerCluster(name="관광지(공식)").add_to(m)
        for _, spot in tourism_nearby["tourism"].iterrows():
            folium.Marker(
                location=[spot["lat"], spot["lon"]],
                tooltip=spot["name"],
                icon=emoji_icon("🏞️"),
            ).add_to(tourism_cluster)

    kakao_emojis = {
        "관광명소": "🎡",
        "키즈카페": "🧸",
        "문화체험": "🏛️",
        "집객시설": "🛍️",
    }
    for category, data in kakao_nearby.items():
        if not show_layers.get(category):
            continue
        cluster = MarkerCluster(name=category).add_to(m)
        for place_name, category_name, address_name, place_lat, place_lon, distance in data["places"]:
            folium.Marker(
                location=[place_lat, place_lon],
                tooltip=place_name,
                icon=emoji_icon(kakao_emojis[category]),
            ).add_to(cluster)

    # 반경이 화면에 딱 맞게 보이도록 위도/경도 범위를 계산해서 자동 줌 조정
    delta_lat = radius_km / 111
    delta_lon = radius_km / (111 * math.cos(math.radians(lat)))
    bounds = [[lat - delta_lat, lon - delta_lon], [lat + delta_lat, lon + delta_lon]]
    m.fit_bounds(bounds)

    # folium_static은 클릭 이벤트를 아예 캡처하지 않는 정적 렌더링이라 클릭 시 사각형이 생기지 않음
    # (width=None이면 st_folium의 use_container_width=True와 동일하게 화면 폭에 맞춰짐)
    folium_static(m, width=None, height=420)
    st.caption(f"📍 직선거리 기준 약 {radius_km:.1f} km 범위 (실제 도로 이동거리와 다를 수 있음)")
    st.caption(
        "🏫 학교 · 📚 도서관 · 🏞️ 관광지(공식) 　 카카오 실시간: 🎡 관광명소 · 🧸 키즈카페 · 🏛️ 문화체험 · 🛍️ 집객시설"
    )
    st.caption("숫자 원은 확대하면 개별 마커로 펼쳐지는 클러스터입니다")

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

    st.subheader("생활권 관광자원")

    tourism_count = tourism_nearby["count"]
    if tourism_count == 0:
        st.info("이 생활권에는 공식 지정 관광지가 없습니다 (생활밀착형에 가까움)")
    else:
        tourism_col, _blank_col1, _blank_col2 = st.columns(3)
        kpi_card(tourism_col, "관광지", f"{tourism_count}", "개", "lavender")

        spot_names = tourism_nearby["tourism"]["name"].tolist()
        shown = spot_names[:10]
        more_suffix = f" 외 {len(spot_names) - 10}곳" if len(spot_names) > 10 else ""
        st.caption(f"📍 {', '.join(shown)}{more_suffix}")

    st.subheader("생활권 주변 시설 (카카오)")

    kakao_col1, kakao_col2, kakao_col3, kakao_col4 = st.columns(4)
    kpi_card(kakao_col1, "관광명소", f"{kakao_nearby['관광명소']['count']}", "개", "teal")
    kpi_card(kakao_col2, "키즈카페 (경쟁시설)", f"{kakao_nearby['키즈카페']['count']}", "개", "rose")
    kpi_card(kakao_col3, "문화체험", f"{kakao_nearby['문화체험']['count']}", "개", "violet")
    kpi_card(kakao_col4, "집객시설", f"{kakao_nearby['집객시설']['count']}", "개", "tangerine")

    st.caption("※ 카카오 실시간 검색 결과이며, 앞의 인구/학교/도서관/관광지와 달리 매번 최신 상태를 반영합니다")

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

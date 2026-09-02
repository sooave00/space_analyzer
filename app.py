"""생활권 분석 도구 - 첫 Streamlit 화면.

실행: streamlit run app.py
"""

import math

import folium
import streamlit as st
from streamlit_folium import st_folium

from analysis.living_area import calc_radius_km, get_dong_geometries, get_dongs_in_circle
from services.kakao_service import find_location

st.title("생활권 분석 도구")

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

    st.subheader("N분 생활권")

    minutes = st.radio("이동시간", [10, 20, 30], index=1, format_func=lambda m: f"{m}분", key="living_area_minutes")
    speed_kmh = st.slider(
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

    m = folium.Map(location=[lat, lon], zoom_start=13)
    folium.Marker([lat, lon], popup=name).add_to(m)
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

    # 반경이 화면에 딱 맞게 보이도록 위도/경도 범위를 계산해서 자동 줌 조정
    delta_lat = radius_km / 111
    delta_lon = radius_km / (111 * math.cos(math.radians(lat)))
    bounds = [[lat - delta_lat, lon - delta_lon], [lat + delta_lat, lon + delta_lon]]
    m.fit_bounds(bounds)

    st_folium(m, width=700, height=500)
    st.caption(f"📍 직선거리 기준 약 {radius_km:.1f} km 범위 (실제 도로 이동거리와 다를 수 있음)")

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

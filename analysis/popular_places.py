"""블로그·카페 글에서 자주 언급되는 공간을 추출·집계한다.

방법: 카카오 장소검색으로 그 지역의 공간 후보 목록을 뽑고, 같은 지역+목적으로
검색한 블로그/카페 글 텍스트에 각 공간명이 몇 번 등장하는지 센다.

실행(테스트): python -m analysis.popular_places
(services.kakao_service를 import하므로 python analysis/popular_places.py로 직접 실행하면 안 됨)
"""

import sys

from services.kakao_service import find_location, search_blog_all, search_cafe, search_places_nearby

# 공간 후보를 찾을 때 쓰는 검색 키워드 (목적에 맞는 카테고리 위주)
CANDIDATE_KEYWORDS = ["관광명소", "박물관", "미술관", "과학관", "키즈카페", "공원", "테마파크"]
CANDIDATE_SEARCH_RADIUS_M = 15000  # 지역 중심에서 공간 후보를 찾을 반경

BLOG_MAX_DOCS = 100
CAFE_MAX_DOCS = 50

# 이보다 짧은 공간명은 흔한 단어와 겹쳐 오탐(예: "공원"만으로 카운트)될 위험이 커서 제외한다
MIN_NAME_LENGTH = 2

# Windows 콘솔에서 한글 출력이 깨지는 것을 방지
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def _collect_text(region_name, purpose_keyword):
    """블로그+카페 글의 제목+본문을 하나의 텍스트로 모은다."""
    query = f"{region_name} {purpose_keyword}"

    blog_items = search_blog_all(query, max_docs=BLOG_MAX_DOCS)

    cafe_result = search_cafe(query, size=CAFE_MAX_DOCS)
    cafe_items = cafe_result["items"] if cafe_result else []

    texts = [f"{item['title']} {item['contents']}" for item in blog_items + cafe_items]
    return " ".join(texts)


def _collect_candidate_places(region_name, radius_m=CANDIDATE_SEARCH_RADIUS_M):
    """지역 중심 주변에서 관광/문화/키즈 관련 공간 후보를 모은다 (이름 기준 중복 제거)."""
    result = find_location(region_name)
    if not result:
        print(f"'{region_name}' 위치를 찾을 수 없습니다.")
        return []

    candidates, _method = result
    _center_name, _addr, center_lat, center_lon = candidates[0]

    seen = set()
    places = []
    for keyword in CANDIDATE_KEYWORDS:
        for place in search_places_nearby(keyword, center_lat, center_lon, radius_m):
            place_name, category_name, _address, lat, lon, distance = place

            if distance is None or distance > radius_m:
                continue
            if len(place_name) < MIN_NAME_LENGTH:
                continue
            if place_name in seen:
                continue

            seen.add(place_name)
            places.append({"name": place_name, "category": category_name, "lat": lat, "lon": lon})

    return places


def get_popular_places(region_name, purpose_keyword):
    """지역+목적 블로그/카페 글에서 자주 언급되는 공간을 언급 횟수 순으로 반환한다.

    반환: [{"name", "category", "mention_count", "lat", "lon"}, ...] (언급 많은 순으로 정렬)
    """
    text = _collect_text(region_name, purpose_keyword)
    if not text.strip():
        print("블로그·카페 검색 결과가 없습니다.")
        return []

    places = _collect_candidate_places(region_name)
    if not places:
        print("공간 후보를 찾을 수 없습니다.")
        return []

    for place in places:
        place["mention_count"] = text.count(place["name"])

    places.sort(key=lambda p: p["mention_count"], reverse=True)
    return places


if __name__ == "__main__":
    region_name = "경주"
    purpose_keyword = "아이랑 가볼만한 곳"

    results = get_popular_places(region_name, purpose_keyword)

    print(f"'{region_name} {purpose_keyword}' - 공간 후보 {len(results)}개 중 언급 많은 TOP 10:\n")
    for rank, place in enumerate(results[:10], start=1):
        print(f"{rank}. {place['name']} - {place['mention_count']}회 언급 ({place['category']})")

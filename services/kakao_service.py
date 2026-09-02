"""카카오 로컬 API로 주소/장소를 좌표(위도/경도)로 변환하는 기능. 첫 검증용.

실행: python services/kakao_service.py
"""

import os
import sys

import requests
from dotenv import load_dotenv

ADDRESS_API_URL = "https://dapi.kakao.com/v2/local/search/address.json"
KEYWORD_API_URL = "https://dapi.kakao.com/v2/local/search/keyword.json"

# Windows 콘솔에서 한글 출력이 깨지는 것을 방지
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def _search(url, query):
    """카카오 로컬 API를 호출해서 documents 리스트를 반환한다. 실패 시 None을 반환한다."""
    load_dotenv()
    api_key = os.getenv("KAKAO_REST_KEY")

    if not api_key:
        print("KAKAO_REST_KEY가 설정되어 있지 않습니다. .env 파일을 확인해주세요.")
        return None

    headers = {"Authorization": f"KakaoAK {api_key}"}
    params = {"query": query}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
    except requests.exceptions.RequestException as e:
        print(f"API 호출 중 네트워크 오류가 발생했습니다: {e}")
        return None

    if response.status_code != 200:
        print(f"HTTP 상태코드: {response.status_code}")
        print(f"응답 본문: {response.text}")
        return None

    return response.json().get("documents", [])


def address_to_coord(address):
    """주소를 (위도, 경도, 정제된 주소)로 변환한다. 실패 시 None을 반환한다."""
    documents = _search(ADDRESS_API_URL, address)
    if not documents:
        print("주소를 찾을 수 없습니다")
        return None

    doc = documents[0]
    return float(doc["y"]), float(doc["x"]), doc["address_name"]


def search_places(keyword):
    """키워드(장소명)로 검색해서 최대 10개의 결과 리스트를 반환한다.

    각 항목은 (장소명, 주소, 위도, 경도) 튜플이다. 실패 시 빈 리스트를 반환한다.
    """
    documents = _search(KEYWORD_API_URL, keyword)
    if not documents:
        print("검색 결과를 찾을 수 없습니다")
        return []

    return [
        (doc["place_name"], doc["address_name"], float(doc["y"]), float(doc["x"]))
        for doc in documents[:10]
    ]


def find_location(text):
    """주소검색을 먼저 시도하고 실패하면 키워드검색을 시도한다.

    반환: (candidates, 방식) 또는 둘 다 실패 시 None.
    candidates는 (장소명, 주소, 위도, 경도) 튜플의 리스트.
    방식은 "주소검색" 또는 "키워드검색".
    """
    result = address_to_coord(text)
    if result:
        latitude, longitude, refined_address = result
        return [(refined_address, refined_address, latitude, longitude)], "주소검색"

    places = search_places(text)
    if places:
        return places, "키워드검색"

    return None


if __name__ == "__main__":
    test_inputs = [
        "경기도 파주시 와석순환로 500",
        "포항 우현더힐",
        "포항시청",
    ]

    for text in test_inputs:
        print(f"--- {text} ---")
        result = find_location(text)
        if result:
            candidates, method = result
            print(f"[{method}] {len(candidates)}개 결과")
            for name, addr, lat, lon in candidates:
                print(f"  - {name} ({addr}) 위도: {lat}, 경도: {lon}")
        print()

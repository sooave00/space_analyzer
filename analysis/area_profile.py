"""생활권(원 안 행정동)에 인구 지표를 붙여서 합산한다.

실행(테스트): python -m analysis.area_profile
(다른 패키지의 living_area를 import하므로 python analysis/area_profile.py로 직접 실행하면 안 됨)
"""

import sys

import pandas as pd

from analysis.living_area import _haversine_km

POPULATION_PATH = "data/processed/population.parquet"
MAPPING_PATH = "data/reference/adm_cd_mapping.csv"
SCHOOLS_PATH = "data/processed/schools.parquet"
SCHOOL_LEVELS = ["초등학교", "중학교", "고등학교"]

LIBRARIES_PATH = "data/processed/libraries.parquet"
LIBRARY_GROUPS = ["주요도서관", "작은도서관", "기타"]

# Windows 콘솔에서 한글 출력이 깨지는 것을 방지
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def get_living_area_population(dongs, population_path=POPULATION_PATH, mapping_path=MAPPING_PATH):
    """생활권에 포함된 행정동의 인구를 합산한다.

    dongs: get_dongs_in_circle()이 반환하는 DataFrame (ADM_CD, ADM_NM 컬럼 필요).

    반환: dict
      - total, age_0_9, age_10_14, age_30_49: 생활권 합계
      - matched_count: 인구 데이터에 매칭된 행정동 개수
      - unmatched: 매칭 안 된 행정동의 [(ADM_CD, ADM_NM), ...] 목록
        (행정구역 개편 등으로 인구 데이터에 없는 동 - 조용히 0으로 처리하지 않고 그대로 알려준다)
    """
    if dongs.empty:
        return {
            "total": 0,
            "age_0_9": 0,
            "age_10_14": 0,
            "age_30_49": 0,
            "matched_count": 0,
            "unmatched": [],
        }

    mapping = pd.read_csv(mapping_path, dtype=str)
    population = pd.read_parquet(population_path)

    merged = dongs[["ADM_CD", "ADM_NM"]].merge(
        mapping[["adm_cd", "sgis_adm_cd"]],
        left_on="ADM_CD",
        right_on="sgis_adm_cd",
        how="left",
    )

    matched = merged[merged["adm_cd"].notna()]
    unmatched = list(
        merged.loc[merged["adm_cd"].isna(), ["ADM_CD", "ADM_NM"]].itertuples(index=False, name=None)
    )

    pop_matched = population[population["adm_cd"].isin(matched["adm_cd"])]

    return {
        "total": int(pop_matched["total"].sum()),
        "age_0_9": int(pop_matched["age_0_9"].sum()),
        "age_10_14": int(pop_matched["age_10_14"].sum()),
        "age_30_49": int(pop_matched["age_30_49"].sum()),
        "matched_count": len(matched),
        "unmatched": unmatched,
    }


def get_facilities_in_circle(center_lat, center_lon, radius_km, schools_path=SCHOOLS_PATH):
    """생활권 원 안에 있는 학교를 학교급별로 정리해서 반환한다.

    반환: dict
      - counts: {"초등학교": N, "중학교": N, "고등학교": N}
      - schools: DataFrame (school_name, school_level, lat, lon, distance_km), 거리 가까운 순 정렬
    """
    schools = pd.read_parquet(schools_path)

    distance_km = _haversine_km(center_lat, center_lon, schools["lat"].values, schools["lon"].values)
    schools = schools.assign(distance_km=distance_km)

    in_circle = schools[schools["distance_km"] <= radius_km].sort_values("distance_km").reset_index(drop=True)

    level_counts = in_circle["school_level"].value_counts()
    counts = {level: int(level_counts.get(level, 0)) for level in SCHOOL_LEVELS}

    return {"counts": counts, "schools": in_circle}


def get_libraries_in_circle(center_lat, center_lon, radius_km, libraries_path=LIBRARIES_PATH):
    """생활권 원 안에 있는 도서관을 그룹별(주요도서관/작은도서관/기타)로 정리해서 반환한다.

    반환: dict
      - counts: {"주요도서관": N, "작은도서관": N, "기타": N}
      - libraries: DataFrame (library_name, library_type, group, lat, lon, distance_km),
        거리 가까운 순 정렬
    """
    libraries = pd.read_parquet(libraries_path)

    distance_km = _haversine_km(center_lat, center_lon, libraries["lat"].values, libraries["lon"].values)
    libraries = libraries.assign(distance_km=distance_km)

    in_circle = (
        libraries[libraries["distance_km"] <= radius_km].sort_values("distance_km").reset_index(drop=True)
    )

    group_counts = in_circle["group"].value_counts()
    counts = {group: int(group_counts.get(group, 0)) for group in LIBRARY_GROUPS}

    return {"counts": counts, "libraries": in_circle}


if __name__ == "__main__":
    from analysis.living_area import get_dongs_in_circle

    center_lat, center_lon, radius_km = 36.019, 129.343, 10.0

    dongs = get_dongs_in_circle(center_lat, center_lon, radius_km)
    profile = get_living_area_population(dongs)

    print(f"포항시청 좌표({center_lat}, {center_lon}) 기준 반경 {radius_km}km 생활권 인구")
    print(f"매칭된 행정동: {profile['matched_count']} / {len(dongs)}개")
    print(f"총인구: {profile['total']:,}명")
    print(f"0~9세: {profile['age_0_9']:,}명")
    print(f"10~14세: {profile['age_10_14']:,}명")
    print(f"30~49세: {profile['age_30_49']:,}명")
    if profile["unmatched"]:
        print(f"\n인구 미매칭 행정동 {len(profile['unmatched'])}개:")
        for adm_cd, adm_nm in profile["unmatched"]:
            print(f"  {adm_cd}  {adm_nm}")

    facilities = get_facilities_in_circle(center_lat, center_lon, radius_km)
    print(f"\n생활권 학교: 초 {facilities['counts']['초등학교']}개 / "
          f"중 {facilities['counts']['중학교']}개 / 고 {facilities['counts']['고등학교']}개")
    print("\n가까운 순 10개:")
    print(facilities["schools"].head(10))

    libraries = get_libraries_in_circle(center_lat, center_lon, radius_km)
    print(f"\n생활권 도서관: 주요도서관 {libraries['counts']['주요도서관']}개 / "
          f"작은도서관 {libraries['counts']['작은도서관']}개 / 기타 {libraries['counts']['기타']}개")
    print("\n가까운 순 10개:")
    print(libraries["libraries"].head(10))

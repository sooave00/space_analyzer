"""생활권(원 안 행정동)에 인구 지표를 붙여서 합산한다.

실행(테스트): python -m analysis.area_profile
(다른 패키지의 living_area를 import하므로 python analysis/area_profile.py로 직접 실행하면 안 됨)
"""

import sys

import pandas as pd

POPULATION_PATH = "data/processed/population.parquet"
MAPPING_PATH = "data/reference/adm_cd_mapping.csv"

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


if __name__ == "__main__":
    from analysis.living_area import get_dongs_in_circle

    center_lat, center_lon, radius_km = 36.019, 129.343, 6.5

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

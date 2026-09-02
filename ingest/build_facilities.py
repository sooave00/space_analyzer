"""전국 학교/도서관/관광지 표준데이터를 정제해서 필요한 컬럼만 저장하는 1회성 스크립트.

실행: python ingest/build_facilities.py
"""

import os
import sys

import pandas as pd

SCHOOLS_RAW_PATH = "data/raw/schools.csv"
SCHOOLS_PROCESSED_PATH = "data/processed/schools.parquet"

LIBRARIES_RAW_PATH = "data/raw/libraries.csv"
LIBRARIES_PROCESSED_PATH = "data/processed/libraries.parquet"

TOURISM_RAW_PATH = "data/raw/tourism.csv"
TOURISM_PROCESSED_PATH = "data/processed/tourism.parquet"

VALID_LAT_RANGE = (33, 39)
VALID_LON_RANGE = (124, 132)

SCHOOL_COLUMN_MAP = {
    "학교명": "school_name",
    "학교급구분": "school_level",
    "소재지도로명주소": "address",
    "위도": "lat",
    "경도": "lon",
}

LIBRARY_COLUMN_MAP = {
    "도서관명": "library_name",
    "도서관유형": "library_type",
    "소재지도로명주소": "address",
    "위도": "lat",
    "경도": "lon",
}

# "도서관유형" 원본값 -> 3그룹 재분류 (이름에 "작은도서관"/"마을문고"가 있으면 원본 유형과 무관하게
# 작은도서관으로 우선 분류한다 - 지자체에 따라 소규모 문고를 "공공도서관"으로 등록해두는 경우가 있어서,
# 원본 유형만 믿으면 실제로는 작은도서관인 곳이 주요도서관으로 잘못 잡힌다)
SMALL_LIBRARY_NAME_KEYWORDS = ["작은도서관", "마을문고"]
LIBRARY_GROUP_MAP = {
    "공공도서관": "주요도서관",
    "어린이도서관": "주요도서관",
    "작은도서관": "작은도서관",
}
LIBRARY_GROUP_DEFAULT = "기타"  # 학교/전문/대학/장애인도서관 등

TOURISM_COLUMN_MAP = {
    "관광지명": "name",
    "관광지구분": "category",
    "소재지도로명주소": "address",
    "위도": "lat",
    "경도": "lon",
}

# Windows 콘솔에서 한글 출력이 깨지는 것을 방지
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def _read_valid_coords(raw_path, column_map):
    """원본 CSV를 읽어 필요한 컬럼만 남기고, 위도/경도가 유효한 행만 남긴다."""
    try:
        df = pd.read_csv(raw_path, encoding="cp949")
    except FileNotFoundError:
        print(f"파일을 찾을 수 없습니다: {raw_path}")
        return None
    except Exception as e:
        print(f"CSV를 읽는 중 오류가 발생했습니다: {e}")
        return None

    df = df.rename(columns=column_map)[list(column_map.values())]

    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")

    valid = df["lat"].between(*VALID_LAT_RANGE) & df["lon"].between(*VALID_LON_RANGE)
    return df[valid].reset_index(drop=True)


def build_schools(raw_path=SCHOOLS_RAW_PATH):
    """학교 위치 데이터를 정제한다."""
    return _read_valid_coords(raw_path, SCHOOL_COLUMN_MAP)


def build_libraries(raw_path=LIBRARIES_RAW_PATH):
    """도서관 위치 데이터를 정제하고 유형을 3그룹으로 재분류한다."""
    df = _read_valid_coords(raw_path, LIBRARY_COLUMN_MAP)
    if df is None:
        return None

    df["group"] = df["library_type"].map(LIBRARY_GROUP_MAP).fillna(LIBRARY_GROUP_DEFAULT)

    name_says_small = df["library_name"].str.contains("|".join(SMALL_LIBRARY_NAME_KEYWORDS))
    df.loc[name_says_small, "group"] = "작은도서관"

    return df


def build_tourism(raw_path=TOURISM_RAW_PATH):
    """관광지 위치 데이터를 정제한다."""
    return _read_valid_coords(raw_path, TOURISM_COLUMN_MAP)


def save_processed(df, out_path):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    df.to_parquet(out_path, index=False)
    return out_path


def main():
    schools = build_schools()
    if schools is not None:
        out_path = save_processed(schools, SCHOOLS_PROCESSED_PATH)
        print(f"저장 완료: {out_path}")
        print(f"\n학교 개수: {len(schools)}개")
        print("\n학교급별 개수:")
        print(schools["school_level"].value_counts())
        print("\n샘플 5행:")
        print(schools.head())

    print("\n" + "=" * 40 + "\n")

    libraries = build_libraries()
    if libraries is not None:
        out_path = save_processed(libraries, LIBRARIES_PROCESSED_PATH)
        print(f"저장 완료: {out_path}")
        print(f"\n도서관 개수: {len(libraries)}개")
        print("\n그룹별 개수:")
        print(libraries["group"].value_counts())
        print("\n샘플 5행:")
        print(libraries.head())

    print("\n" + "=" * 40 + "\n")

    tourism = build_tourism()
    if tourism is not None:
        out_path = save_processed(tourism, TOURISM_PROCESSED_PATH)
        print(f"저장 완료: {out_path}")
        print(f"\n관광지 개수: {len(tourism)}개")
        print("\n구분별 개수:")
        print(tourism["category"].value_counts())
        print("\n샘플 5행:")
        print(tourism.head())


if __name__ == "__main__":
    main()

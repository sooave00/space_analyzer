"""전국 학교 위치 표준데이터를 정제해서 필요한 컬럼만 저장하는 1회성 스크립트.

실행: python ingest/build_facilities.py
"""

import os
import sys

import pandas as pd

RAW_PATH = "data/raw/schools.csv"
PROCESSED_PATH = "data/processed/schools.parquet"

VALID_LAT_RANGE = (33, 39)
VALID_LON_RANGE = (124, 132)

COLUMN_MAP = {
    "학교명": "school_name",
    "학교급구분": "school_level",
    "소재지도로명주소": "address",
    "위도": "lat",
    "경도": "lon",
}

# Windows 콘솔에서 한글 출력이 깨지는 것을 방지
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def load_and_clean(raw_path=RAW_PATH):
    """원본 CSV를 읽어 필요한 컬럼만 남기고, 위도/경도가 유효한 행만 남긴다."""
    try:
        df = pd.read_csv(raw_path, encoding="cp949")
    except FileNotFoundError:
        print(f"파일을 찾을 수 없습니다: {raw_path}")
        return None
    except Exception as e:
        print(f"CSV를 읽는 중 오류가 발생했습니다: {e}")
        return None

    df = df.rename(columns=COLUMN_MAP)[list(COLUMN_MAP.values())]

    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")

    valid = df["lat"].between(*VALID_LAT_RANGE) & df["lon"].between(*VALID_LON_RANGE)
    return df[valid].reset_index(drop=True)


def save_processed(df, out_path=PROCESSED_PATH):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    df.to_parquet(out_path, index=False)
    return out_path


def main():
    df = load_and_clean()
    if df is None:
        return

    out_path = save_processed(df)

    print(f"저장 완료: {out_path}")
    print(f"\n학교 개수: {len(df)}개")
    print("\n학교급별 개수:")
    print(df["school_level"].value_counts())
    print("\n샘플 5행:")
    print(df.head())


if __name__ == "__main__":
    main()

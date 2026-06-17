"""stat.csv 무결성 검증 + region_codes.json 을 stat.csv 기준으로 재생성."""
import json
import pandas as pd
from src import config

df = pd.read_csv("data/stat.csv")
print("총 행:", len(df))
print("연도:", sorted(df["연도"].unique().tolist()))
print("시도 수:", df["시도"].nunique(), "/ 기대 17")

# 시도별 고유 시군구 수
print("\n시도별 시군구 수(고유):")
per = df.groupby("시도")["시군구"].nunique().sort_values(ascending=False)
for name, n in per.items():
    print(f"  {name}: {n}")

uniq = df[["시도", "시군구"]].drop_duplicates()
print("\n전국 고유 시군구 수:", len(uniq))

# 사고유형 합 == 사고건수 인지 검산(첫 5행)
type_cols = config.ACC_TYPE_LABELS
chk = df.copy()
chk["유형합"] = chk[type_cols].sum(axis=1)
mism = (chk["유형합"] != chk["사고건수"]).sum()
print(f"\n사고유형합 != 사고건수 인 행 수: {mism} (0 이어야 정상)")

# 샘플
print("\n[샘플] 서울 강남구 연도별:")
g = df[df["시군구"].str.contains("강남구", na=False)].sort_values("연도")
print(g[["연도", "시군구", "사고건수", "사망자수", "부상자수"]].to_string(index=False))

# region_codes.json 재생성 (stat.csv 기준, 코드는 config 매핑 사용 불가하므로
# 기존 json 의 코드 + stat 의 이름을 합치되, 누락 시도는 config 코드로 채움)
name_to_code = {s["name"]: s["code"] for s in config.SIDO_LIST}
regions = {}
for sido_name, sub in uniq.groupby("시도"):
    # 이 시점에서 정확한 guGun 코드는 build/repair 가 만든 기존 json 에 있음.
    regions[sido_name] = sorted(sub["시군구"].tolist())
with open("src/region_names.json", "w", encoding="utf-8") as f:
    json.dump(regions, f, ensure_ascii=False, indent=2)
print("\nsrc/region_names.json 재생성 완료 (시도→시군구명 목록)")

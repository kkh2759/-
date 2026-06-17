"""개발용 빠른 점검 (streamlit 런타임 없이 데이터 로직/컴파일 검증)."""
import py_compile
from src import data_loader, config

print("stat_source:", data_loader.stat_source())
print("freq_source:", data_loader.freq_source())

stat = data_loader.load_stat()
print("stat:", stat.shape, "| 시도수:", stat["시도"].nunique())
need = {"연도", "시도", "시군구", "사고건수", "사망자수", "부상자수"}
assert need <= set(stat.columns), f"누락 컬럼: {need - set(stat.columns)}"
assert set(config.ACC_TYPE_LABELS) <= set(stat.columns)
assert set(config.VIOLATION_LABELS) <= set(stat.columns)

# 사고유형 합 == 사고건수 (실데이터 무결성)
chk = (stat[config.ACC_TYPE_LABELS].sum(axis=1) != stat["사고건수"]).sum()
print("유형합!=사고건수 행:", chk)

z = data_loader.load_freq_zones("서울특별시")
print("서울 다발지역:", z.shape, "| cols:", list(z.columns))
assert {"위도", "경도", "발생건수"} <= set(z.columns) and len(z) > 0

for f in ["app.py"]:
    py_compile.compile(f, doraise=True)
print("\nOK: 컴파일 + 실데이터 파이프라인 정상")

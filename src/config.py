"""
프로젝트 전역 설정값 모음.
- API 엔드포인트 주소
- 분석 대상 연도 목록
- 시도(광역시/도) 코드 목록

※ 시도코드는 '법정동 2자리 × 100' (서울 1100), 시군구코드는 '시도앞2자리 + 순번'
   (강남구 1116) 형식임을 실제 호출로 확인함.
   전체 시군구 코드표는 build_region_codes.py 로 한 번 탐색해
   src/region_codes.json 에 저장해 두었다.
"""
import json
import os

# ── 도로교통공단(B552061) Open API 엔드포인트 ───────────────────
# 1) 지자체별 교통사고 통계  → 연도/지역/사고유형 분석용 (집계 데이터)
ENDPOINT_STAT = "http://apis.data.go.kr/B552061/lgStat/getRestLgStat"

# 2) 교통사고 다발지역  → 지도용 (위도 la_crd / 경도 lo_crd 포함)
ENDPOINT_FREQ = "http://apis.data.go.kr/B552061/frequentzoneLg/getRestFrequentzoneLg"

# 3) 사망 교통사고 정보  → 시간대/요일 분석용 (개별 사고 레코드)
#    (서비스 신청 후 상세 엔드포인트가 확정되면 여기에 넣으세요)
ENDPOINT_DEATH = "http://apis.data.go.kr/B552061/sjnh/getRestSjnh"  # ← 신청 페이지에서 재확인 필요

# ── 분석 대상 연도 (필요에 맞게 추가/수정) ──────────────────────
YEARS = [2019, 2020, 2021, 2022, 2023]

# ── 시도 코드 (도로교통공단 lgStat API의 자체 코드, 실측 확인) ──
#    name: API 가 돌려주는 시도명,  code: 호출용 siDo 값(1100~2700)
SIDO_LIST = [
    {"name": "서울특별시", "code": "1100"},
    {"name": "부산광역시", "code": "1200"},
    {"name": "대구광역시", "code": "2200"},
    {"name": "인천광역시", "code": "2300"},
    {"name": "광주광역시", "code": "2400"},
    {"name": "대전광역시", "code": "2500"},
    {"name": "울산광역시", "code": "2600"},
    {"name": "세종특별자치시", "code": "2700"},
    {"name": "경기도", "code": "1300"},
    {"name": "강원도", "code": "1400"},
    {"name": "충청북도", "code": "1500"},
    {"name": "충청남도", "code": "1600"},
    {"name": "전라북도", "code": "1700"},
    {"name": "전라남도", "code": "1800"},
    {"name": "경상북도", "code": "1900"},
    {"name": "경상남도", "code": "2000"},
    {"name": "제주도", "code": "2100"},
]

# 이름 → 코드, 코드 → 이름 빠른 변환용
SIDO_NAME_TO_CODE = {x["name"]: x["code"] for x in SIDO_LIST}
SIDO_CODE_TO_NAME = {x["code"]: x["name"] for x in SIDO_LIST}
SIDO_NAMES = [x["name"] for x in SIDO_LIST]

# ── 통계 API 응답의 코드형 컬럼 의미 ────────────────────────────
# (실제 응답으로 검산 완료: 차대사람+차대차+차량단독+철길 = 사고건수)
# cnt_014_* : 사고유형
ACC_TYPE_014 = {
    "cnt_014_01": "차대사람",
    "cnt_014_02": "차대차",
    "cnt_014_03": "차량단독",
    "cnt_014_04": "철길건널목",
}
# cnt_027_* : 법규위반(사고원인)  ※ 세부 라벨은 추후 확인 후 조정 가능
VIOLATION_027 = {
    "cnt_027_01": "과속",
    "cnt_027_02": "중앙선 침범",
    "cnt_027_03": "신호위반",
    "cnt_027_04": "안전거리 미확보",
    "cnt_027_05": "안전운전 의무 불이행",
    "cnt_027_06": "보행자 보호의무 위반",
    "cnt_027_07": "교차로 통행방법 위반",
    "cnt_027_99": "기타",
}

# 분석에서 쓰는 표준 컬럼 묶음
ACC_TYPE_LABELS = list(ACC_TYPE_014.values())
VIOLATION_LABELS = list(VIOLATION_027.values())

# ── 전국 시군구 코드표 로드 (build_region_codes.py 결과) ─────────
_REGION_PATH = os.path.join(os.path.dirname(__file__), "region_codes.json")


def load_region_codes() -> dict:
    """{시도명: {"sido_code": "...", "guguns": [{"code","name"}, ...]}} 반환. 없으면 {}."""
    if os.path.exists(_REGION_PATH):
        with open(_REGION_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}

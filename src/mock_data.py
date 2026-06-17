"""
샘플(가짜) 데이터 생성기.

API 키가 아직 없어도 웹사이트 화면/그래프/지도를 100% 그대로 볼 수 있도록
실제 응답과 '같은 모양'의 DataFrame 을 만들어 준다.
나중에 실제 API 가 연결되면 이 파일은 더 이상 호출되지 않는다.
"""

import random
import pandas as pd

from . import config

random.seed(42)  # 매번 같은 샘플이 나오도록 고정

# 시도별 대략적인 중심 좌표 (지도 샘플용)
_SIDO_CENTER = {
    "서울특별시": (37.5665, 126.9780), "부산광역시": (35.1796, 129.0756),
    "대구광역시": (35.8714, 128.6014), "인천광역시": (37.4563, 126.7052),
    "광주광역시": (35.1595, 126.8526), "대전광역시": (36.3504, 127.3845),
    "울산광역시": (35.5384, 129.3114), "세종특별자치시": (36.4800, 127.2890),
    "경기도": (37.4138, 127.5183), "강원도": (37.8228, 128.1555),
    "충청북도": (36.6357, 127.4917), "충청남도": (36.6588, 126.6728),
    "전라북도": (35.7175, 127.1530), "전라남도": (34.8161, 126.4630),
    "경상북도": (36.4919, 128.8889), "경상남도": (35.4606, 128.2132),
    "제주도": (33.4996, 126.5312),
}


def stat_all() -> pd.DataFrame:
    """연도 × 시도 별 집계 샘플 (실제 stat.csv 와 동일한 wide 스키마).

    컬럼: 연도, 시도, 시군구, 사고건수, 사망자수, 부상자수, 치사율,
          (사고유형 4종) 차대사람/차대차/차량단독/철길건널목,
          (법규위반 8종) 과속/중앙선 침범/.../기타
    """
    type_labels = list(config.ACC_TYPE_014.values())
    viol_labels = list(config.VIOLATION_027.values())
    type_share = {"차대사람": 0.25, "차대차": 0.62, "차량단독": 0.12, "철길건널목": 0.01}
    viol_share = {"과속": 0.03, "중앙선 침범": 0.05, "신호위반": 0.10,
                  "안전거리 미확보": 0.13, "안전운전 의무 불이행": 0.55,
                  "보행자 보호의무 위반": 0.05, "교차로 통행방법 위반": 0.06, "기타": 0.03}

    rows = []
    for year in config.YEARS:
        for sido in config.SIDO_NAMES:
            base = random.randint(800, 6000)
            cnt = max(1, int(base * (1 - 0.03 * (year - config.YEARS[0]))))
            deaths = max(0, int(cnt * random.uniform(0.005, 0.02)))
            injuries = int(cnt * random.uniform(1.2, 1.6))
            row = {
                "연도": year, "시도": sido, "시군구": f"{sido} 전체",
                "사고건수": cnt, "사망자수": deaths, "부상자수": injuries,
                "치사율": round(deaths / cnt * 100, 2),
            }
            for lbl in type_labels:
                row[lbl] = int(cnt * type_share[lbl] * random.uniform(0.85, 1.15))
            for lbl in viol_labels:
                row[lbl] = int(cnt * viol_share[lbl] * random.uniform(0.85, 1.15))
            rows.append(row)
    return pd.DataFrame(rows)


def freq_zones(sido_name: str) -> pd.DataFrame:
    """선택한 시도의 사고 다발지역 좌표 샘플. (지도용)"""
    lat0, lon0 = _SIDO_CENTER.get(sido_name, (36.5, 127.8))
    rows = []
    for i in range(25):
        rows.append({
            "지점명": f"{sido_name} 다발지역 {i + 1}",
            "위도": lat0 + random.uniform(-0.15, 0.15),
            "경도": lon0 + random.uniform(-0.15, 0.15),
            "발생건수": random.randint(3, 20),
            "사상자수": random.randint(3, 35),
            "사망자수": random.randint(0, 2),
        })
    return pd.DataFrame(rows)

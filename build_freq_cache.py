"""
[데이터 갱신용] 전국 교통사고 다발지역(좌표 포함)을 받아 data/freq.csv 로 저장.

발견:
- 다발지역 API 는 '법정동' 코드 사용(siDo 2자리, guGun 3자리). 통계 API 코드와 다름.
- guGun 을 빈값("")으로 보내면 해당 시도 전체 다발지역이 반환된다. → 시도 17개만 호출.
"""
import os, re, requests
import pandas as pd

from src import config

KEY = re.search(r'TAAS_API_KEY\s*=\s*"([^"]+)"',
                open(".streamlit/secrets.toml", encoding="utf-8").read()).group(1)
URL = config.ENDPOINT_FREQ
YEAR = 2022   # 다발지역 공개 기준 연도

# 법정동 시도코드 → 통계 데이터와 동일한 시도명 (지도 필터 일치를 위해)
LDONG_SIDO = {
    "11": "서울특별시", "26": "부산광역시", "27": "대구광역시", "28": "인천광역시",
    "29": "광주광역시", "30": "대전광역시", "31": "울산광역시", "36": "세종특별자치시",
    "41": "경기도", "42": "강원도", "43": "충청북도", "44": "충청남도",
    "45": "전라북도", "46": "전라남도", "47": "경상북도", "48": "경상남도", "50": "제주도",
}


def fetch_sido(sido_code):
    """해당 시도의 모든 다발지역 item (페이지네이션 포함)."""
    out, page = [], 1
    while True:
        params = {"ServiceKey": KEY, "type": "json", "searchYearCd": YEAR,
                  "siDo": sido_code, "guGun": "", "numOfRows": 100, "pageNo": page}
        for _ in range(8):   # throttle 재시도
            try:
                j = requests.get(URL, params=params, timeout=20).json()
                code = j.get("resultCode")
                if code == "00":
                    it = j["items"]["item"]
                    it = it if isinstance(it, list) else [it]
                    out.extend(it)
                    total = int(j.get("totalCount", len(out)))
                    if page * 100 >= total:
                        return out, total
                    page += 1
                    break
                if code in ("03", "10"):
                    return out, 0
            except Exception:
                pass
            import time; time.sleep(0.4)
        else:
            return out, len(out)


def main():
    rows = []
    for code, name in LDONG_SIDO.items():
        items, total = fetch_sido(code)
        for it in items:
            try:
                rows.append({
                    "시도": name,
                    "지점명": it.get("spot_nm", ""),
                    "위도": float(it["la_crd"]),
                    "경도": float(it["lo_crd"]),
                    "발생건수": int(it.get("occrrnc_cnt", 0) or 0),
                    "사상자수": int(it.get("caslt_cnt", 0) or 0),
                    "사망자수": int(it.get("dth_dnv_cnt", 0) or 0),
                    "중상자수": int(it.get("se_dnv_cnt", 0) or 0),
                    "경상자수": int(it.get("sl_dnv_cnt", 0) or 0),
                })
            except (KeyError, ValueError, TypeError):
                continue
        print(f"  {name}: {len(items)}곳", flush=True)

    os.makedirs("data", exist_ok=True)
    df = pd.DataFrame(rows)
    df.to_csv("data/freq.csv", index=False, encoding="utf-8-sig")
    print(f"\n저장 완료: data/freq.csv ({len(df)}곳)", flush=True)


if __name__ == "__main__":
    main()

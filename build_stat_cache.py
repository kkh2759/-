"""
[데이터 갱신용] 전국 시군구 × 연도 교통사고 통계를 받아 data/stat.csv 로 저장.
부수적으로 시군구 코드표를 src/region_codes.json 으로도 저장한다.

- 이 API 는 동시 호출 10개 이상이면 일부 응답이 누락된다(throttle). → 5 workers 로 제한.
- 각 (연도, 시군구) 에서 acc_cl_nm == '전체사고' 한 행만 사용.
  (이 행에 사고유형 cnt_014_*, 법규위반 cnt_027_* 가 들어있다.)
- 앱은 런타임에 API 를 부르지 않고 이 CSV 만 읽는다.

새 연도 데이터가 공개되면 config.YEARS 에 추가하고 다시 실행하면 된다.
"""
import json, os, re, time
from concurrent.futures import ThreadPoolExecutor
import requests
import pandas as pd

from src import config

# secrets.toml 에서 키 읽기 (streamlit 밖이므로 파일에서 직접)
_txt = open(".streamlit/secrets.toml", encoding="utf-8").read()
KEY = re.search(r'TAAS_API_KEY\s*=\s*"([^"]+)"', _txt).group(1)

URL = config.ENDPOINT_STAT
WORKERS = 3      # 동시 호출이 많으면 throttle → 3 으로 제한
SCAN_MAX = 45    # 시군구 순번 최대 (경기 31 < 45)


def fetch(year, sido_code, gugun_code):
    """해당 (연도, 시군구) 의 item 리스트. 없으면 [].

    핵심: throttle(비-JSON 에러 응답/HTTP오류/예외)는 '데이터 없음'과 다르므로
    깨끗한 JSON(resultCode 00/03/10) 을 받을 때까지 재시도한다.
    """
    params = {"ServiceKey": KEY, "type": "json", "searchYearCd": year,
              "siDo": sido_code, "guGun": gugun_code, "numOfRows": 20, "pageNo": 1}
    for attempt in range(8):
        try:
            r = requests.get(URL, params=params, timeout=20)
            if r.status_code == 200:
                j = r.json()                       # throttle 응답은 보통 XML → 예외
                code = j.get("resultCode")
                if code == "00":
                    it = j["items"]["item"]
                    return it if isinstance(it, list) else [it]
                if code in ("03", "10"):
                    return []                      # 진짜 데이터 없음(공번)
            # 그 외(throttle 등) → 재시도
        except Exception:
            pass
        time.sleep(0.4 * (attempt + 1))            # 백오프
    return []


def total_row(items):
    return next((it for it in items if it.get("acc_cl_nm") == "전체사고"), None)


def main():
    pool = ThreadPoolExecutor(max_workers=WORKERS)
    base_year = config.YEARS[-1]

    # ── 1단계: 시군구 코드/이름 발견 (최신 연도로 스캔) ──────────
    print("[1단계] 시군구 코드 발견...", flush=True)
    regions = {}
    for sido in config.SIDO_LIST:
        prefix = sido["code"][:2]
        codes = [f"{prefix}{seq:02d}" for seq in range(1, SCAN_MAX + 1)]
        items_list = list(pool.map(lambda g: fetch(base_year, sido["code"], g), codes))
        guguns = []
        for g, items in zip(codes, items_list):
            t = total_row(items)
            if t:
                guguns.append({"code": g, "name": t.get("sido_sgg_nm", "")})
        regions[sido["name"]] = {"sido_code": sido["code"], "guguns": guguns}
        print(f"  {sido['name']}: {len(guguns)}개", flush=True)

    with open("src/region_codes.json", "w", encoding="utf-8") as f:
        json.dump(regions, f, ensure_ascii=False, indent=2)

    # ── 2단계: 발견한 시군구 × 전체 연도 통계 수집 ───────────────
    print("[2단계] 연도별 통계 수집...", flush=True)
    jobs = []   # (year, sido_name, sido_code, gugun_code)
    for sido_name, info in regions.items():
        for gg in info["guguns"]:
            for year in config.YEARS:
                jobs.append((year, sido_name, info["sido_code"], gg["code"]))

    def run(job):
        year, sido_name, sc, gc = job
        t = total_row(fetch(year, sc, gc))
        if not t:
            return None
        row = {
            "연도": year, "시도": sido_name,
            "시군구": t.get("sido_sgg_nm", ""),
            "사고건수": int(t.get("acc_cnt", 0) or 0),
            "사망자수": int(t.get("dth_dnv_cnt", 0) or 0),
            "부상자수": int(t.get("injpsn_cnt", 0) or 0),
            "치사율": float(t.get("ftlt_rate", 0) or 0),
        }
        for col, label in config.ACC_TYPE_014.items():
            row[label] = int(t.get(col, 0) or 0)
        for col, label in config.VIOLATION_027.items():
            row[label] = int(t.get(col, 0) or 0)
        return row

    rows = [r for r in pool.map(run, jobs) if r]
    pool.shutdown()

    os.makedirs("data", exist_ok=True)
    df = pd.DataFrame(rows).sort_values(["연도", "시도", "시군구"])
    df.to_csv("data/stat.csv", index=False, encoding="utf-8-sig")
    print(f"\n저장 완료: data/stat.csv ({len(df)}행), src/region_codes.json "
          f"(시군구 {sum(len(v['guguns']) for v in regions.values())}개)", flush=True)


if __name__ == "__main__":
    main()

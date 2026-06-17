"""
[1회 실행] TAAS 자체 시도/시군구 코드를 전수 발견해 src/region_codes.json 으로 저장.

주의: 이 API 는 동시 호출(병렬)을 제한(throttle)한다. → 순차 호출만 신뢰 가능.
호출당 ~0.6초. 시군구는 번호가 연속이므로 연속 공번 10개면 조기 종료.

발견된 사실:
- 코드 = siDo(4자리) + guGun(4자리). guGun 앞 2자리 = siDo 앞 2자리.
- siDo 는 100 단위 자체 코드(1100=서울, 1200=부산, ...). 법정동 코드와 무관.
- resultCode: 00=정상, 03=NODATA(공번), 10=INVALID → 00 만 유효, 나머지는 즉시 건너뜀.
"""
import json, time, requests

KEY = "5aba1891a83c1bfad8f50be96ba4950cab9c26acf30de3ca45cc80ec83d1120b"
URL = "http://apis.data.go.kr/B552061/lgStat/getRestLgStat"
YEAR = 2022
DELAY = 0.05


def query(sido_code, gugun_code):
    """반환: 지역명(str) 또는 None. 네트워크 오류만 짧게 재시도."""
    params = {"ServiceKey": KEY, "type": "json", "searchYearCd": YEAR,
              "siDo": sido_code, "guGun": gugun_code, "numOfRows": 1, "pageNo": 1}
    for attempt in range(3):
        try:
            r = requests.get(URL, params=params, timeout=20)
            if r.status_code == 200:
                j = r.json()
                if j.get("resultCode") == "00":
                    it = j["items"]["item"]
                    it = it[0] if isinstance(it, list) else it
                    return it["sido_sgg_nm"]
                return None
        except Exception:
            time.sleep(0.4 * (attempt + 1))
    return None


# 1) 시도 코드 발견: XX(11~52) × siDo=XX00, guGun=XX01~XX03 중 첫 유효
print("[1단계] 시도 코드 탐색...", flush=True)
sido = []   # (sido_code, sido_name)
for xx in range(11, 53):
    sc = f"{xx:02d}00"
    for s in range(1, 4):
        nm = query(sc, f"{xx:02d}{s:02d}")
        time.sleep(DELAY)
        if nm:
            sido.append((sc, nm.split()[0]))
            print(f"  {sc} -> {nm.split()[0]}", flush=True)
            break

# 2) 각 시도의 시군구 스캔 (연속 공번 10개면 조기 종료)
print("[2단계] 시군구 코드 탐색...", flush=True)
result = {}
for sc, sname in sido:
    prefix = sc[:2]
    guguns = []
    miss = 0
    for seq in range(1, 61):
        nm = query(sc, f"{prefix}{seq:02d}")
        time.sleep(DELAY)
        if nm:
            guguns.append({"code": f"{prefix}{seq:02d}", "name": nm})
            miss = 0
        else:
            miss += 1
            if miss >= 10:
                break
    result[sname] = {"sido_code": sc, "guguns": guguns}
    print(f"  {sname}: {len(guguns)}개", flush=True)

with open("src/region_codes.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
total = sum(len(v["guguns"]) for v in result.values())
print(f"\n저장 완료: src/region_codes.json  (시도 {len(result)}, 시군구 총 {total}개)", flush=True)

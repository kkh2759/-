"""
도로교통공단 Open API 호출 담당.

핵심 아이디어
- 모든 함수는 결과를 pandas DataFrame 으로 돌려준다.
- @st.cache_data 로 같은 요청은 캐시 → API 호출 횟수(하루 1만회 제한) 절약 + 속도 향상.
- 키가 없으면 호출하지 않는다(상위 data_loader 에서 mock 으로 우회).
"""

import requests
import pandas as pd
import streamlit as st

from . import config


def get_api_key():
    """secrets.toml 의 TAAS_API_KEY 를 읽는다. 없으면 None."""
    try:
        return st.secrets["TAAS_API_KEY"]
    except Exception:
        return None


def _call(endpoint: str, params: dict) -> dict:
    """API 를 호출하고 JSON(dict) 으로 반환. 실패 시 예외를 그대로 올린다."""
    params = {**params, "type": "json"}
    resp = requests.get(endpoint, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_stat(year: int, sido_code: str) -> pd.DataFrame:
    """지자체별 교통사고 통계 (집계). 연도/지역/사고유형 분석에 사용."""
    key = get_api_key()
    data = _call(
        config.ENDPOINT_STAT,
        {"ServiceKey": key, "searchYearCd": year, "siDo": sido_code,
         "numOfRows": 100, "pageNo": 1},
    )
    rows = _extract_items(data)
    df = pd.DataFrame(rows)
    df["연도"] = year
    return df


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_freq_zone(year: int, sido_code: str, gugun_code: str) -> pd.DataFrame:
    """교통사고 다발지역 (위경도 포함). 지도에 사용."""
    key = get_api_key()
    data = _call(
        config.ENDPOINT_FREQ,
        {"ServiceKey": key, "searchYearCd": year, "siDo": sido_code,
         "guGun": gugun_code, "numOfRows": 100, "pageNo": 1},
    )
    rows = _extract_items(data)
    return pd.DataFrame(rows)


def _extract_items(data: dict):
    """공공데이터포털 표준 응답에서 items 리스트만 꺼낸다.

    응답 구조가 API마다 조금씩 달라서 흔한 두 가지 형태를 모두 처리한다.
    구조가 안 맞으면 raw 를 보고 이 함수를 살짝 고치면 된다.
    """
    # 형태 A: { "items": { "item": [ ... ] } }
    if isinstance(data.get("items"), dict):
        item = data["items"].get("item", [])
        return item if isinstance(item, list) else [item]
    # 형태 B: { "response": { "body": { "items": { "item": [...] } } } }
    body = data.get("response", {}).get("body", {})
    items = body.get("items", {})
    if isinstance(items, dict):
        item = items.get("item", [])
        return item if isinstance(item, list) else [item]
    if isinstance(items, list):
        return items
    return []


def raw_probe(endpoint: str, params: dict) -> dict:
    """연결 테스트용: 캐시 없이 그대로 호출해 원본 JSON 을 반환."""
    params = {**params, "ServiceKey": get_api_key(), "type": "json"}
    resp = requests.get(endpoint, params=params, timeout=15)
    return {"status_code": resp.status_code, "url": resp.url, "body": resp.text[:4000]}

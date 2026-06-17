"""
화면(app.py)이 데이터를 가져오는 단일 창구.

통계 데이터 우선순위:
  1) data/stat.csv 가 있으면 → 실제 데이터 (build_stat_cache.py 로 미리 받아둔 것)
  2) 없으면              → 샘플(mock) 데이터

이렇게 하면 앱은 런타임에 API 를 직접 호출하지 않아 빠르고, 호출 한도도 아끼게 된다.
지도(다발지역)/시간대 데이터는 해당 API 키가 준비되면 같은 방식으로 확장한다.
"""
import os
import pandas as pd
import streamlit as st

from . import api_client, mock_data, config

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
_STAT_CSV = os.path.join(_DATA_DIR, "stat.csv")
_FREQ_CSV = os.path.join(_DATA_DIR, "freq.csv")


def stat_source() -> str:
    """'real' (CSV 있음) 또는 'mock' 반환."""
    return "real" if os.path.exists(_STAT_CSV) else "mock"


# ── 연도/지역/사고유형/원인 통계 (wide 스키마) ──────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def load_stat() -> pd.DataFrame:
    if stat_source() == "real":
        return pd.read_csv(_STAT_CSV)
    return mock_data.stat_all()


# ── 다발지역(지도) ─────────────────────────────────────────────
def freq_source() -> str:
    """'real' (freq.csv 있음) 또는 'mock'."""
    return "real" if os.path.exists(_FREQ_CSV) else "mock"


@st.cache_data(ttl=3600, show_spinner=False)
def _load_freq_all() -> pd.DataFrame:
    return pd.read_csv(_FREQ_CSV)


def load_freq_zones(sido_name: str) -> pd.DataFrame:
    if freq_source() == "mock":
        return mock_data.freq_zones(sido_name)
    df = _load_freq_all()
    return df[df["시도"] == sido_name].reset_index(drop=True)

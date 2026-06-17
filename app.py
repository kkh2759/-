"""
교통사고 분석 대시보드 (Streamlit)
실행:  streamlit run app.py

API 키가 없으면 '샘플 데이터'로, 있으면 '실제 데이터'로 자동 전환됩니다.
"""

import pandas as pd
import plotly.express as px
import streamlit as st
import folium
import streamlit.components.v1 as components

from src import data_loader, api_client, config

# ── 페이지 기본 설정 ───────────────────────────────────────────
st.set_page_config(page_title="교통사고 분석 대시보드", page_icon="🚦", layout="wide")

st.title("🚦 교통사고 분석 대시보드")

# 데이터 출처 표시 (샘플 / 실제)
_stat_real = data_loader.stat_source() == "real"
_freq_real = data_loader.freq_source() == "real"
if _stat_real and _freq_real:
    st.success("✅ 전부 실제 데이터 사용 중 (도로교통공단 / data.go.kr)")
elif _stat_real:
    st.success("✅ 통계는 실제 데이터, 지도는 샘플입니다.")
else:
    st.warning("⚠️ 현재 **샘플(가짜) 데이터**입니다. "
               "`build_stat_cache.py` / `build_freq_cache.py` 실행 시 실제 데이터로 바뀝니다.")

# ── 사이드바: 필터 ─────────────────────────────────────────────
st.sidebar.header("🔎 필터")
sel_sido = st.sidebar.selectbox("시도(지역)", config.SIDO_NAMES, index=0)
sel_years = st.sidebar.select_slider(
    "분석 기간(연도)", options=config.YEARS,
    value=(config.YEARS[0], config.YEARS[-1]),
)

# 통계 데이터 로드 (캐시됨)
stat = data_loader.load_stat()
y0, y1 = sel_years
stat_f = stat[(stat["연도"] >= y0) & (stat["연도"] <= y1)]

# ── 상단 요약 지표 ─────────────────────────────────────────────
c1, c2, c3 = st.columns(3)
c1.metric("총 사고건수", f"{int(stat_f['사고건수'].sum()):,} 건")
c2.metric("총 사망자수", f"{int(stat_f['사망자수'].sum()):,} 명")
c3.metric("총 부상자수", f"{int(stat_f['부상자수'].sum()):,} 명")

# ── 탭 구성 ────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📈 연도별 추이", "🗺️ 지역별 비교", "⚠️ 위험지역·치사율",
    "🚗 사고유형·원인", "📍 다발지역 지도", "🔌 API 연결 테스트",
])

# 1) 연도별 추이 ------------------------------------------------
with tab1:
    st.subheader("연도별 사고 추이")
    by_year = stat_f.groupby("연도", as_index=False)[["사고건수", "사망자수", "부상자수"]].sum()
    metric = st.radio("지표 선택", ["사고건수", "사망자수", "부상자수"], horizontal=True, key="t1")
    fig = px.line(by_year, x="연도", y=metric, markers=True,
                  title=f"연도별 {metric} 추이")
    fig.update_xaxes(dtick=1)
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(by_year, use_container_width=True)

# 2) 지역별 비교 ------------------------------------------------
with tab2:
    st.subheader("지역(시도)별 비교")
    by_sido = stat_f.groupby("시도", as_index=False)[["사고건수", "사망자수", "부상자수"]].sum()
    metric = st.radio("지표 선택", ["사고건수", "사망자수", "부상자수"], horizontal=True, key="t2")
    by_sido = by_sido.sort_values(metric, ascending=True)
    fig = px.bar(by_sido, x=metric, y="시도", orientation="h",
                 title=f"시도별 {metric}", text_auto=True)
    st.plotly_chart(fig, use_container_width=True)

# 3) 위험지역·치사율 --------------------------------------------
with tab3:
    st.subheader("시군구별 위험지역 순위 · 치사율")
    g = stat_f.groupby(["시도", "시군구"], as_index=False)[
        ["사고건수", "사망자수", "부상자수"]].sum()
    # 치사율 = 사망자수 / 사고건수 × 100 (집계 후 계산해야 정확)
    g["치사율"] = (g["사망자수"] / g["사고건수"] * 100).round(2)

    c1, c2 = st.columns([2, 1])
    metric = c1.radio("기준 지표", ["사고건수", "사망자수", "치사율"],
                      horizontal=True, key="t3")
    topn = c2.slider("표시 개수", 5, 30, 15, key="t3n")
    top = g.sort_values(metric, ascending=False).head(topn)
    fig = px.bar(top.sort_values(metric), x=metric, y="시군구", orientation="h",
                 title=f"{metric} 상위 {topn}개 시군구", text_auto=True, height=520)
    st.plotly_chart(fig, use_container_width=True)
    st.caption("치사율 = 사망자수 ÷ 사고건수 × 100. 기간 내 합계 기준.")
    st.dataframe(g.sort_values(metric, ascending=False), use_container_width=True)

# 4) 사고유형·원인 ----------------------------------------------
with tab4:
    st.subheader("사고유형 · 법규위반(원인)별 분석")
    colA, colB = st.columns(2)
    with colA:
        type_cols = [c for c in config.ACC_TYPE_LABELS if c in stat_f.columns]
        by_type = stat_f[type_cols].sum().reset_index()
        by_type.columns = ["사고유형", "사고건수"]
        by_type = by_type[by_type["사고건수"] > 0]
        fig = px.pie(by_type, names="사고유형", values="사고건수", title="사고유형 비율")
        st.plotly_chart(fig, use_container_width=True)
    with colB:
        viol_cols = [c for c in config.VIOLATION_LABELS if c in stat_f.columns]
        by_v = stat_f[viol_cols].sum().reset_index()
        by_v.columns = ["법규위반", "사고건수"]
        by_v = by_v[by_v["사고건수"] > 0].sort_values("사고건수", ascending=True)
        fig = px.bar(by_v, x="사고건수", y="법규위반", orientation="h",
                     title="법규위반(원인)별 사고건수", text_auto=True)
        st.plotly_chart(fig, use_container_width=True)

# 5) 다발지역 지도 ----------------------------------------------
with tab5:
    st.subheader(f"📍 {sel_sido} 사고 다발지역 지도")
    zones = data_loader.load_freq_zones(sel_sido)
    if zones.empty or "위도" not in zones.columns:
        st.info("이 지역의 다발지역 데이터가 없습니다.")
    else:
        st.caption(f"다발지역 {len(zones)}곳 · 원 크기 = 발생건수 "
                   + ("(실제 데이터)" if data_loader.freq_source() == "real" else "(샘플)"))
        center = [zones["위도"].mean(), zones["경도"].mean()]
        m = folium.Map(location=center, zoom_start=11)
        for _, r in zones.iterrows():
            radius = 4 + float(r.get("발생건수", 5)) ** 0.5 * 2
            popup = (f"<b>{r.get('지점명', '')}</b><br>"
                     f"발생 {r.get('발생건수', '-')}건 · "
                     f"사상자 {r.get('사상자수', '-')}명 · "
                     f"사망 {r.get('사망자수', '-')}명")
            folium.CircleMarker(
                location=[r["위도"], r["경도"]],
                radius=min(radius, 25),
                popup=folium.Popup(popup, max_width=300),
                color="#E03131", fill=True, fill_opacity=0.5,
            ).add_to(m)
        # st_folium 은 탭 안에서 렌더링이 불안정하여 정적 HTML 로 표출
        components.html(m._repr_html_(), height=560)

# 6) API 연결 테스트 --------------------------------------------
with tab6:
    st.subheader("🔌 API 연결 테스트")
    st.write("발급받은 키가 제대로 동작하는지, 응답 필드명이 무엇인지 직접 확인하는 곳입니다.")
    if api_client.get_api_key() is None:
        st.error("아직 API 키가 없습니다. `.streamlit/secrets.toml` 에 TAAS_API_KEY 를 넣어주세요.")
    else:
        year = st.selectbox("연도", config.YEARS, index=len(config.YEARS) - 1)
        sido = st.selectbox("시도", config.SIDO_LIST, format_func=lambda x: x["name"])
        if st.button("통계 API 호출해 보기"):
            res = api_client.raw_probe(config.ENDPOINT_STAT, {
                "searchYearCd": year, "siDo": sido["code"], "numOfRows": 5, "pageNo": 1,
            })
            st.write("상태코드:", res["status_code"])
            st.code(res["body"], language="json")

st.sidebar.markdown("---")
st.sidebar.caption("데이터: 도로교통공단 / 공공데이터포털(data.go.kr)")

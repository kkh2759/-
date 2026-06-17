# 🚦 교통사고 분석 대시보드

공공데이터(도로교통공단 / data.go.kr)를 활용한 교통사고 분석 웹사이트입니다.
**Python + Streamlit + Plotly + Folium** 으로 만들었고, **무료로 배포**할 수 있습니다.

분석 항목: ① 연도별 추이 ② 지역별 비교 ③ 위험지역·치사율 순위 ④ 사고유형·원인 ⑤ 다발지역 지도
(모든 분석이 **실제 데이터**로 동작합니다.)

---

## 1. 지금 바로 실행하기 (API 키 없이도 됨)

API 키가 없어도 **샘플 데이터**로 모든 화면이 그대로 보입니다.

Windows PowerShell에서:

```powershell
# 프로젝트 폴더로 이동
cd "C:\Users\user\Desktop\기환"

# 가상환경의 Streamlit으로 실행
.\.venv\Scripts\streamlit.exe run app.py
```

→ 잠시 뒤 브라우저에서 `http://localhost:8501` 이 자동으로 열립니다.

---

## 2. 실제 데이터 연결하기 (API 키 발급)

1. [공공데이터포털(data.go.kr)](https://www.data.go.kr) 회원가입 / 로그인
2. 아래 2개 API에서 **[활용신청]** 클릭 (즉시 자동승인, 무료)
   - **한국도로교통공단_지자체별 대상 교통사고 통계** → 연도/지역/유형/치사율 분석용
   - **한국도로교통공단_지자체별 교통사고 다발지역** → 지도용 (위경도 제공)
   - (계정당 인증키 1개로 신청한 모든 API를 사용합니다)
3. 마이페이지 → **일반 인증키(Decoding)** 값을 복사
4. `.streamlit\secrets.toml.example` 을 복사해 같은 폴더에 **`secrets.toml`** 로 저장하고,
   키 값을 붙여넣기:
   ```toml
   TAAS_API_KEY = "복사한_인증키"
   ```
5. 앱을 다시 실행하면 상단이 **"✅ 실제 API 데이터 사용 중"** 으로 바뀝니다.

> 💡 키를 넣은 뒤 **`🔌 API 연결 테스트`** 탭에서 버튼을 누르면 실제 응답을 눈으로 확인할 수 있습니다.
> 응답의 실제 필드명이 코드와 다르면 `src/data_loader.py` 의 `rename` 부분만 맞춰주면 됩니다.

---

## 3. 데이터 갱신 (실제 데이터 받아오기)

앱은 빠른 속도와 API 호출 한도 절약을 위해 **미리 받아둔 CSV**(`data/stat.csv`, `data/freq.csv`)를
읽습니다. 새 연도 데이터가 공개되면 아래 스크립트로 다시 받으면 됩니다.

```powershell
cd "C:\Users\user\Desktop\기환"
.\.venv\Scripts\python.exe build_stat_cache.py   # 통계(연도/지역/유형/원인) → data/stat.csv
.\.venv\Scripts\python.exe build_freq_cache.py   # 다발지역(지도)            → data/freq.csv
.\.venv\Scripts\python.exe verify_data.py        # 무결성 검증
```

> ⚠️ 이 API는 **동시 호출이 많으면 응답을 누락(throttle)** 합니다. 빌더는 워커 3개 +
> 재시도로 이를 회피하므로, 빌더 실행 중에는 다른 API 호출 스크립트를 동시에 돌리지 마세요.

### 확인된 API 코드 체계 (참고)
- **통계 API**(`lgStat`): TAAS 자체 시도코드(서울 `1100`·부산 `1200`…`2700`) + 시군구 `시도앞2자리+순번`. 시군구 단위 조회.
- **다발지역 API**(`frequentzoneLg`): **법정동 코드**(서울 `11`·강남 `680`). `guGun=""`(빈값)이면 시도 전체 반환.

## 4. 무료 배포 (Streamlit Community Cloud)

1. [Git](https://git-scm.com/download/win) 설치 (아직 미설치)
2. 이 폴더를 GitHub 저장소에 업로드
   - ⚠️ `secrets.toml` 은 `.gitignore` 에 등록되어 **올라가지 않습니다(정상)**
3. [share.streamlit.io](https://share.streamlit.io) 접속 → GitHub 연동 → 저장소 선택
4. 배포 설정의 **Secrets** 칸에 아래를 입력 (로컬 secrets.toml과 동일):
   ```toml
   TAAS_API_KEY = "복사한_인증키"
   ```
5. Deploy → 몇 분 뒤 누구나 접속 가능한 주소가 생성됩니다.

---

## 폴더 구조

```
기환/
├─ app.py                  # 메인 화면 (탭 6개)
├─ requirements.txt        # 배포 시 필요한 라이브러리 목록
├─ build_stat_cache.py     # [갱신] 통계 데이터 수집 → data/stat.csv
├─ build_freq_cache.py     # [갱신] 다발지역 데이터 수집 → data/freq.csv
├─ build_region_codes.py   # [참고] 시도/시군구 코드 탐색
├─ verify_data.py          # 데이터 무결성 검증
├─ smoke_test.py           # 개발용 빠른 점검 스크립트
├─ .gitignore
├─ data/
│  ├─ stat.csv             # 연도×시군구 통계 (실제 데이터, 1,146행)
│  └─ freq.csv             # 다발지역 좌표 (실제 데이터, 658곳)
├─ .streamlit/
│  ├─ config.toml          # 화면 테마
│  └─ secrets.toml.example # API 키 입력 템플릿 (복사해서 secrets.toml 생성)
└─ src/
   ├─ config.py            # 엔드포인트 / 연도 / 시도코드 / 사고유형·법규위반 매핑
   ├─ api_client.py        # API 호출 헬퍼 + 캐시 (연결테스트 탭용)
   ├─ mock_data.py         # 샘플(가짜) 데이터 생성 (CSV 없을 때 대체)
   ├─ data_loader.py       # 화면이 부르는 단일 데이터 창구 (CSV/샘플 자동 전환)
   └─ region_codes.json    # 시도→시군구 코드표 (빌더가 생성)
```

## 참고

- 데이터 출처: 도로교통공단 / [공공데이터포털](https://www.data.go.kr)
- 개발 요청 한도: 일 10,000회 (앱에 1시간 캐시가 걸려 있어 절약됨)

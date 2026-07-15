# 데이터 디렉터리

`raw/`는 승인된 원본 데이터를 보관하기 위한 위치입니다. 일반 SQLite 파일(`*.db`,
`*.sqlite`, `*.sqlite3`)과 별도로 전달받은 원본 데이터는 Git에 커밋하지 않습니다. 단,
Render에서 사용하는 `backend/data/sai42.db`는 공공데이터가 적재된 배포 스냅샷이므로 추적합니다.

## 대전·충청권 관광 공공데이터

장소 데이터는 한국관광공사 TourAPI 4.0의 대전·충청권 자료를 사용합니다.

- 제공 기관: 한국관광공사
- 원본 API: https://www.data.go.kr/data/15101578/openapi.do
- 라이선스: 공공누리 제3유형(출처 표시 + 변경 금지)
- 전달받은 원본: 8개 유형 1,365건
- DB 적재: DB/API 명세에서 제외한 축제·공연·행사(유형 15) 26건을 뺀 1,339건

원본 TourAPI 필드는 의미를 바꾸지 않고 `places`의 snake_case 컬럼으로 옮깁니다. 좌표는
검색을 위해 `REAL`, 지도 레벨과 콘텐츠 유형은 `INTEGER`, 원본 일시는 Asia/Seoul 기준 ISO
8601 `TEXT`로 저장합니다. 빈 원본 문자열은 그대로 보존합니다.

현재 API의 `District`는 대전 5개 구만 정의하므로 대전 주소만 `district`로 매핑하고 추천
가능 상태로 표시합니다. 공주·논산·계룡·옥천 등 나머지 충청권 장소도 원본 조회와 향후 지역
확장을 위해 적재하지만, 현재 대전 코스 추천에서는 제외합니다. 원본에 없는 실내외, 분위기,
비용, 체류시간과 추천 점수는 임의로 추정하지 않습니다.

콘텐츠 유형과 향후 Place API 카테고리의 변환 기준은 다음과 같습니다.

| TourAPI ID | 유형 | PlaceCategory | 기본 ActivityType |
|---:|---|---|---|
| 12 | 관광지 | `ATTRACTION` | `TOURISM` |
| 14 | 문화시설 | `CULTURAL_FACILITY` | `CULTURE_EXHIBITION` |
| 25 | 여행코스 | `TRAVEL_COURSE` | `TOURISM`, `WALK` |
| 28 | 레포츠 | `LEPORTS` | `LEPORTS` |
| 32 | 숙박 | `ACCOMMODATION` | 없음 |
| 38 | 쇼핑 | `SHOPPING` | `SHOPPING` |
| 39 | 음식점 | `RESTAURANT` | `FOOD` |
| 15 | 축제공연행사 | 명세상 제외 | 명세상 제외 |

## 적재 방법

백엔드 가상환경에서 마이그레이션을 먼저 적용한 후, 원본 JSON 파일들이 있는 디렉터리를
전달합니다. 같은 `content_id`는 갱신되므로 명령을 다시 실행해도 중복 행이 생기지 않습니다.

```powershell
cd backend
python -m alembic upgrade head
python -m scripts.import_places --source-dir "C:\path\to\대전_충청권"
```

기본 DB 경로는 `backend/data/sai42.db`이며 `DATABASE_URL` 또는 `--database-url`로 바꿀 수
있습니다. 이 DB는 Render 배포 초기 상태로 사용되므로 공공데이터를 갱신한 경우 코드와 함께
DB 파일도 반영해야 합니다.

배포 DB에는 실제 개인정보, 실제 비밀번호, Secret 또는 라이선스가 불명확한 데이터를 넣지
않습니다. Render 실행 중 생성된 과제용 사용자 데이터는 재배포·재시작 시 커밋된 DB 상태로
초기화됩니다.

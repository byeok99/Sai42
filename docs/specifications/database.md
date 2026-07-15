# 사이42 데이터베이스 명세

> 원본: [`DB-v4.0.pdf`](../sources/DB-v4.0.pdf), v4.0 (9쪽)
>
> 변환 기준일: 2026-07-15
>
> 문서 성격: 원본을 구조화하고 2026-07-15 확정 결정을 반영한 구현 기준 명세

## 1. 기본 정책

| 항목 | 계약 |
|---|---|
| DBMS | SQLite |
| ORM | SQLAlchemy |
| 서비스 PK | UUID v4 문자열 (`TEXT`) |
| 장소 PK | TourAPI `content_id` |
| 날짜·시간 | ISO 8601 `TEXT` |
| Boolean | `INTEGER` 0/1 |
| Enum | `TEXT` + `CHECK` |
| JSON | JSON 문자열을 담은 `TEXT` |
| 외래키 | 연결 직후 `PRAGMA foreign_keys = ON` |

비밀번호는 과제 요구에 따라 숫자 4자리 평문으로 저장한다. 로그, 오류 응답, trace에는 절대 노출하지 않는다.

## 2. 테이블과 책임

| 테이블 | 책임 |
|---|---|
| `user_profiles` | 익명 프로필 |
| `places` | 공공데이터 및 추천용 장소 정보 |
| `chat_sessions` | 데이트 조건, AI 대화, 코스 초안 |
| `date_courses` | 현재·완료 데이트 코스 |
| `date_course_places` | 코스 장소 스냅샷 및 장소별 하트 |
| `community_posts` | 랭킹보드 게시글 |
| `community_likes` | 게시글 좋아요 |

총 7개 테이블로 구성한다.

## 3. `user_profiles`

| 컬럼 | 타입 | 제약 | 설명 |
|---|---|---|---|
| `id` | `TEXT` | PK | 프로필 UUID |
| `nickname` | `TEXT` | NOT NULL | 표시 닉네임 |
| `nickname_normalized` | `TEXT` | NOT NULL, UNIQUE | 중복 검사용 닉네임 |
| `password` | `TEXT` | NOT NULL | 숫자 4자리 평문 비밀번호 |
| `created_at` | `TEXT` | NOT NULL | 생성일 |
| `updated_at` | `TEXT` | NOT NULL | 수정일 |
| `deleted_at` | `TEXT` | NULL | 논리 삭제일 |

추가 제약:

```sql
CHECK(length(nickname) BETWEEN 2 AND 14)
CHECK(length(password) = 4 AND password GLOB '[0-9][0-9][0-9][0-9]')
```

데이트 성향은 이 테이블에 저장하지 않는다. 코스를 만들 때마다 `chat_sessions.conditions_json`에 저장한다.

## 4. `places`

TourAPI 원본 데이터와 추천용 가공 컬럼을 함께 저장한다. 축제·공연인 `content_type_id = 15`는 적재 및 추천 대상에서 제외한다.

### 4.1 원본 컬럼

원본 `DB-v4.0.pdf`는 `places`의 개별 타입을 생략한다. 아래 타입과 null 허용 여부는 현재 마이그레이션 `20260715_0001_create_places.py`와 대조해 보완 표기했다.

| 컬럼 | 타입 | Null | 설명 |
|---|---|---:|---|
| `content_id` | `TEXT` | N | PK, TourAPI 콘텐츠 ID |
| `content_type_id` | `INTEGER` | N | TourAPI 콘텐츠 유형 |
| `title` | `TEXT` | N | 장소명 |
| `address` | `TEXT` | N | 기본 주소 |
| `address_detail` | `TEXT` | N | 상세 주소, 원본 공백 문자열 보존 |
| `zipcode` | `TEXT` | N | 우편번호 |
| `telephone` | `TEXT` | N | 전화번호 |
| `longitude` | `REAL` | N | 경도 |
| `latitude` | `REAL` | N | 위도 |
| `map_level` | `INTEGER` | Y | 지도 레벨 |
| `area_code` | `TEXT` | N | 지역 코드 |
| `sigungu_code` | `TEXT` | N | 시군구 코드 |
| `legal_region_code` | `TEXT` | N | 법정동 지역 코드 |
| `legal_sigungu_code` | `TEXT` | N | 법정동 시군구 코드 |
| `category1` | `TEXT` | N | TourAPI 대분류 |
| `category2` | `TEXT` | N | TourAPI 중분류 |
| `category3` | `TEXT` | N | TourAPI 소분류 |
| `class_code1` | `TEXT` | N | 분류체계 1 |
| `class_code2` | `TEXT` | N | 분류체계 2 |
| `class_code3` | `TEXT` | N | 분류체계 3 |
| `image_url` | `TEXT` | N | 대표 이미지 URL |
| `thumbnail_url` | `TEXT` | N | 썸네일 URL |
| `copyright_code` | `TEXT` | N | 저작권 코드 |
| `source_created_at` | `TEXT` | Y | 원본 생성 시각 |
| `source_modified_at` | `TEXT` | Y | 원본 수정 시각 |

### 4.2 추천용 컬럼

| 컬럼 | 타입 | Null/기본값 | 설명 |
|---|---|---|---|
| `district` | `TEXT` | NULL | 대전 5개 구 enum 값 |
| `space_type` | `TEXT` | NULL | 실내·실외 유형 |
| `moods_json` | `TEXT` | NOT NULL, `[]` | 분위기 배열 |
| `activities_json` | `TEXT` | NOT NULL, `[]` | 활동 배열 |
| `keywords_json` | `TEXT` | NOT NULL, `[]` | 검색·추천 키워드 배열 |
| `description` | `TEXT` | NULL | 장소 설명 |
| `estimated_stay_minutes` | `INTEGER` | NULL | 예상 체류 시간 |
| `estimated_cost` | `INTEGER` | NULL | 예상 비용 |
| `rain_suitability` | `REAL` | NULL | 우천 적합도 |
| `conversation_score` | `REAL` | NULL | 대화 적합도 |
| `photo_score` | `REAL` | NULL | 사진 적합도 |
| `is_recommendable` | `INTEGER` | NOT NULL, 0 | 추천 가능 여부 |
| `created_at` | `TEXT` | NOT NULL | 생성일 |
| `updated_at` | `TEXT` | NOT NULL | 수정일 |

추가 제약:

```sql
CHECK(content_type_id IN (12, 14, 25, 28, 32, 38, 39))
CHECK(is_recommendable IN (0, 1))
```

공공데이터 및 추천용 컬럼 구조는 현재 상태를 유지한다.

## 5. `chat_sessions`

| 컬럼 | 타입 | 제약 | 설명 |
|---|---|---|---|
| `id` | `TEXT` | PK | 채팅 세션 UUID |
| `profile_id` | `TEXT` | FK, NOT NULL | 프로필 |
| `status` | `TEXT` | NOT NULL | `ACTIVE`, `CONFIRMED`, `DISCARDED`, `EXPIRED` |
| `conditions_json` | `TEXT` | NOT NULL | 이번 데이트 조건 |
| `messages_json` | `TEXT` | NOT NULL | AI 대화 내역 |
| `draft_json` | `TEXT` | NULL | 현재 코스 초안 |
| `draft_version` | `INTEGER` | NOT NULL | 낙관적 잠금 버전 |
| `weather_json` | `TEXT` | NULL | 추천 당시 날씨 |
| `created_at` | `TEXT` | NOT NULL | 생성일 |
| `updated_at` | `TEXT` | NOT NULL | 수정일 |
| `confirmed_at` | `TEXT` | NULL | 확정일 |
| `expires_at` | `TEXT` | NULL | 만료일 |

`conditions_json` 필수 의미 필드:

```json
{
  "date": "YYYY-MM-DD",
  "timeSlot": "MORNING | AFTERNOON | FULL_DAY",
  "startTime": "HH:mm",
  "district": "District",
  "spaceType": "SpaceType",
  "moods": ["Mood"],
  "activities": ["ActivityType"],
  "scheduleDensity": "ScheduleDensity",
  "transportation": "Transportation"
}
```

## 6. `date_courses`

| 컬럼 | 타입 | 제약 | 설명 |
|---|---|---|---|
| `id` | `TEXT` | PK | 코스 UUID |
| `profile_id` | `TEXT` | FK, NOT NULL | 소유 프로필 |
| `chat_session_id` | `TEXT` | FK, NULL | 원본 AI 세션 |
| `status` | `TEXT` | NOT NULL | `ACTIVE`, `COMPLETED` |
| `source_type` | `TEXT` | NOT NULL | `AI_CHAT`, `RANKING_COPY`, `HISTORY_RESTART` |
| `source_course_id` | `TEXT` | Self FK, NULL | 복사 원본 코스 |
| `title` | `TEXT` | NOT NULL | 코스 제목 |
| `date` | `TEXT` | NOT NULL | 데이트 날짜 |
| `start_time` | `TEXT` | NOT NULL | 시작 시간 |
| `time_slot` | `TEXT` | NOT NULL | 시간대 |
| `main_district` | `TEXT` | NOT NULL | 대표 지역구 |
| `space_type` | `TEXT` | NOT NULL | 공간 조건 |
| `moods_json` | `TEXT` | NOT NULL | 분위기 조건 |
| `activities_json` | `TEXT` | NOT NULL | 활동 조건 |
| `schedule_density` | `TEXT` | NOT NULL | 일정 밀도 |
| `transportation` | `TEXT` | NULL | 이동수단 |
| `overall_comment` | `TEXT` | NOT NULL | AI 전체 멘트 |
| `tags_json` | `TEXT` | NOT NULL | 코스 태그 |
| `weather_json` | `TEXT` | NULL | 날씨 스냅샷 |
| `current_order_no` | `INTEGER` | NOT NULL | 다음에 완료할 장소 순서. 마지막 장소 완료 후에는 마지막 순서를 유지 |
| `completion_comment` | `TEXT` | NULL | 종료 한 줄 코멘트 |
| `started_at` | `TEXT` | NULL | 시작 시각 |
| `completed_at` | `TEXT` | NULL | 완료 시각 |
| `created_at` | `TEXT` | NOT NULL | 생성일 |
| `updated_at` | `TEXT` | NOT NULL | 수정일 |

상태와 활성 코스 제약:

```sql
CHECK(status IN ('ACTIVE', 'COMPLETED'))

CREATE UNIQUE INDEX uq_one_active_course_per_profile
ON date_courses(profile_id)
WHERE status = 'ACTIVE';
```

현재 데이트 취소 기능은 없으므로 `CANCELED`, `canceled_at`, `cancel_reason`을 사용하지 않는다. 확정된 코스의 내용은 수정할 수 없다.

코스 생성·복사 시 애플리케이션 트랜잭션은 `date_course_places`를 2~4개 생성해야 한다. `current_order_no`의 초기값은 가장 작은 `order_no`다. 전체 예상 소요시간은 첫 `scheduled_at`부터 마지막 `scheduled_at + estimated_stay_minutes`까지를 API에서 계산하며 별도 컬럼으로 저장하지 않는다.

## 7. `date_course_places`

| 컬럼 | 타입 | 제약 | 설명 |
|---|---|---|---|
| `id` | `TEXT` | PK | 코스 장소 UUID |
| `date_course_id` | `TEXT` | FK, NOT NULL | 데이트 코스 |
| `content_id` | `TEXT` | FK, NULL | 원본 장소 |
| `order_no` | `INTEGER` | NOT NULL | 방문 순서 |
| `scheduled_at` | `TEXT` | NOT NULL | 예정 시간 |
| `estimated_stay_minutes` | `INTEGER` | NOT NULL | 예상 체류시간 |
| `sweet_comment` | `TEXT` | NOT NULL | 장소별 AI 멘트 |
| `hearted` | `INTEGER` | NOT NULL, DEFAULT 0 | 장소 하트 여부 |
| `hearted_at` | `TEXT` | NULL | 장소 하트 시각 |
| `completed_at` | `TEXT` | NULL | 방문 완료 시각 |
| `title_snapshot` | `TEXT` | NOT NULL | 장소명 스냅샷 |
| `address_snapshot` | `TEXT` | NULL | 주소 스냅샷 |
| `address_detail_snapshot` | `TEXT` | NULL | 상세 주소 스냅샷 |
| `longitude_snapshot` | `REAL` | NULL | 경도 스냅샷 |
| `latitude_snapshot` | `REAL` | NULL | 위도 스냅샷 |
| `content_type_id_snapshot` | `INTEGER` | NOT NULL | 유형 스냅샷 |
| `district_snapshot` | `TEXT` | NULL | 지역구 스냅샷 |
| `space_type_snapshot` | `TEXT` | NOT NULL | 공간 유형 스냅샷 |
| `image_url_snapshot` | `TEXT` | NULL | 이미지 스냅샷 |
| `created_at` | `TEXT` | NOT NULL | 생성일 |

추가 제약:

```sql
UNIQUE(date_course_id, order_no)
UNIQUE(date_course_id, content_id)
CHECK(hearted IN (0, 1))
```

장소별 하트는 본인의 `ACTIVE` 코스에서만 변경한다. 랭킹과 추억에서는 조회만 가능하다.

## 8. `community_posts`

| 컬럼 | 타입 | 제약 | 설명 |
|---|---|---|---|
| `id` | `TEXT` | PK | 게시글 UUID |
| `date_course_id` | `TEXT` | FK, UNIQUE, NOT NULL | 완료 코스 |
| `author_profile_id` | `TEXT` | FK, NULL | 작성자 |
| `author_nickname_snapshot` | `TEXT` | NOT NULL | 공개 당시 닉네임 |
| `one_line_comment` | `TEXT` | NOT NULL | 공개 코멘트 |
| `status` | `TEXT` | NOT NULL | `PUBLISHED`, `DELETED` |
| `published_at` | `TEXT` | NOT NULL | 가장 최근 공개 또는 재공개 시각 |
| `updated_at` | `TEXT` | NOT NULL | 수정일 |
| `deleted_at` | `TEXT` | NULL | 삭제일 |

작성자는 본인의 `one_line_comment`만 수정할 수 있다. 게시글 삭제는 논리 삭제이며 완료 코스와 좋아요 행은 유지한다.

삭제 게시글 재발행 규칙:

1. `date_course_id`로 `DELETED` 행을 조회한다.
2. 새 행을 INSERT하지 않고 같은 `id`의 행을 `PUBLISHED`로 복원한다.
3. `published_at`과 `updated_at`을 복원 처리 시각으로 갱신하고 `deleted_at`을 NULL로 만든다.
4. `one_line_comment`를 재발행 요청 값으로 교체한다.
5. 작성자 ID와 닉네임 스냅샷을 재발행한 현재 프로필로 갱신한다.
6. 기존 `community_likes` 행을 유지하므로 좋아요 수와 사용자별 좋아요 상태도 이어진다.

이 규칙은 `UNIQUE(date_course_id)`와 논리 삭제 정책을 함께 만족한다.

## 9. `community_likes`

| 컬럼 | 타입 | 제약 | 설명 |
|---|---|---|---|
| `id` | `TEXT` | PK | 좋아요 UUID |
| `profile_id` | `TEXT` | FK, NOT NULL | 좋아요 사용자 |
| `community_post_id` | `TEXT` | FK, NOT NULL | 대상 게시글 |
| `created_at` | `TEXT` | NOT NULL | 생성일 |

```sql
UNIQUE(profile_id, community_post_id)
```

게시글 좋아요는 다시 누르면 취소한다. 삭제된 게시글에는 좋아요를 등록할 수 없다.

## 10. FK와 삭제 정책

| 자식 FK | 부모 | 삭제 정책 |
|---|---|---|
| `chat_sessions.profile_id` | `user_profiles.id` | CASCADE |
| `date_courses.profile_id` | `user_profiles.id` | CASCADE |
| `date_courses.chat_session_id` | `chat_sessions.id` | SET NULL |
| `date_courses.source_course_id` | `date_courses.id` | SET NULL |
| `date_course_places.date_course_id` | `date_courses.id` | CASCADE |
| `date_course_places.content_id` | `places.content_id` | SET NULL |
| `community_posts.date_course_id` | `date_courses.id` | RESTRICT |
| `community_posts.author_profile_id` | `user_profiles.id` | SET NULL |
| `community_likes.profile_id` | `user_profiles.id` | CASCADE |
| `community_likes.community_post_id` | `community_posts.id` | CASCADE |

## 11. 랭킹 산출

### 11.1 인기 코스

```sql
SELECT cp.id, COUNT(cl.id) AS like_count
FROM community_posts cp
LEFT JOIN community_likes cl ON cl.community_post_id = cp.id
WHERE cp.status = 'PUBLISHED'
GROUP BY cp.id
ORDER BY like_count DESC, cp.published_at DESC, cp.id ASC;
```

### 11.2 데이트 마스터

사용자별 공개 게시글이 받은 좋아요 합계를 기준으로 계산한다.

### 11.3 장소별 누적 하트

```sql
SELECT content_id, COUNT(*) AS heart_count
FROM date_course_places
WHERE hearted = 1
GROUP BY content_id;
```

게시글 좋아요와 장소별 하트는 별개의 데이터다.

## 12. 핵심 트랜잭션

### 12.1 코스 확정

1. 초안과 버전을 확인한다.
2. `ACTIVE` 코스 중복을 확인한다.
3. `date_courses`를 생성한다.
4. `date_course_places` 스냅샷을 생성한다.
5. `chat_sessions.status`를 `CONFIRMED`로 변경한다.
6. 전체를 커밋한다.

### 12.2 데이트 종료

1. 본인의 `ACTIVE` 코스를 확인한다.
2. 모든 `date_course_places.completed_at`이 존재하는지 확인한다.
3. 장소별 하트 상태를 유지한다.
4. 한 줄 코멘트를 저장한다. 평점·만족도는 저장하지 않는다.
5. 코스를 `COMPLETED`로 변경한다.
6. `community_posts`를 자동 생성한다.
7. 전체를 커밋한다.

### 12.3 게시글 좋아요

1. 게시글이 `PUBLISHED`인지 확인한다.
2. 기존 좋아요 유무를 확인한다.
3. `community_likes`를 삽입하거나 삭제한다.
4. 커밋한다.

### 12.4 코스 다시 진행

1. 원본 코스를 조회한다.
2. `ACTIVE` 코스 중복을 확인한다.
3. 새 `date_courses`를 생성한다.
4. 장소·추천 문구·조건 스냅샷을 복사한다.
5. 새 장소의 `hearted=0`, `hearted_at=NULL`, `completed_at=NULL`로 초기화한다.
6. 코스의 `current_order_no`를 첫 순서, `started_at=NULL`로 초기화한다.
7. 커밋한다.

랭킹보드 공개 코스 복사에도 같은 초기화 규칙을 적용한다.

### 12.5 현재 장소 완료와 다음 장소 전환

1. 본인의 `ACTIVE` 코스와 대상 `date_course_places`를 조회한다.
2. 대상이 이미 완료됐으면 저장 값을 바꾸지 않고 현재 진행 상태를 반환한다.
3. 미완료 대상의 `order_no`가 `date_courses.current_order_no`와 같은지 확인한다.
4. 다르면 순서 충돌로 롤백한다.
5. 대상의 `completed_at`에 서버 시각을 기록한다.
6. 다음 장소가 있으면 `current_order_no`를 다음 `order_no`로 갱신한다.
7. 마지막 장소면 `current_order_no`는 마지막 순서를 유지한다. 코스 상태는 종료 요청 전까지 `ACTIVE`다.
8. 커밋하고 완료 수, 전체 수, 다음 장소를 반환한다.

### 12.6 삭제 게시글 재발행

1. 본인의 완료 코스와 `date_course_id`가 같은 게시글을 삭제 상태까지 포함해 조회한다.
2. `PUBLISHED`면 중복 오류로 종료한다.
3. `DELETED` 행의 상태, 공개일, 코멘트, 작성자 스냅샷을 재발행 규칙대로 갱신한다.
4. 기존 좋아요 행은 변경하지 않는다.
5. 커밋한다.

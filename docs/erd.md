# HomeLens AI — ERD 설계 문서

> Entity Relationship Diagram v4.0 | MVP 우선순위 1 전용

| 항목 | 내용 |
|------|------|
| 문서 버전 | v4.0 |
| 작성일 | 2026-04-27 |
| 기반 문서 | 요구사항 정의서 v3.0 / API 명세서 v4.0 |
| 적용 범위 | MVP 우선순위 1 기능 전용 (FR-01~FR-09) |

### 컬럼 색상 범례

| 색상 | 의미 |
|------|------|
| 노란 배경 | Primary Key (PK) |
| 연두 배경 | Foreign Key (FK) |
| 파란 배경 헤더 | 테이블명/컬럼명 헤더 |
| 흰 배경 | NOT NULL 일반 컬럼 |

---

## 변경 이력

| 버전 | 일자 | 주요 변경 내용 |
|------|------|----------------|
| v1.0 | 2026-04-22 | 최초 작성 |
| v2.0 | 2026-04-23 | 신규 테이블 6개 추가 (analysis_summaries, price_stats, analysis_decisions, analysis_decision_regions, analysis_decision_points, map_markers, commercial_density) |
| v4.0 | 2026-04-27 | MVP 우선순위 1 기준 재편: 상권분석·종합요약·종합판단·AI질의응답·용어사전·정책 관련 테이블 제외. 가격분석·뉴스/이슈·AI리포트·지도시각화 테이블만 유지. |

---

## 목차 (MVP 1순위 테이블)

1. [지역/위치 마스터](#1-지역위치-마스터) — `regions`, `locations`, `places`
2. [뉴스/이슈](#2-뉴스이슈) — `news`, `news_keywords`, `news_regions`, `issues`
3. [가격 분석](#3-가격-분석) — `price_snapshots`, `price_trends`, `price_stats`
4. [지도 시각화](#4-지도-시각화) — `map_markers`
5. [AI 리포트](#5-ai-리포트) — `reports`, `report_items`, `report_sections`
6. [테이블 간 관계 요약](#6-테이블-간-관계-요약-mvp-1순위)

---

## 1. 지역/위치 마스터

### `regions` — 행정구역 마스터

서비스 내부 지역 식별자(regionId) 기준 마스터 테이블. 모든 분석 API의 핵심 참조 테이블.

| 컬럼명 | 타입 | NULL | Key | 설명 |
|--------|------|------|-----|------|
| **id** | VARCHAR(50) | NOT NULL | PK | 서비스 내부 지역 ID (예: `REGION_11680_DONG_001`) |
| name | VARCHAR(100) | NOT NULL | | 지역명 (예: 성수동) |
| full_address | VARCHAR(300) | NOT NULL | | 전체 주소 (예: 서울특별시 성동구 성수1가1동) |
| legal_dong_code | VARCHAR(20) | NOT NULL | | 법정동 코드 (국토부 API 내부 연동용) |
| lat | DECIMAL(10,7) | NOT NULL | | 중심 위도 (WGS84) |
| lng | DECIMAL(10,7) | NOT NULL | | 중심 경도 (WGS84) |
| property_type | VARCHAR(20) | NOT NULL | | Enum: `apartment` \| `commercial` \| `area` \| `landmark` |
| source_type | VARCHAR(20) | NOT NULL | | Enum: `region` \| `address` \| `building` \| `complex` |
| created_at | TIMESTAMP | NOT NULL | | 생성 일시 |
| updated_at | TIMESTAMP | NOT NULL | | 수정 일시 |

> MVP 1순위에서 `supported_modes` 컬럼 제외 (모드 선택 기능 2차 이후). 단지 단위 검색을 위해 `property_type='apartment'` 위주 사용.

---

### `locations` — 건물/단지/상가 위치 마스터

아파트 단지, 개별 건물 등 구체적 위치 정보. `regions`의 하위 개념. `/places/search` 및 검색 결과 화면에 활용.

| 컬럼명 | 타입 | NULL | Key | 설명 |
|--------|------|------|-----|------|
| **id** | VARCHAR(50) | NOT NULL | PK | 위치 고유 ID |
| region_id | VARCHAR(50) | NOT NULL | FK | FK → `regions.id` |
| name | VARCHAR(200) | NOT NULL | | 건물/단지명 |
| address | VARCHAR(300) | NOT NULL | | 도로명 주소 |
| property_type | VARCHAR(20) | NOT NULL | | Enum: `apartment` \| `commercial` \| `landmark` |
| lat | DECIMAL(10,7) | NOT NULL | | 위도 (WGS84) |
| lng | DECIMAL(10,7) | NOT NULL | | 경도 (WGS84) |
| floors | INT | NULL | | 층수 |
| build_year | INT | NULL | | 건축연도 |
| created_at | TIMESTAMP | NOT NULL | | 생성 일시 |

---

### `places` — 카카오맵 장소 검색 결과

카카오맵 API 프록시 처리 결과. `/places/search` 응답 캐시. 주변 인프라 정보(FR-04) 및 지도 표시(FR-03)에 활용.

| 컬럼명 | 타입 | NULL | Key | 설명 |
|--------|------|------|-----|------|
| **id** | VARCHAR(50) | NOT NULL | PK | 장소 고유 ID (서비스 내부) |
| region_id | VARCHAR(50) | NOT NULL | FK | FK → `regions.id` (속한 행정 지역) |
| kakao_place_id | VARCHAR(50) | NULL | | 카카오맵 원본 장소 ID (외부 키 보관) |
| name | VARCHAR(200) | NOT NULL | | 장소명 |
| address | VARCHAR(300) | NOT NULL | | 도로명 주소 |
| place_type | VARCHAR(20) | NOT NULL | | Enum: `subway` \| `school` \| `mart` \| `hospital` \| `apartment` \| `landmark` |
| lat | DECIMAL(10,7) | NOT NULL | | 위도 |
| lng | DECIMAL(10,7) | NOT NULL | | 경도 |
| distance_m | INT | NULL | | 단지 중심 기준 도보 거리 (미터, 주로 지하철역) |
| created_at | TIMESTAMP | NOT NULL | | 생성 일시 |

> v4.0 변경: `place_type`에 `subway`, `school`, `mart`, `hospital` 추가 (FR-04 주변 인프라 목록 표시 지원). `property_type` → `place_type`으로 필드명 변경.

---

## 2. 뉴스/이슈

### `news` — 부동산 뉴스

네이버 뉴스 API 수집 후 AI 요약 처리. `/news/highlights` (FR-09) 및 `/analysis/issues` (FR-06) 연동.

| 컬럼명 | 타입 | NULL | Key | 설명 |
|--------|------|------|-----|------|
| **id** | VARCHAR(50) | NOT NULL | PK | 뉴스 고유 ID |
| title | VARCHAR(500) | NOT NULL | | 뉴스 제목 |
| summary | TEXT | NOT NULL | | AI 요약문 (1~2줄) |
| source | VARCHAR(100) | NOT NULL | | 출처 언론사명 |
| url | VARCHAR(1000) | NOT NULL | | 원문 링크 |
| category | VARCHAR(20) | NOT NULL | | Enum: `policy` \| `market` \| `development` \| `law` |
| published_at | TIMESTAMP | NOT NULL | | 기사 발행 일시 |
| created_at | TIMESTAMP | NOT NULL | | 수집 일시 |

---

### `news_keywords` — 뉴스 키워드 (`news` 자식)

| 컬럼명 | 타입 | NULL | Key | 설명 |
|--------|------|------|-----|------|
| **id** | BIGINT AUTO_INCREMENT | NOT NULL | PK | 자동 증가 PK |
| news_id | VARCHAR(50) | NOT NULL | FK | FK → `news.id` |
| keyword | VARCHAR(100) | NOT NULL | | 키워드 |
| sort_order | INT | NOT NULL | | 정렬 순서 |

---

### `news_regions` — 뉴스 ↔ 지역 연결 (N:M)

| 컬럼명 | 타입 | NULL | Key | 설명 |
|--------|------|------|-----|------|
| **news_id** | VARCHAR(50) | NOT NULL | PK/FK | FK → `news.id` (복합 PK) |
| **region_id** | VARCHAR(50) | NOT NULL | PK/FK | FK → `regions.id` (복합 PK) |

---

### `issues` — 통합 이슈 타임라인

`/analysis/issues` 응답 (FR-06). 뉴스·이슈를 통합한 지역별 이슈 타임라인.

| 컬럼명 | 타입 | NULL | Key | 설명 |
|--------|------|------|-----|------|
| **id** | VARCHAR(50) | NOT NULL | PK | 이슈 ID |
| region_id | VARCHAR(50) | NOT NULL | FK | FK → `regions.id` |
| type | VARCHAR(20) | NOT NULL | | Enum: `news` \| `policy` \| `traffic` |
| title | VARCHAR(500) | NOT NULL | | 이슈 제목 |
| summary | TEXT | NOT NULL | | AI 요약 (1~2줄) |
| impact_type | VARCHAR(20) | NOT NULL | | Enum: `positive` \| `negative` \| `neutral` |
| published_at | TIMESTAMP | NOT NULL | | 발생/발표 일시 |
| url | VARCHAR(1000) | NULL | | 원문 링크 |
| ref_id | VARCHAR(50) | NULL | | 원본 ID (`news.id` 참조) |
| created_at | TIMESTAMP | NOT NULL | | 수집 일시 |

> v4.0 변경: MVP 1순위에서 개발계획(`development`) 미포함. `type` Enum에서 `development` 제외. `data_source` 컬럼 제외 (2차 이후 도입).

---

## 3. 가격 분석

### `price_snapshots` — 지역별 가격 현황 스냅샷

국토부 실거래가 API 수집 결과. `/analysis/price` (FR-02, FR-05) 응답. `dataBaseDate` 변경 시 재생성.

| 컬럼명 | 타입 | NULL | Key | 설명 |
|--------|------|------|-----|------|
| **id** | BIGINT AUTO_INCREMENT | NOT NULL | PK | 자동 증가 PK |
| region_id | VARCHAR(50) | NOT NULL | FK | FK → `regions.id` |
| avg_sale_price | BIGINT | NULL | | 평균 매매가 (원) |
| avg_jeonse_price | BIGINT | NULL | | 평균 전세가 (원) |
| avg_monthly_rent | BIGINT | NULL | | 평균 월세 (원) |
| avg_monthly_deposit | BIGINT | NULL | | 평균 월세 보증금 (원) |
| jeonse_ratio | DECIMAL(5,2) | NULL | | 전세가율 (%). 메인 지도 '전세가율' 탭에 활용 |
| recent_trade_count | INT | NULL | | 최근 1개월 거래 건수. 메인 지도 '매매 거래량' 탭에 활용 |
| price_stability_grade | VARCHAR(10) | NOT NULL | | Enum: `stable` \| `normal` \| `volatile` |
| price_level | VARCHAR(15) | NOT NULL | | Enum: `low` \| `below_avg` \| `avg` \| `above_avg` \| `high` |
| data_base_date | DATE | NOT NULL | | 실거래가 기준일 (국토부 공공데이터, 캐시 무효화 기준) |
| created_at | TIMESTAMP | NOT NULL | | 수집 일시 |

> 동일 `region_id` + `data_base_date` 조합에 UNIQUE 인덱스 적용 권장.  
> v4.0 변경: `recent_trade_count` 추가 (FR-08 메인 지도 거래량 탭 지원).

---

### `price_trends` — 월별 가격 추이

`/analysis/price/trend` (FR-05) 응답. 차트 시각화용 월별 데이터. 국토부 실거래가 API 기반.

| 컬럼명 | 타입 | NULL | Key | 설명 |
|--------|------|------|-----|------|
| **id** | BIGINT AUTO_INCREMENT | NOT NULL | PK | 자동 증가 PK |
| region_id | VARCHAR(50) | NOT NULL | FK | FK → `regions.id` |
| month | CHAR(7) | NOT NULL | | 기준 월 (YYYY-MM) |
| deal_type | VARCHAR(10) | NOT NULL | | Enum: `sale` \| `jeonse` \| `monthly` |
| avg_price | BIGINT | NOT NULL | | 해당 월 평균 가격 (원) |
| trade_count | INT | NOT NULL | | 해당 월 거래 건수 |
| created_at | TIMESTAMP | NOT NULL | | 수집 일시 |

---

### `price_stats` — 가격 통계 (최저/평균/최고)

`/analysis/price/stats` (FR-05) 응답 캐시. 기간별 최저·평균·최고 가격 및 거래량 통계.

| 컬럼명 | 타입 | NULL | Key | 설명 |
|--------|------|------|-----|------|
| **id** | BIGINT AUTO_INCREMENT | NOT NULL | PK | 자동 증가 PK |
| region_id | VARCHAR(50) | NOT NULL | FK | FK → `regions.id` |
| deal_type | VARCHAR(10) | NOT NULL | | Enum: `sale` \| `jeonse` \| `monthly` \| `all` |
| period | VARCHAR(5) | NOT NULL | | 분석 기간 Enum: `1m` \| `3m` \| `1y` |
| min_price | BIGINT | NOT NULL | | 최저 거래가 (원) |
| avg_price | BIGINT | NOT NULL | | 평균 거래가 (원) |
| max_price | BIGINT | NOT NULL | | 최고 거래가 (원) |
| total_trade_count | INT | NOT NULL | | 기간 내 총 거래 건수 |
| recent_trade_count | INT | NOT NULL | | 최근 1개월 거래 건수 |
| trade_signal | VARCHAR(10) | NOT NULL | | Enum: `active` \| `normal` \| `low` (거래 활성도) |
| data_base_date | DATE | NOT NULL | | 실거래가 기준일 (캐시 무효화 기준) |
| created_at | TIMESTAMP | NOT NULL | | 수집 일시 |

> `region_id` + `deal_type` + `period` + `data_base_date` 조합에 UNIQUE 인덱스 권장.  
> v4.0 변경: `period` Enum을 v2.0(`1y`\|`3y`)에서 `1m`\|`3m`\|`1y`로 확장 (FR-05 가격분석 탭 1개월/3개월/1년 지원).

---

## 4. 지도 시각화

### `map_markers` — 지도 마커 캐시

`/map/markers` (FR-03) 응답 캐시. 지역 내 아파트 마커 위치 및 가격 수준. 카카오맵 마커 연동. 메인 지도 탭 버튼(FR-08) 색상 레이어에도 활용.

| 컬럼명 | 타입 | NULL | Key | 설명 |
|--------|------|------|-----|------|
| **id** | VARCHAR(50) | NOT NULL | PK | 마커 고유 ID |
| region_id | VARCHAR(50) | NOT NULL | FK | FK → `regions.id` |
| name | VARCHAR(200) | NOT NULL | | 건물/단지명 |
| address | VARCHAR(300) | NOT NULL | | 주소 |
| lat | DECIMAL(10,7) | NOT NULL | | 위도 |
| lng | DECIMAL(10,7) | NOT NULL | | 경도 |
| marker_type | VARCHAR(20) | NOT NULL | | Enum: `apartment` \| `landmark` (MVP에서 상권 마커 제외) |
| avg_price | BIGINT | NULL | | 평균 가격 (원, 아파트 시) |
| price_level | VARCHAR(10) | NULL | | Enum: `low` \| `avg` \| `high` (가격 수준) |
| trade_count | INT | NULL | | 최근 거래량 (FR-08 메인 지도 거래량 탭) |
| jeonse_ratio | DECIMAL(5,2) | NULL | | 전세가율 (FR-08 메인 지도 전세가율 탭) |
| created_at | TIMESTAMP | NOT NULL | | 수집 일시 |
| updated_at | TIMESTAMP | NOT NULL | | 갱신 일시 |

> v4.0 변경: `marker_type`에서 `commercial` 제외 (상권 마커 2차 이후). `trade_count`, `jeonse_ratio` 컬럼 추가 (FR-08 메인 지도 탭 버튼 지원).  
> `locations` 테이블과 병행 운영, 지도 렌더링 전용 최적화 캐시.

---

## 5. AI 리포트

### `reports` — AI 리포트 (비동기 생성)

`POST /reports` 요청 관리 + `GET /reports/{id}` 결과 저장. Polling 상태 관리 포함. FR-07 AI 요약 리포트.

| 컬럼명 | 타입 | NULL | Key | 설명 |
|--------|------|------|-----|------|
| **id** | VARCHAR(50) | NOT NULL | PK | 리포트 고유 ID |
| region_id | VARCHAR(50) | NOT NULL | FK | FK → `regions.id` |
| status | VARCHAR(15) | NOT NULL | | Enum: `pending` \| `processing` \| `completed` \| `failed` |
| progress_pct | INT | NULL | | 진행률 (0~100, `processing` 시) |
| summary | TEXT | NULL | | 핵심 요약 (2~3줄) |
| disclaimer | TEXT | NULL | | 면책 문구 (필수 포함) |
| fail_reason | TEXT | NULL | | 실패 사유 |
| data_base_date | DATE | NULL | | 데이터 기준일 (캐시 무효화 기준) |
| cached_at | TIMESTAMP | NULL | | 캐시 생성 시각 |
| completed_at | TIMESTAMP | NULL | | 리포트 완료 시각 |
| generated_at | TIMESTAMP | NULL | | 리포트 생성 시각 |
| created_at | TIMESTAMP | NOT NULL | | 요청 생성 일시 |

> v4.0 변경: v2.0의 `mode`, `deal_type`, `budget`, `industry` 컬럼 제외 (모드선택 2차 이후).  
> `region_id` + `data_base_date` 조합으로 캐시 관리. 동일 조건 리포트 존재 시 `409 REPORT_ALREADY_EXISTS` 반환.

---

### `report_sections` — AI 리포트 세부 섹션 (`reports` 자식)

FR-07 AI 요약 리포트의 4섹션 (가격동향/생활환경/지역이슈/종합의견) 저장.

| 컬럼명 | 타입 | NULL | Key | 설명 |
|--------|------|------|-----|------|
| **id** | BIGINT AUTO_INCREMENT | NOT NULL | PK | 자동 증가 PK |
| report_id | VARCHAR(50) | NOT NULL | FK | FK → `reports.id` |
| section_key | VARCHAR(30) | NOT NULL | | Enum: `price_trend` \| `life_env` \| `local_issues` \| `overall` (4섹션 고정) |
| section_title | VARCHAR(200) | NOT NULL | | 섹션 제목 (예: 가격 동향) |
| content | TEXT | NOT NULL | | 섹션 내용 (AI 생성) |
| sort_order | INT | NOT NULL | | 정렬 순서 (1~4) |

> v4.0 변경: `section_key` 컬럼 추가 (v3.0 4섹션 구조 고정: `price_trend`/`life_env`/`local_issues`/`overall`).  
> `report_items` 테이블은 2차 이후 (strengths/weaknesses 등 모드별 항목).

---

## 6. 테이블 간 관계 요약 (MVP 1순위)

| From 테이블 | 관계 | To 테이블 | 설명 |
|-------------|------|-----------|------|
| `regions` | 1 : N | `locations` | 한 지역에 여러 건물/단지 위치 |
| `regions` | 1 : N | `places` | 한 지역에 여러 카카오맵 장소 (주변 인프라 포함) |
| `regions` | 1 : N | `issues` | 한 지역에 여러 통합 이슈 |
| `regions` | 1 : N | `price_snapshots` | 한 지역에 날짜별 가격 스냅샷 |
| `regions` | 1 : N | `price_trends` | 한 지역에 월별 가격 추이 |
| `regions` | 1 : N | `price_stats` | 한 지역에 기간별 가격 통계 |
| `regions` | 1 : N | `map_markers` | 한 지역에 여러 지도 마커 |
| `regions` | 1 : N | `reports` | 한 지역에 여러 AI 리포트 |
| `news` | 1 : N | `news_keywords` | 뉴스 1건 : 키워드 N개 |
| `news` | N : M | `regions` (via `news_regions`) | 뉴스 ↔ 영향 지역 다대다 |
| `reports` | 1 : N | `report_sections` | 리포트 1건 : 4섹션 (가격동향/생활환경/지역이슈/종합의견) |

---

## 7. 설계 노트

- 모든 타임스탬프는 **UTC 기준 저장**. 서비스 레이어에서 KST(+09:00) 변환.
- `regionId`는 서비스 내부 식별자 (`REGION_11680_DONG_001` 형식). 법정동 코드(`legalDongCode`)와 별도 관리.
- `price_snapshots`는 `data_base_date` 기준 캐시 무효화. 동일 `region_id` + `data_base_date`에 UNIQUE 인덱스 권장.
- `price_stats`의 `period`는 `1m`\|`3m`\|`1y` (FR-05 가격분석 탭 기간 선택 지원).
- `map_markers`는 `locations` 테이블과 병행 운영. 지도 렌더링 전용 최적화 캐시.
- `reports`는 비동기 생성(Polling 방식). 동일 `region_id` + `data_base_date` 조건 리포트 존재 시 409 반환 (재사용 권장).

### MVP 1순위 제외 테이블 (2차 이후 도입)

| 그룹 | 테이블 |
|------|--------|
| 상권 분석 | `commercial_analysis`, `commercial_top_categories`, `competitors`, `commercial_density` |
| 종합 요약/판단 | `analysis_summaries`, `analysis_decisions`, `analysis_decision_regions`, `analysis_decision_points` |
| AI 질의응답 | `conversations`, `chat_messages`, `chat_suggested_questions`, `chat_related_terms` |
| 용어 사전 | `glossary`, `glossary_metrics`, `glossary_relations` |
| 정책/개발계획 | `policies`, `policy_regions`, `developments` (이슈 탭에서 뉴스 중심으로 대체) |
| 모드별 리포트 항목 | `report_items` (모드별 strengths/weaknesses 항목) |

---

*CONFIDENTIAL | HomeLens AI ERD 설계 문서 | MVP v4.0 (1순위 전용)*

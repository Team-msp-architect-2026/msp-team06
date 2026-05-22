# HomeLens AI — API 명세서

> v4.0 | MVP 우선순위 1 전용 | BASE URL: `https://api.homelens.ai/api/v1`

| 항목 | 내용 |
|------|------|
| 문서 버전 | v4.0 |
| 작성일 | 2026-04-27 |
| Base URL | https://api.homelens.ai/api/v1 |
| 인증 방식 | API Key (HTTP Header: `X-API-KEY`) |
| Rate Limit | 분당 5회 / 일 20회 (API Key 단위) |
| 적용 범위 | MVP 우선순위 1 기능 전용 (FR-01~FR-09). 상권분석·모드별분석·AI질의응답·용어사전 제외. |

---

## 목차

1. [공통 규격](#1-공통-규격)
2. [메인화면 API](#2-메인화면-api)
   - 2-1. 지역 검색 (자동완성) `GET /regions/search`
   - 2-2. 장소 검색 (아파트/단지) `GET /places/search`
   - 2-3. 부동산 뉴스 하이라이트 `GET /news/highlights`
   - 2-4. 지도 가격 레이어 `GET /map/price-layer`
3. [지역 기본 정보 API](#3-지역-기본-정보-api)
   - 3-1. 지역 기본 정보 조회 `GET /regions/{regionId}`
   - 3-2. 위치 기반 조회 `GET /locations/{locationId}`
4. [가격 분석 API](#4-가격-분석-api)
   - 4-1. 가격 분석 (최신 현황) `GET /analysis/price`
   - 4-2. 가격 추이 `GET /analysis/price/trend`
   - 4-3. 가격 통계 `GET /analysis/price/stats`
   - 4-4. 이슈/뉴스 분석 `GET /analysis/issues`
5. [지도 시각화 API](#5-지도-시각화-api)
   - 5-1. 지도 마커 `GET /map/markers`
6. [AI 리포트 API](#6-ai-리포트-api)
   - 6-1. AI 리포트 생성 요청 `POST /reports`
   - 6-2. AI 리포트 상태 조회 `GET /reports/{reportId}/status`
   - 6-3. AI 리포트 결과 조회 `GET /reports/{reportId}`
7. [에러 코드](#7-에러-코드)
8. [외부 API 연동 매핑](#8-외부-api-연동-매핑)

---

## 1. 공통 규격

### 1-1. 환경별 Base URL

| 환경 | Base URL |
|------|----------|
| Production | `https://api.homelens.ai/api/v1` |
| Staging | `https://staging-api.homelens.ai/api/v1` |
| Local Dev | `http://localhost:8080/api/v1` |

### 1-2. 인증

| 헤더명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| `X-API-KEY` | String (Header) | ✓ 필수 | 발급된 API Key. 모든 요청에 반드시 포함 |
| `Content-Type` | String (Header) | POST 필수 | `application/json` (POST 요청 시) |

### 1-3. 공통 응답 구조

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `success` | Boolean | ✓ 필수 | 요청 처리 성공 여부 |
| `data` | Object\|Array | 선택 | 실제 응답 데이터 (실패 시 null) |
| `error` | Object\|null | 선택 | 오류 정보 (성공 시 null) |
| `error.code` | String | 선택 | 에러 코드 (예: `INVALID_PARAMETER`) |
| `error.message` | String | 선택 | 한국어 오류 메시지 |
| `meta` | Object\|null | 선택 | 페이지네이션 메타 (cursor, hasNext, total) |

---

## 2. 메인화면 API

### 2-1. 지역 검색 (자동완성)

**`GET /regions/search`**

행정동명, 구·동·아파트명 입력 시 자동완성 결과 반환. 도로명주소 API를 백엔드에서 프록시 처리. (FR-01)

#### Query Parameters

| 필드명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| `q` | String | ✓ 필수 | 검색 키워드 (최소 1자). 예: `마포래미안`, `아현동` |
| `limit` | Integer | 선택 | 반환 최대 건수 (기본 10, 최대 20) |
| `cursor` | String | 선택 | Cursor 기반 페이지네이션 토큰 |

#### Response Body

| 필드명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| `regionId` | String | ✓ 필수 | 서비스 내부 지역 ID |
| `name` | String | ✓ 필수 | 지역명 (예: 성수동) |
| `fullAddress` | String | ✓ 필수 | 전체 주소 |
| `propertyType` | Enum | ✓ 필수 | `area` \| `building` \| `complex` \| `landmark` |
| `lat` | Float | ✓ 필수 | 중심 위도 |
| `lng` | Float | ✓ 필수 | 중심 경도 |

> 도로명주소 API (행정안전부) + 카카오맵 API를 백엔드에서 프록시 처리. 클라이언트에 원본 키 미노출.

---

### 2-2. 장소 검색 (아파트/단지)

**`GET /places/search`**

건물명·아파트명으로 장소 검색. 카카오맵 API 프록시 처리. (FR-01)

#### Query Parameters

| 필드명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| `q` | String | ✓ 필수 | 검색 키워드 (예: `마포래미안푸르지오`) |
| `type` | Enum | 선택 | `apartment` \| `all` (기본 `all`) |
| `lat` | Float | 선택 | 현재 위치 위도 (근처 우선 정렬 시) |
| `lng` | Float | 선택 | 현재 위치 경도 (근처 우선 정렬 시) |
| `limit` | Integer | 선택 | 반환 최대 건수 (기본 10, 최대 20) |

#### Response Body

| 필드명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| `placeId` | String | ✓ 필수 | 장소 고유 ID |
| `regionId` | String | ✓ 필수 | 해당 장소가 속한 서비스 내부 지역 ID |
| `name` | String | ✓ 필수 | 장소명 |
| `address` | String | ✓ 필수 | 도로명 주소 |
| `propertyType` | Enum | ✓ 필수 | `apartment` \| `landmark` |
| `lat` | Float | ✓ 필수 | 위도 |
| `lng` | Float | ✓ 필수 | 경도 |

> 카카오맵 API를 백엔드에서 프록시 처리. 주변 인프라 검색(FR-04)에도 동일 엔드포인트 활용.

---

### 2-3. 부동산 뉴스 하이라이트

**`GET /news/highlights`**

메인화면 하단 주요 부동산 뉴스 반환. 네이버 뉴스 API 수집·AI요약. (FR-09)

#### Query Parameters

| 필드명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| `limit` | Integer | 선택 | 반환 건수 (기본 10, 최대 20) |
| `cursor` | String | 선택 | Cursor 기반 페이지네이션 토큰 |
| `category` | Enum | 선택 | `all` \| `policy` \| `market` \| `development` \| `law` (기본 `all`) |

#### Response Body

| 필드명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| `newsId` | String | ✓ 필수 | 뉴스 고유 ID |
| `title` | String | ✓ 필수 | 뉴스 제목 |
| `summary` | String | ✓ 필수 | AI 요약문 (1~2줄) |
| `source` | String | ✓ 필수 | 출처 언론사명 |
| `url` | String | ✓ 필수 | 원문 링크 |
| `publishedAt` | ISO 8601 | ✓ 필수 | 기사 발행 일시 |
| `category` | Enum | ✓ 필수 | `policy` \| `market` \| `development` \| `law` |
| `keywords` | Array\<String\> | 선택 | 주요 키워드 목록 |

> 기사 원문 미전재. 제목·AI요약·원문 링크만 제공. 저작권 준수 정책 적용.

---

### 2-4. 지도 가격 레이어 (메인 지도 탭 버튼)

**`GET /map/price-layer`**

메인화면 지도 탭 버튼 ('매매 거래량' / '전세가율' / '월세 부담 낮은 곳') 데이터 반환. (FR-08)

#### Query Parameters

| 필드명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| `regionId` | String | ✓ 필수 | 서비스 내부 지역 ID |
| `type` | Enum | 선택 | `sale_count` (매매 거래량) \| `jeonse_ratio` (전세가율) \| `monthly_burden` (월세 부담) (기본 `sale_count`) |

#### Response Body

| 필드명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| `zones` | Array\<Object\> | ✓ 필수 | 구역별 색상 데이터 목록 |
| `zones[].zoneId` | String | ✓ 필수 | 구역 ID |
| `zones[].lat` | Float | ✓ 필수 | 구역 중심 위도 |
| `zones[].lng` | Float | ✓ 필수 | 구역 중심 경도 |
| `zones[].value` | Float | ✓ 필수 | type별 수치 (거래건수 \| 전세가율% \| 월세부담지수) |
| `zones[].priceGrade` | Integer | ✓ 필수 | 색상 등급 (1~5, 1=최저/5=최고) |
| `dataBaseDate` | ISO 8601 (Date) | ✓ 필수 | 데이터 기준일 |

---

## 3. 지역 기본 정보 API

### 3-1. 지역 기본 정보 조회

**`GET /regions/{regionId}`**

서비스 내부 regionId로 지역 메타 정보 조회.

#### Path Variables

| 필드명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| `regionId` | String (Path) | ✓ 필수 | 서비스 내부 지역 ID |

#### Response Body

| 필드명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| `regionId` | String | ✓ 필수 | 서비스 내부 지역 ID |
| `name` | String | ✓ 필수 | 지역명 |
| `fullAddress` | String | ✓ 필수 | 전체 주소 |
| `legalDongCode` | String | ✓ 필수 | 법정동 코드 |
| `lat` | Float | ✓ 필수 | 중심 위도 (WGS84) |
| `lng` | Float | ✓ 필수 | 중심 경도 (WGS84) |
| `propertyType` | Enum | ✓ 필수 | `apartment` \| `commercial` \| `area` \| `landmark` |
| `sourceType` | Enum | ✓ 필수 | `region` \| `address` \| `building` \| `complex` |

---

### 3-2. 위치 기반 조회

**`GET /locations/{locationId}`**

개별 건물/아파트 단지 위치 기본 정보 반환. 한 줄 설명(FR-02) 데이터 소스.

#### Path Variables

| 필드명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| `locationId` | String (Path) | ✓ 필수 | 위치 고유 ID |

#### Response Body

| 필드명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| `locationId` | String | ✓ 필수 | 위치 고유 ID |
| `regionId` | String | ✓ 필수 | 속한 행정 지역 ID |
| `name` | String | ✓ 필수 | 건물/단지명 |
| `address` | String | ✓ 필수 | 도로명 주소 |
| `propertyType` | Enum | ✓ 필수 | `apartment` \| `landmark` |
| `lat` | Float | ✓ 필수 | 위도 |
| `lng` | Float | ✓ 필수 | 경도 |
| `floors` | Integer | 선택 | 층수 |
| `buildYear` | Integer | 선택 | 건축연도. 한 줄 설명에 활용 (예: 2015년 준공) |
| `totalHouseholds` | Integer | 선택 | 총 세대수. 한 줄 설명에 활용 (예: 3,885세대) |

---

## 4. 가격 분석 API

### 4-1. 가격 분석 (최신 현황)

**`GET /analysis/price`**

국토부 아파트 매매/전세/월세 실거래가 API 기반. 검색 결과 화면 가격 정보표(FR-02) 및 가격 분석 탭(FR-05) 현황.

#### Query Parameters

| 필드명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| `regionId` | String | ✓ 필수 | 서비스 내부 지역 ID |
| `dealType` | Enum | 선택 | `sale` \| `jeonse` \| `monthly` \| `all` (기본 `all`) |

#### Response Body

| 필드명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| `avgSalePrice` | Long | 선택 | 평균 매매가 (원). 최근 3개월 기준 |
| `avgJeonsePrice` | Long | 선택 | 평균 전세가 (원) |
| `avgMonthlyRent` | Long | 선택 | 평균 월세 (원) |
| `avgMonthlyDeposit` | Long | 선택 | 평균 월세 보증금 (원) |
| `jeonseRatio` | Float | 선택 | 전세가율 (%) |
| `recentTradeCount` | Integer | ✓ 필수 | 최근 1개월 거래 건수 |
| `priceStabilityGrade` | Enum | ✓ 필수 | `stable` \| `normal` \| `volatile` |
| `priceLevel` | Enum | ✓ 필수 | `low` \| `below_avg` \| `avg` \| `above_avg` \| `high` |
| `dataBaseDate` | ISO 8601 (Date) | ✓ 필수 | '실거래가 데이터 최신화 기준' 표시용 |

> 국토부 아파트 매매/전세/월세 실거래가 API 수집 후 가공. 캐시는 `dataBaseDate` 변경 시 재생성.

---

### 4-2. 가격 추이

**`GET /analysis/price/trend`**

월별 가격 변동 추이. 가격 분석 탭 기간별 차트(FR-05) 데이터.

#### Query Parameters

| 필드명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| `regionId` | String | ✓ 필수 | 서비스 내부 지역 ID |
| `period` | Enum | 선택 | `1m` \| `3m` \| `1y` (기본 `1y`). FR-05 가격분석 탭 기간 선택 |
| `dealType` | Enum | 선택 | `sale` \| `jeonse` \| `monthly` \| `all` (기본 `all`) |

#### Response Body

| 필드명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| `trend` | Array\<Object\> | ✓ 필수 | 기간별 가격 배열 |
| `trend[].month` | String | ✓ 필수 | 기준 월 (YYYY-MM) |
| `trend[].avgPrice` | Long | ✓ 필수 | 해당 월 평균 가격 (원) |
| `trend[].dealType` | Enum | ✓ 필수 | `sale` \| `jeonse` \| `monthly` |
| `trend[].tradeCount` | Integer | ✓ 필수 | 해당 월 거래 건수 |
| `changeRate1m` | Float | ✓ 필수 | 전월 대비 변동률 (%) |
| `changeRate3m` | Float | ✓ 필수 | 3개월 전 대비 변동률 (%) |
| `changeRate1y` | Float | 선택 | 1년 전 대비 변동률 (%) |
| `dataBaseDate` | ISO 8601 (Date) | ✓ 필수 | 데이터 기준일 |

---

### 4-3. 가격 통계

**`GET /analysis/price/stats`**

기간별 최저·평균·최고 가격 통계. 가격 분석 탭(FR-05) 상세 수치.

#### Query Parameters

| 필드명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| `regionId` | String | ✓ 필수 | 서비스 내부 지역 ID |
| `dealType` | Enum | 선택 | `sale` \| `jeonse` \| `monthly` \| `all` (기본 `all`) |
| `period` | Enum | 선택 | `1m` \| `3m` \| `1y` (기본 `1m`). 가격분석 탭 기간 선택 연동 |

#### Response Body

| 필드명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| `minPrice` | Long | ✓ 필수 | 최저 거래가 (원) |
| `avgPrice` | Long | ✓ 필수 | 평균 거래가 (원) |
| `maxPrice` | Long | ✓ 필수 | 최고 거래가 (원) |
| `totalTradeCount` | Integer | ✓ 필수 | 기간 내 총 거래 건수 |
| `recentTradeCount` | Integer | ✓ 필수 | 최근 1개월 거래 건수 |
| `tradeSignal` | Enum | ✓ 필수 | `active` \| `normal` \| `low` (거래 활성도) |
| `dataBaseDate` | ISO 8601 (Date) | ✓ 필수 | 데이터 기준일 |

---

### 4-4. 이슈/뉴스 분석

**`GET /analysis/issues`**

해당 단지·지역과 연관된 뉴스·이슈를 시간순으로 반환. 이슈 분석 탭(FR-06) 데이터.

#### Query Parameters

| 필드명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| `regionId` | String | ✓ 필수 | 서비스 내부 지역 ID |
| `limit` | Integer | 선택 | 반환 건수 (기본 20) |
| `cursor` | String | 선택 | Cursor 기반 페이지네이션 |

#### Response Body

| 필드명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| `items` | Array\<Object\> | ✓ 필수 | 이슈 목록 (시간 역순) |
| `items[].issueId` | String | ✓ 필수 | 이슈 ID |
| `items[].type` | Enum | ✓ 필수 | `news` \| `policy` \| `traffic` |
| `items[].title` | String | ✓ 필수 | 이슈 제목 |
| `items[].summary` | String | ✓ 필수 | AI 요약 (1~2줄) |
| `items[].impactType` | Enum | ✓ 필수 | `positive` \| `negative` \| `neutral` |
| `items[].publishedAt` | ISO 8601 | ✓ 필수 | 발생/발표 일시 |
| `items[].url` | String | 선택 | 원문 링크 |
| `meta.cursor` | String | 선택 | 다음 페이지 커서 |
| `meta.hasNext` | Boolean | 선택 | 다음 페이지 존재 여부 |

> v4.0 변경: `type`에서 `development` 제외 (개발계획 이슈 2차 이후). `dataSource` 객체 제외 (2차 이후). 기사 원문 미전재, 제목·AI요약·링크만 표시.

---

## 5. 지도 시각화 API

### 5-1. 지도 마커

**`GET /map/markers`**

단지 중심 카카오맵 아파트 마커 데이터. 주변 인프라 마커(지하철/학교/마트/병원) 포함. (FR-03, FR-04)

#### Query Parameters

| 필드명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| `regionId` | String | ✓ 필수 | 서비스 내부 지역 ID |
| `type` | Enum | 선택 | `apartment` \| `infra` \| `all` (기본 `all`). `infra`=지하철/학교/마트/병원 |
| `infraRadius` | Integer | 선택 | 주변 인프라 검색 반경 (미터, 기본 1000) |

#### Response Body

| 필드명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| `markers` | Array\<Object\> | ✓ 필수 | 마커 목록 |
| `markers[].markerId` | String | ✓ 필수 | 마커 ID |
| `markers[].name` | String | ✓ 필수 | 건물/단지명 또는 인프라명 |
| `markers[].address` | String | ✓ 필수 | 주소 |
| `markers[].lat` | Float | ✓ 필수 | 위도 |
| `markers[].lng` | Float | ✓ 필수 | 경도 |
| `markers[].markerType` | Enum | ✓ 필수 | `apartment` \| `subway` \| `school` \| `mart` \| `hospital` \| `landmark` |
| `markers[].avgPrice` | Long | 선택 | 평균 가격 (원, `apartment` 시) |
| `markers[].priceLevel` | Enum | 선택 | `low` \| `avg` \| `high` (`apartment` 시) |
| `markers[].distanceM` | Integer | 선택 | 단지 중심 기준 도보 거리 (인프라 마커 시) |

> v4.0 변경: `markerType`에 `subway`, `school`, `mart`, `hospital` 추가 (FR-04 인프라 마커 지원).  
> 마커 색상 정책: 지하철=파랑, 학교=초록, 병원=빨강, 마트=주황.

---

## 6. AI 리포트 API

AI 리포트는 비동기 방식으로 생성됩니다. 권장 Polling 간격: 2~3초. 스트리밍 미지원.

| 단계 | 방향 | 설명 |
|------|------|------|
| 1단계 | → | `POST /reports` — 리포트 생성 요청, `reportId` 반환 (status: `pending`) |
| 2단계 | → | `GET /reports/{reportId}/status` — 상태 Polling (`processing` → `completed` \| `failed`). 권장 간격: 2~3초 |
| 3단계 | → | `GET /reports/{reportId}` — `completed` 확인 후 전체 결과 조회 |

### 6-1. AI 리포트 생성 요청

**`POST /reports`**

지역 기반 AI 리포트 생성 요청. 동일 조건 캐시 리포트 존재 시 409 반환 (재사용 권장). (FR-07)

#### Request Body

| 필드명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| `regionId` | String | ✓ 필수 | 서비스 내부 지역 ID |

#### Response Body

| 필드명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| `reportId` | String | ✓ 필수 | 리포트 고유 ID |
| `status` | Enum | ✓ 필수 | `pending` \| `cached` (캐시 히트 시 `cached` 반환) |
| `estimatedSeconds` | Integer | 선택 | 예상 생성 소요 시간 (초, `pending` 시) |
| `cachedAt` | ISO 8601 | 선택 | 캐시 생성 시각 (`cached` 시) |

> v4.0 변경: v2.0의 `mode`, `dealType`, `budget`, `industry` 파라미터 제거 (모드선택 2차 이후).  
> 캐시 조건: 동일 `regionId` + `dataBaseDate`. 동일 조건 리포트 존재 시 `409 REPORT_ALREADY_EXISTS` 반환.

---

### 6-2. AI 리포트 상태 조회 (Polling)

**`GET /reports/{reportId}/status`**

리포트 생성 상태 조회. `completed` 상태 확인 후 6-3으로 전체 결과 조회.

#### Path Variables

| 필드명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| `reportId` | String (Path) | ✓ 필수 | 리포트 고유 ID |

#### Response Body

| 필드명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| `reportId` | String | ✓ 필수 | 리포트 ID |
| `status` | Enum | ✓ 필수 | `pending` \| `processing` \| `completed` \| `failed` |
| `progressPct` | Integer | 선택 | 진행률 (0~100, `processing` 시) |
| `completedAt` | ISO 8601 | 선택 | 완료 시각 (`completed` 시) |
| `failReason` | String | 선택 | 실패 사유 (`failed` 시) |

---

### 6-3. AI 리포트 결과 조회

**`GET /reports/{reportId}`**

생성 완료된 AI 리포트 전체 내용 반환. 4섹션(가격동향/생활환경/지역이슈/종합의견) 구조.

#### Path Variables

| 필드명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| `reportId` | String (Path) | ✓ 필수 | 리포트 고유 ID |

#### Response Body

| 필드명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| `reportId` | String | ✓ 필수 | 리포트 ID |
| `regionId` | String | ✓ 필수 | 지역 ID |
| `summary` | String | ✓ 필수 | 핵심 요약 (2~3줄) |
| `sections` | Array\<Object\> | ✓ 필수 | 4섹션 상세 내용 |
| `sections[].sectionKey` | Enum | ✓ 필수 | `price_trend` \| `life_env` \| `local_issues` \| `overall` |
| `sections[].sectionTitle` | String | ✓ 필수 | 섹션 제목 (예: 가격 동향) |
| `sections[].content` | String | ✓ 필수 | 섹션 내용 (AI 생성) |
| `sections[].sortOrder` | Integer | ✓ 필수 | 정렬 순서 (1~4) |
| `disclaimer` | String | ✓ 필수 | 면책 문구 (투자 권유 아님 명시). 하단 필수 표시 |
| `generatedAt` | ISO 8601 | ✓ 필수 | 리포트 생성 시각 |
| `dataBaseDate` | ISO 8601 (Date) | ✓ 필수 | 데이터 기준일 |

> 리포트는 원인 단정 금지. '영향 가능 요인 후보' 형태로 표현. 면책 문구 하단 필수 표시.  
> v4.0 변경: `priceChangeReasons`/`strengths`/`weaknesses`/`recommendations` 항목 2차 이후 (모드별 항목).

---

## 7. 에러 코드

| Status | errorCode | 상황 | 설명 |
|--------|-----------|------|------|
| 400 | `INVALID_PARAMETER` | 파라미터 오류 | 요청 파라미터 누락 또는 형식 오류 |
| 401 | `INVALID_API_KEY` | 인증 실패 | API Key 미제공 또는 유효하지 않음 |
| 404 | `RESOURCE_NOT_FOUND` | 리소스 없음 | 요청한 지역/리소스 없음 |
| 409 | `REPORT_ALREADY_EXISTS` | 리포트 중복 | 동일 `regionId` + `dataBaseDate` 기준 리포트 존재 시 (재사용 권장) |
| 422 | `UNSUPPORTED_REGION` | 지원 범위 외 | 서울 외 지역 요청 시 |
| 429 | `RATE_LIMIT_EXCEEDED` | 호출 한도 초과 | 분당 5회 / 일 20회 초과 |
| 500 | `INTERNAL_ERROR` | 서버 오류 | 서버 내부 오류 |
| 503 | `EXTERNAL_API_ERROR` | 외부 API 오류 | 외부 공공 API 연결 실패 |

응답 헤더: `X-RateLimit-Remaining` (잔여 호출 수), `X-RateLimit-Reset` (초기화 시각 ISO 8601)

---

## 8. 외부 API 연동 매핑 (MVP 1순위)

모든 외부 API는 백엔드에서 프록시 처리. 클라이언트에 원본 키 및 응답 직접 노출 없음.

| 외부 API | 활용 내부 API | 비고 |
|----------|---------------|------|
| 국토부 아파트 매매 실거래가 API | `/analysis/price` `/analysis/price/trend` `/analysis/price/stats` `/map/price-layer` | 기준일 변경 시 캐시 무효화 |
| 국토부 아파트 전세/월세 실거래가 API | `/analysis/price` `/analysis/price/stats` | 매매 API와 통합 처리 |
| 도로명주소 API (행정안전부) | `/regions/search` | 지역명→법정동 코드 변환 |
| 카카오맵 API | `/places/search` `/map/markers` | 좌표·장소 검색·지도 렌더링·인프라 마커 |
| 네이버 부동산 뉴스 API | `/news/highlights` `/analysis/issues` | AI요약 후 제목·요약·링크만 노출. 저작권 준수 |

> ★ 2차 이후 연동 예정 (MVP 1순위 제외): 상권분석·종합요약·종합판단 API — 소상공인진흥공단 상가API, 국토교통부 도시계획API

---

*CONFIDENTIAL | HomeLens AI API 명세서 | MVP v4.0 (1순위 전용)*

// HomeLens AI - 앱 전체 TypeScript 타입 정의

// 화면 이름 타입
export type Screen = 'home' | 'list' | 'area' | 'complex';

// AI 리포트 생성 상태 타입
export type ReportStatus = 'idle' | 'loading' | 'done';

// 검색 드롭다운 타입 (동/단지)
export type DropdownType = 'area' | 'complex';

// AI 리포트 생성 대상 타입 (동 단위/단지 단위)
export type ReportTarget = 'ra' | 'rc';

// AI 리포트 섹션 타입
export interface ReportSection {
  title: string;
  body: string;
}

// AI 리포트 전체 타입
export interface Report {
  summary: string;
  sections: ReportSection[];
  disclaimer: string;
}

// 가격 추이 차트 데이터 타입
export interface ChartDataItem {
  v: number[];
  c: string;
  u: string;
}

// 주변 인프라 아이템 타입
export interface AmenityItem {
  category: string;
  name: string;
  distance: string;
  color: string;
}

// 검색 목록 아이템 타입
export interface SearchListItem {
  type: DropdownType;
  name: string;
  sub: string;
  label: string;
  dest: Screen;
}

// 단지 목록 아이템 타입
export interface ComplexListItem {
  name: string;
  type: string;
  count: string;
}

// 지도 마커 타입
export interface MapMarker {
  x: number;
  y: number;
  r: number;
  op: number;
  rank: string;
  name: string;
  val: string;
  dest: Screen;
}
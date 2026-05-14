// HomeLens AI - 목업 데이터 (백엔드 API 연동 전 임시 데이터)
// API 연동 후 src/api/ 폴더의 실제 API 호출 함수로 교체 예정

import { AmenityItem, ChartDataItem, MapMarker, Report } from '../types';
import { CATEGORY_COLORS } from './colors';

// 차트 월별 레이블
export const MONTHS: string[] = ['11월', '12월', '1월', '2월', '3월', '4월'];

// 가격 추이 차트 데이터 (매매/전세/월세/보증금)
export const CHART_DATA: ChartDataItem[] = [
  { v: [14.2, 14.5, 14.8, 15.0, 15.1, 15.2], c: '#1A1A18', u: '억' },
  { v: [7.8, 8.0, 8.1, 8.3, 8.4, 8.5], c: '#185FA5', u: '억' },
  { v: [110, 115, 118, 122, 126, 130], c: '#854F0B', u: '만' },
  { v: [1000, 1200, 1500, 1800, 2000, 2000], c: '#3B6D11', u: '천만' },
];

// 메인 지도 탭 레이블
export const MAP_TAB_LABELS: string[] = [
  '이번달 매매 거래량 TOP 3',
  '이번달 전세가율 낮은 단지 TOP 3',
  '이번달 월세 부담 낮은 단지 TOP 3',
];

// 메인 지도 탭별 마커 색상
export const MARKER_COLORS: { bg: string; text: string }[] = [
  { bg: '#1A3A2A', text: '#9FE1CB' },
  { bg: '#0C447C', text: '#B5D4F4' },
  { bg: '#633806', text: '#FAC775' },
];

// 메인 지도 탭별 마커 데이터 (매매 거래량/전세가율/월세 부담)
export const MARKER_DATA: MapMarker[][] = [
  [
    { x: 120, y: 70, r: 17, op: 0.92, rank: '1위', name: '롯데캐슬', val: '23건', dest: 'area' },
    { x: 222, y: 60, r: 15, op: 0.85, rank: '2위', name: '아이파크', val: '19건', dest: 'area' },
    { x: 46, y: 64, r: 13, op: 0.78, rank: '3위', name: '트리마제', val: '17건', dest: 'area' },
  ],
  [
    { x: 75, y: 66, r: 17, op: 0.92, rank: '1위', name: '롯데캐슬', val: '48%', dest: 'area' },
    { x: 207, y: 61, r: 15, op: 0.85, rank: '2위', name: '아이파크', val: '51%', dest: 'area' },
    { x: 132, y: 152, r: 13, op: 0.78, rank: '3위', name: '트리마제', val: '54%', dest: 'area' },
  ],
  [
    { x: 58, y: 152, r: 17, op: 0.92, rank: '1위', name: '롯데캐슬', val: '85만', dest: 'area' },
    { x: 202, y: 66, r: 15, op: 0.85, rank: '2위', name: '아이파크', val: '92만', dest: 'area' },
    { x: 100, y: 63, r: 13, op: 0.78, rank: '3위', name: '트리마제', val: '110만', dest: 'area' },
  ],
];

// 단지 주변 인프라 목록 (반경 1km)
export const COMPLEX_AMENITIES: AmenityItem[] = [
  { category: '지하철', name: '2호선 성수역', distance: '도보 3분 · 250m', color: CATEGORY_COLORS.subway },
  { category: '지하철', name: '2호선 뚝섬역', distance: '도보 11분 · 850m', color: CATEGORY_COLORS.subway },
  { category: '대형마트', name: '이마트 성수점', distance: '450m', color: CATEGORY_COLORS.mart },
  { category: '백화점', name: '갤러리아백화점', distance: '1.2km', color: CATEGORY_COLORS.department },
  { category: '종합병원', name: '한양대병원', distance: '1.4km', color: CATEGORY_COLORS.hospital },
  { category: '학교', name: '초·중·고 각 1개교', distance: '반경 내', color: CATEGORY_COLORS.school },
];

// 동 단위 AI 리포트 샘플 데이터
export const RA_REPORT: Report = {
  summary: '"2호선·5호선 역세권에 개발 기대감이 더해진 성수동, 실수요 꾸준한 지역"',
  sections: [
    {
      title: '가격 동향',
      body: '최근 6개월 매매 평균가가 완만한 상승세를 보이며 거래량도 전월 대비 증가하고 있습니다. 성수 전략정비구역 개발 계획 발표 이후 실수요자 유입이 늘어난 영향으로 보입니다. 전세 시장도 안정적인 수준을 유지하고 있어 갭투자 리스크는 낮은 편으로 판단됩니다.',
    },
    {
      title: '지역 이슈',
      body: '전략정비구역 개발이 본격화되면 장기적 가치 상승 가능성이 있으나 완료 시기가 불확실하므로 단기 의사결정에 과도하게 반영하는 것은 바람직하지 않습니다. 토지거래허가구역 규제 강화 논의도 매매 시 유의가 필요한 사항입니다.',
    },
    {
      title: '종합 의견',
      body: '2호선과 5호선이 통과하는 대중교통 우수 지역으로 직주근접을 중시하는 1~2인 가구에게 특히 적합한 환경입니다.',
    },
  ],
  disclaimer:
    '본 리포트는 국토교통부 실거래가·네이버 뉴스 데이터를 기반으로 AI가 생성한 참고 자료이며, 부동산 중개나 투자자문이 아닙니다. AI 생성 내용은 부정확할 수 있으므로 실제 거래 시에는 공인중개사 등 전문가 상담을 권장하며, 거래 결정과 결과에 대한 책임은 이용자에게 있습니다.',
};

// 단지 단위 AI 리포트 샘플 데이터
export const RC_REPORT: Report = {
  summary: '"성수역 도보 3분, 우수한 생활 인프라와 개발 기대감을 갖춘 실거주 적합 단지"',
  sections: [
    {
      title: '가격 동향',
      body: '최근 6개월간 14억대에서 15억대로 완만하게 상승했습니다.',
    },
    {
      title: '생활 환경',
      body: '이마트 성수점(450m)과 갤러리아백화점(1.2km)이 인근에 위치해 생활 편의성이 높습니다.',
    },
    {
      title: '지역 이슈',
      body: '성수 전략정비구역 개발 계획 본격화로 장기적 가치 상승 가능성이 있습니다.',
    },
    {
      title: '종합 의견',
      body: '교통·생활 편의·의료 인프라 전반에서 우수한 수준을 보이고 있어 1~2인 가구 및 자녀 있는 가구 모두에게 적합한 단지로 판단됩니다.',
    },
  ],
  disclaimer:
    '본 리포트는 국토교통부 실거래가·네이버 뉴스 데이터를 기반으로 AI가 생성한 참고 자료이며, 부동산 중개나 투자자문이 아닙니다. AI 생성 내용은 부정확할 수 있으므로 실제 거래 시에는 공인중개사 등 전문가 상담을 권장하며, 거래 결정과 결과에 대한 책임은 이용자에게 있습니다.',
};
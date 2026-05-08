// HomeLens AI - 앱 전체 색상 상수

// 기본 색상 팔레트
export const COLORS = {
  bgPrimary: '#FAF9F5',
  bgSecondary: '#F0EEE6',
  textPrimary: '#1A1A18',
  textSecondary: '#6B6B66',
  textTertiary: '#9B9B95',
  borderSecondary: '#D9D6CB',
  borderTertiary: '#E8E5DA',
  borderPrimary: '#1A1A18',
} as const;

// 지도 마커 카테고리별 색상
// 지하철=초록, 마트=주황, 백화점=보라, 병원=빨강, 학교=파랑
export const CATEGORY_COLORS = {
  subway: '#3CB44B',
  mart: '#E67E22',
  department: '#9B59B6',
  hospital: '#E74C3C',
  school: '#3498DB',
} as const;
// HomeLens AI - 지도 색상 범례 아이템 컴포넌트
// 단지 지도 하단 인프라 범례에서 사용

import React from "react";
import { S } from "../constants/styles";

interface LegendItemProps {
  color: string;
  label: string;
}

const LegendItem: React.FC<LegendItemProps> = ({ color, label }) => (
  <div style={S.legendItem}>
    <span style={{ ...S.legendDot, background: color }} />
    <span style={S.legendLabel}>{label}</span>
  </div>
);

export default LegendItem;

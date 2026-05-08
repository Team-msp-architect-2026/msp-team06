// HomeLens AI - 최저/평균/최고가 3박스 통계 컴포넌트
// 가격 분석 탭 차트 하단에 표시

import React from "react";
import { S } from "../constants/styles";

interface Stats3Props {
  items: [string, string][];
}

const Stats3: React.FC<Stats3Props> = ({ items }) => (
  <div style={S.s3}>
    {/* 통계 박스 렌더링 ([레이블, 값] 배열) */}
    {items.map(([l, v], i) => (
      <div key={i} style={S.s3b}>
        <div style={S.s3l}>{l}</div>
        <div style={S.s3v}>{v}</div>
      </div>
    ))}
  </div>
);

export default Stats3;

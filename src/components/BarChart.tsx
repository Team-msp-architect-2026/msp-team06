// HomeLens AI - 가격 추이 막대 차트 컴포넌트
// idx로 CHART_DATA 선택 (0:매매 / 1:전세 / 2:월세 / 3:보증금)

import React from "react";
import { CHART_DATA, MONTHS } from "../constants/mockData";
import { S } from "../constants/styles";

interface BarChartProps {
  idx: number;
}

const BarChart: React.FC<BarChartProps> = ({ idx }) => {
  // 차트 데이터 선택 및 최대값 계산
  const d = CHART_DATA[idx];
  const mx = Math.max(...d.v);
  return (
    <div style={S.chtOuter}>
      <div style={S.chtBars}>
        {/* 막대 차트 렌더링 (높이는 최대값 대비 비율로 계산) */}
        {d.v.map((v, i) => {
          const h = Math.round((v / mx) * 68);
          const lbl = idx === 3 ? (v / 1000).toFixed(1) + "천" : v + d.u;
          return (
            <div key={i} style={S.cc}>
              <div style={S.cv}>{lbl}</div>
              <div style={S.cbw}>
                <div style={{ ...S.cb, height: h + "px", background: d.c }} />
              </div>
            </div>
          );
        })}
      </div>
      <div style={S.chtSep} />
      <div style={S.chtLbls}>
        {MONTHS.map((m, i) => (
          <div key={i} style={S.cl}>{m}</div>
        ))}
      </div>
    </div>
  );
};

export default BarChart;
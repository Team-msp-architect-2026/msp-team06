// HomeLens AI - AI 리포트 컴포넌트
// idle/loading/done 3가지 상태에 따라 다른 UI 표시

import React from "react";
import { COLORS } from "../constants/colors";
import { S } from "../constants/styles";
import { Report, ReportStatus } from "../types";

interface AIReportProps {
  report: Report;
  onGenerate: () => void;
  status: ReportStatus;
}

const AIReport: React.FC<AIReportProps> = ({ report, onGenerate, status }) => {
  // 리포트 생성 전 상태 (생성하기 버튼 표시)
  if (status === "idle") {
    return (
      <div style={S.rstart}>
        <svg width="36" height="36" viewBox="0 0 36 36" style={{ margin: "0 auto", display: "block" }}>
          <circle cx="18" cy="18" r="17" fill={COLORS.bgSecondary} stroke={COLORS.borderSecondary} strokeWidth="1" />
          <text x="18" y="23" textAnchor="middle" fontSize="18">🤖</text>
        </svg>
        <div style={S.rst}>AI 실거주 분석 리포트</div>
        <div style={S.rss}>
          가격 흐름과 지역 이슈를<br />AI가 종합 분석해드려요
        </div>
        <button style={S.rbtn} onClick={onGenerate}>리포트 생성하기</button>
      </div>
    );
  }

  // 리포트 생성 중 상태 (로딩 표시)
  if (status === "loading") {
    return (
      <div style={S.rstart}>
        <svg width="36" height="36" viewBox="0 0 36 36" style={{ margin: "0 auto", display: "block" }}>
          <circle cx="18" cy="18" r="17" fill={COLORS.bgSecondary} stroke={COLORS.borderSecondary} strokeWidth="1" />
          <text x="18" y="23" textAnchor="middle" fontSize="18">⏳</text>
        </svg>
        <div style={S.rst}>분석 중이에요...</div>
        <div style={S.rss}>
          AI가 가격·인프라·이슈 데이터를<br />종합 분석하고 있어요
        </div>
      </div>
    );
  }

  // 리포트 완료 상태 (섹션별 내용 + 면책고지 표시)
  return (
    <div>
      <div style={S.rsum}>
        <div style={S.rsuml}>한줄 요약</div>
        <div style={S.rsumq}>{report.summary}</div>
      </div>
      {/* 리포트 섹션 렌더링 (가격동향/생활환경/지역이슈/종합의견) */}
      {report.sections.map((sec, i) => (
        <div key={i} style={S.rsec}>
          <div style={S.rset}>{sec.title}</div>
          <div style={S.rbody}>{sec.body}</div>
        </div>
      ))}
      <div style={S.disc}>{report.disclaimer}</div>
      <div style={S.rdate}>
        데이터 출처: 국토교통부 실거래가 공개시스템 (2026년 4월 기준)
      </div>
    </div>
  );
};

export default AIReport;
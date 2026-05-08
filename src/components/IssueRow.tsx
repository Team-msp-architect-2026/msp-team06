// HomeLens AI - 이슈 행 컴포넌트
// 메인화면 최근 주요 이슈 목록에서 사용

import React from "react";
import { COLORS } from "../constants/colors";
import { S } from "../constants/styles";
import { formatRelativeDate } from "../utils/formatDate";

interface IssueRowProps {
  badge: string;
  badgeBg: string;
  badgeColor: string;
  text: string;
  summary?: string;
  publishedAt?: string;
}

const IssueRow: React.FC<IssueRowProps> = ({
  badge,
  badgeBg,
  badgeColor,
  text,
  summary,
  publishedAt,
}) => (
  <div style={S.ir}>
    <div style={{ marginBottom: 4 }}>
      <span
        style={{
          ...S.ib,
          background: badgeBg,
          color: badgeColor,
          marginRight: 6,
        }}
      >
        {badge}
      </span>
      {publishedAt && (
        <span
          style={{ fontSize: 10, color: COLORS.textTertiary, marginRight: 6 }}
        >
          {formatRelativeDate(publishedAt)}
        </span>
      )}
      <span style={{ fontSize: 11 }}>{text}</span>
    </div>
    {summary && (
      <div
        style={{ fontSize: 11, color: COLORS.textSecondary, lineHeight: 1.5 }}
      >
        {summary}
      </div>
    )}
  </div>
);

export default IssueRow;

// HomeLens AI - 이슈 카드 컴포넌트
// 동 단위/단지 단위 이슈 분석 탭에서 사용

import React from "react";
import { COLORS } from "../constants/colors";
import { S } from "../constants/styles";
import { formatRelativeDate } from "../utils/formatDate";

interface IssueCardProps {
  badge: string;
  badgeBg: string;
  badgeColor: string;
  text: string;
  summary?: string;
  publishedAt?: string;
}

const IssueCard: React.FC<IssueCardProps> = ({
  badge,
  badgeBg,
  badgeColor,
  text,
  summary,
  publishedAt,
}) => (
  <div style={S.ic}>
    <div style={S.im}>
      <span
        style={{ ...S.ib, background: badgeBg, color: badgeColor, fontSize: 9 }}
      >
        {badge}
      </span>
      {publishedAt && (
        <span
          style={{ fontSize: 10, color: COLORS.textTertiary, marginLeft: 6 }}
        >
          {formatRelativeDate(publishedAt)}
        </span>
      )}
    </div>
    <div style={S.ict}>{text}</div>
    {summary && (
      <div
        style={{
          fontSize: 11,
          color: COLORS.textSecondary,
          marginTop: 4,
          lineHeight: 1.5,
        }}
      >
        {summary}
      </div>
    )}
  </div>
);

export default IssueCard;

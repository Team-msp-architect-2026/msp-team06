// HomeLens AI - 검색 자동완성 드롭다운 아이템 컴포넌트

import React from "react";
import { COLORS } from "../constants/colors";
import { S } from "../constants/styles";
import { DropdownType } from "../types";

interface DropdownItemProps {
  type: DropdownType;
  name: string;
  sub: string;
  onClick: () => void;
}

const DropdownItem: React.FC<DropdownItemProps> = ({
  type,
  name,
  sub,
  onClick,
}) => (
  <div style={S.ddi} onClick={onClick}>
    {/* 동(area)/단지(complex) 구분 아이콘 렌더링 */}
    {type === "area" ? (
      <svg
        width="12"
        height="12"
        viewBox="0 0 16 16"
        fill="none"
        style={{ flexShrink: 0 }}
      >
        <path
          d="M8 1.5C5.5 1.5 3.5 3.5 3.5 6C3.5 9.5 8 14.5 8 14.5S12.5 9.5 12.5 6C12.5 3.5 10.5 1.5 8 1.5Z"
          stroke={COLORS.textSecondary}
          strokeWidth="1.2"
          fill="none"
        />
        <circle cx="8" cy="6" r="1.5" fill={COLORS.textSecondary} />
      </svg>
    ) : (
      <svg
        width="12"
        height="12"
        viewBox="0 0 16 16"
        fill="none"
        style={{ flexShrink: 0 }}
      >
        <rect
          x="2"
          y="5"
          width="12"
          height="9"
          rx="1"
          stroke={COLORS.textSecondary}
          strokeWidth="1.2"
          fill="none"
        />
        <path
          d="M5 5V3.5C5 2.7 5.7 2 6.5 2H9.5C10.3 2 11 2.7 11 3.5V5"
          stroke={COLORS.textSecondary}
          strokeWidth="1.2"
        />
      </svg>
    )}
    <div>
      <div style={S.ddn}>{name}</div>
      <div style={S.dds}>{sub}</div>
    </div>
    <span style={S.dda}>›</span>
  </div>
);

export default DropdownItem;

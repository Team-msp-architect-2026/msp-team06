// 이슈 행 컴포넌트 - 메인화면 최근 주요 이슈 목록에서 사용

import React from "react";
import { StyleSheet, Text, View } from "react-native";
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
  <View style={styles.ir}>
    <View style={styles.meta}>
      <View style={[styles.ibWrap, { backgroundColor: badgeBg }]}>
        <Text style={[styles.ib, { color: badgeColor }]}>{badge}</Text>
      </View>
      {publishedAt && (
        <Text style={styles.date}>{formatRelativeDate(publishedAt)}</Text>
      )}
      <Text style={styles.text} numberOfLines={1}>
        {text}
      </Text>
    </View>
    {summary && <Text style={styles.summary}>{summary}</Text>}
  </View>
);

const styles = StyleSheet.create({
  ir: {
    backgroundColor: "#FAF9F5",
    borderRadius: 10,
    borderWidth: 0.5,
    borderColor: "#E8E5DA",
    padding: 10,
    marginBottom: 8,
  },
  meta: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    flexWrap: "nowrap",
  },
  ibWrap: {
    borderRadius: 4,
    paddingHorizontal: 6,
    paddingVertical: 2,
    flexShrink: 0,
  },
  ib: { fontSize: 9, fontWeight: "500" },
  date: { fontSize: 10, color: "#9B9B95", flexShrink: 0 },
  text: { fontSize: 11, color: "#1A1A18", flex: 1 },
  summary: { fontSize: 11, color: "#6B6B66", marginTop: 6, lineHeight: 16 },
});

export default IssueRow;

// 이슈 카드 컴포넌트 - 동/단지 이슈 분석 탭에서 사용

import React from "react";
import { StyleSheet, Text, View } from "react-native";
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
  <View style={styles.ic}>
    <View style={styles.im}>
      <View style={[styles.ibWrap, { backgroundColor: badgeBg }]}>
        <Text style={[styles.ib, { color: badgeColor }]}>{badge}</Text>
      </View>
      {publishedAt && (
        <Text style={styles.date}>{formatRelativeDate(publishedAt)}</Text>
      )}
      <Text style={styles.ict} numberOfLines={1}>
        {text}
      </Text>
    </View>
    {summary && <Text style={styles.summary}>{summary}</Text>}
  </View>
);

const styles = StyleSheet.create({
  ic: {
    backgroundColor: "#FAF9F5",
    borderRadius: 10,
    borderWidth: 0.5,
    borderColor: "#E8E5DA",
    padding: 12,
    marginBottom: 8,
  },
  im: { flexDirection: "row", alignItems: "center", gap: 4 },
  ibWrap: {
    borderRadius: 4,
    paddingHorizontal: 6,
    paddingVertical: 2,
    flexShrink: 0,
  },
  ib: { fontSize: 9, fontWeight: "500" },
  date: { fontSize: 10, color: "#9B9B95", flexShrink: 0 },
  ict: { fontSize: 11, color: "#1A1A18", fontWeight: "500", flex: 1 },
  summary: { fontSize: 11, color: "#6B6B66", marginTop: 6, lineHeight: 16 },
});

export default IssueCard;

// 이슈 행 컴포넌트 - 메인화면 최근 주요 이슈 목록에서 사용

import React from "react";
import { StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { Linking } from "react-native";
import { formatRelativeDate } from "../utils/formatDate";

interface IssueRowProps {
  badge: string;
  badgeBg: string;
  badgeColor: string;
  text: string;
  summary?: string;
  publishedAt?: string;
  url?: string;
}

const IssueRow: React.FC<IssueRowProps> = ({
  badge,
  badgeBg,
  badgeColor,
  text,
  summary,
  publishedAt,
  url,
}) => {
  const handlePress = async () => {
    if (!url) return;
    try {
      await Linking.openURL(url);
    } catch (e) {
      console.log("브라우저 오류:", e);
    }
  };

  return (
    <TouchableOpacity
      style={styles.ir}
      onPress={handlePress}
      activeOpacity={url ? 0.7 : 1}
    >
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
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  ir: {
    backgroundColor: "#FFFFFF",
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#E5E5E5",
    padding: 14,
    marginBottom: 10,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 4,
    elevation: 2,
  },
  meta: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    flexWrap: "nowrap",
  },
  ibWrap: {
    borderRadius: 4,
    paddingHorizontal: 7,
    paddingVertical: 3,
    flexShrink: 0,
  },
  ib: { fontSize: 11, fontWeight: "600" },
  date: { fontSize: 11, color: "#AAAAAA", flexShrink: 0 },
  text: { fontSize: 13, color: "#111111", flex: 1, fontWeight: "500" },
  summary: { fontSize: 13, color: "#888888", marginTop: 8, lineHeight: 18 },
});

export default IssueRow;
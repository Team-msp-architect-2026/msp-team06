// 이슈 행 컴포넌트 - 메인화면 최근 주요 이슈 목록에서 사용

import React from "react";
import { StyleSheet, Text, TouchableOpacity, View } from "react-native";
import InAppBrowser from "react-native-inappbrowser-reborn";
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
      if (await InAppBrowser.isAvailable()) {
        await InAppBrowser.open(url, {
          toolbarColor: "#FFFFFF",
          secondaryToolbarColor: "#111111",
          navigationBarColor: "#FFFFFF",
          showTitle: true,
          enableUrlBarHiding: true,
          enableDefaultShare: true,
        });
      }
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
    borderRadius: 10,
    borderWidth: 0.5,
    borderColor: "#E5E5E5",
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
  date: { fontSize: 10, color: "#AAAAAA", flexShrink: 0 },
  text: { fontSize: 11, color: "#111111", flex: 1 },
  summary: { fontSize: 11, color: "#888888", marginTop: 6, lineHeight: 16 },
});

export default IssueRow;
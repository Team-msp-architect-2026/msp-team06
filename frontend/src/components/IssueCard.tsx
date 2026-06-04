// 이슈 카드 컴포넌트 - 동/단지 이슈 분석 탭에서 사용

import React from "react";
import { StyleSheet, Text, TouchableOpacity, View } from "react-native";
import InAppBrowser from "react-native-inappbrowser-reborn";
import { formatRelativeDate } from "../utils/formatDate";

interface IssueCardProps {
  badge: string;
  badgeBg: string;
  badgeColor: string;
  text: string;
  summary?: string;
  publishedAt?: string;
  url?: string;
}

const IssueCard: React.FC<IssueCardProps> = ({
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
      style={styles.ic}
      onPress={handlePress}
      activeOpacity={url ? 0.7 : 1}
    >
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
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  ic: {
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
  im: { flexDirection: "row", alignItems: "center", gap: 6 },
  ibWrap: {
    borderRadius: 4,
    paddingHorizontal: 7,
    paddingVertical: 3,
    flexShrink: 0,
  },
  ib: { fontSize: 11, fontWeight: "600" },
  date: { fontSize: 11, color: "#AAAAAA", flexShrink: 0 },
  ict: { fontSize: 13, color: "#111111", fontWeight: "500", flex: 1 },
  summary: { fontSize: 13, color: "#888888", marginTop: 8, lineHeight: 18 },
});

export default IssueCard;
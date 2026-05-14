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
          toolbarColor: "#FAF9F5",
          secondaryToolbarColor: "#1A1A18",
          navigationBarColor: "#FAF9F5",
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
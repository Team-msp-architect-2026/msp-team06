// 최저/평균/최고가 3박스 통계 - 가격 분석 탭 차트 하단에 표시

import React from "react";
import { StyleSheet, Text, View } from "react-native";

interface Stats3Props {
  items: [string, string][];
}

const Stats3: React.FC<Stats3Props> = ({ items }) => (
  <View style={styles.s3}>
    {items.map(([l, v], i) => (
      <View key={i} style={styles.s3b}>
        <Text style={styles.s3l}>{l}</Text>
        <Text style={styles.s3v}>{v}</Text>
      </View>
    ))}
  </View>
);

const styles = StyleSheet.create({
  s3: { flexDirection: "row", gap: 6, marginTop: 8 },
  s3b: {
    flex: 1,
    backgroundColor: "#F5F5F5",
    borderRadius: 8,
    padding: 8,
    alignItems: "center",
  },
  s3l: { fontSize: 10, color: "#888888", marginBottom: 2 },
  s3v: { fontSize: 13, fontWeight: "600", color: "#111111" },
});

export default Stats3;

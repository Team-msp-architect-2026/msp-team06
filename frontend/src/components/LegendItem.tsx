// 지도 색상 범례 아이템 - 인프라 마커 범례에서 사용

import React from "react";
import { StyleSheet, Text, View } from "react-native";

interface LegendItemProps {
  color: string;
  label: string;
}

const LegendItem: React.FC<LegendItemProps> = ({ color, label }) => (
  <View style={styles.legendItem}>
    <View style={[styles.legendDot, { backgroundColor: color }]} />
    <Text style={styles.legendLabel}>{label}</Text>
  </View>
);

const styles = StyleSheet.create({
  legendItem: { flexDirection: "row", alignItems: "center", marginRight: 10 },
  legendDot: { width: 8, height: 8, borderRadius: 4, marginRight: 4 },
  legendLabel: { fontSize: 10, color: "#6B6B66" },
});

export default LegendItem;

// 검색 자동완성 드롭다운 아이템 - 동(area)/단지(complex) 구분 표시

import React from "react";
import { StyleSheet, Text, TouchableOpacity, View } from "react-native";
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
  <TouchableOpacity style={styles.ddi} onPress={onClick}>
    <View style={styles.icon}>
      <Text style={styles.iconText}>{type === "area" ? "📍" : "🏢"}</Text>
    </View>
    <View style={styles.info}>
      <Text style={styles.ddn}>{name}</Text>
      <Text style={styles.dds}>{sub}</Text>
    </View>
    <Text style={styles.dda}>›</Text>
  </TouchableOpacity>
);

const styles = StyleSheet.create({
  ddi: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderBottomWidth: 0.5,
    borderBottomColor: "#E5E5E5",
    gap: 8,
  },
  icon: { width: 20, alignItems: "center" },
  iconText: { fontSize: 12 },
  info: { flex: 1 },
  ddn: { fontSize: 13, color: "#111111", fontWeight: "500" },
  dds: { fontSize: 11, color: "#888888", marginTop: 1 },
  dda: { fontSize: 16, color: "#AAAAAA" },
});

export default DropdownItem;

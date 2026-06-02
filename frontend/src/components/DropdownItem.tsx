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
    paddingHorizontal: 14,
    paddingVertical: 12,
    backgroundColor: "#FFFFFF",
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#E5E5E5",
    marginBottom: 8,
    gap: 10,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 4,
    elevation: 2,
  },
  icon: { width: 22, alignItems: "center" },
  iconText: { fontSize: 14 },
  info: { flex: 1 },
  ddn: { fontSize: 15, color: "#111111", fontWeight: "600" },
  dds: { fontSize: 12, color: "#888888", marginTop: 2 },
  dda: { fontSize: 18, color: "#CCCCCC" },
});

export default DropdownItem;

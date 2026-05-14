// 가격 추이 막대 차트 - idx로 데이터 선택 (0:매매/1:전세/2:월세/3:보증금)

import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { CHART_DATA, MONTHS } from "../constants/mockData";

interface BarChartProps {
  idx: number;
}

const BarChart: React.FC<BarChartProps> = ({ idx }) => {
  const d = CHART_DATA[idx];
  const mx = Math.max(...d.v);
  return (
    <View style={styles.chtOuter}>
      <View style={styles.chtBars}>
        {d.v.map((v, i) => {
          const h = Math.round((v / mx) * 68);
          const lbl = idx === 3 ? (v / 1000).toFixed(1) + "천" : v + d.u;
          return (
            <View key={i} style={styles.cc}>
              <Text style={styles.cv}>{lbl}</Text>
              <View style={styles.cbw}>
                <View
                  style={[styles.cb, { height: h, backgroundColor: d.c }]}
                />
              </View>
            </View>
          );
        })}
      </View>
      <View style={styles.chtSep} />
      <View style={styles.chtLbls}>
        {MONTHS.map((m, i) => (
          <Text key={i} style={styles.cl}>
            {m}
          </Text>
        ))}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  chtOuter: { marginVertical: 8 },
  chtBars: { flexDirection: "row", alignItems: "flex-end", height: 80 },
  cc: { flex: 1, alignItems: "center" },
  cv: { fontSize: 8, color: "#6B6B66", marginBottom: 2 },
  cbw: {
    width: "60%",
    alignItems: "center",
    justifyContent: "flex-end",
    height: 68,
  },
  cb: { width: "100%", borderRadius: 2 },
  chtSep: { height: 0.5, backgroundColor: "#E8E5DA", marginTop: 2 },
  chtLbls: { flexDirection: "row", marginTop: 4 },
  cl: { flex: 1, fontSize: 8, color: "#9B9B95", textAlign: "center" },
});

export default BarChart;

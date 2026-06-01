// 가격 추이 막대 차트 - 실제 API 데이터 사용
import React from "react";
import { StyleSheet, Text, View } from "react-native";

interface BarChartItem {
  month: string;
  avgPrice: number;
}

interface BarChartProps {
  data: BarChartItem[];
  color: string;
  unit: string;      // "억" | "만"
  divisor: number;   // 가격 나누기 단위 (매매/전세: 10000, 월세: 1)
}

const BarChart: React.FC<BarChartProps> = ({ data, color, unit, divisor }) => {
  if (!data || data.length === 0) {
    return (
      <View style={styles.empty}>
        <Text style={styles.emptyText}>데이터 없음</Text>
      </View>
    );
  }

  // 최근 6개월만 표시 (최신순 정렬 후 슬라이스)
  const recent = [...data].slice(0, 6).reverse();
  const prices = recent.map((d) => d.avgPrice / divisor);
  const mx = Math.max(...prices);

  return (
    <View style={styles.chtOuter}>
      <View style={styles.chtBars}>
        {recent.map((item, i) => {
          const price = item.avgPrice / divisor;
          const h = Math.round((price / mx) * 68);
          const lbl =
            divisor === 10000
              ? (price).toFixed(1) + "억"
              : Math.round(price) + unit;
          return (
            <View key={i} style={styles.cc}>
              <Text style={styles.cv}>{lbl}</Text>
              <View style={styles.cbw}>
                <View style={[styles.cb, { height: h, backgroundColor: color }]} />
              </View>
            </View>
          );
        })}
      </View>
      <View style={styles.chtSep} />
      <View style={styles.chtLbls}>
        {recent.map((item, i) => (
          <Text key={i} style={styles.cl}>
            {item.month.slice(5)}월
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
  cv: { fontSize: 10, color: "#111111", marginBottom: 2, fontWeight: "500" },
  cbw: {
    width: "60%",
    alignItems: "center",
    justifyContent: "flex-end",
    height: 68,
  },
  cb: { width: "100%", borderRadius: 2 },
  chtSep: { height: 0.5, backgroundColor: "#E5E5E5", marginTop: 2 },
  chtLbls: { flexDirection: "row", marginTop: 4 },
  cl: { flex: 1, fontSize: 10, color: "#888888", textAlign: "center", fontWeight: "500" },
  empty: { height: 80, justifyContent: "center", alignItems: "center" },
  emptyText: { fontSize: 12, color: "#AAAAAA" },
});

export default BarChart;
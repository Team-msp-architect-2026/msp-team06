// AI 리포트 컴포넌트 - idle/loading/done 상태별 UI 표시
import React from "react";
import { StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { ReportResponse } from "../api/reports";
import { Report, ReportStatus } from "../types";

interface AIReportProps {
  report?: Report | ReportResponse;
  onGenerate: () => void;
  status: ReportStatus;
}

const AIReport: React.FC<AIReportProps> = ({ report, onGenerate, status }) => {
  if (status === "idle") {
    return (
      <View style={styles.rstart}>
        <Text style={styles.emoji}>🤖</Text>
        <Text style={styles.rst}>AI 실거주 분석 리포트</Text>
        <Text style={styles.rss}>
          가격 흐름과 지역 이슈를{"\n"}AI가 종합 분석해드려요
        </Text>
        <TouchableOpacity style={styles.rbtn} onPress={onGenerate}>
          <Text style={styles.rbtnText}>리포트 생성하기</Text>
        </TouchableOpacity>
      </View>
    );
  }

  if (status === "loading") {
    return (
      <View style={styles.rstart}>
        <Text style={styles.emoji}>⏳</Text>
        <Text style={styles.rst}>분석 중이에요...</Text>
        <Text style={styles.rss}>
          AI가 가격·인프라·이슈 데이터를{"\n"}종합 분석하고 있어요
        </Text>
      </View>
    );
  }

  if (status === "done" && !report) {
    return (
      <View style={styles.rstart}>
        <Text style={styles.rst}>리포트를 불러오지 못했습니다</Text>
      </View>
    );
  }

  return (
    <View>
      <View style={styles.rsum}>
        <Text style={styles.rsuml}>한줄 요약</Text>
        <Text style={styles.rsumq}>{report?.summary}</Text>
      </View>
      {report?.sections.map((sec, i) => (
        <View key={i} style={styles.rsec}>
          <Text style={styles.rset}>
            {(sec as any).sectionTitle || (sec as any).title}
          </Text>
          <Text style={styles.rbody}>
            {(sec as any).content || (sec as any).body}
          </Text>
        </View>
      ))}
      <Text style={styles.disc}>{report?.disclaimer}</Text>
      <Text style={styles.rdate}>
        데이터 출처: 국토교통부 실거래가 공개시스템 (2026년 4월 기준)
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  rstart: { alignItems: "center", paddingVertical: 24 },
  emoji: { fontSize: 36, marginBottom: 10 },
  rst: { fontSize: 14, fontWeight: "500", color: "#1A1A18", marginBottom: 6 },
  rss: { fontSize: 12, color: "#6B6B66", textAlign: "center", lineHeight: 18 },
  rbtn: {
    marginTop: 14,
    backgroundColor: "#1A1A18",
    borderRadius: 10,
    paddingHorizontal: 20,
    paddingVertical: 10,
  },
  rbtnText: { fontSize: 13, color: "white", fontWeight: "500" },
  rsum: {
    backgroundColor: "#F0EEE6",
    borderRadius: 10,
    borderWidth: 0.5,
    borderColor: "#D9D6CB",
    padding: 12,
    marginBottom: 10,
  },
  rsuml: { fontSize: 10, color: "#6B6B66", marginBottom: 4 },
  rsumq: { fontSize: 13, color: "#1A1A18", lineHeight: 18 },
  rsec: {
    backgroundColor: "#FAF9F5",
    borderRadius: 10,
    borderWidth: 0.5,
    borderColor: "#E8E5DA",
    padding: 12,
    marginBottom: 8,
  },
  rset: {
    fontSize: 13,
    fontWeight: "500",
    color: "#1A1A18",
    marginBottom: 6,
    paddingBottom: 6,
    borderBottomWidth: 0.5,
    borderBottomColor: "#E8E5DA",
  },
  rbody: { fontSize: 12, color: "#3B3B38", lineHeight: 18 },
  disc: { fontSize: 10, color: "#9B9B95", lineHeight: 15, marginTop: 10 },
  rdate: { fontSize: 10, color: "#9B9B95", marginTop: 4 },
});

export default AIReport;
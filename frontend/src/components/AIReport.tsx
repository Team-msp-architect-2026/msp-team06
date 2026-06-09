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
        <Text style={styles.rst}>AI 리포트</Text>
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
        <Text style={styles.emoji}>⏳</Text>
        <Text style={styles.rst}>리포트 불러오는 중...</Text>
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
        데이터 출처: 국토교통부 실거래가 공개시스템
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  rstart: { alignItems: "center", paddingVertical: 24 },
  emoji: { fontSize: 36, marginBottom: 10 },
  rst: { fontSize: 16, fontWeight: "600", color: "#111111", marginBottom: 6 },
  rss: { fontSize: 13, color: "#888888", textAlign: "center", lineHeight: 20 },
  rbtn: {
    marginTop: 16,
    backgroundColor: "#2563EB",
    borderRadius: 10,
    paddingHorizontal: 24,
    paddingVertical: 12,
  },
  rbtnText: { fontSize: 14, color: "white", fontWeight: "600" },
  rsum: {
    backgroundColor: "#E6F1FB",
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#C5DCEF",
    padding: 16,
    marginBottom: 12,
  },
  rsuml: { 
    fontSize: 15, 
    color: "#0C447C", 
    marginBottom: 8, 
    fontWeight: "700",
    paddingBottom: 8,
    borderBottomWidth: 1,
    borderBottomColor: "#C5DCEF",
  },
  rsumq: { fontSize: 14, color: "#111111", lineHeight: 22 },
  rsec: {
    backgroundColor: "#FFFFFF",
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#E5E5E5",
    padding: 16,
    marginBottom: 10,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 4,
    elevation: 2,
  },
  rset: {
    fontSize: 15,
    fontWeight: "700",
    color: "#111111",
    marginBottom: 8,
    paddingBottom: 8,
    borderBottomWidth: 1,
    borderBottomColor: "#E5E5E5",
  },
  rbody: { fontSize: 13, color: "#3B3B38", lineHeight: 22 },
  disc: { fontSize: 11, color: "#AAAAAA", lineHeight: 16, marginTop: 12 },
  rdate: { fontSize: 11, color: "#AAAAAA", marginTop: 4 },
});

export default AIReport;
// 동 단위 결과 화면 - 가격 정보, 지하철 노선, 지도, 이슈/AI리포트 탭

import React, { useRef } from "react";
import {
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import AIReport from "../components/AIReport";
import IssueCard from "../components/IssueCard";
import KakaoMap from "../components/KakaoMap";
import seoulDong from "../constants/seoul_dong.json";
import { useIssues, usePrice, usePriceTrend } from "../hooks/useAnalysis";
import { useMapMarkers } from "../hooks/useMap";
import { useAppStore } from "../store/useAppStore";
import { ReportStatus, ReportTarget, Screen } from "../types";
import { useReport } from "../hooks/useReport";

interface AreaScreenProps {
  areaTab: number;
  setAreaTab: (n: number) => void;
  raStatus: ReportStatus;
  raReportId: string | null;  
  generate: (which: ReportTarget) => void;
  go: (s: Screen) => void;
}

const ISSUE_TYPE_LABELS: Record<string, string> = {
  market: "시장",
  policy: "정책",
  development: "개발",
  law: "법률",
};

const AreaScreen: React.FC<AreaScreenProps> = ({
  areaTab,
  setAreaTab,
  raStatus,
  raReportId,  
  generate,
  go,
}) => {
  const { data: reportData } = useReport(raReportId, raStatus === 'done' ? 'completed' : raStatus);  
  const { selectedRegion } = useAppStore();

  const scrollRef = useRef<ScrollView>(null);

  const { data: issuesData, isLoading: issuesLoading } = useIssues(
    selectedRegion?.regionId || "",
    selectedRegion?.name || "",
  );

  const now = new Date();
  const dealYmd = `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, "0")}`;

  const { data: priceData, isLoading: priceLoading } = usePrice(
    selectedRegion?.regionId || "",
    selectedRegion?.lat || 0,
    selectedRegion?.lng || 0,
    dealYmd,
    selectedRegion?.name || "",
  );

  const { data: trendData, isLoading: trendLoading } = usePriceTrend(
    selectedRegion?.regionId || "",
    selectedRegion?.lat || 0,
    selectedRegion?.lng || 0,
    "1y",
    selectedRegion?.name || "",
  );

  // 전월 대비 변동률 계산
  const saleTrend = trendData?.trend.filter((t) => t.dealType === "sale") || [];
  const latestSale = trendData?.trend
    ?.filter(t => t.dealType === "sale")
    .sort((a, b) => b.month.localeCompare(a.month))[0];
  const latestJeonse = trendData?.trend
    ?.filter(t => t.dealType === "jeonse")
    .sort((a, b) => b.month.localeCompare(a.month))[0];
  const latestMonthly = trendData?.trend
    ?.filter(t => t.dealType === "monthly")
    .sort((a, b) => b.month.localeCompare(a.month))[0];
  const changeRate = saleTrend.length >= 2
    ? ((saleTrend[0].avgPrice - saleTrend[1].avgPrice) / saleTrend[1].avgPrice * 100).toFixed(1)
    : null;

  const { data: markerData, isLoading: markerLoading } = useMapMarkers(
    selectedRegion?.regionId || "",
    selectedRegion?.lat || 0,
    selectedRegion?.lng || 0,
    "infra",
    800,
  );

  // 지하철 노선명 추출 (중복 제거)
  const subwayLines = Array.from(
    new Set(
      markerData?.markers
        .filter(
          (m) => m.markerType === "subway" && !m.markerId.endsWith("_none"),
        )
        .map((m) => {
          const match = m.name.match(
            /(\d+호선|수인분당선|경의중앙선|공항철도|신분당선|GTX-[A-C])/,
          );
          return match ? match[0] : null;
        })
        .filter(Boolean) || [],
    ),
  );

  return (
    <View style={styles.scr}>
      {/* 상단 헤더 */}
      <View style={styles.bar}>
        <TouchableOpacity onPress={() => go("home")}>
          <Text style={styles.bk}>‹</Text>
        </TouchableOpacity>
        <View>
          <Text style={styles.regionName}>{selectedRegion?.name || ""}</Text>
          <Text style={styles.regionAddr}>
            {selectedRegion?.fullAddress || ""}
          </Text>
        </View>
      </View>

      <ScrollView
        ref={scrollRef}
        style={styles.sc}
        showsVerticalScrollIndicator={false}
        scrollEventThrottle={16}
      >
        {/* 가격 정보 카드 */}
        <View style={styles.scard}>
          <View style={styles.sr}>
            <View style={styles.si}>
              <Text style={styles.sl}>매매 평균가</Text>
              <Text style={styles.sv}>
                {priceLoading || trendLoading ? "조회 중..." : latestSale?.avgPrice
                  ? `${Math.floor(latestSale.avgPrice / 10000)}억 ${Math.round((latestSale.avgPrice % 10000) / 1000)}천`
                  : "데이터 없음"}
              </Text>
              {changeRate && (
                <Text style={[styles.sd, { color: Number(changeRate) >= 0 ? "#27AE60" : "#E74C3C" }]}>
                  {Number(changeRate) >= 0 ? `▲ 전월 +${changeRate}%` : `▼ 전월 ${changeRate}%`}
                </Text>
              )}
            </View>
            <View style={styles.sp} />
            <View style={styles.si}>
              <Text style={styles.sl}>전세 평균가</Text>
              <Text style={styles.sv}>
                {priceLoading || trendLoading ? "조회 중..." : latestJeonse?.avgPrice
                  ? `${Math.floor(latestJeonse.avgPrice / 10000)}억 ${Math.round((latestJeonse.avgPrice % 10000) / 1000)}천`
                  : "데이터 없음"}
              </Text>
            </View>
          </View>
          <View style={styles.sdv} />
          <View style={styles.sr}>
            <View style={styles.si}>
              <Text style={styles.sl}>월세 평균</Text>
              <Text style={styles.svsm}>
                {priceLoading || trendLoading ? "조회 중..." : latestMonthly?.avgPrice
                  ? latestMonthly?.avgDeposit
                    ? `보증금 ${Math.floor(latestMonthly.avgDeposit / 1000)}천/월 ${latestMonthly.avgPrice}만`
                    : `월 ${latestMonthly.avgPrice}만`
                  : "데이터 없음"}
              </Text>
            </View>
            <View style={styles.sp} />
            <View style={styles.si}>
              <Text style={styles.sl}>이번달 거래량</Text>
              <Text style={styles.sv}>
                {priceLoading || trendLoading ? "조회 중..." : `${latestSale?.tradeCount ?? 0}건`}
              </Text>
              <Text style={styles.tertiary}>
                {latestSale?.month ? `${latestSale.month.slice(0,4)}년 ${parseInt(latestSale.month.slice(5))}월 기준` : ""}
              </Text>
            </View>
          </View>

        </View>

        {/* 지도 영역 - 터치 시 스크롤 고정 */}
        <View
          onTouchStart={() =>
            scrollRef.current?.setNativeProps({ scrollEnabled: false })
          }
          onTouchEnd={() =>
            scrollRef.current?.setNativeProps({ scrollEnabled: true })
          }
          onTouchCancel={() =>
            scrollRef.current?.setNativeProps({ scrollEnabled: true })
          }
        >
          <KakaoMap
            lat={selectedRegion?.lat || 37.5665}
            lng={selectedRegion?.lng || 126.978}
            level={5}
            markers={[]}
            geoJson={seoulDong}
            polygons={selectedRegion?.name ? [{
              code: selectedRegion.name,
              grade: 3,
              name: selectedRegion.name,
              value: 0,
            }] : []}
            highlightOnly={true}
          />
        </View>

        {/* 탭 버튼 */}
        <View style={styles.tabbar}>
          {["이슈 분석", "AI 리포트"].map((t, i) => (
            <TouchableOpacity
              key={i}
              style={[styles.ti, areaTab === i && styles.tiOn]}
              onPress={() => setAreaTab(i)}
            >
              <Text style={[styles.tiText, areaTab === i && styles.tiTextOn]}>
                {t}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* 탭 콘텐츠 */}
        <View style={styles.tc}>
          {areaTab === 0 && (
            <View>
              {issuesLoading && (
                <Text style={styles.loadingText}>불러오는 중...</Text>
              )}
              {issuesData?.items.map((issue, i) => (
                <IssueCard
                  key={i}
                  badge={ISSUE_TYPE_LABELS[issue.type] || issue.type}
                  badgeBg="#E6F1FB"
                  badgeColor="#0C447C"
                  text={issue.title
                    .replace(/&quot;/g, '"')
                    .replace(/&amp;/g, "&")}
                  summary={issue.summary
                    ?.replace(/&quot;/g, '"')
                    .replace(/&amp;/g, "&")}
                  publishedAt={issue.publishedAt}
                  url={issue.url || ""}
                />
              ))}
              {!issuesLoading &&
                (!issuesData?.items || issuesData.items.length === 0) && (
                  <Text style={styles.emptyText}>관련 이슈가 없습니다</Text>
                )}
            </View>
          )}
          {areaTab === 1 && (
            <AIReport
              report={reportData}
              status={raStatus}
              onGenerate={() => generate("ra")}
            />
          )}
        </View>
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  scr: { flex: 1, backgroundColor: "#F5F5F5" },
  bar: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: "#E5E5E5",
    backgroundColor: "#FFFFFF",
    gap: 10,
  },
  bk: { fontSize: 24, color: "#111111" },
  regionName: { fontSize: 16, fontWeight: "700", color: "#111111" },
  regionAddr: { fontSize: 12, color: "#888888" },
  sc: { flex: 1 },
  scard: {
    backgroundColor: "#FFFFFF",
    borderRadius: 14,
    borderWidth: 1,
    borderColor: "#E5E5E5",
    padding: 16,
    margin: 12,
    marginBottom: 0,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 4,
    elevation: 2,
  },
  sr: { flexDirection: "row", alignItems: "flex-start" },
  si: { flex: 1 },
  sp: { width: 1, backgroundColor: "#E5E5E5", marginHorizontal: 12 },
  sdv: { height: 1, backgroundColor: "#E5E5E5", marginVertical: 12 },
  sl: { fontSize: 12, color: "#888888", marginBottom: 4 },
  sv: { fontSize: 18, fontWeight: "700", color: "#111111" },
  svsm: { fontSize: 14, fontWeight: "600", color: "#111111" },
  sd: { fontSize: 11, color: "#27AE60", marginTop: 2 },
  subwayRow: { flexDirection: "row", flexWrap: "wrap", gap: 5, marginTop: 6 },
  subwayTag: {
    backgroundColor: "#E8F5E9",
    borderRadius: 6,
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  subwayTagText: { fontSize: 12, color: "#27AE60", fontWeight: "500" },
  loadingText: { fontSize: 12, color: "#AAAAAA" },
  mapPlaceholder: {
    margin: 12,
    marginBottom: 0,
    height: 180,
    backgroundColor: "#E8EEE4",
    borderRadius: 14,
    borderWidth: 0.5,
    borderColor: "#E5E5E5",
  },
  cp: { margin: 12, marginBottom: 0 },
  cpt: { fontSize: 15, fontWeight: "600", color: "#111111" },
  cps: { fontSize: 12, color: "#AAAAAA", marginTop: 4 },
  tabbar: {
    flexDirection: "row",
    margin: 12,
    marginBottom: 0,
    backgroundColor: "#EEEEEE",
    borderRadius: 10,
    padding: 3,
  },
  ti: { flex: 1, alignItems: "center", paddingVertical: 8, borderRadius: 8 },
  tiOn: {
    backgroundColor: "#2563EB",
  },
  tiText: { fontSize: 13, color: "#888888" },
  tiTextOn: { color: "#FFFFFF", fontWeight: "600" },
  tc: { padding: 12 },
  tertiary: { fontSize: 11, color: "#AAAAAA", marginTop: 2 },
  emptyText: {
    fontSize: 13,
    color: "#AAAAAA",
    textAlign: "center",
    paddingVertical: 24,
  },
});

export default AreaScreen;

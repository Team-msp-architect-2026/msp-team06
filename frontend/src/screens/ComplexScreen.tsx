// 단지 단위 결과 화면 - 가격 정보, 인프라 목록, 지도, 가격분석/이슈/AI리포트 탭

import React, { useRef } from "react";
import {
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import AIReport from "../components/AIReport";
import BarChart from "../components/BarChart";
import IssueCard from "../components/IssueCard";
import KakaoMap from "../components/KakaoMap";
import { useIssues, usePrice, usePriceTrend, usePriceStats } from "../hooks/useAnalysis";
import { useMapMarkers } from "../hooks/useMap";
import { useAppStore } from "../store/useAppStore";
import { ReportStatus, ReportTarget, Screen } from "../types";
import { useReport } from "../hooks/useReport";

interface ComplexScreenProps {
  cxTab: number;
  setCxTab: (n: number) => void;
  priceTab: number;
  setPriceTab: (n: number) => void;
  rentTab: number;
  setRentTab: (n: number) => void;
  rcStatus: ReportStatus;
  generate: (which: ReportTarget) => void;
  go: (s: Screen) => void;
  rcReportId: string | null;
}

const INFRA_COLORS: Record<string, string> = {
  subway: "#3CB44B",
  mart: "#E67E22",
  department: "#9B59B6",
  hospital: "#E74C3C",
  school: "#3498DB",
  school_elementary: "#3498DB",
  school_middle: "#3498DB",
  school_high: "#3498DB",
};

const INFRA_LABELS: Record<string, string> = {
  subway: "지하철",
  mart: "대형마트",
  department: "백화점",
  hospital: "종합병원",
  school: "학교",
};

const ISSUE_TYPE_LABELS: Record<string, string> = {
  policy: "정책",
  market: "시장",
  development: "개발",
  law: "법률",
};

const ComplexScreen: React.FC<ComplexScreenProps> = ({
  cxTab,
  setCxTab,
  priceTab,
  setPriceTab,
  rentTab,
  setRentTab,
  rcStatus,
  rcReportId,
  generate,
  go,
}) => {
  const { selectedRegion, prevScreen } = useAppStore();
  const { data: reportData } = useReport(rcReportId, rcStatus === 'done' ? 'completed' : rcStatus);
  const scrollRef = useRef<ScrollView>(null);

  const { data: markerData, isLoading: markerLoading } = useMapMarkers(
    selectedRegion?.regionId || "",
    selectedRegion?.lat || 0,
    selectedRegion?.lng || 0,
    "infra",
);

  const now = new Date();
  const dealYmd = `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, "0")}`;

  const { data: priceData, isLoading: priceLoading } = usePrice(
    selectedRegion?.regionId || "",
    selectedRegion?.lat || 0,
    selectedRegion?.lng || 0,
    dealYmd,
  );

  const { data: trendData, isLoading: trendLoading } = usePriceTrend(
  selectedRegion?.regionId || "",
  selectedRegion?.lat || 0,
  selectedRegion?.lng || 0,
  "1y",
  selectedRegion?.name || "",
);

  const { data: statsData } = usePriceStats(
  selectedRegion?.regionId || "",
  selectedRegion?.lat || 0,
  selectedRegion?.lng || 0,
  dealYmd,
  "1m",
  selectedRegion?.name || "",
);

  const monthlyTrend = trendData?.trend.filter((t) => t.dealType === "monthly") || [];
  const deposits = monthlyTrend.map((t) => (t as any).avgDeposit || 0).filter((d) => d > 0);

  const latestSale = trendData?.trend
    ?.filter(t => t.dealType === "sale")
    .sort((a, b) => b.month.localeCompare(a.month))[0];
  const latestJeonse = trendData?.trend
    ?.filter(t => t.dealType === "jeonse")
    .sort((a, b) => b.month.localeCompare(a.month))[0];
  const latestMonthly = trendData?.trend
    ?.filter(t => t.dealType === "monthly")
    .sort((a, b) => b.month.localeCompare(a.month))[0];

  const { data: issuesData, isLoading: issuesLoading } = useIssues(
    selectedRegion?.regionId || "",
    selectedRegion?.name || "",
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
                {priceLoading || trendLoading
                  ? "조회 중..."
                  : latestSale?.avgPrice
                    ? `${Math.floor(latestSale.avgPrice / 10000)}억 ${Math.round((latestSale.avgPrice % 10000) / 1000)}천`
                    : "데이터 없음"}
              </Text>
            </View>
            <View style={styles.sp} />
            <View style={styles.si}>
              <Text style={styles.sl}>전세 평균가</Text>
              <Text style={styles.sv}>
                {priceLoading || trendLoading
                  ? "조회 중..."
                  : latestJeonse?.avgPrice
                    ? `${Math.floor(latestJeonse.avgPrice / 10000)}억 ${Math.round((latestJeonse.avgPrice % 10000) / 1000)}천`
                    : "데이터 없음"}
              </Text>
              <Text style={styles.tertiary}>
                {latestJeonse && latestSale
                  ? `전세가율 ${Math.round(latestJeonse.avgPrice / latestSale.avgPrice * 100)}%`
                  : ""}
              </Text>
            </View>
          </View>
          <View style={styles.sdv} />
          <View style={styles.sr}>
            <View style={styles.si}>
              <Text style={styles.sl}>월세 평균</Text>
              <Text style={styles.svsm}>
                {priceLoading || trendLoading
                  ? "조회 중..."
                  : latestMonthly?.avgPrice
                    ? (latestMonthly as any)?.avgDeposit
                      ? (() => {
                          const dep = (latestMonthly as any).avgDeposit;
                          const depStr = dep >= 10000
                            ? `${Math.floor(dep / 10000)}억 ${dep % 10000 > 0 ? `${dep % 10000}만` : ""}`
                            : `${dep}만`;
                          return `보증금 ${depStr}\n월 ${latestMonthly.avgPrice}만`;
                        })()
                      : `월 ${latestMonthly.avgPrice}만`
                    : "데이터 없음"}
              </Text>
            </View>
            <View style={styles.sp} />
            <View style={styles.si}>
              <Text style={styles.sl}>최근 거래량</Text>
              <Text style={styles.sv}>
                {priceLoading || trendLoading
                  ? "조회 중..."
                  : `${latestSale?.tradeCount ?? 0}건`}
              </Text>
              <Text style={styles.tertiary}>
                {latestSale?.month ? `${latestSale.month.slice(0,4)}년 ${parseInt(latestSale.month.slice(5))}월 기준` : ""}
              </Text>
            </View>
          </View>
          <View style={styles.sdv} />

          {/* 인프라 목록 */}
          <Text style={styles.sl}>주변 인프라 (반경 1.5km)</Text>
          <View style={styles.amenityList}>
            {markerLoading && (
              <Text style={styles.loadingText}>불러오는 중...</Text>
            )}
            {markerData?.markers.map((marker, i) => {
              const isNone = marker.markerId.endsWith("_none");
              const schoolType =
                marker.markerType === "school"
                  ? (marker as any).school_type
                  : null;
              const colorKey = schoolType
                ? `school_${schoolType}`
                : marker.markerType;
              const color = INFRA_COLORS[colorKey] || "#888";
              const label =
                INFRA_LABELS[marker.markerType] || marker.markerType;
              const dist = marker.distanceM
                ? marker.distanceM >= 1000
                  ? `${(marker.distanceM / 1000).toFixed(1)}km`
                  : `${marker.distanceM}m`
                : "";
              return (
                <View key={i} style={styles.amenityRow}>
                  <View
                    style={[
                      styles.amenityDot,
                      { backgroundColor: isNone ? "#ccc" : color },
                    ]}
                  />
                  <Text style={styles.amenityCat}>{label}</Text>
                  <Text style={styles.amenityName}>
                    {isNone ? "반경 내 없음" : marker.name}
                  </Text>
                  <Text style={styles.amenityDist}>{dist}</Text>
                </View>
              );
            })}
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
            level={3}
            markers={markerData?.markers.map((m) => ({
              lat: m.lat,
              lng: m.lng,
              type: m.markerType,
              name: m.name,
              markerId: m.markerId,
            }))}
          />
        </View>

        {/* 탭 버튼 */}
        <View style={styles.tabbar}>
          {["가격 분석", "이슈 분석", "AI 리포트"].map((t, i) => (
            <TouchableOpacity
              key={i}
              style={[styles.ti, cxTab === i && styles.tiOn]}
              onPress={() => setCxTab(i)}
            >
              <Text style={[styles.tiText, cxTab === i && styles.tiTextOn]}>
                {t}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* 탭 콘텐츠 */}
        <View style={styles.tc}>
          {/* 가격 분석 탭 */}
          {cxTab === 0 && (
            <View>
              <View style={styles.ptog}>
                {["매매", "전세", "월세"].map((p, i) => (
                  <TouchableOpacity
                    key={i}
                    style={[styles.ptb, priceTab === i && styles.ptbOn]}
                    onPress={() => setPriceTab(i)}
                  >
                    <Text style={[styles.ptbText, priceTab === i && styles.ptbTextOn]}>
                      {p}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>

              {/* 매매 추이 차트 */}
              {priceTab === 0 && (
                <View>
                  <BarChart
                    data={trendData?.trend.filter((t) => t.dealType === "sale") || []}
                    color="#111111"
                    unit="억"
                    divisor={10000}
                  />
                </View>
              )}
              {/* 전세 추이 차트 */}
              {priceTab === 1 && (
                <View>
                  <BarChart
                    data={trendData?.trend.filter((t) => t.dealType === "jeonse") || []}
                    color="#185FA5"
                    unit="억"
                    divisor={10000}
                  />
                </View>
              )}

              {/* 월세/보증금 추이 차트 */}
              {priceTab === 2 && (
                <View>
                  <View style={styles.rtog}>
                    {["월세 추이", "보증금 추이"].map((r, i) => (
                      <TouchableOpacity
                        key={i}
                        style={[styles.rtb, rentTab === i && styles.rtbOn]}
                        onPress={() => setRentTab(i)}
                      >
                        <Text style={[styles.rtbText, rentTab === i && styles.rtbTextOn]}>
                          {r}
                        </Text>
                      </TouchableOpacity>
                    ))}
                  </View>

                  {/* 월세 추이 차트 */}
                  {rentTab === 0 && (
                    <View>
                      <BarChart
                        data={trendData?.trend.filter((t) => t.dealType === "monthly") || []}
                        color="#854F0B"
                        unit="만"
                        divisor={1}
                      />
                    </View>
                  )}

                  {/* 보증금 추이 차트 */}
                  {rentTab === 1 && (
                    <View>
                      <BarChart
                        data={trendData?.trend.filter((t) => t.dealType === "monthly").map((t) => ({
                          ...t,
                          avgPrice: (t as any).avgDeposit || 0,
                        })) || []}
                        color="#3B6D11"
                        unit="만"
                        divisor={10000}
                      />
                    </View>
                  )}
                </View>
              )}
            </View>
          )}

          {/* 이슈 분석 탭 */}
          {cxTab === 1 && (
            <View>
              {issuesLoading && (
                <Text style={styles.loadingText}>불러오는 중...</Text>
              )}
              {issuesData?.items.map((issue, i) => {
                const badgeStyle: Record<string, { bg: string; color: string }> = {
                  market: { bg: "#FFF3E0", color: "#E65100" },
                  policy: { bg: "#E8F5E9", color: "#2E7D32" },
                  development: { bg: "#E3F2FD", color: "#1565C0" },
                  law: { bg: "#F3E5F5", color: "#6A1B9A" },
                };
                const bs = badgeStyle[issue.type] || { bg: "#E6F1FB", color: "#0C447C" };
                return (
                <IssueCard
                  key={i}
                  badge={ISSUE_TYPE_LABELS[issue.type] || issue.type}
                  badgeBg={bs.bg}
                  badgeColor={bs.color}
                  text={issue.title
                    .replace(/&quot;/g, '"')
                    .replace(/&amp;/g, "&")}
                  summary={issue.summary
                    ?.replace(/&quot;/g, '"')
                    .replace(/&amp;/g, "&")}
                  publishedAt={issue.publishedAt}
                  url={issue.url || ""}
                />
                );
              })}
              {!issuesLoading &&
                (!issuesData?.items || issuesData.items.length === 0) && (
                  <Text style={styles.emptyText}>관련 이슈가 없습니다</Text>
                )}
            </View>
          )}

          {/* AI 리포트 탭 */}
          {cxTab === 2 && (
            <AIReport
              report={reportData}
              status={rcStatus}
              onGenerate={() => generate("rc")}
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
  tertiary: { fontSize: 11, color: "#AAAAAA", marginTop: 2 },
  loadingText: { fontSize: 12, color: "#AAAAAA" },
  amenityList: { marginTop: 8 },
  amenityRow: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 6,
  },
  amenityDot: { width: 9, height: 9, borderRadius: 5, marginRight: 8 },
  amenityCat: { fontSize: 12, color: "#888888", width: 56 },
  amenityName: { flex: 1, fontSize: 13, color: "#111111", fontWeight: "500" },
  amenityDist: { fontSize: 12, color: "#AAAAAA" },
  mapPlaceholder: {
    margin: 12,
    marginBottom: 0,
    height: 180,
    backgroundColor: "#E8EEE4",
    borderRadius: 14,
    borderWidth: 0.5,
    borderColor: "#E5E5E5",
  },
  tabbar: {
    flexDirection: "row",
    marginHorizontal: 12,
    marginTop: 12,
    backgroundColor: "#FFFFFF",
    borderBottomWidth: 1,
    borderBottomColor: "#E5E5E5",
  },
  ti: { flex: 1, alignItems: "center", paddingVertical: 10, borderRadius: 0 },
  tiOn: {
    borderBottomWidth: 2,
    borderBottomColor: "#2563EB",
    backgroundColor: "#FFFFFF",
  },
  tiText: { fontSize: 13, color: "#888888" },
  tiTextOn: { color: "#2563EB", fontWeight: "600" },
  tc: { padding: 12 },
  ptog: { flexDirection: "row", marginBottom: 12, backgroundColor: "#F5F5F5", borderRadius: 8, padding: 3 },
  ptb: {
    flex: 1,
    alignItems: "center",
    paddingVertical: 6,
    borderRadius: 6,
  },
  ptbOn: { backgroundColor: "#FFFFFF", shadowColor: "#000", shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.08, shadowRadius: 2, elevation: 1 },
  ptbText: { fontSize: 12, color: "#AAAAAA" },
  ptbTextOn: { color: "#111111", fontWeight: "600" },
  rtog: { flexDirection: "row", marginBottom: 12, backgroundColor: "#F5F5F5", borderRadius: 8, padding: 3 },
  rtb: {
    flex: 1,
    alignItems: "center",
    paddingVertical: 6,
    borderRadius: 6,
  },
  rtbOn: { backgroundColor: "#FFFFFF", shadowColor: "#000", shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.08, shadowRadius: 2, elevation: 1 },
  rtbText: { fontSize: 12, color: "#AAAAAA" },
  rtbTextOn: { color: "#111111", fontWeight: "600" },
  chartTitle: { fontSize: 13, color: "#888888", marginBottom: 8 },
  emptyText: {
    fontSize: 13,
    color: "#AAAAAA",
    textAlign: "center",
    paddingVertical: 24,
  },
});

export default ComplexScreen;

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

  const { data: trendData } = usePriceTrend(
    selectedRegion?.regionId || "",
    selectedRegion?.lat || 0,
    selectedRegion?.lng || 0,
    "1y",
    selectedRegion?.name || "",
  );

  // 전월 대비 변동률 계산
  const saleTrend = trendData?.trend.filter((t) => t.dealType === "sale") || [];
  const changeRate = saleTrend.length >= 2
    ? ((saleTrend[0].avgPrice - saleTrend[1].avgPrice) / saleTrend[1].avgPrice * 100).toFixed(1)
    : null;

  const { data: markerData, isLoading: markerLoading } = useMapMarkers(
    selectedRegion?.regionId || "",
    selectedRegion?.lat || 0,
    selectedRegion?.lng || 0,
    "infra",
    2000,
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
                {priceLoading ? "조회 중..." : priceData?.avgSalePrice
                  ? `${Math.round(priceData.avgSalePrice / 10000)}억 ${Math.round((priceData.avgSalePrice % 10000) / 1000)}천`
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
                {priceLoading ? "조회 중..." : priceData?.avgJeonsePrice
                  ? `${Math.round(priceData.avgJeonsePrice / 10000)}억 ${Math.round((priceData.avgJeonsePrice % 10000) / 1000)}천`
                  : "데이터 없음"}
              </Text>
            </View>
          </View>
          <View style={styles.sdv} />
          <View style={styles.sr}>
            <View style={styles.si}>
              <Text style={styles.sl}>월세 평균</Text>
              <Text style={styles.svsm}>
                {priceLoading ? "조회 중..." : priceData?.avgMonthlyRent
                  ? `보증금 ${Math.round((priceData.avgMonthlyDeposit || 0) / 1000)}천/월 ${priceData.avgMonthlyRent}만`
                  : "데이터 없음"}
              </Text>
            </View>
            <View style={styles.sp} />
            <View style={styles.si}>
              <Text style={styles.sl}>이번달 거래량</Text>
              <Text style={styles.sv}>
                {priceLoading ? "조회 중..." : `${priceData?.recentTradeCount ?? 0}건`}
              </Text>
            </View>
          </View>
          <View style={styles.sdv} />

          {/* 지하철 노선 */}
          <Text style={styles.sl}>지하철 노선</Text>
          <View style={styles.subwayRow}>
            {markerLoading ? (
              <Text style={styles.loadingText}>불러오는 중...</Text>
            ) : subwayLines.length > 0 ? (
              subwayLines.map((line, i) => (
                <View key={i} style={styles.subwayTag}>
                  <Text style={styles.subwayTagText}>{line} 통과</Text>
                </View>
              ))
            ) : (
              <Text style={styles.loadingText}>반경 내 지하철 없음</Text>
            )}
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
            markers={markerData?.markers
              .filter((m) => m.markerType === "subway")
              .map((m) => ({
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
  scr: { flex: 1, backgroundColor: "#F0EEE6" },
  bar: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 16,
    paddingVertical: 13,
    borderBottomWidth: 0.5,
    borderBottomColor: "#E8E5DA",
    backgroundColor: "#FAF9F5",
    gap: 10,
  },
  bk: { fontSize: 22, color: "#1A1A18" },
  regionName: { fontSize: 14, fontWeight: "500", color: "#1A1A18" },
  regionAddr: { fontSize: 10, color: "#6B6B66" },
  sc: { flex: 1 },
  scard: {
    backgroundColor: "#FAF9F5",
    borderRadius: 14,
    borderWidth: 0.5,
    borderColor: "#E8E5DA",
    padding: 14,
    margin: 10,
    marginBottom: 0,
  },
  sr: { flexDirection: "row", alignItems: "flex-start" },
  si: { flex: 1 },
  sp: { width: 0.5, backgroundColor: "#E8E5DA", marginHorizontal: 10 },
  sdv: { height: 0.5, backgroundColor: "#E8E5DA", marginVertical: 10 },
  sl: { fontSize: 10, color: "#6B6B66", marginBottom: 2 },
  sv: { fontSize: 16, fontWeight: "600", color: "#1A1A18" },
  svsm: { fontSize: 12, fontWeight: "500", color: "#1A1A18" },
  sd: { fontSize: 10, color: "#27AE60", marginTop: 1 },
  subwayRow: { flexDirection: "row", flexWrap: "wrap", gap: 5, marginTop: 5 },
  subwayTag: {
    backgroundColor: "#E8F5E9",
    borderRadius: 6,
    paddingHorizontal: 8,
    paddingVertical: 3,
  },
  subwayTagText: { fontSize: 11, color: "#27AE60", fontWeight: "500" },
  loadingText: { fontSize: 11, color: "#9B9B95" },
  mapPlaceholder: {
    margin: 10,
    marginBottom: 0,
    height: 180,
    backgroundColor: "#E8EEE4",
    borderRadius: 14,
    borderWidth: 0.5,
    borderColor: "#E8E5DA",
  },
  cp: { margin: 10, marginBottom: 0 },
  cpt: { fontSize: 13, fontWeight: "500", color: "#1A1A18" },
  cps: { fontSize: 11, color: "#9B9B95", marginTop: 4 },
  tabbar: {
    flexDirection: "row",
    margin: 10,
    marginBottom: 0,
    backgroundColor: "#F0EEE6",
    borderRadius: 10,
    padding: 3,
  },
  ti: { flex: 1, alignItems: "center", paddingVertical: 7, borderRadius: 8 },
  tiOn: {
    backgroundColor: "#FAF9F5",
    borderWidth: 0.5,
    borderColor: "#E8E5DA",
  },
  tiText: { fontSize: 12, color: "#6B6B66" },
  tiTextOn: { color: "#1A1A18", fontWeight: "500" },
  tc: { padding: 10 },
  emptyText: {
    fontSize: 12,
    color: "#9B9B95",
    textAlign: "center",
    paddingVertical: 24,
  },
});

export default AreaScreen;

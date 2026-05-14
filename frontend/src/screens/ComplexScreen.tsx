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
import Stats3 from "../components/Stats3";
import { RC_REPORT } from "../constants/mockData";
import { useIssues, usePrice } from "../hooks/useAnalysis";
import { useMapMarkers } from "../hooks/useMap";
import { useAppStore } from "../store/useAppStore";
import { ReportStatus, ReportTarget, Screen } from "../types";

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
  generate,
  go,
}) => {
  const { selectedRegion, prevScreen } = useAppStore();

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

  const { data: issuesData, isLoading: issuesLoading } = useIssues(
    selectedRegion?.regionId || "",
    selectedRegion?.name || "",
  );

  return (
    <View style={styles.scr}>
      {/* 상단 헤더 */}
      <View style={styles.bar}>
        <TouchableOpacity onPress={() => go(prevScreen)}>
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
                {priceLoading
                  ? "조회 중..."
                  : priceData?.avgSalePrice
                    ? `${Math.round(priceData.avgSalePrice / 10000)}억 ${Math.round((priceData.avgSalePrice % 10000) / 1000)}천`
                    : "데이터 없음"}
              </Text>
            </View>
            <View style={styles.sp} />
            <View style={styles.si}>
              <Text style={styles.sl}>전세 평균가</Text>
              <Text style={styles.sv}>
                {priceLoading
                  ? "조회 중..."
                  : priceData?.avgJeonsePrice
                    ? `${Math.round(priceData.avgJeonsePrice / 10000)}억 ${Math.round((priceData.avgJeonsePrice % 10000) / 1000)}천`
                    : "데이터 없음"}
              </Text>
              <Text style={styles.tertiary}>
                {priceData?.jeonseRatio
                  ? `전세가율 ${priceData.jeonseRatio}%`
                  : ""}
              </Text>
            </View>
          </View>
          <View style={styles.sdv} />
          <View style={styles.sr}>
            <View style={styles.si}>
              <Text style={styles.sl}>월세 평균</Text>
              <Text style={styles.svsm}>
                {priceLoading
                  ? "조회 중..."
                  : priceData?.avgMonthlyRent
                    ? `보증금 ${Math.round((priceData.avgMonthlyDeposit || 0) / 1000)}천/월 ${priceData.avgMonthlyRent}만`
                    : "데이터 없음"}
              </Text>
            </View>
            <View style={styles.sp} />
            <View style={styles.si}>
              <Text style={styles.sl}>이번달 거래량</Text>
              <Text style={styles.sv}>
                {priceLoading
                  ? "조회 중..."
                  : `${priceData?.recentTradeCount ?? 0}건`}
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
                    <Text
                      style={[
                        styles.ptbText,
                        priceTab === i && styles.ptbTextOn,
                      ]}
                    >
                      {p}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
              {priceTab === 0 && (
                <View>
                  <Text style={styles.chartTitle}>
                    매매가 추이 (최근 6개월)
                  </Text>
                  <BarChart idx={0} />
                  <Stats3
                    items={[
                      ["최저가", "14.2억"],
                      ["평균가", "14.8억"],
                      ["최고가", "15.2억"],
                    ]}
                  />
                </View>
              )}
              {priceTab === 1 && (
                <View>
                  <Text style={styles.chartTitle}>
                    전세가 추이 (최근 6개월)
                  </Text>
                  <BarChart idx={1} />
                  <Stats3
                    items={[
                      ["최저가", "7.8억"],
                      ["평균가", "8.2억"],
                      ["최고가", "8.5억"],
                    ]}
                  />
                </View>
              )}
              {priceTab === 2 && (
                <View>
                  <View style={styles.rtog}>
                    {["월세 추이", "보증금 추이"].map((r, i) => (
                      <TouchableOpacity
                        key={i}
                        style={[styles.rtb, rentTab === i && styles.rtbOn]}
                        onPress={() => setRentTab(i)}
                      >
                        <Text
                          style={[
                            styles.rtbText,
                            rentTab === i && styles.rtbTextOn,
                          ]}
                        >
                          {r}
                        </Text>
                      </TouchableOpacity>
                    ))}
                  </View>
                  {rentTab === 0 ? (
                    <View>
                      <Text style={styles.chartTitle}>
                        월세 추이 (최근 6개월)
                      </Text>
                      <BarChart idx={2} />
                      <Stats3
                        items={[
                          ["최저", "78만"],
                          ["평균", "130만"],
                          ["최고", "165만"],
                        ]}
                      />
                    </View>
                  ) : (
                    <View>
                      <Text style={styles.chartTitle}>
                        보증금 추이 (최근 6개월)
                      </Text>
                      <BarChart idx={3} />
                      <Stats3
                        items={[
                          ["최저", "500만"],
                          ["평균", "2,000만"],
                          ["최고", "5,000만"],
                        ]}
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

          {/* AI 리포트 탭 */}
          {cxTab === 2 && (
            <AIReport
              report={RC_REPORT}
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
  tertiary: { fontSize: 10, color: "#9B9B95", marginTop: 1 },
  loadingText: { fontSize: 11, color: "#9B9B95" },
  amenityList: { marginTop: 6 },
  amenityRow: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 4,
  },
  amenityDot: { width: 8, height: 8, borderRadius: 4, marginRight: 6 },
  amenityCat: { fontSize: 11, color: "#6B6B66", width: 50 },
  amenityName: { flex: 1, fontSize: 11, color: "#1A1A18", fontWeight: "500" },
  amenityDist: { fontSize: 11, color: "#9B9B95" },
  mapPlaceholder: {
    margin: 10,
    marginBottom: 0,
    height: 180,
    backgroundColor: "#E8EEE4",
    borderRadius: 14,
    borderWidth: 0.5,
    borderColor: "#E8E5DA",
  },
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
  ptog: { flexDirection: "row", marginBottom: 10 },
  ptb: {
    flex: 1,
    alignItems: "center",
    paddingVertical: 6,
    borderRadius: 8,
    backgroundColor: "#F0EEE6",
  },
  ptbOn: { backgroundColor: "#1A1A18" },
  ptbText: { fontSize: 12, color: "#6B6B66" },
  ptbTextOn: { color: "white", fontWeight: "500" },
  rtog: { flexDirection: "row", marginBottom: 10 },
  rtb: {
    flex: 1,
    alignItems: "center",
    paddingVertical: 6,
    borderRadius: 8,
    backgroundColor: "#F0EEE6",
  },
  rtbOn: { backgroundColor: "#1A1A18" },
  rtbText: { fontSize: 12, color: "#6B6B66" },
  rtbTextOn: { color: "white", fontWeight: "500" },
  chartTitle: { fontSize: 12, color: "#6B6B66", marginBottom: 8 },
  emptyText: {
    fontSize: 12,
    color: "#9B9B95",
    textAlign: "center",
    paddingVertical: 24,
  },
});

export default ComplexScreen;

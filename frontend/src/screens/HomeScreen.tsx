// 메인화면 - 검색, 지도 탭, 뉴스 목록

import React, { useRef } from "react";
import {
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import DropdownItem from "../components/DropdownItem";
import IssueRow from "../components/IssueRow";
import KakaoMap from "../components/KakaoMap";
import seoulGu from "../constants/seoul_gu.json";
import { COLORS } from "../constants/colors";
import { MAP_TAB_LABELS } from "../constants/mockData";
import { useNewsHighlights } from "../hooks/useNews";
import { useRegionSearch } from "../hooks/useRegions";
import { useAppStore } from "../store/useAppStore";
import { Screen } from "../types";
import { usePriceLayer } from "../hooks/useMap";

interface HomeScreenProps {
  mapTab: number;
  setMapTab: (n: number) => void;
  go: (s: Screen) => void;
}

const NEWS_CATEGORY_LABELS: Record<string, string> = {
  market: "시장",
  policy: "정책",
  development: "개발",
  law: "법률",
};

const HomeScreen: React.FC<HomeScreenProps> = ({ mapTab, setMapTab, go }) => {
  const {
    searchVal,
    setSearchVal,
    setSelectedRegion,
    addRecentSearch,
    setListSearchVal,
  } = useAppStore();

  const TAB_TYPES = ["sale", "jeonse", "monthly"];
  const { data: priceLayerData } = usePriceLayer(
    "seoul-11680",  // 서울 전체 기준 (임시)
    TAB_TYPES[mapTab]
  );

  const scrollRef = useRef<ScrollView>(null);

  const showDD = searchVal.length > 0;

  const { data: searchData, isLoading: searchLoading } =
    useRegionSearch(searchVal);

  const { data: newsData, isLoading: newsLoading } = useNewsHighlights();

  const handleSearch = async () => {
    const trimmed = searchVal.trim();
    if (trimmed.length === 0) return;
    try {
      const res = await fetch(
        `https://api-dev.ourhomelens.com/api/v1/regions/search?q=${encodeURIComponent(trimmed)}&limit=1`,
      );
      const data = await res.json();
      if (data && data.length > 0) {
        const first = data[0];
        if (first.propertyType === "area" && first.name === searchVal.trim()) {
          setSelectedRegion({
            regionId: first.regionId,
            name: first.name,
            fullAddress: first.fullAddress,
            lat: first.lat,
            lng: first.lng,
            aptSeq: first.aptSeq ?? undefined,
          });
          addRecentSearch(first.name);
          setSearchVal("");
          go("area");
          return;
        }
      }
    } catch (err) {
      console.error(err);
    }
    setListSearchVal(searchVal);
    go("list");
  };

  return (
    <View style={styles.scr}>
      {/* 상단 헤더 */}
      <View style={styles.bar}>
        <View style={styles.barLeft}>
          <View style={styles.logoIcon}>
            <Text style={styles.logoIconText}>🏠</Text>
          </View>
          <Text style={styles.logo}>HomeLens</Text>
        </View>
      </View>

      <ScrollView
        ref={scrollRef}
        style={styles.sc}
        showsVerticalScrollIndicator={false}
        scrollEventThrottle={16}
      >

        {/* 검색창 */}
        <View style={styles.sb}>
          <Text style={styles.searchIcon}>🔍</Text>
          <TextInput
            style={styles.sbInput}
            placeholder="동 이름이나 아파트명으로 검색"
            placeholderTextColor={COLORS.textTertiary}
            value={searchVal}
            onChangeText={(text) => setSearchVal(text.trim())}
            onSubmitEditing={handleSearch}
            returnKeyType="search"
            submitBehavior="blurAndSubmit"
          />
        </View>

        {/* 자동완성 드롭다운 */}
        {showDD && (
          <View style={styles.dd}>
            {searchLoading && (
              <Text style={styles.loadingText}>검색 중...</Text>
            )}
            {searchData?.map((item, i) => (
              <DropdownItem
                key={i}
                type={item.propertyType === "area" ? "area" : "complex"}
                name={item.name}
                sub={item.fullAddress}
                onClick={() => {
                  setSelectedRegion({
                    regionId: item.regionId,
                    name: item.name,
                    fullAddress: item.fullAddress,
                    lat: item.lat,
                    lng: item.lng,
                    aptSeq: item.aptSeq ?? undefined,
                  });
                  addRecentSearch(item.name);
                  setSearchVal("");
                  go(item.propertyType === "area" ? "area" : "complex");
                }}
              />
            ))}
          </View>
        )}

        {/* 지도 탭 라벨 */}
        <View style={styles.mclb}>
          <Text style={styles.mct}>{MAP_TAB_LABELS[mapTab]}</Text>
        </View>

        {/* 지도 탭 버튼 */}
        <View style={styles.mtab}>
          {["매매", "전세", "월세"].map(
            (t, i) => (
              <TouchableOpacity
                key={i}
                style={[styles.mt, mapTab === i && styles.mtOn]}
                onPress={() => setMapTab(i)}
              >
                <Text style={[styles.mtText, mapTab === i && styles.mtTextOn]}>
                  {t}
                </Text>
              </TouchableOpacity>
            ),
          )}
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
            lat={37.5665}
            lng={126.978}
            level={10}
            markers={[]}
            polygons={priceLayerData?.zones.map((zone) => ({
              code: zone.aptName || zone.zoneId,
              grade: zone.priceGrade,
              name: zone.aptName || "",
              value: zone.value,
            }))}
            geoJson={seoulGu}
            onMarkerClick={(marker) => {
              if (marker.kakaoPlaceId) {
                setSelectedRegion({
                  regionId: `KAKAO_${marker.kakaoPlaceId}`,
                  name: marker.name,
                  fullAddress: "",
                  lat: marker.lat,
                  lng: marker.lng,
                  aptSeq: marker.aptSeq,
                });
                go("complex");
              }
            }}
          />
        </View>

        {/* 뉴스 목록 */}
        <View style={styles.sec}>
          <Text style={styles.st}>최근 주요 이슈</Text>
          {newsLoading && (
            <Text style={styles.loadingText}>뉴스 불러오는 중...</Text>
          )}
          {newsData?.items.map((item, i) => {
            const badgeStyle: Record<string, { bg: string; color: string }> = {
              market: { bg: "#FFF3E0", color: "#E65100" },
              policy: { bg: "#E8F5E9", color: "#2E7D32" },
              development: { bg: "#E3F2FD", color: "#1565C0" },
              law: { bg: "#F3E5F5", color: "#6A1B9A" },
            };
            const bs = badgeStyle[item.category] || { bg: "#E6F1FB", color: "#0C447C" };
            return (
            <IssueRow
              key={i}
              badge={NEWS_CATEGORY_LABELS[item.category] || item.category}
              badgeBg={bs.bg}
              badgeColor={bs.color}
              text={item.title.replace(/&quot;/g, '"').replace(/&amp;/g, "&")}
              summary={item.summary
                ?.replace(/&quot;/g, '"')
                .replace(/&amp;/g, "&")}
              publishedAt={item.publishedAt}
              url={item.url || ""}
            />
            );
          })}
        </View>
        <View style={{ height: 16 }} />
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  scr: { flex: 1, backgroundColor: "#F5F5F5" },
  bar: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: "#E5E5E5",
    backgroundColor: "#FFFFFF",
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  barLeft: { flexDirection: "row", alignItems: "center", gap: 8 },
  logoIcon: {
    width: 32,
    height: 32,
    backgroundColor: "#2563EB",
    borderRadius: 8,
    alignItems: "center",
    justifyContent: "center",
  },
  logoIconText: { fontSize: 16 },
  logo: { fontSize: 20, fontWeight: "700", color: "#111111" },
  sc: { flex: 1 },
  title: { fontSize: 20, fontWeight: "700", color: "#111111", marginBottom: 4 },
  subtitle: { fontSize: 14, color: "#888888" },
  sb: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#F0F0F0",
    borderRadius: 24,
    paddingHorizontal: 14,
    paddingVertical: 10,
    marginHorizontal: 16,
    marginTop: 14,
    gap: 8,
  },
  searchIcon: { fontSize: 16 },
  sbInput: { flex: 1, fontSize: 15, color: "#111111" },
  dd: {
    marginHorizontal: 16,
    backgroundColor: "#FFFFFF",
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#E0E0E0",
    marginTop: 4,
    overflow: "hidden",
  },
  loadingText: { fontSize: 12, color: "#AAAAAA", padding: 10 },
  mclb: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginHorizontal: 16,
    marginTop: 14,
  },
  mct: { fontSize: 14, fontWeight: "600", color: "#111111" },
  mcs: { fontSize: 11, color: "#AAAAAA" },
  mtab: {
    flexDirection: "row",
    gap: 8,
    marginHorizontal: 16,
    marginTop: 8,
  },
  mt: {
    paddingHorizontal: 20,
    paddingVertical: 8,
    borderRadius: 20,
  },
  mtOn: { backgroundColor: "#2563EB" },
  mtText: { fontSize: 13, color: "#888888", fontWeight: "500" },
  mtTextOn: { color: "#FFFFFF", fontWeight: "600" },
  mapPlaceholder: {
    marginHorizontal: 16,
    marginTop: 6,
    height: 192,
    backgroundColor: "#E8EEE4",
    borderRadius: 14,
    borderWidth: 0.5,
    borderColor: "#E5E5E5",
  },
  sec: { marginTop: 20, paddingHorizontal: 16 },
  st: { fontSize: 16, fontWeight: "700", color: "#111111", marginBottom: 10 },
});

export default HomeScreen;

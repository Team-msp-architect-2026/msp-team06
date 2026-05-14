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
import { COLORS } from "../constants/colors";
import { MAP_TAB_LABELS } from "../constants/mockData";
import { useNewsHighlights } from "../hooks/useNews";
import { useRegionSearch } from "../hooks/useRegions";
import { useAppStore } from "../store/useAppStore";
import { Screen } from "../types";

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

  const scrollRef = useRef<ScrollView>(null);

  const showDD = searchVal.length > 0;

  const { data: searchData, isLoading: searchLoading } =
    useRegionSearch(searchVal);

  const { data: newsData, isLoading: newsLoading } = useNewsHighlights();

  const handleSearch = async () => {
    if (searchVal.trim().length === 0) return;
    try {
      const res = await fetch(
        `http://10.0.2.2:8000/api/v1/regions/search?q=${encodeURIComponent(searchVal.trim())}&limit=1`,
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
        <Text style={styles.logo}>HomeLens</Text>
      </View>

      <ScrollView
        ref={scrollRef}
        style={styles.sc}
        showsVerticalScrollIndicator={false}
        scrollEventThrottle={16}
      >
        {/* 검색 안내 텍스트 */}
        <View style={{ padding: 14, paddingBottom: 4 }}>
          <Text style={styles.title}>어디서 살고 싶으세요?</Text>
          <Text style={styles.subtitle}>동 이름이나 아파트명으로 검색</Text>
        </View>

        {/* 검색창 */}
        <View style={styles.sb}>
          <TextInput
            style={styles.sbInput}
            placeholder="성수동, 성수 롯데캐슬 파크..."
            placeholderTextColor={COLORS.textTertiary}
            value={searchVal}
            onChangeText={setSearchVal}
            onSubmitEditing={handleSearch}
            returnKeyType="search"
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
          <Text style={styles.mcs}>단지 단위 · 탭하면 분석 이동</Text>
        </View>

        {/* 지도 탭 버튼 */}
        <View style={styles.mtab}>
          {["매매 거래량", "전세가율 낮은 곳", "월세 부담 낮은 곳"].map(
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
          <KakaoMap lat={37.5665} lng={126.978} level={8} />
        </View>

        {/* 뉴스 목록 */}
        <View style={styles.sec}>
          <Text style={styles.st}>최근 주요 이슈</Text>
          {newsLoading && (
            <Text style={styles.loadingText}>뉴스 불러오는 중...</Text>
          )}
          {newsData?.items.map((item, i) => (
            <IssueRow
              key={i}
              badge={NEWS_CATEGORY_LABELS[item.category] || item.category}
              badgeBg="#E6F1FB"
              badgeColor="#0C447C"
              text={item.title.replace(/&quot;/g, '"').replace(/&amp;/g, "&")}
              summary={item.summary
                ?.replace(/&quot;/g, '"')
                .replace(/&amp;/g, "&")}
              publishedAt={item.publishedAt}
              url={item.url || ""}
            />
          ))}
        </View>
        <View style={{ height: 16 }} />
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  scr: { flex: 1, backgroundColor: "#F0EEE6" },
  bar: {
    paddingHorizontal: 16,
    paddingVertical: 13,
    borderBottomWidth: 0.5,
    borderBottomColor: "#E8E5DA",
    backgroundColor: "#FAF9F5",
  },
  logo: { fontSize: 19, fontWeight: "500", color: "#1A1A18" },
  sc: { flex: 1 },
  title: { fontSize: 17, fontWeight: "500", color: "#1A1A18", marginBottom: 3 },
  subtitle: { fontSize: 12, color: "#6B6B66" },
  sb: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#FAF9F5",
    borderWidth: 1,
    borderColor: "#D9D6CB",
    borderRadius: 11,
    paddingHorizontal: 12,
    paddingVertical: 9,
    marginHorizontal: 16,
    marginTop: 14,
  },
  sbInput: { flex: 1, fontSize: 13, color: "#1A1A18" },
  dd: {
    marginHorizontal: 16,
    backgroundColor: "#FAF9F5",
    borderWidth: 1,
    borderColor: "#D9D6CB",
    borderRadius: 11,
    marginTop: 4,
  },
  loadingText: { fontSize: 11, color: "#9B9B95", padding: 10 },
  mclb: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginHorizontal: 16,
    marginTop: 10,
  },
  mct: { fontSize: 12, fontWeight: "500", color: "#1A1A18" },
  mcs: { fontSize: 10, color: "#9B9B95" },
  mtab: {
    flexDirection: "row",
    backgroundColor: "#F0EEE6",
    borderRadius: 10,
    padding: 3,
    marginHorizontal: 16,
    marginTop: 6,
  },
  mt: { flex: 1, alignItems: "center", paddingVertical: 6, borderRadius: 8 },
  mtOn: {
    backgroundColor: "#FAF9F5",
    borderWidth: 0.5,
    borderColor: "#E8E5DA",
  },
  mtText: { fontSize: 10, color: "#6B6B66" },
  mtTextOn: { color: "#1A1A18", fontWeight: "500" },
  mapPlaceholder: {
    marginHorizontal: 16,
    marginTop: 6,
    height: 192,
    backgroundColor: "#E8EEE4",
    borderRadius: 14,
    borderWidth: 0.5,
    borderColor: "#E8E5DA",
  },
  sec: { marginTop: 10, paddingHorizontal: 16 },
  st: { fontSize: 13, fontWeight: "500", color: "#1A1A18", marginBottom: 7 },
});

export default HomeScreen;

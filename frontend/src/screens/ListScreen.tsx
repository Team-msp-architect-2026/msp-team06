// 검색 목록 화면 - 검색어 기반 지역/단지 결과 목록 표시
import React from "react";
import {
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import DropdownItem from "../components/DropdownItem";
import { useRegionSearch } from "../hooks/useRegions";
import { useAppStore } from "../store/useAppStore";
import { Screen } from "../types";

interface ListScreenProps {
  go: (s: Screen) => void;
}

const ListScreen: React.FC<ListScreenProps> = ({ go }) => {
  const { listSearchVal, setSelectedRegion, addRecentSearch, setSearchVal } =
    useAppStore();
  const { data: searchData, isLoading } = useRegionSearch(listSearchVal);

  return (
    <View style={styles.scr}>
      <View style={styles.bar}>
        <TouchableOpacity onPress={() => go("home")}>
          <Text style={styles.bk}>‹</Text>
        </TouchableOpacity>
        <Text style={styles.title}>{`"${listSearchVal}" 검색 결과`}</Text>
      </View>
      <ScrollView style={styles.sc} showsVerticalScrollIndicator={false}>
        <Text style={styles.count}>
          {isLoading ? "검색 중..." : `총 ${searchData?.length || 0}개 결과`}
        </Text>
        <View style={styles.list}>
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
          {!isLoading && (!searchData || searchData.length === 0) && (
            <Text style={styles.empty}>검색 결과가 없습니다</Text>
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
  title: { fontSize: 13, fontWeight: "500", color: "#1A1A18" },
  sc: { flex: 1 },
  count: { fontSize: 11, color: "#6B6B66", padding: 8, paddingHorizontal: 16 },
  list: { paddingHorizontal: 16, paddingBottom: 16 },
  empty: {
    fontSize: 12,
    color: "#9B9B95",
    textAlign: "center",
    paddingVertical: 24,
  },
});

export default ListScreen;
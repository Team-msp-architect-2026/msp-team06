// HomeLens AI - 검색 목록 화면 컴포넌트

import React from "react";
import DropdownItem from "../components/DropdownItem";
import { COLORS } from "../constants/colors";
import { S } from "../constants/styles";
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
    <div style={S.scr}>
      <div style={S.bar}>
        <span style={S.bk} onClick={() => go("home")}>
          ‹
        </span>
        <span
          style={{ fontSize: 13, fontWeight: 500, color: COLORS.textPrimary }}
        >
          &ldquo;{listSearchVal}&rdquo; 검색 결과
        </span>
      </div>
      <div style={S.sc}>
        <div
          style={{
            fontSize: 11,
            color: COLORS.textSecondary,
            padding: "8px 16px",
          }}
        >
          {isLoading ? "검색 중..." : `총 ${searchData?.length || 0}개 결과`}
        </div>
        <div style={{ padding: "0 16px 16px" }}>
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
          {!isLoading && (!searchData || searchData.length === 0) && (
            <div
              style={{
                fontSize: 12,
                color: COLORS.textTertiary,
                textAlign: "center",
                padding: "24px 0",
              }}
            >
              검색 결과가 없습니다
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ListScreen;

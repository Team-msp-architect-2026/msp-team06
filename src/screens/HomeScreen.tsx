// HomeLens AI - 메인화면 컴포넌트
// 뉴스 데이터 실제 API 연동 완료
// 지도/검색 API 연동은 카카오맵 도메인 등록 후 진행 예정

import React, { useEffect, useRef } from "react";
import DropdownItem from "../components/DropdownItem";
import IssueRow from "../components/IssueRow";
import { COLORS } from "../constants/colors";
import { MAP_TAB_LABELS } from "../constants/mockData";
import { S } from "../constants/styles";
import { useNewsHighlights } from "../hooks/useNews";
import { useRegionSearch } from "../hooks/useRegions";
import { useAppStore } from "../store/useAppStore";
import { Screen } from "../types";

interface HomeScreenProps {
  mapTab: number;
  setMapTab: (n: number) => void;
  go: (s: Screen) => void;
}

const HomeScreen: React.FC<HomeScreenProps> = ({ mapTab, setMapTab, go }) => {
  // Zustand 전역 상태에서 검색어 관리
  const {
    searchVal,
    setSearchVal,
    setSelectedRegion,
    addRecentSearch,
    setListSearchVal,
  } = useAppStore();

  const mapRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!mapRef.current) return;

    const initMap = () => {
      const kakao = (window as any).kakao;
      if (!kakao || !mapRef.current) return;
      kakao.maps.load(() => {
        const options = {
          center: new kakao.maps.LatLng(37.5665, 126.978), // 서울 중심
          level: 8,
        };
        new kakao.maps.Map(mapRef.current!, options);
      });
    };

    if ((window as any).kakao) {
      initMap();
    } else {
      setTimeout(initMap, 1000);
    }
  }, []);

  const showDD = searchVal.length > 0;
  // 실제 카카오맵 API 자동완성 검색
  const { data: searchData, isLoading: searchLoading } =
    useRegionSearch(searchVal);

  // 실제 뉴스 API 데이터 조회
  const { data: newsData, isLoading: newsLoading } = useNewsHighlights();

  const NEWS_CATEGORY_LABELS: Record<string, string> = {
    market: "시장",
    policy: "정책",
    development: "개발",
    law: "법률",
  };

  return (
    <div style={S.scr}>
      <div style={S.bar}>
        <span style={S.logo}>HomeLens</span>
      </div>
      <div style={S.sc}>
        <div style={{ padding: "14px 16px 4px" }}>
          <div
            style={{
              fontSize: 17,
              fontWeight: 500,
              color: COLORS.textPrimary,
              marginBottom: 3,
            }}
          >
            어디서 살고 싶으세요?
          </div>
          <div style={{ fontSize: 12, color: COLORS.textSecondary }}>
            동 이름이나 아파트명으로 검색
          </div>
        </div>
        <div style={S.sb}>
          <svg width="13" height="13" viewBox="0 0 16 16" fill="none">
            <circle
              cx="6.5"
              cy="6.5"
              r="5"
              stroke={COLORS.textTertiary}
              strokeWidth="1.5"
            />
            <line
              x1="10.5"
              y1="10.5"
              x2="14"
              y2="14"
              stroke={COLORS.textTertiary}
              strokeWidth="1.5"
              strokeLinecap="round"
            />
          </svg>
          <input
            style={S.sbInput}
            placeholder="성수동, 성수 롯데캐슬 파크..."
            value={searchVal}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
              setSearchVal(e.target.value)
            }
            onKeyDown={async (e: React.KeyboardEvent<HTMLInputElement>) => {
              if (e.key === "Enter" && searchVal.trim().length > 0) {
                try {
                  const res = await fetch(
                    `http://localhost:8000/api/v1/regions/search?q=${encodeURIComponent(searchVal.trim())}&limit=1`,
                  );
                  const data = await res.json();
                  if (data && data.length > 0) {
                    const first = data[0];
                    if (
                      first.propertyType === "area" &&
                      first.name === searchVal.trim()
                    ) {
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
              }
            }}
          />
        </div>
        {showDD && (
          <div style={S.dd}>
            {searchLoading && (
              <div
                style={{
                  padding: "10px 12px",
                  fontSize: 11,
                  color: COLORS.textTertiary,
                }}
              >
                검색 중...
              </div>
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
          </div>
        )}
        <div style={S.mclb}>
          <span style={S.mct}>{MAP_TAB_LABELS[mapTab]}</span>
          <span style={S.mcs}>단지 단위 · 탭하면 분석 이동</span>
        </div>
        <div style={S.mtab}>
          {["매매 거래량", "전세가율 낮은 곳", "월세 부담 낮은 곳"].map(
            (t, i) => (
              <div
                key={i}
                style={{ ...S.mt, ...(mapTab === i ? S.mtOn : {}) }}
                onClick={() => setMapTab(i)}
              >
                {t}
              </div>
            ),
          )}
        </div>
        <div ref={mapRef} style={{ ...S.mw, height: 192 }} />

        <div style={S.sec}>
          <div style={S.st}>최근 주요 이슈</div>
          {newsLoading && (
            <div
              style={{
                fontSize: 11,
                color: COLORS.textTertiary,
                padding: "8px 0",
              }}
            >
              뉴스 불러오는 중...
            </div>
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
            />
          ))}
        </div>
        <div style={{ height: 16 }} />
      </div>
    </div>
  );
};

export default HomeScreen;

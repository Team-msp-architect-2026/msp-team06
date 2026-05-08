// HomeLens AI - 단지 단위 결과 화면 컴포넌트

import React, { useEffect, useRef } from "react";
import AIReport from "../components/AIReport";
import BarChart from "../components/BarChart";
import IssueCard from "../components/IssueCard";
import Stats3 from "../components/Stats3";
import { COLORS } from "../constants/colors";
import { RC_REPORT } from "../constants/mockData";
import { S } from "../constants/styles";
import { useIssues } from "../hooks/useAnalysis";
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
  const { selectedRegion } = useAppStore();

  const { data: markerData, isLoading: markerLoading } = useMapMarkers(
    selectedRegion?.regionId || "",
    selectedRegion?.lat || 0,
    selectedRegion?.lng || 0,
    "infra",
  );

  const { data: issuesData, isLoading: issuesLoading } = useIssues(
    selectedRegion?.regionId || "",
    selectedRegion?.name || "",
  );

  const mapRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!selectedRegion?.lat || !selectedRegion?.lng || !mapRef.current) return;

    const initMap = () => {
      const kakao = (window as any).kakao;
      if (!kakao || !mapRef.current) return;
      kakao.maps.load(() => {
        const options = {
          center: new kakao.maps.LatLng(selectedRegion.lat, selectedRegion.lng),
          level: 3,
        };
        const map = new kakao.maps.Map(mapRef.current!, options);

        // 단지 중심 마커
        new kakao.maps.Marker({
          position: new kakao.maps.LatLng(
            selectedRegion.lat,
            selectedRegion.lng,
          ),
          map,
        });

        // 인프라 마커
        if (markerData?.markers) {
          markerData.markers.forEach((marker) => {
            if (marker.markerId.endsWith("_none")) return;
            if (!marker.lat || !marker.lng) return;

            const markerColors: Record<string, string> = {
              subway: "#3CB44B",
              mart: "#E67E22",
              department: "#9B59B6",
              hospital: "#E74C3C",
              school: "#3498DB",
            };

            const color = markerColors[marker.markerType] || "#888";

            const dotContent = document.createElement("div");
            dotContent.style.cssText = `
              width:12px;
              height:12px;
              background:${color};
              border-radius:50%;
              border:2px solid white;
              box-shadow:0 1px 3px rgba(0,0,0,0.4);
              cursor:pointer;
            `;

            const pos = new kakao.maps.LatLng(marker.lat, marker.lng);

            const overlay = new kakao.maps.CustomOverlay({
              position: pos,
              content: dotContent,
              yAnchor: 1,
            });
            overlay.setMap(map);

            dotContent.addEventListener("click", () => {
              // 기존 라벨 제거
              const existing = document.getElementById(
                `label-${marker.markerId}`,
              );
              if (existing) {
                existing.remove();
                return;
              }

              const label = document.createElement("div");
              label.id = `label-${marker.markerId}`;
              label.style.cssText = `
                position:absolute;
                background:white;
                border:1px solid #ddd;
                border-radius:6px;
                padding:3px 7px;
                font-size:11px;
                white-space:nowrap;
                box-shadow:0 1px 4px rgba(0,0,0,0.2);
                transform:translate(-50%, -130%);
                pointer-events:none;
              `;
              label.innerText = marker.name;
              dotContent.style.position = "relative";
              dotContent.appendChild(label);
            });
          });
        }
      });
    };

    if ((window as any).kakao) {
      initMap();
    } else {
      setTimeout(initMap, 1000);
    }
  }, [selectedRegion, markerData]);

  return (
    <div style={S.scr}>
      <div style={S.bar}>
        <span style={S.bk} onClick={() => go("area")}>
          ‹
        </span>
        <div>
          <div
            style={{ fontSize: 14, fontWeight: 500, color: COLORS.textPrimary }}
          >
            {selectedRegion?.name || ""}
          </div>
          <div style={{ fontSize: 10, color: COLORS.textSecondary }}>
            {selectedRegion?.fullAddress || ""}
          </div>
        </div>
      </div>
      <div style={S.sc}>
        {/* 단지 가격 정보 카드 */}
        <div style={S.scard}>
          <div style={S.sr}>
            <div style={S.si}>
              <div style={S.sl}>매매 평균가</div>
              <div style={S.sv}>15억 2천</div>
              <div style={S.sd}>▲ 전월 +2.1%</div>
            </div>
            <div style={S.sp} />
            <div style={S.si}>
              <div style={S.sl}>전세 평균가</div>
              <div style={S.sv}>8억 5천</div>
              <div
                style={{
                  fontSize: 10,
                  color: COLORS.textTertiary,
                  marginTop: 1,
                }}
              >
                전세가율 56%
              </div>
            </div>
          </div>
          <div style={S.sdv} />
          <div style={S.sr}>
            <div style={S.si}>
              <div style={S.sl}>월세 평균</div>
              <div style={S.svsm}>보증금 2천/월 130만</div>
            </div>
            <div style={S.sp} />
            <div style={S.si}>
              <div style={S.sl}>이번달 거래량</div>
              <div style={S.sv}>3건</div>
              <div style={S.sd}>▲ 전월 +1건</div>
            </div>
          </div>
          <div style={S.sdv} />
          <div style={S.sl}>주변 인프라 (반경 1.5km)</div>
          <div style={S.amenityList}>
            {markerLoading && (
              <div style={{ fontSize: 11, color: COLORS.textTertiary }}>
                불러오는 중...
              </div>
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
                <div key={i} style={S.amenityRow}>
                  <span
                    style={{
                      ...S.amenityDot,
                      background: isNone ? "#ccc" : color,
                    }}
                  />
                  <span style={S.amenityCat}>{label}</span>
                  <span style={S.amenityName}>
                    {isNone ? "반경 내 없음" : marker.name}
                  </span>
                  <span style={S.amenityDist}>{dist}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* 단지 지도 SVG 주석처리 */}
        {/*
        <div style={{ ...S.mw, marginTop: 10 }}>
          <svg width="288" height="180" viewBox="0 0 288 180">
            ...
          </svg>
          <div style={S.legend}>...</div>
        </div>
        */}

        {/* 카카오맵 SDK */}
        <div ref={mapRef} style={{ ...S.mw, marginTop: 10, height: 180 }} />

        {/* 가격 분석 / 이슈 분석 / AI 리포트 탭 전환 */}
        <div style={S.tabbar}>
          {["가격 분석", "이슈 분석", "AI 리포트"].map((t, i) => (
            <div
              key={i}
              style={{ ...S.ti, ...(cxTab === i ? S.tiOn : {}) }}
              onClick={() => setCxTab(i)}
            >
              {t}
            </div>
          ))}
        </div>
        <div style={S.tc}>
          {/* 가격 분석 탭 */}
          {cxTab === 0 && (
            <>
              <div style={S.ptog}>
                {["매매", "전세", "월세"].map((p, i) => (
                  <button
                    key={i}
                    style={{ ...S.ptb, ...(priceTab === i ? S.ptbOn : {}) }}
                    onClick={() => setPriceTab(i)}
                  >
                    {p}
                  </button>
                ))}
              </div>
              {priceTab === 0 && (
                <div>
                  <div style={S.chartTitle}>매매가 추이 (최근 6개월)</div>
                  <BarChart idx={0} />
                  <Stats3
                    items={[
                      ["최저가", "14.2억"],
                      ["평균가", "14.8억"],
                      ["최고가", "15.2억"],
                    ]}
                  />
                </div>
              )}
              {priceTab === 1 && (
                <div>
                  <div style={S.chartTitle}>전세가 추이 (최근 6개월)</div>
                  <BarChart idx={1} />
                  <Stats3
                    items={[
                      ["최저가", "7.8억"],
                      ["평균가", "8.2억"],
                      ["최고가", "8.5억"],
                    ]}
                  />
                </div>
              )}
              {priceTab === 2 && (
                <div>
                  <div style={S.rtog}>
                    {["월세 추이", "보증금 추이"].map((r, i) => (
                      <button
                        key={i}
                        style={{ ...S.rtb, ...(rentTab === i ? S.rtbOn : {}) }}
                        onClick={() => setRentTab(i)}
                      >
                        {r}
                      </button>
                    ))}
                  </div>
                  {rentTab === 0 ? (
                    <div>
                      <div style={S.chartTitle}>월세 추이 (최근 6개월)</div>
                      <BarChart idx={2} />
                      <Stats3
                        items={[
                          ["최저", "78만"],
                          ["평균", "130만"],
                          ["최고", "165만"],
                        ]}
                      />
                    </div>
                  ) : (
                    <div>
                      <div style={S.chartTitle}>보증금 추이 (최근 6개월)</div>
                      <BarChart idx={3} />
                      <Stats3
                        items={[
                          ["최저", "500만"],
                          ["평균", "2,000만"],
                          ["최고", "5,000만"],
                        ]}
                      />
                    </div>
                  )}
                </div>
              )}
            </>
          )}
          {/* 이슈 분석 탭 */}
          {cxTab === 1 && (
            <div>
              {issuesLoading && (
                <div
                  style={{
                    fontSize: 11,
                    color: COLORS.textTertiary,
                    padding: "8px 0",
                  }}
                >
                  불러오는 중...
                </div>
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
                />
              ))}
              {!issuesLoading &&
                (!issuesData?.items || issuesData.items.length === 0) && (
                  <div
                    style={{
                      fontSize: 12,
                      color: COLORS.textTertiary,
                      textAlign: "center",
                      padding: "24px 0",
                    }}
                  >
                    관련 이슈가 없습니다
                  </div>
                )}
            </div>
          )}
          {/* AI 리포트 탭 */}
          {cxTab === 2 && (
            <AIReport
              report={RC_REPORT}
              status={rcStatus}
              onGenerate={() => generate("rc")}
            />
          )}
        </div>
      </div>
    </div>
  );
};

export default ComplexScreen;

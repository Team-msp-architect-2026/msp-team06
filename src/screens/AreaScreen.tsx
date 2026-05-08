// HomeLens AI - 동 단위 결과 화면 컴포넌트

import React, { useEffect, useRef } from "react";
import AIReport from "../components/AIReport";
import IssueCard from "../components/IssueCard";
import { COLORS } from "../constants/colors";
import { RA_REPORT } from "../constants/mockData";
import { S } from "../constants/styles";
import { useIssues } from "../hooks/useAnalysis";
import { useMapMarkers } from "../hooks/useMap";
import { useAppStore } from "../store/useAppStore";
import { ReportStatus, ReportTarget, Screen } from "../types";

interface AreaScreenProps {
  areaTab: number;
  setAreaTab: (n: number) => void;
  raStatus: ReportStatus;
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
  generate,
  go,
}) => {
  const { selectedRegion } = useAppStore();

  const { data: issuesData, isLoading: issuesLoading } = useIssues(
    selectedRegion?.regionId || "",
    selectedRegion?.name || "",
  );

  const { data: markerData, isLoading: markerLoading } = useMapMarkers(
    selectedRegion?.regionId || "",
    selectedRegion?.lat || 0,
    selectedRegion?.lng || 0,
    "infra",
    2000,
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
          level: 5,
        };
        const map = new kakao.maps.Map(mapRef.current!, options);

        new kakao.maps.Marker({
          position: new kakao.maps.LatLng(
            selectedRegion.lat,
            selectedRegion.lng,
          ),
          map,
        });

        if (markerData?.markers) {
          markerData.markers
            .filter((marker) => marker.markerType === "subway")
            .forEach((marker) => {
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
                const existing = document.getElementById(
                  `area-label-${marker.markerId}`,
                );
                if (existing) {
                  existing.remove();
                  return;
                }
                const label = document.createElement("div");
                label.id = `area-label-${marker.markerId}`;
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

  // 지하철 노선만 추출 (중복 제거)
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
    <div style={S.scr}>
      <div style={S.bar}>
        <span style={S.bk} onClick={() => go("home")}>
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
        {/* 동 단위 가격 정보 카드 (매매/전세/월세/거래량) */}
        <div style={S.scard}>
          <div style={S.sr}>
            <div style={S.si}>
              <div style={S.sl}>매매 평균가</div>
              <div style={S.sv}>8억 2천</div>
              <div style={S.sd}>▲ 전월 +1.2%</div>
            </div>
            <div style={S.sp} />
            <div style={S.si}>
              <div style={S.sl}>전세 평균가</div>
              <div style={S.sv}>5억 1천</div>
            </div>
          </div>
          <div style={S.sdv} />
          <div style={S.sr}>
            <div style={S.si}>
              <div style={S.sl}>월세 평균</div>
              <div style={S.svsm}>보증금 1천/월 85만</div>
            </div>
            <div style={S.sp} />
            <div style={S.si}>
              <div style={S.sl}>이번달 거래량</div>
              <div style={S.sv}>23건</div>
              <div style={S.sd}>▲ 전월 +5건</div>
            </div>
          </div>
          <div style={S.sdv} />
          <div style={S.sl}>지하철 노선</div>
          <div
            style={{ display: "flex", gap: 5, marginTop: 5, flexWrap: "wrap" }}
          >
            {markerLoading ? (
              <span style={{ fontSize: 11, color: COLORS.textTertiary }}>
                불러오는 중...
              </span>
            ) : subwayLines.length > 0 ? (
              subwayLines.map((line, i) => (
                <span key={i} style={S.subwayTag}>
                  {line} 통과
                </span>
              ))
            ) : (
              <span style={{ fontSize: 11, color: COLORS.textTertiary }}>
                반경 내 지하철 없음
              </span>
            )}
          </div>
        </div>

        {/* 카카오맵 SDK */}
        <div ref={mapRef} style={{ ...S.mw, marginTop: 10, height: 180 }} />

        {/* 동 내 단지 목록 */}
        <div style={S.cp}>
          <div style={S.cpt}>아파트 목록</div>
          <div style={S.cps}>거래량 순</div>
          <div
            style={{
              fontSize: 11,
              color: COLORS.textTertiary,
              padding: "8px 0",
            }}
          >
            국토부 API 연동 후 실제 단지 목록 표시 예정
          </div>
        </div>

        {/* 이슈 분석 / AI 리포트 탭 전환 */}
        <div style={S.tabbar}>
          {["이슈 분석", "AI 리포트"].map((t, i) => (
            <div
              key={i}
              style={{ ...S.ti, ...(areaTab === i ? S.tiOn : {}) }}
              onClick={() => setAreaTab(i)}
            >
              {t}
            </div>
          ))}
        </div>
        <div style={S.tc}>
          {/* 이슈 분석 탭 */}
          {areaTab === 0 && (
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
          {areaTab === 1 && (
            <AIReport
              report={RA_REPORT}
              status={raStatus}
              onGenerate={() => generate("ra")}
            />
          )}
        </div>
      </div>
    </div>
  );
};

export default AreaScreen;

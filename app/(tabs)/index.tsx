// 앱 메인 진입점 - 화면 상태 관리 및 화면 전환 처리

import { QueryClientProvider } from "@tanstack/react-query";
import React, { useState } from "react";
import { SafeAreaView } from "react-native-safe-area-context";
import { queryClient } from "../../src/api/queryClient";
import AreaScreen from "../../src/screens/AreaScreen";
import ComplexScreen from "../../src/screens/ComplexScreen";
import HomeScreen from "../../src/screens/HomeScreen";
import ListScreen from "../../src/screens/ListScreen";
import { ReportStatus, ReportTarget, Screen } from "../../src/types";

export default function HomeLensApp(): React.ReactElement {
  // 현재 활성 화면
  const [screen, setScreen] = useState<Screen>("home");
  // 메인 지도 탭 (매매거래량/전세가율/월세부담)
  const [mapTab, setMapTab] = useState<number>(0);
  // 동 단위 화면 탭 (이슈분석/AI리포트)
  const [areaTab, setAreaTab] = useState<number>(0);
  // 단지 화면 탭 (가격분석/이슈분석/AI리포트)
  const [cxTab, setCxTab] = useState<number>(0);
  // 가격 분석 탭 (매매/전세/월세)
  const [priceTab, setPriceTab] = useState<number>(0);
  // 월세 탭 (월세추이/보증금추이)
  const [rentTab, setRentTab] = useState<number>(0);
  // 동 단위 AI 리포트 생성 상태
  const [raStatus, setRaStatus] = useState<ReportStatus>("idle");
  // 단지 단위 AI 리포트 생성 상태
  const [rcStatus, setRcStatus] = useState<ReportStatus>("idle");

  // 화면 전환
  const go = (s: Screen): void => setScreen(s);

  // AI 리포트 생성 요청 (백엔드 POST /reports 연동 예정)
  const generate = (which: ReportTarget): void => {
    if (which === "ra") {
      setRaStatus("loading");
      setTimeout(() => setRaStatus("done"), 2000);
    } else {
      setRcStatus("loading");
      setTimeout(() => setRcStatus("done"), 2000);
    }
  };

  return (
    <QueryClientProvider client={queryClient}>
      <SafeAreaView style={{ flex: 1 }}>
        {screen === "home" && (
          <HomeScreen mapTab={mapTab} setMapTab={setMapTab} go={go} />
        )}
        {screen === "list" && <ListScreen go={go} />}
        {screen === "area" && (
          <AreaScreen
            areaTab={areaTab}
            setAreaTab={setAreaTab}
            raStatus={raStatus}
            generate={generate}
            go={go}
          />
        )}
        {screen === "complex" && (
          <ComplexScreen
            cxTab={cxTab}
            setCxTab={setCxTab}
            priceTab={priceTab}
            setPriceTab={setPriceTab}
            rentTab={rentTab}
            setRentTab={setRentTab}
            rcStatus={rcStatus}
            generate={generate}
            go={go}
          />
        )}
      </SafeAreaView>
    </QueryClientProvider>
  );
}

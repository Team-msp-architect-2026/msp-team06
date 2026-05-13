// 앱 메인 진입점 - 화면 상태 관리 및 화면 전환 처리

import { QueryClientProvider } from "@tanstack/react-query";
import React, { useState } from "react";
import { SafeAreaView } from "react-native-safe-area-context";
import { queryClient } from "../../src/api/queryClient";
import AreaScreen from "../../src/screens/AreaScreen";
import ComplexScreen from "../../src/screens/ComplexScreen";
import HomeScreen from "../../src/screens/HomeScreen";
import ListScreen from "../../src/screens/ListScreen";
import { useAppStore } from "../../src/store/useAppStore";
import { ReportStatus, ReportTarget, Screen } from "../../src/types";

export default function HomeLensApp(): React.ReactElement {
  const { setPrevScreen } = useAppStore();

  const [screen, setScreen] = useState<Screen>("home");
  const [mapTab, setMapTab] = useState<number>(0);
  const [areaTab, setAreaTab] = useState<number>(0);
  const [cxTab, setCxTab] = useState<number>(0);
  const [priceTab, setPriceTab] = useState<number>(0);
  const [rentTab, setRentTab] = useState<number>(0);
  const [raStatus, setRaStatus] = useState<ReportStatus>("idle");
  const [rcStatus, setRcStatus] = useState<ReportStatus>("idle");

  // 화면 전환 - 이전 화면 저장
  const go = (s: Screen): void => {
    setPrevScreen(screen);
    setScreen(s);
  };

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

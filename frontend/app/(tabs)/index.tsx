// 앱 메인 진입점 - 화면 상태 관리 및 화면 전환 처리
import { QueryClientProvider } from "@tanstack/react-query";
import React, { useState } from "react";
import { SafeAreaView } from "react-native-safe-area-context";
import { queryClient } from "../../src/api/queryClient";
import AreaScreen from "../../src/screens/AreaScreen";
import ComplexScreen from "../../src/screens/ComplexScreen";
import HomeScreen from "../../src/screens/HomeScreen";
import ListScreen from "../../src/screens/ListScreen";
import { useCreateReport, useReportStatus } from "../../src/hooks/useReport";
import { useAppStore } from "../../src/store/useAppStore";
import { ReportStatus, ReportTarget, Screen } from "../../src/types";

function AppContent(): React.ReactElement {
  const { setPrevScreen, selectedRegion } = useAppStore();
  const createReportMutation = useCreateReport();

  const [screen, setScreen] = useState<Screen>("home");
  const [mapTab, setMapTab] = useState<number>(0);
  const [areaTab, setAreaTab] = useState<number>(0);
  const [cxTab, setCxTab] = useState<number>(0);
  const [priceTab, setPriceTab] = useState<number>(0);
  const [rentTab, setRentTab] = useState<number>(0);
  const [raStatus, setRaStatus] = useState<ReportStatus>("idle");
  const [rcStatus, setRcStatus] = useState<ReportStatus>("idle");
  const [raReportId, setRaReportId] = useState<string | null>(null);
  const [rcReportId, setRcReportId] = useState<string | null>(null);

  const { data: raStatusData } = useReportStatus(raReportId);
  const { data: rcStatusData } = useReportStatus(rcReportId);

  /* AI 리포트 상태 동기화 */
  React.useEffect(() => {
    if (raStatusData?.status === "completed") setRaStatus("done");
    if (raStatusData?.status === "failed") setRaStatus("idle");
  }, [raStatusData]);

  React.useEffect(() => {
    if (rcStatusData?.status === "completed") setRcStatus("done");
    if (rcStatusData?.status === "failed") setRcStatus("idle");
  }, [rcStatusData]);

  /* 화면 전환 */
  const go = (s: Screen): void => {
  setPrevScreen(screen);
  setScreen(s);
  // 다른 화면으로 이동 시 리포트 초기화
  if (s === "complex") {
    setRcReportId(null);
    setRcStatus("idle");
    setCxTab(0);
    setPriceTab(0);
    setRentTab(0);
  }
  if (s === "area") {
    setRaReportId(null);
    setRaStatus("idle");
    setAreaTab(0);
  }
};

  /* AI 리포트 생성 요청 */
  const generate = async (which: ReportTarget): Promise<void> => {
    if (!selectedRegion) return;
    if (which === "ra") {
      setRaStatus("loading");
      try {
        const res = await createReportMutation.mutateAsync({
          regionId: selectedRegion.regionId,
          regionName: selectedRegion.name,
          lat: selectedRegion.lat,
          lng: selectedRegion.lng,
        });
        setRaReportId(res.reportId);
      } catch {
        setRaStatus("idle");
      }
    } else {
      setRcStatus("loading");
      try {
        const res = await createReportMutation.mutateAsync({
          regionId: selectedRegion.regionId,
          regionName: selectedRegion.name,
          lat: selectedRegion.lat,
          lng: selectedRegion.lng,
        });
        setRcReportId(res.reportId);
      } catch {
        setRcStatus("idle");
      }
    }
  };

  return (
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
          raReportId={raReportId}
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
          rcReportId={rcReportId}
          generate={generate}
          go={go}
        />
      )}
    </SafeAreaView>
  );
}

export default function HomeLensApp(): React.ReactElement {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
    </QueryClientProvider>
  );
}
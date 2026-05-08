// HomeLens AI - 앱 메인 진입점 및 화면 상태 관리

import { QueryClientProvider } from '@tanstack/react-query';
import React, { useState } from 'react';
import { queryClient } from '../../src/api/queryClient';
import { S } from '../../src/constants/styles';
import AreaScreen from '../../src/screens/AreaScreen';
import ComplexScreen from '../../src/screens/ComplexScreen';
import HomeScreen from '../../src/screens/HomeScreen';
import ListScreen from '../../src/screens/ListScreen';
import { ReportStatus, ReportTarget, Screen } from '../../src/types';

export default function HomeLensApp(): React.ReactElement {
  // 현재 활성화된 화면 상태
  const [screen, setScreen] = useState<Screen>('home');

  // 지도 탭 상태 (0: 매매 거래량 / 1: 전세가율 / 2: 월세 부담)
  const [mapTab, setMapTab] = useState<number>(0);

  // 동 단위 결과화면 탭 상태 (0: 이슈 분석 / 1: AI 리포트)
  const [areaTab, setAreaTab] = useState<number>(0);

  // 단지 결과화면 탭 상태 (0: 가격 분석 / 1: 이슈 분석 / 2: AI 리포트)
  const [cxTab, setCxTab] = useState<number>(0);

  // 가격 분석 탭 상태 (0: 매매 / 1: 전세 / 2: 월세)
  const [priceTab, setPriceTab] = useState<number>(0);

  // 월세 탭 상태 (0: 월세 추이 / 1: 보증금 추이)
  const [rentTab, setRentTab] = useState<number>(0);

  // 동 단위 AI 리포트 상태 (idle/loading/done)
  const [raStatus, setRaStatus] = useState<ReportStatus>('idle');

  // 단지 단위 AI 리포트 상태 (idle/loading/done)
  const [rcStatus, setRcStatus] = useState<ReportStatus>('idle');

  // 화면 이동 함수
  const go = (s: Screen): void => setScreen(s);

  // AI 리포트 생성 함수 (ra: 동 단위 / rc: 단지 단위)
  // 실제 연동 시 백엔드 POST /reports 호출로 교체
  const generate = (which: ReportTarget): void => {
    if (which === 'ra') {
      setRaStatus('loading');
      setTimeout(() => setRaStatus('done'), 2000);
    } else {
      setRcStatus('loading');
      setTimeout(() => setRcStatus('done'), 2000);
    }
  };

  return (
    <QueryClientProvider client={queryClient}>
      <div style={S.wrap}>
        {/* 개발용 화면 전환 네비게이션 버튼 (실제 앱에서는 제거) */}
        <div style={S.nav}>
          {[
            { id: 'home' as Screen, label: '메인' },
            { id: 'list' as Screen, label: '검색 목록' },
            { id: 'area' as Screen, label: '결과 (동 단위)' },
            { id: 'complex' as Screen, label: '결과 (단지)' },
          ].map((b) => (
            <button
              key={b.id}
              style={{ ...S.nb, ...(screen === b.id ? S.nbOn : {}) }}
              onClick={() => go(b.id)}
            >
              {b.label}
            </button>
          ))}
        </div>
        <div style={S.phone}>
          {screen === 'home' && (
            <HomeScreen
              mapTab={mapTab}
              setMapTab={setMapTab}
              go={go}
            />
          )}
          {screen === 'list' && <ListScreen go={go} />}
          {screen === 'area' && (
            <AreaScreen
              areaTab={areaTab}
              setAreaTab={setAreaTab}
              raStatus={raStatus}
              generate={generate}
              go={go}
            />
          )}
          {screen === 'complex' && (
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
        </div>
      </div>
    </QueryClientProvider>
  );
}
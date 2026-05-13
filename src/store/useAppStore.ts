// HomeLens AI - Zustand 전역 상태 관리
// 검색 결과, 선택된 지역 등 앱 전체에서 공유하는 상태 관리

import { create } from "zustand";
import { Screen } from "../types";

interface SelectedRegion {
  regionId: string;
  name: string;
  fullAddress: string;
  lat: number;
  lng: number;
  lawdCd?: string;
}

interface AppState {
  // 현재 선택된 지역/단지 정보
  selectedRegion: SelectedRegion | null;
  setSelectedRegion: (region: SelectedRegion | null) => void;

  // 검색어 (입력창)
  searchVal: string;
  setSearchVal: (val: string) => void;

  // 검색 결과 화면용 검색어 (ListScreen에서 사용)
  listSearchVal: string;
  setListSearchVal: (val: string) => void;

  // 최근 검색어 목록 (최대 5개)
  recentSearches: string[];
  addRecentSearch: (val: string) => void;

  // 이전 화면 (뒤로가기 처리용)
  prevScreen: Screen;
  setPrevScreen: (screen: Screen) => void;
}

export const useAppStore = create<AppState>((set) => ({
  selectedRegion: null,
  setSelectedRegion: (region) => set({ selectedRegion: region }),

  searchVal: "",
  setSearchVal: (val) => set({ searchVal: val }),

  listSearchVal: "",
  setListSearchVal: (val) => set({ listSearchVal: val }),

  recentSearches: [],
  addRecentSearch: (val) =>
    set((state) => ({
      recentSearches: [
        val,
        ...state.recentSearches.filter((s) => s !== val),
      ].slice(0, 5),
    })),

  prevScreen: "home",
  setPrevScreen: (screen) => set({ prevScreen: screen }),
}));

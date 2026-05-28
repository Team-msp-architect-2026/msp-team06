// HomeLens AI - Zustand 전역 상태 관리
import { create } from "zustand";
import { Screen } from "../types";

interface SelectedRegion {
  regionId: string;
  name: string;
  fullAddress: string;
  lat: number;
  lng: number;
  lawdCd?: string;
  aptSeq?: string;  
}

interface AppState {
  selectedRegion: SelectedRegion | null;
  setSelectedRegion: (region: SelectedRegion | null) => void;

  searchVal: string;
  setSearchVal: (val: string) => void;

  listSearchVal: string;
  setListSearchVal: (val: string) => void;

  recentSearches: string[];
  addRecentSearch: (val: string) => void;

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
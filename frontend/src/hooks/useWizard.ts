"use client";

import { useState, useCallback } from "react";
import type { GameAnalysis, GeneratedAssetSet, PlayableResult, MechanicType } from "@/lib/types";

export type WizardStep = 1 | 2 | 3 | 4;

export interface WizardState {
  step: WizardStep;
  screenshots: File[];
  gameName: string;
  analysis: GameAnalysis | null;
  selectedMechanic: MechanicType | null;
  styleId: string | null;
  assets: GeneratedAssetSet | null;
  result: PlayableResult | null;
  isDemo: boolean;
}

const initialState: WizardState = {
  step: 1,
  screenshots: [],
  gameName: "",
  analysis: null,
  selectedMechanic: null,
  styleId: null,
  assets: null,
  result: null,
  isDemo: false,
};

export function useWizard() {
  const [state, setState] = useState<WizardState>(initialState);

  const setStep = useCallback((step: WizardStep) => {
    setState((s) => ({ ...s, step }));
  }, []);

  const setScreenshots = useCallback((screenshots: File[]) => {
    setState((s) => ({ ...s, screenshots }));
  }, []);

  const setGameName = useCallback((gameName: string) => {
    setState((s) => ({ ...s, gameName }));
  }, []);

  const setAnalysis = useCallback((analysis: GameAnalysis) => {
    setState((s) => ({
      ...s,
      analysis,
      selectedMechanic: analysis.mechanic_type,
      step: 2 as WizardStep,
    }));
  }, []);

  const setSelectedMechanic = useCallback((mechanic: MechanicType) => {
    setState((s) => ({ ...s, selectedMechanic: mechanic }));
  }, []);

  const setStyleId = useCallback((styleId: string) => {
    setState((s) => ({ ...s, styleId }));
  }, []);

  const setAssets = useCallback((assets: GeneratedAssetSet) => {
    setState((s) => ({ ...s, assets, step: 4 as WizardStep }));
  }, []);

  const setResult = useCallback((result: PlayableResult) => {
    setState((s) => ({ ...s, result }));
  }, []);

  const setDemoResult = useCallback((result: PlayableResult) => {
    setState((s) => ({
      ...s,
      result,
      isDemo: true,
      step: 4 as WizardStep,
    }));
  }, []);

  const reset = useCallback(() => {
    setState(initialState);
  }, []);

  return {
    state,
    setStep,
    setScreenshots,
    setGameName,
    setAnalysis,
    setSelectedMechanic,
    setStyleId,
    setAssets,
    setResult,
    setDemoResult,
    reset,
  };
}

"use client";

import { useEffect, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { AppSidebar } from "@/components/sidebar/AppSidebar";
import { StepUpload } from "./StepUpload";
import { StepAnalysis } from "./StepAnalysis";
import { StepGenerate } from "./StepGenerate";
import { StepExport } from "./StepExport";
import { useWizard } from "@/hooks/useWizard";
import { fetchHealth, fetchWorkspace, fetchTemplates } from "@/lib/api";
import type { HealthResponse, WorkspaceResponse } from "@/lib/types";

const STEP_TITLES = {
  1: "Input Your Game",
  2: "Review Analysis",
  3: "Generate Assets",
  4: "Export Playable Ad",
};

const stepVariants = {
  enter: { opacity: 0, x: 30 },
  center: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: -30 },
};

export function WizardShell() {
  const {
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
  } = useWizard();

  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [workspace, setWorkspace] = useState<WorkspaceResponse | null>(null);
  const [mechanics, setMechanics] = useState<string[]>([]);

  // Load initial data
  useEffect(() => {
    fetchHealth().then(setHealth).catch(() => {});
    fetchWorkspace().then(setWorkspace).catch(() => {});
    fetchTemplates()
      .then((data) => setMechanics(data.templates.map((t) => t.name)))
      .catch(() => {});
  }, []);

  const handleDemoResult = useCallback(
    (result: Parameters<typeof setDemoResult>[0]) => setDemoResult(result),
    [setDemoResult]
  );

  return (
    <div className="flex min-h-screen">
      <AppSidebar
        currentStep={state.step}
        health={health}
        workspace={workspace}
        supportedMechanics={mechanics}
        onDemoResult={handleDemoResult}
      />

      <main className="flex-1 min-w-0 overflow-y-auto">
        <div className="max-w-4xl mx-auto px-6 py-8">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-extrabold bg-gradient-to-r from-[var(--color-purple)] to-[var(--color-pink)] bg-clip-text text-transparent">
              Playable Ad Generator
            </h1>
            <p className="text-sm text-[var(--color-text-muted)] mt-1">
              Create game-specific playable ads using AI
            </p>
          </div>

          {/* Step header */}
          <div className="flex items-center gap-3 border-b border-white/5 pb-5 mb-6">
            <div className="flex gap-1.5">
              {[1, 2, 3, 4].map((s) => (
                <div
                  key={s}
                  className={`w-2.5 h-2.5 rounded-full transition-colors ${
                    s === state.step
                      ? "bg-[var(--color-purple)]"
                      : s < state.step
                      ? "bg-[var(--color-purple)]/40"
                      : "bg-white/10"
                  }`}
                />
              ))}
            </div>
            <span className="text-base font-semibold text-[var(--color-text-light)]">
              Step {state.step}: {STEP_TITLES[state.step]}
            </span>
          </div>

          {/* Step content */}
          <AnimatePresence mode="wait">
            <motion.div
              key={state.step}
              variants={stepVariants}
              initial="enter"
              animate="center"
              exit="exit"
              transition={{ duration: 0.25, ease: "easeInOut" }}
            >
              {state.step === 1 && (
                <StepUpload
                  screenshots={state.screenshots}
                  gameName={state.gameName}
                  onScreenshotsChange={setScreenshots}
                  onGameNameChange={setGameName}
                  onAnalysisComplete={setAnalysis}
                />
              )}
              {state.step === 2 && state.analysis && (
                <StepAnalysis
                  analysis={state.analysis}
                  selectedMechanic={state.selectedMechanic ?? state.analysis.mechanic_type}
                  onMechanicChange={setSelectedMechanic}
                  onBack={() => setStep(1)}
                  onContinue={() => setStep(3)}
                />
              )}
              {state.step === 3 && state.analysis && (
                <StepGenerate
                  analysis={state.analysis}
                  styleId={state.styleId}
                  onStyleChange={setStyleId}
                  onAssetsGenerated={setAssets}
                  onBack={() => setStep(2)}
                />
              )}
              {state.step === 4 && (
                <StepExport
                  analysis={state.analysis}
                  assets={state.assets}
                  result={state.result}
                  isDemo={state.isDemo}
                  onResult={setResult}
                  onBack={() => setStep(3)}
                  onReset={reset}
                />
              )}
            </motion.div>
          </AnimatePresence>
        </div>
      </main>
    </div>
  );
}

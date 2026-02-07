"use client";

import { ArrowLeft, ArrowRight, Sparkles, RefreshCw, Palette, Layers } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ContentCard } from "@/components/cards/ContentCard";
import { StatusBadge } from "@/components/StatusBadge";
import { ColorPalette } from "@/components/ColorPalette";
import type { GameAnalysis, MechanicType } from "@/lib/types";

interface StepAnalysisProps {
  analysis: GameAnalysis;
  selectedMechanic: MechanicType;
  onMechanicChange: (m: MechanicType) => void;
  onBack: () => void;
  onContinue: () => void;
}

const MECHANIC_LABELS: Record<string, string> = {
  match3: "Match-3 Puzzle",
  runner: "Endless Runner",
  tapper: "Tapper / Idle Clicker",
  merger: "Merger",
  puzzle: "Puzzle",
  shooter: "Shooter",
  unknown: "Unknown",
};

export function StepAnalysis({
  analysis,
  selectedMechanic,
  onMechanicChange,
  onBack,
  onContinue,
}: StepAnalysisProps) {
  const confidenceVariant =
    analysis.confidence_level === "high"
      ? "success"
      : analysis.confidence_level === "medium"
      ? "warning"
      : "error";

  return (
    <div className="space-y-5">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Left column: Game identity + Core loop */}
        <div className="lg:col-span-2 space-y-5">
          <ContentCard title="Game Identity" icon={<Sparkles className="w-4 h-4" />}>
            <div className="text-lg font-bold text-[var(--color-text-dark)]">
              {analysis.game_name}
            </div>
            {analysis.publisher && (
              <div className="text-xs text-[var(--color-text-muted)] mt-0.5">
                by {analysis.publisher}
              </div>
            )}
            <div className="flex items-center gap-2 mt-3">
              <StatusBadge
                label={`${selectedMechanic.toUpperCase()} — ${Math.round(analysis.mechanic_confidence * 100)}%`}
                variant={confidenceVariant}
              />
            </div>
            <div className="text-sm text-[var(--color-text-body)] mt-3">
              <span className="font-semibold">Why:</span> {analysis.mechanic_reasoning}
            </div>
          </ContentCard>

          <ContentCard title="Core Game Loop" icon={<RefreshCw className="w-4 h-4" />}>
            <p>{analysis.core_loop_description}</p>
          </ContentCard>
        </div>

        {/* Right column: Visual style */}
        <div>
          <ContentCard title="Visual Style" icon={<Palette className="w-4 h-4" />}>
            <div className="space-y-2 text-sm">
              <div><span className="font-semibold">Art:</span> {analysis.visual_style.art_type}</div>
              <div><span className="font-semibold">Theme:</span> {analysis.visual_style.theme}</div>
              <div><span className="font-semibold">Mood:</span> {analysis.visual_style.mood}</div>
            </div>
            <div className="mt-4">
              <div className="text-[10px] font-semibold text-[var(--color-text-muted)] uppercase tracking-wide mb-2">
                Color Palette
              </div>
              <ColorPalette colors={analysis.visual_style.color_palette.slice(0, 6)} />
            </div>
          </ContentCard>
        </div>
      </div>

      {/* Mechanic selector */}
      <ContentCard title="Confirm Game Type" icon={<Layers className="w-4 h-4" />}>
        <select
          value={selectedMechanic}
          onChange={(e) => onMechanicChange(e.target.value as MechanicType)}
          className="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-[var(--color-text-dark)] focus:outline-none focus:ring-2 focus:ring-[var(--color-purple)]"
        >
          {Object.entries(MECHANIC_LABELS).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
      </ContentCard>

      {/* Assets needed */}
      {analysis.assets_needed.length > 0 && (
        <ContentCard title="Assets to Generate" accent="var(--color-purple)">
          <div className="space-y-1.5">
            {analysis.assets_needed.map((asset) => (
              <div
                key={asset.key}
                className="flex items-center gap-3 py-1.5 px-3 rounded-md bg-gray-50 border-l-2 border-[var(--color-purple)]"
              >
                <span className="text-xs font-semibold text-[var(--color-text-dark)]">
                  {asset.key}
                </span>
                <span className="text-xs text-[var(--color-text-muted)]">
                  {asset.description}
                </span>
              </div>
            ))}
          </div>
        </ContentCard>
      )}

      {/* Navigation */}
      <div className="flex gap-3">
        <Button variant="outline" onClick={onBack} className="border-white/10 text-[var(--color-text-light)] hover:bg-white/5">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back
        </Button>
        <Button onClick={onContinue} className="flex-1 bg-[var(--color-purple)] hover:bg-[var(--color-purple-light)] text-white">
          Continue to Asset Generation
          <ArrowRight className="w-4 h-4 ml-2" />
        </Button>
      </div>
    </div>
  );
}

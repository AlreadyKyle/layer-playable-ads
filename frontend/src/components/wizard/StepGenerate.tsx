"use client";

import { useState, useCallback, useEffect } from "react";
import { ArrowLeft, Loader2, Paintbrush, Image as ImageIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ContentCard } from "@/components/cards/ContentCard";
import { fetchStyles, generateAssets } from "@/lib/api";
import { Progress } from "@/components/ui/progress";
import type { GameAnalysis, GeneratedAssetSet, Style } from "@/lib/types";

interface StepGenerateProps {
  analysis: GameAnalysis;
  styleId: string | null;
  onStyleChange: (id: string) => void;
  onAssetsGenerated: (assets: GeneratedAssetSet) => void;
  onBack: () => void;
}

export function StepGenerate({
  analysis,
  styleId,
  onStyleChange,
  onAssetsGenerated,
  onBack,
}: StepGenerateProps) {
  const [styles, setStyles] = useState<Style[]>([]);
  const [stylesError, setStylesError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchStyles()
      .then((data) => {
        if (data.error) setStylesError(data.error);
        const complete = (data.styles ?? []).filter((s) => s.status === "COMPLETE");
        setStyles(complete);
        if (complete.length > 0 && !styleId) {
          onStyleChange(complete[0].id);
        }
      })
      .catch((e) => setStylesError(e.message));
  }, [styleId, onStyleChange]);

  const handleGenerate = useCallback(async () => {
    if (!styleId) return;
    setLoading(true);
    setError(null);
    setProgress(10);

    const timer = setInterval(() => {
      setProgress((p) => Math.min(p + 5, 90));
    }, 2000);

    try {
      const assets = await generateAssets(analysis, styleId);
      setProgress(100);
      onAssetsGenerated(assets);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Generation failed");
    } finally {
      clearInterval(timer);
      setLoading(false);
    }
  }, [analysis, styleId, onAssetsGenerated]);

  return (
    <div className="space-y-5">
      <ContentCard title="Layer.ai Style" icon={<Paintbrush className="w-4 h-4" />}>
        <p className="text-xs text-[var(--color-text-muted)] mb-3">
          Choose a trained style from your workspace to generate assets.
        </p>
        {stylesError ? (
          <div className="text-sm text-red-500 mb-2">Could not fetch styles: {stylesError}</div>
        ) : styles.length === 0 ? (
          <div className="text-sm text-amber-600">
            No completed styles found. Please create one at app.layer.ai
          </div>
        ) : (
          <select
            value={styleId ?? ""}
            onChange={(e) => onStyleChange(e.target.value)}
            className="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-[var(--color-text-dark)] focus:outline-none focus:ring-2 focus:ring-[var(--color-purple)]"
          >
            {styles.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        )}
      </ContentCard>

      <ContentCard title="Assets to Generate" icon={<ImageIcon className="w-4 h-4" />}>
        <div className="space-y-1.5">
          {analysis.assets_needed.map((a) => (
            <div
              key={a.key}
              className="flex items-center gap-3 py-1.5 px-3 rounded-md bg-gray-50 border-l-2 border-[var(--color-purple)]"
            >
              <span className="text-xs font-semibold text-[var(--color-text-dark)]">{a.key}</span>
              <span className="text-xs text-[var(--color-text-muted)]">{a.description}</span>
            </div>
          ))}
        </div>
      </ContentCard>

      {loading && (
        <div className="space-y-2">
          <Progress value={progress} className="h-2" />
          <p className="text-xs text-center text-[var(--color-text-muted)]">
            Generating assets with Layer.ai...
          </p>
        </div>
      )}

      {error && (
        <div className="rounded-lg bg-red-500/10 border border-red-500/20 p-3 text-sm text-red-400">
          {error}
        </div>
      )}

      <div className="flex gap-3">
        <Button variant="outline" onClick={onBack} className="border-white/10 text-[var(--color-text-light)] hover:bg-white/5">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back
        </Button>
        <Button
          onClick={handleGenerate}
          disabled={!styleId || loading}
          className="flex-1 bg-[var(--color-purple)] hover:bg-[var(--color-purple-light)] text-white"
        >
          {loading ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Generating...
            </>
          ) : (
            "Generate Assets"
          )}
        </Button>
      </div>
    </div>
  );
}

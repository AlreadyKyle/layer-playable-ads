"use client";

import { useState, useCallback } from "react";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  Loader2,
  Download,
  FileArchive,
  Eye,
  RotateCcw,
  HardDrive,
  Layers,
  Wrench,
  ShieldCheck,
  Gamepad2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ContentCard } from "@/components/cards/ContentCard";
import { MetricCard } from "@/components/cards/MetricCard";
import { AssetPreview } from "@/components/cards/AssetPreview";
import { NetworkBadges } from "@/components/NetworkBadges";
import { PhonePreview } from "@/components/PhonePreview";
import { buildPlayable } from "@/lib/api";
import type {
  GameAnalysis,
  GeneratedAssetSet,
  PlayableResult,
  PlayableConfig,
} from "@/lib/types";

interface StepExportProps {
  analysis: GameAnalysis | null;
  assets: GeneratedAssetSet | null;
  result: PlayableResult | null;
  isDemo: boolean;
  onResult: (result: PlayableResult) => void;
  onBack: () => void;
  onReset: () => void;
}

export function StepExport({
  analysis,
  assets,
  result,
  isDemo,
  onResult,
  onBack,
  onReset,
}: StepExportProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showPreview, setShowPreview] = useState(false);

  // Form state
  const [config, setConfig] = useState<PlayableConfig>({
    game_name: analysis?.game_name ?? "My Game",
    title: analysis?.game_name ?? "Playable Ad",
    store_url: "https://apps.apple.com/app/id123456789",
    store_url_ios: "https://apps.apple.com/app/id123456789",
    store_url_android:
      "https://play.google.com/store/apps/details?id=com.example.game",
    width: 320,
    height: 480,
    background_color: "#1a1a2e",
    hook_text: analysis?.hook_suggestion ?? "Tap to Play!",
    cta_text: analysis?.cta_suggestion ?? "Download FREE",
    sound_enabled: true,
  });

  const updateConfig = useCallback(
    (partial: Partial<PlayableConfig>) =>
      setConfig((c) => ({ ...c, ...partial })),
    []
  );

  const handleBuild = useCallback(async () => {
    if (!analysis || !assets) return;
    setLoading(true);
    setError(null);
    try {
      const res = await buildPlayable(analysis, assets, config);
      onResult(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Build failed");
    } finally {
      setLoading(false);
    }
  }, [analysis, assets, config, onResult]);

  const downloadHtml = useCallback(() => {
    if (!result) return;
    const blob = new Blob([result.html], { type: "text/html" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "index.html";
    a.click();
    URL.revokeObjectURL(url);
  }, [result]);

  const downloadZip = useCallback(async () => {
    if (!result) return;
    const { default: JSZip } = await import("jszip");
    const zip = new JSZip();
    zip.file("index.html", result.html);
    const blob = await zip.generateAsync({ type: "blob" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "playable_ad.zip";
    a.click();
    URL.revokeObjectURL(url);
  }, [result]);

  return (
    <div className="space-y-5">
      {/* Asset previews (skip for demo) */}
      {!isDemo && assets && (
        <ContentCard title={`Generated Assets`} icon={<Layers className="w-4 h-4" />}>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3 mt-2">
            {Object.entries(assets.assets).map(([key, asset]) => (
              <AssetPreview key={key} assetKey={key} asset={asset} />
            ))}
          </div>
        </ContentCard>
      )}

      {isDemo && (
        <ContentCard
          title="Demo Mode"
          icon={<Gamepad2 className="w-4 h-4" />}
          accent="var(--color-purple)"
        >
          <p className="text-xs text-[var(--color-text-muted)]">
            Using fallback graphics (colored shapes)
          </p>
        </ContentCard>
      )}

      {/* Config form (skip for demo) */}
      {!isDemo && !result && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <ContentCard title="Game Info" icon={<Gamepad2 className="w-4 h-4" />}>
              <div className="space-y-3">
                <Field label="Game Name" value={config.game_name} onChange={(v) => updateConfig({ game_name: v, title: v })} />
                <Field label="Hook Text" value={config.hook_text} onChange={(v) => updateConfig({ hook_text: v })} />
                <Field label="CTA Text" value={config.cta_text} onChange={(v) => updateConfig({ cta_text: v })} />
              </div>
            </ContentCard>
            <ContentCard title="Technical" icon={<Wrench className="w-4 h-4" />}>
              <div className="space-y-3">
                <Field label="App Store URL (iOS)" value={config.store_url_ios} onChange={(v) => updateConfig({ store_url_ios: v, store_url: v })} />
                <Field label="Play Store URL (Android)" value={config.store_url_android} onChange={(v) => updateConfig({ store_url_android: v })} />
                <div>
                  <label className="text-xs font-medium text-[var(--color-text-muted)] mb-1 block">Background Color</label>
                  <input
                    type="color"
                    value={config.background_color}
                    onChange={(e) => updateConfig({ background_color: e.target.value })}
                    className="h-9 w-full rounded-md cursor-pointer"
                  />
                </div>
              </div>
            </ContentCard>
          </div>

          {/* Size preset */}
          <ContentCard>
            <div className="flex gap-3">
              {[
                { label: "Portrait (320x480)", w: 320, h: 480 },
                { label: "Square (320x320)", w: 320, h: 320 },
                { label: "Landscape (480x320)", w: 480, h: 320 },
              ].map((preset) => (
                <button
                  key={preset.label}
                  onClick={() => updateConfig({ width: preset.w, height: preset.h })}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                    config.width === preset.w && config.height === preset.h
                      ? "bg-[var(--color-purple)] text-white"
                      : "bg-gray-100 text-[var(--color-text-body)] hover:bg-gray-200"
                  }`}
                >
                  {preset.label}
                </button>
              ))}
            </div>
          </ContentCard>

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
              onClick={handleBuild}
              disabled={loading}
              className="flex-1 bg-[var(--color-purple)] hover:bg-[var(--color-purple-light)] text-white"
            >
              {loading ? (
                <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Building...</>
              ) : (
                "Build Playable"
              )}
            </Button>
          </div>
        </>
      )}

      {/* Result display */}
      {result && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-5"
        >
          {/* Success banner */}
          <div className="rounded-xl bg-emerald-500/10 border border-emerald-500/20 p-4 text-center">
            <div className="text-sm font-semibold text-emerald-400">
              Playable Ready
            </div>
            <div className="text-xs text-emerald-300/70 mt-0.5">
              Your ad is built and ready for download.
            </div>
          </div>

          {/* Metrics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <MetricCard
              label="File Size"
              value={result.file_size_formatted}
              icon={<HardDrive className="w-4 h-4" />}
              status={result.file_size_mb <= 5 ? "success" : "error"}
            />
            <MetricCard
              label="Assets"
              value={String(result.assets_embedded)}
              icon={<Layers className="w-4 h-4" />}
            />
            <MetricCard
              label="Mechanic"
              value={result.mechanic_type}
              icon={<Gamepad2 className="w-4 h-4" />}
            />
            <MetricCard
              label="Status"
              value={result.is_valid ? "Valid" : "Issues"}
              icon={<ShieldCheck className="w-4 h-4" />}
              status={result.is_valid ? "success" : "warning"}
            />
          </div>

          {result.validation_errors.length > 0 && (
            <div className="space-y-1">
              {result.validation_errors.map((err, i) => (
                <div key={i} className="rounded-lg bg-amber-500/10 border border-amber-500/20 p-2 text-xs text-amber-400">
                  {err}
                </div>
              ))}
            </div>
          )}

          {/* Network compatibility */}
          <ContentCard title="Network Compatibility">
            <NetworkBadges fileSizeMb={result.file_size_mb} />
          </ContentCard>

          {/* Downloads */}
          <ContentCard title="Download" accent="var(--color-success)">
            <p className="text-xs text-[var(--color-text-muted)] mb-3">
              Single self-contained HTML file &middot; MRAID 3.0 compliant
            </p>
            <div className="flex gap-3">
              <Button onClick={downloadHtml} className="flex-1 bg-[var(--color-purple)] hover:bg-[var(--color-purple-light)] text-white">
                <Download className="w-4 h-4 mr-2" />
                Download index.html
              </Button>
              <Button onClick={downloadZip} variant="outline" className="flex-1 border-white/10 text-[var(--color-text-light)] hover:bg-white/5">
                <FileArchive className="w-4 h-4 mr-2" />
                Download ZIP
              </Button>
            </div>
          </ContentCard>

          {/* Preview toggle */}
          <Button variant="outline" onClick={() => setShowPreview(!showPreview)} className="w-full border-white/10 text-[var(--color-text-light)] hover:bg-white/5">
            <Eye className="w-4 h-4 mr-2" />
            {showPreview ? "Hide Preview" : "Show Preview"}
          </Button>

          {showPreview && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              className="flex justify-center"
            >
              <PhonePreview html={result.html} />
            </motion.div>
          )}

          {/* Reset */}
          <Button variant="outline" onClick={onReset} className="w-full border-white/10 text-[var(--color-text-light)] hover:bg-white/5">
            <RotateCcw className="w-4 h-4 mr-2" />
            Create Another Playable
          </Button>
        </motion.div>
      )}
    </div>
  );
}

function Field({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <div>
      <label className="text-xs font-medium text-[var(--color-text-muted)] mb-1 block">
        {label}
      </label>
      <Input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="bg-gray-50 border-gray-200 text-[var(--color-text-dark)] text-sm"
      />
    </div>
  );
}

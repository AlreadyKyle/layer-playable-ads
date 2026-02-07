"use client";

import { useCallback, useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Upload, X, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { analyzeScreenshots } from "@/lib/api";
import type { GameAnalysis } from "@/lib/types";

interface StepUploadProps {
  screenshots: File[];
  gameName: string;
  onScreenshotsChange: (files: File[]) => void;
  onGameNameChange: (name: string) => void;
  onAnalysisComplete: (analysis: GameAnalysis) => void;
}

export function StepUpload({
  screenshots,
  gameName,
  onScreenshotsChange,
  onGameNameChange,
  onAnalysisComplete,
}: StepUploadProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const addFiles = useCallback(
    (files: FileList | File[]) => {
      const arr = Array.from(files).filter((f) =>
        ["image/png", "image/jpeg", "image/jpg"].includes(f.type)
      );
      const combined = [...screenshots, ...arr].slice(0, 5);
      onScreenshotsChange(combined);
    },
    [screenshots, onScreenshotsChange]
  );

  const removeFile = useCallback(
    (index: number) => {
      onScreenshotsChange(screenshots.filter((_, i) => i !== index));
    },
    [screenshots, onScreenshotsChange]
  );

  const handleAnalyze = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const analysis = await analyzeScreenshots(screenshots, gameName || undefined);
      onAnalysisComplete(analysis);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Analysis failed");
    } finally {
      setLoading(false);
    }
  }, [screenshots, gameName, onAnalysisComplete]);

  return (
    <div className="space-y-5">
      {/* Hero drop zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => { e.preventDefault(); setDragOver(false); addFiles(e.dataTransfer.files); }}
        onClick={() => inputRef.current?.click()}
        className={`rounded-xl border-2 border-dashed min-h-[240px] flex flex-col items-center justify-center text-center cursor-pointer transition-all duration-200 ${
          dragOver
            ? "border-[var(--color-purple)] bg-[var(--color-purple)]/5 ring-2 ring-[var(--color-purple)]/30"
            : "border-white/10 hover:border-[var(--color-purple)]/40 bg-white/[0.02] hover:bg-white/[0.03]"
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          accept="image/png,image/jpeg"
          multiple
          className="hidden"
          onChange={(e) => e.target.files && addFiles(e.target.files)}
        />
        <Upload className={`w-12 h-12 mx-auto mb-4 transition-colors duration-200 ${
          dragOver ? "text-[var(--color-purple)]" : "text-[var(--color-text-muted)]"
        }`} />
        <p className="text-base text-[var(--color-text-light)] font-medium">
          Drop screenshots here or click to browse
        </p>
        <p className="text-sm text-[var(--color-text-muted)] mt-1.5">
          Upload 1-5 PNG/JPG screenshots showing core gameplay
        </p>
      </div>

      {/* Previews */}
      <AnimatePresence>
        {screenshots.length > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="grid grid-cols-5 gap-3"
          >
            {screenshots.map((file, i) => (
              <motion.div
                key={`${file.name}-${i}`}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="relative aspect-[3/4] rounded-lg overflow-hidden bg-gray-100 group"
              >
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={URL.createObjectURL(file)}
                  alt={`Screenshot ${i + 1}`}
                  className="w-full h-full object-cover"
                />
                <button
                  onClick={(e) => { e.stopPropagation(); removeFile(i); }}
                  className="absolute top-1 right-1 w-5 h-5 rounded-full bg-black/60 text-white flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <X className="w-3 h-3" />
                </button>
                <div className="absolute bottom-0 inset-x-0 bg-black/50 text-center text-[10px] text-white py-0.5">
                  {i + 1}
                </div>
              </motion.div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {screenshots.length > 0 && (
        <div className="space-y-4">
          <div>
            <label className="text-xs font-medium text-[var(--color-text-muted)] mb-1.5 block">
              Game Name (optional)
            </label>
            <Input
              value={gameName}
              onChange={(e) => onGameNameChange(e.target.value)}
              placeholder="e.g., Candy Crush, Subway Surfers"
              className="bg-white/5 border-white/10 text-[var(--color-text-light)] placeholder:text-[var(--color-text-muted)]"
            />
          </div>

          {error && (
            <div className="rounded-lg bg-red-500/10 border border-red-500/20 p-3 text-sm text-red-400">
              {error}
            </div>
          )}

          <Button
            onClick={handleAnalyze}
            disabled={loading}
            className="w-full bg-[var(--color-purple)] hover:bg-[var(--color-purple-light)] text-white"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Analyzing with Claude Vision...
              </>
            ) : (
              "Analyze Game"
            )}
          </Button>
        </div>
      )}
    </div>
  );
}

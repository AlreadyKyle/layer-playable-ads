"use client";

import { Check } from "lucide-react";
import type { WizardStep } from "@/hooks/useWizard";

const STEPS = [
  { num: 1, label: "Upload Screenshots" },
  { num: 2, label: "Review Analysis" },
  { num: 3, label: "Generate Assets" },
  { num: 4, label: "Export Playable" },
] as const;

interface WorkflowProgressProps {
  currentStep: WizardStep;
}

export function WorkflowProgress({ currentStep }: WorkflowProgressProps) {
  return (
    <div className="space-y-0">
      {STEPS.map((s, i) => {
        const isComplete = s.num < currentStep;
        const isCurrent = s.num === currentStep;
        const isLast = i === STEPS.length - 1;

        return (
          <div key={s.num} className="flex gap-3">
            {/* Dot + line */}
            <div className="flex flex-col items-center">
              <div
                className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-semibold shrink-0 ${
                  isComplete
                    ? "bg-[var(--color-purple)] text-white"
                    : isCurrent
                    ? "bg-[var(--color-purple)]/20 text-[var(--color-purple-light)] ring-2 ring-[var(--color-purple)]"
                    : "bg-white/5 text-[var(--color-text-muted)]"
                }`}
              >
                {isComplete ? <Check className="w-3.5 h-3.5" /> : s.num}
              </div>
              {!isLast && (
                <div
                  className={`w-px h-6 ${
                    isComplete ? "bg-[var(--color-purple)]" : "bg-white/10"
                  }`}
                />
              )}
            </div>

            {/* Label */}
            <div className="pt-0.5">
              <span
                className={`text-xs font-medium ${
                  isCurrent
                    ? "text-[var(--color-text-light)]"
                    : isComplete
                    ? "text-[var(--color-purple-light)]"
                    : "text-[var(--color-text-muted)]"
                }`}
              >
                {s.label}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}

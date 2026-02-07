"use client";

import { useState, useCallback } from "react";
import { Zap, Gamepad2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { WorkflowProgress } from "./WorkflowProgress";
import { createDemo } from "@/lib/api";
import type { WizardStep } from "@/hooks/useWizard";
import type { MechanicType, PlayableResult, HealthResponse, WorkspaceResponse } from "@/lib/types";

interface AppSidebarProps {
  currentStep: WizardStep;
  health: HealthResponse | null;
  workspace: WorkspaceResponse | null;
  supportedMechanics: string[];
  onDemoResult: (result: PlayableResult) => void;
}

export function AppSidebar({
  currentStep,
  health,
  workspace,
  supportedMechanics,
  onDemoResult,
}: AppSidebarProps) {
  const [demoType, setDemoType] = useState<MechanicType>("match3");
  const [demoLoading, setDemoLoading] = useState(false);

  const handleDemo = useCallback(async () => {
    setDemoLoading(true);
    try {
      const result = await createDemo(demoType, `Demo ${demoType}`);
      onDemoResult(result);
    } catch (e) {
      console.error("Demo failed:", e);
    } finally {
      setDemoLoading(false);
    }
  }, [demoType, onDemoResult]);

  const apiKeys = health?.api_keys ?? {};

  return (
    <aside className="w-64 shrink-0 bg-[var(--sidebar)] border-r border-[var(--sidebar-border)] h-screen sticky top-0 flex flex-col overflow-y-auto">
      <div className="p-5 pb-6 flex flex-col gap-5 flex-1 min-h-0">
        {/* Brand */}
        <div>
          <span className="text-2xl font-extrabold bg-gradient-to-r from-[var(--color-purple)] to-[var(--color-pink)] bg-clip-text text-transparent">
            LPS
          </span>
          <div className="text-[10px] uppercase tracking-widest text-[var(--color-text-muted)] mt-0.5">
            Playable Studio
          </div>
        </div>

        {/* Divider */}
        <div className="h-px bg-white/5" />

        {/* API Status */}
        <div>
          <div className="text-[10px] uppercase tracking-wider text-[var(--color-text-muted)] mb-2 font-medium">
            API Status
          </div>
          <div className="space-y-1.5">
            {[
              { key: "layer_api_key", label: "Layer.ai API" },
              { key: "layer_workspace_id", label: "Workspace ID" },
              { key: "anthropic_api_key", label: "Anthropic API" },
            ].map(({ key, label }) => (
              <div key={key} className="flex items-center gap-2">
                <div
                  className={`w-1.5 h-1.5 rounded-full ${
                    apiKeys[key] ? "bg-emerald-400" : "bg-red-400"
                  }`}
                />
                <span className="text-xs text-[var(--color-text-muted)]">{label}</span>
              </div>
            ))}
          </div>
          {workspace && !workspace.error && workspace.credits_available != null && (
            <div className="mt-2 text-xs text-[var(--color-text-muted)]">
              Credits:{" "}
              <span className="text-[var(--color-text-light)] font-semibold">
                {workspace.credits_available}
              </span>
            </div>
          )}
        </div>

        {/* Divider */}
        <div className="h-px bg-white/5" />

        {/* Workflow */}
        <div>
          <div className="text-[10px] uppercase tracking-wider text-[var(--color-text-muted)] mb-3 font-medium">
            Workflow
          </div>
          <WorkflowProgress currentStep={currentStep} />
        </div>

        {/* Divider */}
        <div className="h-px bg-white/5" />

        {/* Supported Games */}
        <div>
          <div className="text-[10px] uppercase tracking-wider text-[var(--color-text-muted)] mb-2 font-medium">
            Supported Games
          </div>
          <div className="flex flex-wrap gap-1">
            {supportedMechanics.map((m) => (
              <span
                key={m}
                className="px-2 py-0.5 rounded-md bg-white/5 text-[10px] text-[var(--color-text-muted)] font-medium"
              >
                {m}
              </span>
            ))}
          </div>
        </div>

        {/* Spacer */}
        <div className="flex-1" />

        {/* Divider */}
        <div className="h-px bg-white/5" />

        {/* Demo Mode */}
        <div className="rounded-xl bg-white/[0.03] border border-white/[0.06] p-3">
          <div className="flex items-center gap-2 mb-2">
            <Zap className="w-3.5 h-3.5 text-[var(--color-warning)]" />
            <span className="text-xs font-semibold text-[var(--color-text-light)]">
              Quick Demo
            </span>
          </div>
          <p className="text-[10px] text-[var(--color-text-muted)] mb-3">
            No API keys needed
          </p>
          <select
            value={demoType}
            onChange={(e) => setDemoType(e.target.value as MechanicType)}
            className="w-full mb-2 rounded-lg bg-white/5 border border-white/10 text-xs text-[var(--color-text-light)] px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-[var(--color-purple)]"
          >
            <option value="match3">Match-3</option>
            <option value="runner">Runner</option>
            <option value="tapper">Tapper</option>
          </select>
          <Button
            size="sm"
            className="w-full bg-[var(--color-purple)] hover:bg-[var(--color-purple-light)] text-white text-xs"
            onClick={handleDemo}
            disabled={demoLoading}
          >
            <Gamepad2 className="w-3.5 h-3.5 mr-1.5" />
            {demoLoading ? "Generating..." : "Generate Demo"}
          </Button>
        </div>
      </div>
    </aside>
  );
}

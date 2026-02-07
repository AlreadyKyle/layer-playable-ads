"use client";

import { motion } from "framer-motion";
import type { ReactNode } from "react";

interface MetricCardProps {
  label: string;
  value: string;
  icon?: ReactNode;
  status?: "default" | "success" | "warning" | "error";
}

const statusColors = {
  default: "text-purple-light",
  success: "text-emerald-400",
  warning: "text-amber-400",
  error: "text-red-400",
};

export function MetricCard({ label, value, icon, status = "default" }: MetricCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-xl bg-[var(--color-bg-secondary)] p-4 hover:bg-white/[0.04] transition-colors duration-200"
    >
      <div className="flex items-center gap-2 text-[var(--color-text-muted)] text-xs font-medium uppercase tracking-wide mb-2">
        {icon && <span className={statusColors[status]}>{icon}</span>}
        {label}
      </div>
      <div className={`text-2xl font-bold ${statusColors[status]}`}>{value}</div>
    </motion.div>
  );
}

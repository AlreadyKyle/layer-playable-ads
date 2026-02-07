"use client";

import { motion } from "framer-motion";
import type { ReactNode } from "react";

interface ContentCardProps {
  title?: string;
  icon?: ReactNode;
  accent?: string;
  children: ReactNode;
  className?: string;
}

export function ContentCard({ title, icon, accent, children, className = "" }: ContentCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className={`rounded-xl bg-white shadow-md shadow-black/5 hover:shadow-lg hover:shadow-black/10 transition-shadow duration-200 overflow-hidden p-5 ${className}`}
      style={accent ? { borderLeft: `3px solid ${accent}` } : undefined}
    >
      {title && (
        <div className="flex items-center gap-2 mb-3">
          {icon && <span className="text-[var(--color-purple)]">{icon}</span>}
          <h3 className="text-sm font-semibold text-[var(--color-text-dark)]">{title}</h3>
        </div>
      )}
      <div className="text-[var(--color-text-body)] text-sm leading-relaxed">{children}</div>
    </motion.div>
  );
}

"use client";

import { CheckCircle, XCircle } from "lucide-react";

const NETWORKS = [
  { name: "IronSource", maxMb: 5 },
  { name: "Unity", maxMb: 5 },
  { name: "AppLovin", maxMb: 5 },
  { name: "Facebook", maxMb: 2 },
  { name: "Google", maxMb: 5 },
];

interface NetworkBadgesProps {
  fileSizeMb: number;
}

export function NetworkBadges({ fileSizeMb }: NetworkBadgesProps) {
  return (
    <div className="flex flex-wrap gap-2">
      {NETWORKS.map((n) => {
        const ok = fileSizeMb <= n.maxMb;
        return (
          <div
            key={n.name}
            className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium ${
              ok
                ? "bg-emerald-50 text-emerald-700"
                : "bg-red-50 text-red-600"
            }`}
          >
            {ok ? <CheckCircle className="w-3.5 h-3.5" /> : <XCircle className="w-3.5 h-3.5" />}
            {n.name}
          </div>
        );
      })}
    </div>
  );
}

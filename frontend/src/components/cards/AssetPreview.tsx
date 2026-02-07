"use client";

import { motion } from "framer-motion";
import { CheckCircle, XCircle } from "lucide-react";
import type { GeneratedAsset } from "@/lib/types";

interface AssetPreviewProps {
  assetKey: string;
  asset: GeneratedAsset;
}

export function AssetPreview({ assetKey, asset }: AssetPreviewProps) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="rounded-lg bg-gray-50 border border-gray-100 overflow-hidden"
    >
      <div className="aspect-square bg-gray-100 relative">
        {asset.is_valid && asset.base64_data ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={asset.base64_data}
            alt={assetKey}
            className="w-full h-full object-contain"
          />
        ) : asset.is_valid && asset.image_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={asset.image_url}
            alt={assetKey}
            className="w-full h-full object-contain"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-400 text-xs">
            No preview
          </div>
        )}
        <div className="absolute top-1.5 right-1.5">
          {asset.is_valid ? (
            <CheckCircle className="w-4 h-4 text-emerald-500" />
          ) : (
            <XCircle className="w-4 h-4 text-red-400" />
          )}
        </div>
      </div>
      <div className="p-2">
        <div className="text-xs font-medium text-[var(--color-text-dark)] truncate">
          {assetKey}
        </div>
        {asset.error && (
          <div className="text-[10px] text-red-400 truncate mt-0.5">{asset.error}</div>
        )}
      </div>
    </motion.div>
  );
}

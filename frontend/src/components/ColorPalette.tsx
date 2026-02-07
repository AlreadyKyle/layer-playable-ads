"use client";

interface ColorPaletteProps {
  colors: string[];
}

export function ColorPalette({ colors }: ColorPaletteProps) {
  return (
    <div className="flex gap-1.5 flex-wrap">
      {colors.map((color) => (
        <div key={color} className="flex flex-col items-center gap-1">
          <div
            className="w-7 h-7 rounded-md border border-gray-200 shadow-sm"
            style={{ backgroundColor: color }}
          />
          <span className="text-[10px] text-[var(--color-text-body)] font-mono">{color}</span>
        </div>
      ))}
    </div>
  );
}

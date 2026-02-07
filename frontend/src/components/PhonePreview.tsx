"use client";

interface PhonePreviewProps {
  html: string;
  width?: number;
  height?: number;
}

export function PhonePreview({ html, width = 320, height = 480 }: PhonePreviewProps) {
  const src = `data:text/html;base64,${btoa(unescape(encodeURIComponent(html)))}`;

  return (
    <div className="inline-flex flex-col items-center">
      <div
        className="rounded-[2rem] border-4 border-gray-800 bg-black p-2 shadow-xl"
        style={{ width: width + 32, height: height + 64 }}
      >
        <div className="w-8 h-1 rounded-full bg-gray-700 mx-auto mb-2" />
        <iframe
          src={src}
          className="rounded-xl bg-white"
          style={{ width, height }}
          sandbox="allow-scripts"
          title="Playable Preview"
        />
      </div>
    </div>
  );
}

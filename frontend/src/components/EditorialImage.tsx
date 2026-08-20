import { useEffect, useState } from "react";

type EditorialImageProps = {
  src?: string | null;
  alt: string;
  category?: string | null;
  width?: string | number | null;
  height?: string | number | null;
  className?: string;
  sizes?: string;
  priority?: boolean;
};

function positiveDimension(value: string | number | null | undefined, fallback: number) {
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}

function shortCue(text: string) {
  const words = text.trim().split(/\s+/).filter(Boolean);
  return `${words.slice(0, 7).join(" ")}${words.length > 7 ? "…" : ""}`;
}

function managedSrcSet(src: string) {
  if (!src.includes("/api/public/images/") || !src.endsWith(".webp")) return undefined;
  const stem = src.slice(0, -5);
  return `${stem}-640.webp 640w, ${stem}-960.webp 960w, ${src} 1200w`;
}

/**
 * Shared image policy for public editorial surfaces.
 *
 * Every published cover is normalized to 1200 x 630 by the backend. Keeping
 * those intrinsic dimensions here prevents layout shifts while the real image
 * loads. Missing or failed media becomes a story-specific typographic card,
 * keeping the layout stable without introducing a generic stock image.
 */
export default function EditorialImage({
  src,
  alt,
  category,
  width,
  height,
  className = "",
  sizes,
  priority = false,
}: EditorialImageProps) {
  const [failed, setFailed] = useState(false);

  useEffect(() => setFailed(false), [src]);

  if (!src || failed) {
    return (
      <div className={`editorial-fallback ${className}`} role="img" aria-label={alt}>
        <span aria-hidden="true">AION / {category || "Editorial"}</span>
        <strong aria-hidden="true">{shortCue(alt)}</strong>
      </div>
    );
  }

  return (
    <img
      src={src}
      srcSet={managedSrcSet(src)}
      alt={alt}
      width={positiveDimension(width, 1200)}
      height={positiveDimension(height, 630)}
      sizes={sizes}
      loading={priority ? "eager" : "lazy"}
      fetchPriority={priority ? "high" : "auto"}
      decoding="async"
      draggable={false}
      onError={() => setFailed(true)}
      className={`editorial-img ${className}`}
    />
  );
}

/** Anúncio AdSense — só renderiza com VITE_ADSENSE_CLIENT definido.
 * Sem a credencial, nada aparece (nem espaço vazio): UX e CWV preservados. */
import { useEffect, useRef } from "react";

const CLIENT = import.meta.env.VITE_ADSENSE_CLIENT;

export default function AdSlot({ slot, className = "" }: { slot: string; className?: string }) {
  const ref = useRef<HTMLModElement>(null);
  useEffect(() => {
    if (!CLIENT || !ref.current) return;
    try { ((window as any).adsbygoogle = (window as any).adsbygoogle || []).push({}); } catch {}
  }, []);
  if (!CLIENT) return null;
  return (
    <ins ref={ref} className={`adsbygoogle block ${className}`}
      style={{ display: "block", minHeight: 90 }}
      data-ad-client={CLIENT} data-ad-slot={slot}
      data-ad-format="auto" data-full-width-responsive="true" />
  );
}

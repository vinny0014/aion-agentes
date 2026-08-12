import { useEffect, useState } from "react";
import {
  getAnalyticsConsent,
  openCookiePreferences,
  setAnalyticsConsent,
  type AnalyticsConsent,
} from "./telemetry";

export default function CookieConsent() {
  const [consent, setConsent] = useState<AnalyticsConsent>(() => getAnalyticsConsent());
  const [preferencesOpen, setPreferencesOpen] = useState(false);
  const [analyticsEnabled, setAnalyticsEnabled] = useState(consent === "granted");

  useEffect(() => {
    const open = () => {
      setAnalyticsEnabled(getAnalyticsConsent() === "granted");
      setPreferencesOpen(true);
    };
    window.addEventListener("aion:open-cookie-preferences", open);
    return () => window.removeEventListener("aion:open-cookie-preferences", open);
  }, []);

  function save(value: "granted" | "denied") {
    setAnalyticsConsent(value);
    setConsent(value);
    setAnalyticsEnabled(value === "granted");
    setPreferencesOpen(false);
  }

  if (consent !== null && !preferencesOpen) return null;

  return (
    <section className="cookie-consent" role="dialog" aria-modal="true" aria-labelledby="cookie-title">
      <div className="cookie-consent__panel">
        <p className="tag">privacy controls</p>
        <h2 id="cookie-title" className="mt-1 font-display text-xl font-bold">Your privacy choices</h2>
        <p className="mt-2 text-sm text-slateui">
          Essential storage keeps the site working. With your permission, Google Analytics 4 measures readership and site performance. We do not load Analytics before you accept.
        </p>
        {preferencesOpen && (
          <div className="mt-4 rounded-lg border border-line p-3">
            <label className="flex items-start gap-3 text-sm">
              <input type="checkbox" className="mt-1" checked={analyticsEnabled}
                onChange={(event) => setAnalyticsEnabled(event.target.checked)} />
              <span><strong>Analytics cookies</strong><span className="mt-1 block text-slateui">Allow anonymized audience, article and navigation measurements.</span></span>
            </label>
            <p className="mt-3 text-xs text-slateui">Essential storage is always active and is not used for advertising.</p>
          </div>
        )}
        <div className="mt-5 flex flex-wrap gap-2">
          {preferencesOpen ? (
            <button className="btn-primary !py-2 text-sm" onClick={() => save(analyticsEnabled ? "granted" : "denied")}>Save preferences</button>
          ) : (
            <button className="btn-ghost !py-2 text-sm" onClick={() => setPreferencesOpen(true)}>Preferences</button>
          )}
          <button className="btn-primary !py-2 text-sm" onClick={() => save("granted")}>Accept analytics</button>
          <button className="btn-ghost !py-2 text-sm" onClick={() => save("denied")}>Reject analytics</button>
          <a href="/privacy" className="px-2 py-2 text-sm text-signal hover:underline">Privacy policy</a>
        </div>
      </div>
    </section>
  );
}

export { openCookiePreferences };

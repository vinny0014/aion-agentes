(function () {
  "use strict";
  var CONSENT_KEY = "aion_cookie_consent_v1";
  var measurementMeta = document.querySelector('meta[name="aion-ga-measurement-id"]');
  var measurementId = measurementMeta ? measurementMeta.content : "";
  var sent = {};
  var loaded = false;
  window.dataLayer = window.dataLayer || [];
  function gtag() { window.dataLayer.push(arguments); }
  function consent() {
    try {
      var value = window.localStorage.getItem(CONSENT_KEY);
      return value === "granted" || value === "denied" ? value : null;
    } catch (_) { return null; }
  }
  function articleData() {
    var meta = document.querySelector(".meta");
    var parts = meta ? meta.textContent.split("·").map(function (value) { return value.trim(); }) : [];
    var published = document.querySelector('meta[property="article:published_time"]');
    return {
      slug: location.pathname.replace(/^\/article\//, ""),
      category: parts[0] || "news",
      author: parts[1] || "AION Editorial",
      published_date: published ? published.content : ""
    };
  }
  function eventOnce(name, parameters) {
    var key = name + ":" + (parameters.slug || location.pathname);
    if (!loaded || consent() !== "granted" || sent[key]) return;
    sent[key] = true;
    gtag("event", name, parameters);
  }
  function loadAnalytics() {
    if (loaded || consent() !== "granted" || !/^G-[A-Z0-9]{6,20}$/.test(measurementId)) return;
    loaded = true;
    var script = document.createElement("script");
    script.async = true;
    script.src = "https://www.googletagmanager.com/gtag/js?id=" + encodeURIComponent(measurementId);
    document.head.appendChild(script);
    gtag("js", new Date());
    gtag("config", measurementId, { anonymize_ip: true, send_page_view: false });
    gtag("event", "page_view", {
      page_path: location.pathname + location.search,
      page_location: location.href,
      page_title: document.title
    });
    eventOnce("article_view", articleData());
  }
  function save(value) {
    try { window.localStorage.setItem(CONSENT_KEY, value); } catch (_) {}
    gtag("consent", "update", { analytics_storage: value });
    document.getElementById("aion-cookie-consent").hidden = true;
    if (value === "granted") loadAnalytics();
  }
  gtag("consent", "default", {
    analytics_storage: consent() === "granted" ? "granted" : "denied",
    ad_storage: "denied",
    ad_user_data: "denied",
    ad_personalization: "denied",
    wait_for_update: 500
  });
  var dialog = document.getElementById("aion-cookie-consent");
  if (dialog && consent() === null) dialog.hidden = false;
  var preferences = document.getElementById("aion-preferences");
  if (preferences) preferences.addEventListener("click", function () {
    document.getElementById("aion-cookie-preferences").hidden = false;
    document.getElementById("aion-analytics-enabled").checked = consent() === "granted";
    preferences.textContent = "Save preferences";
    preferences.onclick = function () {
      save(document.getElementById("aion-analytics-enabled").checked ? "granted" : "denied");
    };
  }, { once: true });
  document.getElementById("aion-accept")?.addEventListener("click", function () { save("granted"); });
  document.getElementById("aion-reject")?.addEventListener("click", function () { save("denied"); });
  document.addEventListener("click", function (event) {
    var link = event.target.closest && event.target.closest('article a[href^="http"]');
    if (!link || !loaded || consent() !== "granted") return;
    var data = articleData();
    try { data.source_host = new URL(link.href).hostname; } catch (_) { data.source_host = "unknown"; }
    gtag("event", "outbound_source_click", data);
  });
  window.addEventListener("scroll", function () {
    var height = Math.max(document.documentElement.scrollHeight - innerHeight, 1);
    var progress = Math.min(100, Math.max(0, scrollY / height * 100));
    [25, 50, 90].forEach(function (threshold) {
      if (progress >= threshold) {
        var data = articleData();
        data.percent_scrolled = threshold;
        eventOnce("article_scroll_" + threshold, data);
      }
    });
  }, { passive: true });
  if (consent() === "granted") loadAnalytics();
})();

// ========================================================
// DOMOS SMART KIOSK - REAL DEVICES, LIQUID GLASS UI & AI ASSISTANT
// Mode Claro (Default) / Modo Oscuro, Anti-Burn-In, Offline Fallback
// ========================================================

let deviceData = {
  lights: [],
  climate: [],
  solar: {},
  battery: {},
  plugs: [],
  security: {},
  cameras: []
};

// ========================================================
// 1. THEME MANAGEMENT (MODO CLARO POR DEFECTO / MODO OSCURO)
// ========================================================

const SVG_SUN = '<svg viewBox="0 0 24 24" width="21" height="21" fill="none" stroke="currentColor" stroke-width="1.85" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/></svg>';
const SVG_MOON = '<svg viewBox="0 0 24 24" width="21" height="21" fill="none" stroke="currentColor" stroke-width="1.85" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/><path d="M19 3v4M21 5h-4"/></svg>';
const SVG_PHOTO = '<svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" stroke-width="1.85" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="3"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="m21 15-5-5L5 21"/></svg>';
const SVG_FOLDER = '<svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" stroke-width="1.85" stroke-linecap="round" stroke-linejoin="round"><path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"/></svg>';
const SVG_SHIELD_OK = '<svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" stroke-width="1.85" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/></svg>';
const SVG_SHIELD_ALERT = '<svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" stroke-width="1.85" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="M12 8v4M12 16h.01"/></svg>';
const SVG_DOOR_CLOSED = '<svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" stroke-width="1.85" stroke-linecap="round" stroke-linejoin="round"><path d="M13 4h3a2 2 0 0 1 2 2v14"/><path d="M2 20h3"/><path d="M13 20h9"/><path d="M10 12v.01"/><path d="M13 4.562v16.157a1 1 0 0 1-1.242.97L5 20V5.562a2 2 0 0 1 1.515-1.94l4-1A2 2 0 0 1 13 4.561Z"/></svg>';
const SVG_DOOR_OPEN = '<svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" stroke-width="1.85" stroke-linecap="round" stroke-linejoin="round"><path d="M11 20H2"/><path d="M11 4.562v16.157a1 1 0 0 0 1.242.97L19 20V5.562a2 2 0 0 0-1.515-1.94l-4-1A2 2 0 0 0 11 4.561Z"/><path d="M22 20h-3"/><path d="M14 12v.01"/></svg>';
const SVG_BATTERY = '<svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" stroke-width="1.85" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="7" width="16" height="10" rx="2"/><line x1="22" y1="11" x2="22" y2="13"/></svg>';
const SVG_BOLT = '<svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>';

function getWeatherNeonSvg(code, size = 22) {
  if (code === 0 || code === 1) {
    return { cls: "neon-svg neon-amber", svg: `<svg viewBox="0 0 24 24" width="${size}" height="${size}" fill="none" stroke="currentColor" stroke-width="1.85" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/></svg>` };
  }
  if (code === 2 || code === 3 || code === 45 || code === 48) {
    return { cls: "neon-svg neon-sky", svg: `<svg viewBox="0 0 24 24" width="${size}" height="${size}" fill="none" stroke="currentColor" stroke-width="1.85" stroke-linecap="round" stroke-linejoin="round"><path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z"/></svg>` };
  }
  if (code >= 95) {
    return { cls: "neon-svg neon-violet", svg: `<svg viewBox="0 0 24 24" width="${size}" height="${size}" fill="none" stroke="currentColor" stroke-width="1.85" stroke-linecap="round" stroke-linejoin="round"><path d="M6 16.326A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 .5 8.973"/><path d="m13 12-3 5h4l-3 5"/></svg>` };
  }
  return { cls: "neon-svg neon-cyan", svg: `<svg viewBox="0 0 24 24" width="${size}" height="${size}" fill="none" stroke="currentColor" stroke-width="1.85" stroke-linecap="round" stroke-linejoin="round"><path d="M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242"/><path d="M8 19v2M8 13v2M16 19v2M16 13v2M12 21v2M12 15v2"/></svg>` };
}

let currentTheme = localStorage.getItem("domos_theme") || "light";

function applyTheme(theme) {
  currentTheme = theme;
  document.documentElement.setAttribute("data-theme", theme);
  document.body.setAttribute("data-theme", theme);
  localStorage.setItem("domos_theme", theme);

  const iconEl = document.getElementById("theme-btn-icon");
  const labelEl = document.getElementById("theme-btn-label");
  const statusTag = document.getElementById("theme-status-tag");
  const btnLight = document.getElementById("btn-theme-light");
  const btnDark = document.getElementById("btn-theme-dark");

  if (theme === "dark") {
    if (iconEl) { iconEl.innerHTML = SVG_MOON; iconEl.className = 'dock-btn-icon neon-svg neon-cyan'; }
    if (labelEl) labelEl.textContent = "Oscuro";
    if (statusTag) statusTag.textContent = "Modo Oscuro";
    btnLight?.classList.remove("active");
    btnDark?.classList.add("active");
  } else {
    if (iconEl) { iconEl.innerHTML = SVG_SUN; iconEl.className = 'dock-btn-icon neon-svg neon-amber'; }
    if (labelEl) labelEl.textContent = "Claro";
    if (statusTag) statusTag.textContent = "Modo Claro";
    btnLight?.classList.add("active");
    btnDark?.classList.remove("active");
  }

  fetch("/api/config", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ theme: theme })
  }).catch(() => {});
}

function toggleTheme() {
  applyTheme(currentTheme === "light" ? "dark" : "light");
}

document.getElementById("btn-theme-toggle")?.addEventListener("click", toggleTheme);
document.getElementById("btn-theme-light")?.addEventListener("click", () => applyTheme("light"));
document.getElementById("btn-theme-dark")?.addEventListener("click", () => applyTheme("dark"));
applyTheme(currentTheme);

// ========================================================
// 2. ANTI-BURN-IN PROTECTION (ANTIQUEMADO PANEL IPS LCD)
// ========================================================
let idleTimer = null;
let isDrawerOpen = false;

let _lastWakePing = 0;
function resetIdleTimer(evt) {
  if (evt && evt.type !== "mousemove") {
    const nowMs = Date.now();
    if (nowMs - _lastWakePing > 10000) {
      _lastWakePing = nowMs;
      fetch("/api/presence/wake", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ seconds: 180 })
      }).catch(() => {});
    }
  }
  const hud = document.getElementById("hud-layer");
  if (hud) hud.classList.remove("hud-idle");

  if (idleTimer) clearTimeout(idleTimer);

  // If drawer is closed, dim HUD elements after 20 seconds of inactivity
  idleTimer = setTimeout(() => {
    if (!isDrawerOpen && hud) {
      hud.classList.add("hud-idle");
    }
  }, 20000);
}

// User interaction events wake up screen elements instantly
["touchstart", "pointerdown", "mousedown", "mousemove", "keydown"].forEach(evt => {
  window.addEventListener(evt, resetIdleTimer, { passive: true });
});
resetIdleTimer();

// Periodic Pixel Shifting (every 60 seconds, shifts ±3px)
function applyPixelShift() {
  const targets = document.querySelectorAll(".pixel-shift-target");
  const dx = (Math.random() * 6 - 3).toFixed(1);
  const dy = (Math.random() * 6 - 3).toFixed(1);

  targets.forEach(el => {
    el.style.transform = `translate(${dx}px, ${dy}px)`;
  });
}
setInterval(applyPixelShift, 60000);

// ========================================================
// 3. CLOCK & DATE
// ========================================================
function updateClock() {
  const now = new Date();
  const timeEl = document.getElementById("clock-time");
  const dateEl = document.getElementById("clock-date");

  if (timeEl) {
    const hours = String(now.getHours()).padStart(2, "0");
    const minutes = String(now.getMinutes()).padStart(2, "0");
    timeEl.textContent = `${hours}:${minutes}`;
  }

  if (dateEl) {
    const options = { weekday: "long", day: "numeric", month: "long" };
    dateEl.textContent = now.toLocaleDateString("es-ES", options);
  }
}
setInterval(updateClock, 1000);
updateClock();

// ========================================================
// 4. WEATHER WIDGET
// ========================================================
let latestWeatherData = null;
const DEFAULT_WEATHER_LOC = {
  name: "Rincón de la Victoria, Málaga",
  lat: 36.7167,
  lon: -4.2833
};
function getWeatherLocation() {
  try {
    const raw = localStorage.getItem("domos_weather_loc");
    if (raw) {
      const parsed = JSON.parse(raw);
      if (parsed && typeof parsed.lat === "number" && typeof parsed.lon === "number") return parsed;
    }
  } catch (e) {}
  return DEFAULT_WEATHER_LOC;
}

function decodeWeatherCode(code) {
  let icon = "☀️";
  let desc = "Despejado";
  if (code >= 1 && code <= 3) { icon = "⛅"; desc = "Parcialmente nublado"; }
  else if (code >= 45 && code <= 48) { icon = "🌫️"; desc = "Niebla"; }
  else if (code >= 51 && code <= 67) { icon = "🌧️"; desc = "Lluvia"; }
  else if (code >= 71 && code <= 77) { icon = "❄️"; desc = "Nieve"; }
  else if (code >= 80 && code <= 82) { icon = "🌦️"; desc = "Chubascos"; }
  else if (code >= 95) { icon = "⛈️"; desc = "Tormenta"; }
  return { icon, desc };
}

async function updateWeather() {
  try {
    const loc = getWeatherLocation();
    const res = await fetch(`https://api.open-meteo.com/v1/forecast?latitude=${loc.lat}&longitude=${loc.lon}&current=temperature_2m,relative_humidity_2m,apparent_temperature,wind_speed_10m,weather_code&hourly=temperature_2m,weather_code,precipitation_probability,wind_speed_10m&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max&timezone=auto&forecast_days=5`);
    if (res.ok) {
      const data = await res.json();
      latestWeatherData = data;
      const temp = Math.round(data.current.temperature_2m);
      const { icon, desc } = decodeWeatherCode(data.current.weather_code);

      const wSvg = getWeatherNeonSvg(data.current.weather_code, 48);
      const wIconEl = document.getElementById("weather-icon");
      if (wIconEl) {
        wIconEl.className = wSvg.cls;
        wIconEl.innerHTML = wSvg.svg;
      }
      const tempEl = document.getElementById("weather-temp");
      if (tempEl) tempEl.textContent = `${temp}°`;
      const descEl = document.getElementById("weather-desc");
      if (descEl) descEl.textContent = desc;

      const rangeEl = document.getElementById("weather-range");
      if (rangeEl && data.daily && Array.isArray(data.daily.temperature_2m_max) && Array.isArray(data.daily.temperature_2m_min)) {
        const tMax = Math.round(data.daily.temperature_2m_max[0]);
        const tMin = Math.round(data.daily.temperature_2m_min[0]);
        const rain = data.daily.precipitation_probability_max ? data.daily.precipitation_probability_max[0] : null;
        const rainStr = (rain !== null && rain > 0) ? ` · 💧 ${rain}%` : "";
        rangeEl.textContent = `▲ ${tMax}° · ▼ ${tMin}°${rainStr}`;
      }
    }
  } catch (e) {
    console.error("Error weather:", e);
  }
}

function openWeatherModal() {
  const modal = document.getElementById("weather-modal");
  if (!modal) return;
  modal.classList.remove("hidden");
  modal.style.display = "flex";

  const locEl = document.getElementById("wmodal-location");
  const curEl = document.getElementById("wmodal-current");
  const daysEl = document.getElementById("wmodal-forecast-days");
  const iconEl = document.getElementById("wmodal-icon");

  if (locEl) locEl.textContent = "📍 " + getWeatherLocation().name;
  if (!latestWeatherData || !latestWeatherData.current) {
    if (curEl) curEl.innerHTML = "<p>Cargando previsión...</p>";
    updateWeather().then(() => openWeatherModal());
    return;
  }

  const cur = latestWeatherData.current;
  const { icon, desc } = decodeWeatherCode(cur.weather_code);
  if (iconEl) { const wSvgM = getWeatherNeonSvg(cur.weather_code, 26); iconEl.className = wSvgM.cls; iconEl.innerHTML = wSvgM.svg; }
  if (curEl) {
    curEl.innerHTML = `
      <div style="display:flex; align-items:center; gap:0.9rem;">
        <span style="font-size:2.6rem; line-height:1;">${icon}</span>
        <div>
          <div style="font-size:2rem; font-weight:700; line-height:1.1;">${Math.round(cur.temperature_2m)}°C</div>
          <div style="font-size:0.95rem; color:var(--modal-text-muted);">${desc}</div>
        </div>
      </div>
      <div style="display:flex; gap:1.25rem; flex-wrap:wrap; font-size:0.9rem; color:var(--modal-text-muted);">
        <div>🌡️ Sensación: <strong>${Math.round(cur.apparent_temperature ?? cur.temperature_2m)}°C</strong></div>
        <div>💧 Humedad: <strong>${cur.relative_humidity_2m ?? "--"}%</strong></div>
        <div>💨 Viento: <strong>${Math.round(cur.wind_speed_10m ?? 0)} km/h</strong></div>
      </div>
    `;
  }


  // Render hourly forecast for today (from current hour onward, min 10 hours)
  const hourlyWrap = document.getElementById("wmodal-hourly-wrap");
  const hourlyStrip = document.getElementById("wmodal-hourly-strip");
  const hourly = latestWeatherData.hourly;
  if (hourlyWrap && hourlyStrip && hourly && Array.isArray(hourly.time)) {
    const now = new Date();
    const curHour = now.getHours();
    const todayPrefix = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;

    let startIdx = hourly.time.findIndex(t => t.startsWith(todayPrefix) && parseInt(t.slice(11, 13), 10) >= curHour);
    if (startIdx < 0) startIdx = 0;

    // Show remaining hours of today, or at least 10 upcoming hours if late at night
    let endIdx = hourly.time.findIndex((t, i) => i >= startIdx && !t.startsWith(todayPrefix));
    if (endIdx < 0) endIdx = Math.min(hourly.time.length, startIdx + 12);
    if (endIdx - startIdx < 10) endIdx = Math.min(hourly.time.length, startIdx + 10);

    const slice = [];
    for (let i = startIdx; i < endIdx; i++) {
      const tStr = hourly.time[i];
      const hh = tStr.slice(11, 13);
      const isNow = (i === startIdx && tStr.startsWith(todayPrefix));
      const hInfo = decodeWeatherCode(hourly.weather_code[i]);
      const hTemp = Math.round(hourly.temperature_2m[i]);
      const hRain = hourly.precipitation_probability ? (hourly.precipitation_probability[i] ?? 0) : 0;
      const hWind = hourly.wind_speed_10m ? Math.round(hourly.wind_speed_10m[i] ?? 0) : 0;
      slice.push(`
        <div class="domos-modal-subcard" style="min-width:68px; flex:0 0 auto; padding:0.55rem 0.45rem; border-radius:14px; text-align:center; display:flex; flex-direction:column; align-items:center; gap:0.2rem; ${isNow ? "border-color:#0284c7; background:rgba(14,165,233,0.12);" : ""}">
          <div style="font-size:0.72rem; font-weight:700; color:${isNow ? "#0284c7" : "var(--modal-text-muted)"};">${isNow ? "Ahora" : hh + ":00"}</div>
          <div style="font-size:1.35rem; line-height:1.1;">${hInfo.icon}</div>
          <div style="font-size:0.92rem; font-weight:800; color:var(--modal-text);">${hTemp}°</div>
          <div style="font-size:0.68rem; color:${hRain > 0 ? "#0284c7" : "var(--modal-text-muted)"}; font-weight:${hRain > 0 ? "700" : "500"};">💧 ${hRain}%</div>
          <div style="font-size:0.63rem; color:var(--modal-text-muted);">💨 ${hWind}</div>
        </div>
      `);
    }
    hourlyStrip.innerHTML = slice.join("");
    hourlyWrap.style.display = slice.length ? "block" : "none";
  }

  const daily = latestWeatherData.daily;
  if (daysEl && daily && Array.isArray(daily.time)) {
    daysEl.innerHTML = daily.time.map((dateStr, idx) => {
      const d = new Date(dateStr + "T12:00:00");
      const dayLabel = idx === 0 ? "Hoy" : d.toLocaleDateString("es-ES", { weekday: "short", day: "numeric" });
      const info = decodeWeatherCode(daily.weather_code[idx]);
      const tMax = Math.round(daily.temperature_2m_max[idx]);
      const tMin = Math.round(daily.temperature_2m_min[idx]);
      const rain = daily.precipitation_probability_max ? daily.precipitation_probability_max[idx] : null;
      return `
        <div style="padding:0.85rem 0.75rem; border-radius:16px; background:var(--modal-subcard-bg); border:1px solid var(--modal-subcard-border); color:var(--modal-text); text-align:center; display:flex; flex-direction:column; gap:0.35rem;">
          <div style="font-weight:700; text-transform:capitalize; font-size:0.9rem;">${dayLabel}</div>
          <div style="font-size:1.8rem; line-height:1.1;">${info.icon}</div>
          <div style="font-size:0.78rem; color:var(--modal-text-muted); min-height:2.1em;">${info.desc}</div>
          <div style="font-size:0.95rem; font-weight:700;">
            <span style="color:var(--modal-text);">${tMax}°</span>
            <span style="color:#64748b; margin:0 2px;">/</span>
            <span style="color:var(--modal-text-muted);">${tMin}°</span>
          </div>
          ${rain !== null ? `<div style="font-size:0.75rem; color:#38bdf8;">💧 ${rain}%</div>` : ""}
        </div>
      `;
    }).join("");
  }
}

document.getElementById("weather-btn")?.addEventListener("click", () => openWeatherModal());
document.getElementById("btn-weather-modal-close")?.addEventListener("click", () => {
  const m = document.getElementById("weather-modal");
  if (m) { m.classList.add("hidden"); m.style.display = "none"; }
});
document.getElementById("weather-modal")?.addEventListener("click", (e) => {
  if (e.target.id === "weather-modal") {
    e.target.classList.add("hidden");
    e.target.style.display = "none";
  }
});
updateWeather();
setInterval(updateWeather, 600000);

// ========================================================
// 5. SLIDESHOW SYSTEM (CAROUSEL: SD CARD + ONLINE NATURE + OFFLINE FALLBACK)
// ========================================================
let sdPhotoList = [];
let currentPhotoIndex = 0;
let slideInterval = null;
let carouselMode = localStorage.getItem("domos_carousel_mode") || "mixed"; // "mixed", "online", "sd"
let carouselTransition = localStorage.getItem("domos_carousel_transition") || "auto"; // "auto", "blur", "black", "white"
let useOnlineForNext = false;

// Curated high-resolution natural landscape collection (1366x768 optimized)
const ONLINE_LANDSCAPES = [
  "https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1366&h=768&q=80", // Yosemite
  "https://images.unsplash.com/photo-1469474968028-56623f02e42e?auto=format&fit=crop&w=1366&h=768&q=80", // Montañas niebla
  "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?auto=format&fit=crop&w=1366&h=768&q=80", // Bosque con niebla
  "https://images.unsplash.com/photo-1472214103451-9374bd1c798e?auto=format&fit=crop&w=1366&h=768&q=80", // Valle atardecer
  "https://images.unsplash.com/photo-1426604966848-d7adac402bff?auto=format&fit=crop&w=1366&h=768&q=80", // Parque Zion
  "https://images.unsplash.com/photo-1501785888041-af3ef285b470?auto=format&fit=crop&w=1366&h=768&q=80", // Lago y montañas
  "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?auto=format&fit=crop&w=1366&h=768&q=80", // Bosque esmeralda
  "https://images.unsplash.com/photo-1511497584788-87676104235f?auto=format&fit=crop&w=1366&h=768&q=80", // Fiordos noruegos
  "https://images.unsplash.com/photo-1519681393784-d120267933ba?auto=format&fit=crop&w=1366&h=768&q=80", // Picos nevados
  "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1366&h=768&q=80", // Playa atardecer
  "https://images.unsplash.com/photo-1433086966358-54859d0ed716?auto=format&fit=crop&w=1366&h=768&q=80", // Cascada en la selva
  "https://images.unsplash.com/photo-1534447677768-be436bb09401?auto=format&fit=crop&w=1366&h=768&q=80", // Aurora boreal
  "https://images.unsplash.com/photo-1518495973542-4542c06a5843?auto=format&fit=crop&w=1366&h=768&q=80", // Rayos de sol en bosque
  "https://images.unsplash.com/photo-1502082553048-f009c37129b9?auto=format&fit=crop&w=1366&h=768&q=80", // Otoño dorado
  "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=1366&h=768&q=80"  // Alpes suizos
];
let onlineIndex = Math.floor(Math.random() * ONLINE_LANDSCAPES.length);

let cachedOnlineLandscapes = [];
async function loadPhotos() {
  try {
    const [sdRes, landRes] = await Promise.all([
      fetch("/api/photos"),
      fetch("/api/landscapes")
    ]);
    if (landRes.ok) {
      const ld = await landRes.json();
      if (Array.isArray(ld.photos) && ld.photos.length > 0) {
        cachedOnlineLandscapes = ld.photos;
      }
    }
    if (sdRes.ok) {
      const data = await sdRes.json();
      sdPhotoList = data.photos || [];
      showNextSlide();
      startSlideshow();
    }
  } catch (e) {
    console.error("Error fetching photos:", e);
  }
}

async function loadFolders() {
  try {
    const res = await fetch("/api/photos/folders");
    if (res.ok) {
      const data = await res.json();
      const select = document.getElementById("photo-folder-select");
      const hint = document.getElementById("sd-folder-count");
      if (select && data.folders) {
        select.innerHTML = data.folders.map(f => {
          const isSelected = f.id === data.current ? "selected" : "";
          return `<option value="${f.id}" ${isSelected}>${f.name}</option>`;
        }).join("");
        if (hint) hint.textContent = `${data.folders.length} carpetas detectadas`;
      }
    }
  } catch (e) {
    console.error("Error loading folders:", e);
  }
}

function updatePhotoBadge(sourceType, label) {
  const iconEl = document.getElementById("hud-photo-icon");
  const labelEl = document.getElementById("hud-photo-label");
  if (!iconEl || !labelEl) return;

  if (sourceType === "online") {
    iconEl.innerHTML = SVG_PHOTO;
    labelEl.textContent = label || "Paisajes HD";
  } else if (sourceType === "sd") {
    iconEl.innerHTML = SVG_FOLDER;
    labelEl.textContent = label || "Fotos SD";
  } else if (sourceType === "fallback_offline") {
    iconEl.innerHTML = SVG_FOLDER;
    labelEl.textContent = "SD (Offline)";
  }
}

let currentSlideEl = null;
let nextSlideEl = null;
let isSlideTransitionInProgress = false;

function analyzeImageLuminance(img) {
  try {
    const cw = 48, ch = 48;
    const canvas = document.createElement("canvas");
    canvas.width = cw;
    canvas.height = ch;
    const ctx = canvas.getContext("2d", { willReadFrequently: true });
    if (!ctx) return { isBright: false, clockNeedsDark: false, globalLum: 100 };

    ctx.drawImage(img, 0, 0, cw, ch);
    const data = ctx.getImageData(0, 0, cw, ch).data;

    // 1. Overall global luminance (0..255)
    let totalLum = 0;
    const count = data.length / 4;
    for (let i = 0; i < data.length; i += 4) {
      totalLum += 0.2126 * data[i] + 0.7152 * data[i + 1] + 0.0722 * data[i + 2];
    }
    const globalAvgLum = totalLum / count;

    // 2. Bottom-left quadrant for clock/date contrast (x: 0..38%, y: 65%..98%)
    const rx = 0, ry = Math.floor(ch * 0.65);
    const rw = Math.floor(cw * 0.38), rh = Math.floor(ch * 0.33);
    const clockData = ctx.getImageData(rx, ry, rw, rh).data;
    let clockLum = 0;
    for (let i = 0; i < clockData.length; i += 4) {
      clockLum += 0.2126 * clockData[i] + 0.7152 * clockData[i + 1] + 0.0722 * clockData[i + 2];
    }
    const clockAvgLum = clockLum / (clockData.length / 4);

    return {
      isBright: globalAvgLum > 135,       // White fade threshold for luminous photos
      clockNeedsDark: clockAvgLum > 140, // Dark clock text threshold
      globalLum: globalAvgLum
    };
  } catch (e) {
    return { isBright: false, clockNeedsDark: false, globalLum: 100 };
  }
}

async function showNextSlide() {
  if (isSlideTransitionInProgress) return;
  let targetUrl = "";
  let isOnlineTarget = false;

  const isOnline = navigator.onLine;

  if (carouselMode === "online" && isOnline) {
    isOnlineTarget = true;
    const onlinePool = cachedOnlineLandscapes.length > 0 ? cachedOnlineLandscapes : ONLINE_LANDSCAPES;
    onlineIndex = (onlineIndex + 1) % onlinePool.length;
    targetUrl = onlinePool[onlineIndex];
  } else if (carouselMode === "sd" || !isOnline || sdPhotoList.length === 0) {
    isOnlineTarget = false;
    if (sdPhotoList.length > 0) {
      currentPhotoIndex = (currentPhotoIndex + 1) % sdPhotoList.length;
      targetUrl = sdPhotoList[currentPhotoIndex];
    } else if (ONLINE_LANDSCAPES.length > 0 && isOnline) {
      isOnlineTarget = true;
      targetUrl = ONLINE_LANDSCAPES[onlineIndex];
    }
  } else {
    // Mode 'mixed': alternate between online landscapes and SD card photos
    useOnlineForNext = !useOnlineForNext;
    if (useOnlineForNext && isOnline) {
      isOnlineTarget = true;
      onlineIndex = (onlineIndex + 1) % ONLINE_LANDSCAPES.length;
      targetUrl = ONLINE_LANDSCAPES[onlineIndex];
    } else {
      isOnlineTarget = false;
      currentPhotoIndex = (currentPhotoIndex + 1) % sdPhotoList.length;
      targetUrl = sdPhotoList[currentPhotoIndex];
    }
  }

  if (!targetUrl) return;

  const img = new Image();
  img.crossOrigin = "anonymous";
  let timedOut = false;
  const timeoutId = setTimeout(() => {
    timedOut = true;
    if (isOnlineTarget && sdPhotoList.length > 0) {
      const fallbackUrl = sdPhotoList[currentPhotoIndex % sdPhotoList.length];
      applySlideImage(fallbackUrl, "fallback_offline", { isBright: false, clockNeedsDark: false });
    }
  }, 10000);

  img.onload = async () => {
    if (timedOut) return;
    clearTimeout(timeoutId);
    try {
      if (img.decode) {
        await img.decode();
      }
    } catch (e) {}
    const analysis = analyzeImageLuminance(img);
    applySlideImage(targetUrl, isOnlineTarget ? "online" : "sd", analysis);
  };

  img.onerror = () => {
    if (timedOut) return;
    clearTimeout(timeoutId);
    if (sdPhotoList.length > 0) {
      const fallbackUrl = sdPhotoList[currentPhotoIndex % sdPhotoList.length];
      applySlideImage(fallbackUrl, "fallback_offline", { isBright: false, clockNeedsDark: false });
    }
  };

  img.src = targetUrl;
}

function applySlideImage(url, sourceBadge, analysis) {
  if (isSlideTransitionInProgress) return;
  isSlideTransitionInProgress = true;

  if (!currentSlideEl) currentSlideEl = document.getElementById("slide-current");
  if (!nextSlideEl) nextSlideEl = document.getElementById("slide-next");
  const container = document.getElementById("slideshow-container");
  const clockBlock = document.querySelector(".clock-container");

  const isBright = analysis ? Boolean(analysis.isBright) : false;

  // Stacking context: incoming slide is always physically on top of outgoing slide
  nextSlideEl.style.zIndex = "2";
  currentSlideEl.style.zIndex = "1";

  if (carouselTransition === "blur") {
    // === 🫧 Glassmorphism: Bokeh suave a Nitidez Absoluta (4.2s cinematográfico) ===
    if (container) container.style.backgroundColor = isBright ? "#1e293b" : "#020617";

    // 1. Pre-cargar imagen entrante con desenfoque cristalino y oculta
    nextSlideEl.style.transition = "none";
    nextSlideEl.style.filter = "blur(28px) brightness(1.12) saturate(1.2)";
    nextSlideEl.style.opacity = "0";
    nextSlideEl.style.backgroundImage = `url("${url}")`;
    void nextSlideEl.offsetWidth; // Forzar reflujo de GPU

    // 2. Imagen saliente se desenfoca progresivamente y se atenúa con calma (2.4s - 3.2s)
    currentSlideEl.style.transition = "filter 2.4s cubic-bezier(0.33, 1, 0.68, 1), opacity 3.2s cubic-bezier(0.33, 1, 0.68, 1)";
    currentSlideEl.style.filter = "blur(28px) brightness(1.08) saturate(1.15)";
    currentSlideEl.style.opacity = "0.15";

    // 3. A los 850ms, la imagen nueva florece pausadamente desde el cristal hacia foco total (2.8s)
    setTimeout(() => {
      if (clockBlock && analysis) {
        clockBlock.classList.toggle("clock-contrast-dark", analysis.clockNeedsDark);
      }
      updatePhotoBadge(sourceBadge);

      nextSlideEl.style.transition = "filter 2.8s cubic-bezier(0.16, 1, 0.3, 1), opacity 2.6s cubic-bezier(0.25, 1, 0.5, 1)";
      nextSlideEl.style.filter = "blur(0px) brightness(1) saturate(1)";
      nextSlideEl.style.opacity = "1";
    }, 850);

    // 4. Completar transición a los 4200ms, liberar textura anterior y alternar punteros
    setTimeout(() => {
      currentSlideEl.style.filter = "none";
      currentSlideEl.style.backgroundImage = "none";
      currentSlideEl.style.transition = "none";
      currentSlideEl.style.opacity = "0";
      currentSlideEl.style.zIndex = "0";

      nextSlideEl.style.filter = "none";
      nextSlideEl.style.zIndex = "1";

      const temp = currentSlideEl;
      currentSlideEl = nextSlideEl;
      nextSlideEl = temp;

      isSlideTransitionInProgress = false;
    }, 4200);

  } else {
    // === ✨ Fundidos Suaves: Dinámico, Fijo Negro, o Fijo Blanco (4.2s deleite visual) ===
    let fadeColor = "#020617";
    if (carouselTransition === "white") {
      fadeColor = "#ffffff";
    } else if (carouselTransition === "black") {
      fadeColor = "#000000";
    } else {
      // Dinámico (auto): fotos claras funden a blanco etéreo, fotos oscuras a negro noche
      fadeColor = isBright ? "#ffffff" : "#020617";
    }

    if (container) {
      container.style.backgroundColor = fadeColor;
    }

    // 1. Preparar slide entrante transparente y sin filtros
    nextSlideEl.style.transition = "none";
    nextSlideEl.style.filter = "none";
    nextSlideEl.style.opacity = "0";
    nextSlideEl.style.backgroundImage = `url("${url}")`;
    void nextSlideEl.offsetWidth; // Forzar reflujo

    // 2. Imagen saliente se disuelve progresivamente (2.8s pausado)
    currentSlideEl.style.filter = "none";
    currentSlideEl.style.transition = "opacity 2.8s cubic-bezier(0.33, 1, 0.68, 1)";
    currentSlideEl.style.opacity = "0";

    // 3. A los 800ms, la imagen entrante emerge en fundido cruzado solapado (2.8s)
    setTimeout(() => {
      if (clockBlock && analysis) {
        clockBlock.classList.toggle("clock-contrast-dark", analysis.clockNeedsDark);
      }
      updatePhotoBadge(sourceBadge);

      nextSlideEl.style.transition = "opacity 2.8s cubic-bezier(0.2, 0.8, 0.2, 1)";
      nextSlideEl.style.opacity = "1";
    }, 800);

    // 4. Completar transición a los 4200ms y alternar punteros limpiamente
    setTimeout(() => {
      currentSlideEl.style.backgroundImage = "none";
      currentSlideEl.style.transition = "none";
      currentSlideEl.style.opacity = "0";
      currentSlideEl.style.zIndex = "0";

      nextSlideEl.style.zIndex = "1";

      const temp = currentSlideEl;
      currentSlideEl = nextSlideEl;
      nextSlideEl = temp;

      isSlideTransitionInProgress = false;
    }, 4200);
  }
}

let slideIntervalSec = parseInt(localStorage.getItem("domos_slide_interval_sec") || "60", 10) || 60;
function startSlideshow() {
  if (slideInterval) clearInterval(slideInterval);
  slideInterval = setInterval(showNextSlide, Math.max(10, slideIntervalSec) * 1000);
}

// Wire Folder Selector & Carousel Mode Selector
document.getElementById("photo-folder-select")?.addEventListener("change", async (e) => {
  const folder = e.target.value;
  try {
    await fetch("/api/photos/folder", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ folder: folder })
    });
    loadPhotos();
  } catch (err) {
    console.error("Error changing folder:", err);
  }
});

const carouselSelect = document.getElementById("carousel-mode-select");
if (carouselSelect) {
  carouselSelect.value = carouselMode;
  carouselSelect.addEventListener("change", (e) => {
    carouselMode = e.target.value;
    localStorage.setItem("domos_carousel_mode", carouselMode);
    fetch("/api/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ carousel_mode: carouselMode })
    }).catch(() => {});
    showNextSlide();
    startSlideshow();
  });
}

loadFolders();
loadPhotos();

// ========================================================
// 6. MINIMALIST LIQUID GLASS ASSISTANT OVERLAY (DOMOS AI)
// ========================================================
const assistantOverlay = document.getElementById("assistant-overlay");
const assistantOrb = document.getElementById("assistant-orb");
const assistantStateTag = document.getElementById("assistant-state-tag");
const assistantPrompt = document.getElementById("assistant-prompt");
const assistantReply = document.getElementById("assistant-reply");
let assistantResetTimer = null;

function showAssistant(state, promptText, replyText) {
  if (assistantResetTimer) clearTimeout(assistantResetTimer);

  if (!assistantOverlay) return;
  assistantOverlay.classList.remove("hidden-assistant");

  // State: "listening" | "processing" | "speaking"
  if (assistantOrb) {
    assistantOrb.className = `assistant-orb state-${state}`;
  }

  if (assistantStateTag) {
    if (state === "listening") {
      assistantStateTag.textContent = "Escuchando";
      assistantStateTag.style.background = "rgba(0, 229, 255, 0.15)";
      assistantStateTag.style.color = "var(--neon-cyan)";
    } else if (state === "processing") {
      assistantStateTag.textContent = "Procesando";
      assistantStateTag.style.background = "rgba(255, 179, 0, 0.15)";
      assistantStateTag.style.color = "var(--neon-amber)";
    } else if (state === "speaking") {
      assistantStateTag.textContent = "Respuesta";
      assistantStateTag.style.background = "rgba(0, 230, 118, 0.15)";
      assistantStateTag.style.color = "var(--neon-emerald)";
    }
  }

  if (promptText && assistantPrompt) {
    assistantPrompt.textContent = promptText;
  }
  if (replyText && assistantReply) {
    assistantReply.textContent = replyText;
  }
}

function hideAssistant() {
  if (assistantOverlay) {
    assistantOverlay.classList.add("hidden-assistant");
  }
}

document.getElementById("assistant-close-btn")?.addEventListener("click", hideAssistant);

// Real Voice Listening Prompt (no simulated demo command)
function triggerAssistantDemo() {
  fetch("/api/voice/arm", { method: "POST" }).catch(() => {});
  showAssistant("listening", 'Escuchando orden directa...', 'Di por ejemplo: "Enciende cocina 1"');
  if (assistantResetTimer) clearTimeout(assistantResetTimer);
  assistantResetTimer = setTimeout(hideAssistant, 9000);
}

document.getElementById("dock-mic-btn")?.addEventListener("click", triggerAssistantDemo);
document.getElementById("btn-test-assistant")?.addEventListener("click", () => {
  closeDrawer();
  triggerAssistantDemo();
});

// ========================================================
// 7. REAL TUYA DEVICE SERVICE, EDITABLE VISIBILITY & RENDERING
// ========================================================
let isEditMode = false;
let hiddenDevices = new Set(JSON.parse(localStorage.getItem("domos_hidden_devices") || "[]"));

function isDeviceHidden(devId) {
  return hiddenDevices.has(devId);
}

function saveHiddenDevicesToServer() {
  const arr = Array.from(hiddenDevices);
  localStorage.setItem("domos_hidden_devices", JSON.stringify(arr));
  fetch("/api/config", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ hidden_devices: arr })
  }).catch(() => {});
}

let _lastVisToggleId = null;
let _lastVisToggleTs = 0;
function toggleDeviceVisibility(devId) {
  if (!devId) return;
  const now = Date.now();
  if (_lastVisToggleId === devId && (now - _lastVisToggleTs) < 400) return;
  _lastVisToggleId = devId;
  _lastVisToggleTs = now;
  if (hiddenDevices.has(devId)) {
    hiddenDevices.delete(devId);
  } else {
    hiddenDevices.add(devId);
  }
  saveHiddenDevicesToServer();
  renderAllDevices(true);
}

const DEFAULT_ROOMS = [
  { id: "cocina", icon: "🍳", label: "Cocina", builtin: true },
  { id: "salon", icon: "🛋️", label: "Salón", builtin: true },
  { id: "habitaciones", icon: "🛏️", label: "Habitaciones y Baño", builtin: true },
  { id: "exterior", icon: "🌿", label: "Exterior y Otros", builtin: true }
];

let customRooms = JSON.parse(localStorage.getItem("domos_custom_rooms") || "[]");
let layoutMode = localStorage.getItem("domos_layout_mode") || "rooms";
let deviceRooms = JSON.parse(localStorage.getItem("domos_device_rooms") || "{}");
let deviceOrder = JSON.parse(localStorage.getItem("domos_device_order") || "[]");
let favoriteDevices = new Set(JSON.parse(localStorage.getItem("domos_favorite_devices") || "[]"));


function isDeviceFavorite(devId) {
  return favoriteDevices.has(devId);
}

function toggleDeviceFavorite(devId) {
  if (!devId) return;
  if (favoriteDevices.has(devId)) {
    favoriteDevices.delete(devId);
  } else {
    favoriteDevices.add(devId);
  }
  const arr = Array.from(favoriteDevices);
  localStorage.setItem("domos_favorite_devices", JSON.stringify(arr));
  fetch("/api/config", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ favorite_devices: arr })
  }).catch(() => {});
  renderAllDevices(true);
}

function getAllRooms() {
  return [...DEFAULT_ROOMS, ...(Array.isArray(customRooms) ? customRooms : [])];
}

function saveCustomRooms() {
  localStorage.setItem("domos_custom_rooms", JSON.stringify(customRooms));
  fetch("/api/config", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ custom_rooms: customRooms })
  }).catch(() => {});
}

function addCustomRoom(label, icon = "🏠") {
  const clean = (label || "").trim();
  if (!clean) return;
  const slug = "zone_" + clean.toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_|_$/g, "") + "_" + Date.now().toString(36).slice(-4);
  customRooms.push({ id: slug, icon: icon || "🏠", label: clean, builtin: false });
  saveCustomRooms();
  renderCustomRoomsList();
  renderAllDevices(true);
}

function deleteCustomRoom(roomId) {
  customRooms = customRooms.filter(r => r.id !== roomId);
  Object.keys(deviceRooms).forEach(devId => {
    if (deviceRooms[devId] === roomId) delete deviceRooms[devId];
  });
  localStorage.setItem("domos_device_rooms", JSON.stringify(deviceRooms));
  saveCustomRooms();
  fetch("/api/config", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ device_rooms: deviceRooms })
  }).catch(() => {});
  renderCustomRoomsList();
  renderAllDevices(true);
}

function renderCustomRoomsList() {
  const el = document.getElementById("custom-rooms-list");
  if (!el) return;
  el.innerHTML = getAllRooms().map(r => `
    <span class="custom-room-chip">
      <span>${r.icon}</span>
      <span>${r.label}</span>
      ${r.builtin ? "" : `<button type="button" class="custom-room-del-btn" data-roomid="${r.id}" title="Eliminar zona">×</button>`}
    </span>
  `).join("");
  el.querySelectorAll(".custom-room-del-btn").forEach(btn => {
    btn.addEventListener("click", () => deleteCustomRoom(btn.getAttribute("data-roomid")));
  });
}

function sortByDeviceOrder(items) {
  if (!Array.isArray(deviceOrder) || deviceOrder.length === 0) return items;
  const rank = new Map(deviceOrder.map((id, idx) => [id, idx]));
  return [...items].sort((a, b) => {
    const idA = a.dev ? a.dev.id : a.id;
    const idB = b.dev ? b.dev.id : b.id;
    const rA = rank.has(idA) ? rank.get(idA) : 99999;
    const rB = rank.has(idB) ? rank.get(idB) : 99999;
    return rA - rB;
  });
}

function moveDeviceOrder(devId, delta, scopeIds) {
  if (!devId || !Array.isArray(scopeIds) || scopeIds.length < 2) return;
  scopeIds.forEach(id => {
    if (!deviceOrder.includes(id)) deviceOrder.push(id);
  });
  const idxInScope = scopeIds.indexOf(devId);
  const targetIdxInScope = idxInScope + delta;
  if (idxInScope < 0 || targetIdxInScope < 0 || targetIdxInScope >= scopeIds.length) return;
  const swapId = scopeIds[targetIdxInScope];
  const i1 = deviceOrder.indexOf(devId);
  const i2 = deviceOrder.indexOf(swapId);
  if (i1 >= 0 && i2 >= 0) {
    deviceOrder[i1] = swapId;
    deviceOrder[i2] = devId;
    localStorage.setItem("domos_device_order", JSON.stringify(deviceOrder));
    fetch("/api/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ device_order: deviceOrder })
    }).catch(() => {});
    renderAllDevices(true);
  }
}

function getDefaultRoomForDevice(dev) {
  const n = ((dev?.name || "") + " " + (dev?.type || "") + " " + (dev?.kind || "")).toLowerCase();
  if (n.includes("cocina") || n.includes("termo") || n.includes("aspiradora") || n.includes("vacuum")) return "cocina";
  if (n.includes("salón") || n.includes("salon") || n.includes("aire acondicionado") || n.includes("tv") || n.includes("ir") || n.includes("purificador") || n.includes("purifier") || n.includes("deshumidificador") || n.includes("regleta")) return "salon";
  if (n.includes("habitación") || n.includes("habitacion") || n.includes("secatoallas") || n.includes("baño") || n.includes("bano")) return "habitaciones";
  return "exterior";
}

function getDeviceRoom(dev) {
  if (!dev || !dev.id) return "exterior";
  const assigned = deviceRooms[dev.id];
  if (assigned && getAllRooms().some(r => r.id === assigned)) return assigned;
  return getDefaultRoomForDevice(dev);
}

function setDeviceRoom(devId, roomId) {
  if (!devId || !getAllRooms().some(r => r.id === roomId)) return;
  deviceRooms[devId] = roomId;
  localStorage.setItem("domos_device_rooms", JSON.stringify(deviceRooms));
  fetch("/api/config", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ device_rooms: deviceRooms })
  }).catch(() => {});
  renderAllDevices(true);
}

function updateLayoutPresetButtons() {
  document.querySelectorAll(".layout-preset-btn").forEach(btn => {
    btn.classList.toggle("active", btn.getAttribute("data-layout") === layoutMode);
  });
}

function setLayoutMode(mode) {
  if (!["rooms", "type", "compact"].includes(mode)) return;
  layoutMode = mode;
  localStorage.setItem("domos_layout_mode", layoutMode);
  updateLayoutPresetButtons();
  fetch("/api/config", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ layout_mode: layoutMode })
  }).catch(() => {});
  renderAllDevices(true);
}

function getEditBadgeHtml(devId, devObj = null, showRoomSelect = true) {
  if (!isEditMode) return "";
  const hidden = isDeviceHidden(devId);
  const visBadge = hidden
    ? `<div class="visibility-toggle-badge vis-hidden"><span>🚫</span> Oculto</div>`
    : `<div class="visibility-toggle-badge vis-shown"><span>👁️</span> Visible</div>`;
  let roomSelectHtml = "";
  const moveBtnsHtml = `<button type="button" class="edit-move-btn" data-devid="${devId}" data-delta="-1" title="Mover antes">◀</button><button type="button" class="edit-move-btn" data-devid="${devId}" data-delta="1" title="Mover después">▶</button>`;
  if (showRoomSelect) {
    const currentRoom = getDeviceRoom(devObj || { id: devId });
    roomSelectHtml = `<select class="edit-room-select" data-devid="${devId}" title="Mover a habitación">${getAllRooms().map(r => `<option value="${r.id}" ${r.id === currentRoom ? "selected" : ""}>${r.icon} ${r.label}</option>`).join("")}</select>`;
  }
  const isFav = isDeviceFavorite(devId);
  const favBtnHtml = `<button type="button" class="edit-fav-btn ${isFav ? "is-fav" : ""}" data-devid="${devId}" title="${isFav ? "Quitar de Favoritos" : "Añadir a Favoritos"}">${isFav ? "★" : "☆"}</button>`;
  return `<div class="edit-card-toolbar">${favBtnHtml}${moveBtnsHtml}${roomSelectHtml}${visBadge}</div>`;
}

function setEditMode(enabled) {
  isEditMode = Boolean(enabled);
  const drawerEl = document.getElementById("controls-drawer");
  const bannerEl = document.getElementById("edit-mode-banner");
  const btnEdit = document.getElementById("btn-edit-controls");
  const btnIcon = document.getElementById("btn-edit-controls-icon");
  const btnLabel = document.getElementById("btn-edit-controls-label");

  if (drawerEl) drawerEl.classList.toggle("is-editing-dashboard", isEditMode);
  if (bannerEl) bannerEl.classList.toggle("hidden", !isEditMode);
  if (btnEdit) btnEdit.classList.toggle("active", isEditMode);
  if (btnIcon) btnIcon.textContent = isEditMode ? "✅" : "✏️";
  if (btnLabel) btnLabel.textContent = isEditMode ? "Guardar Vista" : "Editar Vista";

  renderAllDevices(true);
}

function hideInactiveDevices() {
  // Hide lights that are currently off
  (deviceData.lights || []).forEach(l => {
    if (!Boolean(l.state?.state)) hiddenDevices.add(l.id);
  });
  // Hide plugs that are currently off
  (deviceData.plugs || []).forEach(p => {
    if (!Boolean(p.state?.state)) hiddenDevices.add(p.id);
  });
  // Hide climate sensors without valid temperature
  (deviceData.climate || []).forEach(c => {
    const cid = c.id || ("climate_" + c.name);
    const t = c.state?.temperature;
    if (t === undefined || t === null || t === "--") hiddenDevices.add(cid);
  });
  saveHiddenDevicesToServer();
  renderAllDevices(true);
}

function showAllDevices() {
  hiddenDevices.clear();
  saveHiddenDevicesToServer();
  renderAllDevices(true);
}

document.getElementById("btn-edit-controls")?.addEventListener("click", () => {
  setEditMode(!isEditMode);
});
document.getElementById("btn-finish-edit")?.addEventListener("click", () => {
  setEditMode(false);
});
document.getElementById("btn-hide-inactive")?.addEventListener("click", () => {
  hideInactiveDevices();
});
document.getElementById("btn-show-all-controls")?.addEventListener("click", () => {
  showAllDevices();
});

async function fetchDevices() {
  try {
    const res = await fetch("/api/devices");
    if (res.ok) {
      deviceData = await res.json();
      renderAllDevices();
    }
  } catch (e) {
    console.error("Error fetching devices:", e);
  }
}

function getAllControllableIds() {
  const defaultCams = [
    "bf77eed8534deaf66f2xpj",
    "bf88224fd128fceb4b5vd4",
    "bfce70c5e1e7475542tezv"
  ];
  const camIds = (deviceData.cameras && deviceData.cameras.length > 0)
    ? deviceData.cameras.map(c => c.id)
    : defaultCams;
  const lightIds = (deviceData.lights || []).map(l => l.id);
  const plugIds = (deviceData.plugs || []).map(p => p.id);
  const climateIds = (deviceData.climate || []).map(c => c.id || ("climate_" + c.name));
  const energyIds = ["energy_solar", "energy_battery_20v"];
  const securityIds = ["security_alarm", "security_door"];
  return [...camIds, ...lightIds, ...plugIds, ...climateIds, ...energyIds, ...securityIds];
}

function updateVisibilityCounters() {
  const allIds = getAllControllableIds();
  const totalCount = allIds.length;
  const hiddenCount = allIds.filter(id => hiddenDevices.has(id)).length;
  const visibleCount = Math.max(0, totalCount - hiddenCount);

  const countBadge = document.getElementById("devices-badge-count");
  if (countBadge) {
    if (hiddenCount > 0) {
      countBadge.textContent = `${visibleCount} CONTROLES VISIBLES · ${hiddenCount} OCULTOS`;
    } else {
      countBadge.textContent = `${totalCount} CONTROLES ACTIVOS`;
    }
  }

  const editCounter = document.getElementById("edit-visibility-counter");
  if (editCounter) {
    editCounter.textContent = `${visibleCount} visibles · ${hiddenCount} ocultos`;
  }
}

function renderAllDevices(forceCameraRender = false) {
  renderHudIndicators();
  renderCamerasGrid(forceCameraRender);
  renderClimateGrid();
  renderEnergyGrid();
  renderSecurityGrid();
  renderControlViews();
  updateVisibilityCounters();
}

function renderHudIndicators() {
  // 1. Solar
  const solarWatts = deviceData.solar?.state?.watts ?? "--";
  const solarEl = document.getElementById("hud-solar-val");
  if (solarEl) solarEl.textContent = `${solarWatts} W`;

  const solarBadge = document.getElementById("hud-solar-badge");
  if (solarBadge) {
    const isGenerating = typeof solarWatts === "number" && solarWatts > 0;
    solarBadge.textContent = isGenerating ? "Generando" : "Standby";
    solarBadge.style.color = isGenerating ? "#10b981" : "#f59e0b";
  }

  // 2. Security Alarm
  const alarmState = deviceData.security?.alarm?.state?.master_mode ?? "disarmed";
  const alarmTextEl = document.getElementById("hud-alarm-text");
  const alarmPillEl = document.getElementById("hud-alarm-pill");
  if (alarmTextEl && alarmPillEl) {
    if (alarmState === "disarmed") {
      alarmTextEl.textContent = "Desarmada";
      const aEl = document.getElementById("hud-alarm-icon"); if (aEl) { aEl.className = 'neon-svg neon-emerald'; aEl.innerHTML = SVG_SHIELD_OK; }
    } else {
      alarmTextEl.textContent = alarmState === "arm" ? "ARMADA" : "En Casa";
      const aEl = document.getElementById("hud-alarm-icon"); if (aEl) { aEl.className = 'neon-svg neon-coral'; aEl.innerHTML = SVG_SHIELD_ALERT; }
    }
  }

  // 3. Door Contact
  const doorOpen = deviceData.security?.door?.state?.is_open ?? false;
  const doorTextEl = document.getElementById("hud-door-text");
  if (doorTextEl) {
    doorTextEl.textContent = doorOpen ? "¡ABIERTA!" : "Cerrada";
    const dEl = document.getElementById("hud-door-icon"); if (dEl) { dEl.className = doorOpen ? 'neon-svg neon-coral' : 'neon-svg neon-emerald'; dEl.innerHTML = doorOpen ? SVG_DOOR_OPEN : SVG_DOOR_CLOSED; }
  }

  // 4. Bottom Dock: Quick Lights & Climate
  const light1 = deviceData.lights?.find(l => l.id === "bf9abfe1a19f35a05ceej0");
  const light2 = deviceData.lights?.find(l => l.id === "bf873ba4935f6abf954qsp");
  const dockBtn1 = document.getElementById("dock-light-1");
  const dockBtn2 = document.getElementById("dock-light-2");

  if (dockBtn1 && light1) {
    dockBtn1.classList.toggle("is-on", Boolean(light1.state?.state));
  }
  if (dockBtn2 && light2) {
    dockBtn2.classList.toggle("is-on", Boolean(light2.state?.state));
  }

  // 5. Update HUD Telemetry Widgets: Clima Interior & Calidad de Aire
  const climGrid = document.getElementById("hud-climate-rooms-grid");
  const avgBadge = document.getElementById("hud-climate-avg-badge");
  
  const allClim = [...(deviceData.climate || [])];
  const purDev = (deviceData.xiaomi || []).find(d => d.kind === "purifier");
  if (purDev && purDev.state && purDev.state.temperature !== undefined) {
    allClim.push({
      id: "purifier_climate",
      name: "Purificador",
      state: {
        temperature: purDev.state.temperature,
        humidity: purDev.state.humidity
      }
    });
  }

  if (climGrid && allClim.length > 0) {
    let sumT = 0;
    let countT = 0;
    climGrid.innerHTML = allClim.map(c => {
      const room = (c.name || "Sensor").replace(/^(Higr[oó]metro|Sensor\s*Aire)\s*/i, "").trim() || c.name;
      const t = c.state?.temperature;
      const h = c.state?.humidity;
      if (typeof t === "number") {
        sumT += t;
        countT++;
      }
      const tStr = t !== undefined ? `${t}°C` : "--°C";
      const hStr = h !== undefined ? `${h}%` : "--%";
      const icon = room.toLowerCase().includes("sótano") ? "🌬️" : (room.toLowerCase().includes("purif") ? "🌀" : (room.toLowerCase().includes("dorm") ? "🛏️" : "🛋️"));
      return `
        <div class="hud-room-item" title="${c.name}: ${tStr} · ${hStr}">
          <span class="hud-room-name">${icon} ${room}</span>
          <span class="hud-room-val">${tStr} <span class="hud-hum-pill">💧 ${hStr}</span></span>
        </div>
      `;
    }).join("");

    if (avgBadge && countT > 0) {
      avgBadge.textContent = `Media: ${(sumT / countT).toFixed(1)}°C`;
    }
  }

  updateIndoorAirHud();
}

// Render Cameras Section (Videoportero, Pasillo, Sótano Impresora 3D, etc.)
function renderCamerasGrid(forceRender = false) {
  const container = document.getElementById("cameras-grid");
  const sectionEl = document.getElementById("section-cameras");
  if (!container) return;

  // Preserve live stream playback when background polling syncs devices (unless toggling Edit Mode)
  if (!forceRender && !isEditMode && typeof activeCameraStreams !== 'undefined' && Object.keys(activeCameraStreams).length > 0) {
    return;
  }

  const defaultCams = [
    {
      id: "bf77eed8534deaf66f2xpj",
      name: "Videoportero Exterior",
      location: "Entrada Principal",
      online: true
    },
    {
      id: "bf88224fd128fceb4b5vd4",
      name: "Cámara Sótano (Impresora 3D)",
      location: "Sótano / Impresora 3D",
      online: true
    },
    {
      id: "bfce70c5e1e7475542tezv",
      name: "Cámara Pasillo",
      location: "Pasillo Principal",
      online: true
    }
  ];

  const allCams = (deviceData.cameras && deviceData.cameras.length > 0) ? deviceData.cameras : defaultCams;
  const cams = isEditMode ? allCams : allCams.filter(c => !isDeviceHidden(c.id));

  if (sectionEl) {
    sectionEl.style.display = (cams.length === 0 && !isEditMode) ? "none" : "";
  }

  container.innerHTML = cams.map(cam => {
    const hiddenClass = (isEditMode && isDeviceHidden(cam.id)) ? "control-hidden-in-edit" : "";
    return `
      <div class="camera-card ${hiddenClass}" data-camid="${cam.id}" data-devid="${cam.id}">
        ${getEditBadgeHtml(cam.id)}
        <div class="camera-viewport" onclick="if(!isEditMode) openCameraFullscreen('${cam.id}', '${cam.name.replace(/'/g, "\\'")}', false)" style="cursor:pointer;" title="Pulsa para pantalla completa">
          <div class="camera-scanline"></div>
          <div class="camera-live-badge">
            <span class="live-dot"></span>
            <span>EN DIRECTO</span>
          </div>
          <div class="camera-loc-badge">${cam.location}</div>
          
          <div class="camera-placeholder-screen" id="cam-screen-${cam.id}">
            <svg viewBox="0 0 24 24" width="44" height="44" fill="var(--neon-cyan)">
              <path d="M17 10.5V7c0-.55-.45-1-1-1H4c-.55 0-1 .45-1 1v10c0 .55.45 1 1 1h12c.55 0 1-.45 1-1v-3.5l4 4v-11l-4 4z"/>
            </svg>
            <p><strong>${cam.name}</strong> · Visión Nocturna HD</p>
            <span style="font-size: 0.75rem; color: var(--text-muted);">Sensor Tuya P2P Conectado</span>
          </div>
        </div>
        <div class="camera-footer">
          <div class="camera-info">
            <h4>${cam.name}</h4>
            <span class="camera-status-text">Sensor PIR de Movimiento Activo</span>
          </div>
          <button class="camera-action-btn" id="cam-btn-${cam.id}" onclick="if(!isEditMode) requestCameraLive('${cam.id}')">
            <span>▶</span> Conectar Stream
          </button>
        </div>
      </div>
    `;
  }).join("");

  if (isEditMode) {
    container.querySelectorAll(".camera-card").forEach(card => {
      card.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();
        toggleDeviceVisibility(card.getAttribute("data-devid"));
      });
    });
  }
}

const activeCameraStreams = {};
window.connectAllCameras = function() {
  if (isEditMode) return;
  const defaultCams = ["bf77eed8534deaf66f2xpj", "bf88224fd128fceb4b5vd4", "bfce70c5e1e7475542tezv", "bf7b5ccc66a5c47cbfdkew", "bf4c6936a402c805cfjjae"];
  const allCams = (deviceData.cameras && deviceData.cameras.length > 0) ? deviceData.cameras.map(c => c.id) : defaultCams;
  const cams = allCams.filter(id => !isDeviceHidden(id));
  cams.forEach((id, idx) => {
    setTimeout(() => {
      window.requestCameraLive(id);
    }, idx * 600);
  });
};

window.stopAllCameras = function() {
  Object.keys(activeCameraStreams).forEach(id => {
    window.stopCameraLive(id);
  });
};



// --- Shared Low-Latency WebRTC / HLS Stream Attacher ---
function attachHlsStream(videoEl, url) {
  if (window.Hls && Hls.isSupported()) {
    const hls = new Hls({
      enableWorker: true,
      lowLatencyMode: false,
      liveSyncDurationCount: 1,
      liveMaxLatencyDurationCount: 3,
      maxLiveSyncPlaybackRate: 1.15,
      maxBufferLength: 8,
      manifestLoadingTimeOut: 15000
    });
    hls.loadSource(url);
    hls.attachMedia(videoEl);
    hls.on(Hls.Events.MANIFEST_PARSED, () => {
      videoEl.play().catch(() => {
        videoEl.muted = true;
        videoEl.play().catch(() => {});
      });
    });
    hls.on(Hls.Events.ERROR, (event, errData) => {
      if (errData.fatal) {
        if (errData.type === Hls.ErrorTypes.NETWORK_ERROR) hls.startLoad();
        else if (errData.type === Hls.ErrorTypes.MEDIA_ERROR) hls.recoverMediaError();
      }
    });
    return {
      mode: "hls",
      destroy: () => {
        try { hls.destroy(); } catch (e) {}
      }
    };
  } else if (videoEl.canPlayType("application/vnd.apple.mpegurl")) {
    videoEl.src = url;
    videoEl.play().catch(() => {
      videoEl.muted = true;
      videoEl.play().catch(() => {});
    });
    return {
      mode: "native-hls",
      destroy: () => {
        try { videoEl.pause(); videoEl.removeAttribute("src"); videoEl.load(); } catch (e) {}
      }
    };
  }
  return { mode: "none", destroy: () => {} };
}

async function attachLiveStream(videoEl, camId, streamData) {
  let activeHlsController = null;
  let isHlsActive = false;

  const fallbackToHls = async () => {
    if (isHlsActive) return;
    isHlsActive = true;
    try { videoEl.srcObject = null; } catch (e) {}
    try {
      const fbRes = await fetch("/api/camera/stream/" + camId + "?force_hls=1");
      const fbData = await fbRes.json();
      if (fbData && fbData.success && fbData.url) {
        activeHlsController = attachHlsStream(videoEl, fbData.url);
      }
    } catch (e) {
      console.error("[HLS Fallback Error]", camId, e);
    }
  };

  if (streamData && streamData.mode === "webrtc" && streamData.webrtc_url && window.RTCPeerConnection) {
    try {
      const pc = new RTCPeerConnection({
        iceServers: [
          { urls: ["stun:stun.cloudflare.com:3478", "stun:stun.l.google.com:19302"] }
        ]
      });
      const mediaStream = new MediaStream();

      pc.ontrack = (ev) => {
        if (ev.streams && ev.streams[0]) {
          videoEl.srcObject = ev.streams[0];
        } else if (ev.track) {
          if (!mediaStream.getTracks().some(t => t.id === ev.track.id)) {
            mediaStream.addTrack(ev.track);
          }
          videoEl.srcObject = mediaStream;
        }
        videoEl.play().catch(() => {
          videoEl.muted = true;
          videoEl.play().catch(() => {});
        });
      };

      pc.addTransceiver("video", { direction: "recvonly" });
      pc.addTransceiver("audio", { direction: "recvonly" });

      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);

      await new Promise((resolve) => {
        if (pc.iceGatheringState === "complete") return resolve();
        const t = setTimeout(resolve, 600);
        pc.onicegatheringstatechange = () => {
          if (pc.iceGatheringState === "complete") {
            clearTimeout(t);
            resolve();
          }
        };
      });

      const resp = await fetch(streamData.webrtc_url, {
        method: "POST",
        headers: { "Content-Type": "application/sdp" },
        body: pc.localDescription.sdp,
      });

      if (!resp.ok) throw new Error("WebRTC SDP HTTP " + resp.status);
      const answerSdp = await resp.text();
      await pc.setRemoteDescription({ type: "answer", sdp: answerSdp });

      // Watchdog: If no frames within 4.5s or if ICE fails, fall back to HLS
      const watchdog = setTimeout(() => {
        if (!isHlsActive && videoEl.videoWidth === 0) {
          console.warn("[WebRTC Watchdog] No video frames for " + camId + ", switching to HLS...");
          try { pc.close(); } catch (e) {}
          fallbackToHls();
        }
      }, 4500);

      pc.oniceconnectionstatechange = () => {
        if (pc.iceConnectionState === "failed" || pc.iceConnectionState === "disconnected") {
          clearTimeout(watchdog);
          console.warn("[WebRTC ICE " + pc.iceConnectionState + "] Switching to HLS for " + camId);
          try { pc.close(); } catch (e) {}
          fallbackToHls();
        }
      };

      return {
        mode: "webrtc",
        destroy: () => {
          clearTimeout(watchdog);
          try { pc.close(); } catch (e) {}
          try { videoEl.srcObject = null; } catch (e) {}
          if (activeHlsController) activeHlsController.destroy();
        }
      };
    } catch (err) {
      console.warn("WebRTC falló, usando HLS de respaldo:", err);
      try { videoEl.srcObject = null; } catch (e) {}
      await fallbackToHls();
      return {
        mode: "hls-fallback",
        destroy: () => {
          if (activeHlsController) activeHlsController.destroy();
        }
      };
    }
  }

  const url = streamData && streamData.url;
  if (!url) throw new Error("Sin URL de streaming");
  return attachHlsStream(videoEl, url);
}

window.stopCameraLive = function(camId) {
  if (activeCameraStreams[camId]) {
    try {
      activeCameraStreams[camId].destroy();
    } catch (e) {}
    delete activeCameraStreams[camId];
  }
  const screenEl = document.getElementById("cam-screen-" + camId);
  const btnEl = document.getElementById("cam-btn-" + camId);
  if (btnEl) {
    btnEl.innerHTML = "<span>▶</span> Conectar Stream";
    btnEl.onclick = () => window.requestCameraLive(camId);
  }
  if (screenEl) {
    screenEl.innerHTML = `
      <svg viewBox="0 0 24 24" width="44" height="44" fill="var(--neon-cyan)">
        <path d="M17 10.5V7c0-.55-.45-1-1-1H4c-.55 0-1 .45-1 1v10c0 .55.45 1 1 1h12c.55 0 1-.45 1-1v-3.5l4 4v-11l-4 4z"/>
      </svg>
      <p>Stream en pausa</p>
      <span style="font-size: 0.75rem; color: var(--text-muted);">Pulsa Conectar para reanudar</span>
    `;
  }
};

window.requestCameraLive = async function(camId) {
  if (isEditMode) return;
  const screenEl = document.getElementById("cam-screen-" + camId);
  const btnEl = document.getElementById("cam-btn-" + camId);
  if (btnEl) {
    btnEl.innerHTML = "<span>⏳</span> Conectando...";
  }
  if (screenEl) {
    screenEl.innerHTML = `
      <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; gap:8px; height:100%;">
        <div style="width:28px; height:28px; border:2px solid var(--neon-cyan); border-top-color:transparent; border-radius:50%; animation: spin 0.8s linear infinite;"></div>
        <p style="color: var(--neon-cyan); font-size:0.85rem; margin:0;">Iniciando streaming en directo...</p>
      </div>
    `;
  }
  try {
    const res = await fetch("/api/camera/stream/" + camId);
    const data = await res.json();
    if (data.success && (data.webrtc_url || data.url)) {
      if (screenEl) {
        screenEl.innerHTML = `
          <video id="video-` + camId + `" autoplay playsinline muted style="width:100%; height:100%; object-fit: cover; background: #000; border-radius: 12px; pointer-events: none;"></video>
        `;
        const video = document.getElementById("video-" + camId);
        activeCameraStreams[camId] = await attachLiveStream(video, camId, data);
        if (btnEl) {
          btnEl.innerHTML = "<span>⏹</span> Detener Stream";
          btnEl.onclick = () => window.stopCameraLive(camId);
        }
      }
    } else {
      if (screenEl) {
        screenEl.innerHTML = `
          <p style="color: var(--neon-amber); margin-bottom:4px;"><strong>Cámara en Espera</strong></p>
          <span style="font-size: 0.72rem; color: var(--text-secondary); max-width: 260px;">
            ${data.msg || "No se pudo iniciar el flujo en vivo."}
          </span>
        `;
      }
      if (btnEl) {
        btnEl.innerHTML = "<span>▶</span> Reintentar";
      }
    }
  } catch (e) {
    console.error("Camera stream error:", e);
    if (screenEl) {
      screenEl.innerHTML = "<p style=\"color: var(--neon-amber);\">Error al conectar stream</p>";
    }
    if (btnEl) {
      btnEl.innerHTML = "<span>▶</span> Conectar Stream";
    }
  }
};

function renderLightsGrid() {
  const container = document.getElementById("lights-grid");
  const sectionEl = document.getElementById("section-lights");
  if (!container || !deviceData.lights) return;

  const allLights = deviceData.lights;
  const lights = isEditMode ? allLights : allLights.filter(l => !isDeviceHidden(l.id));

  if (sectionEl) {
    sectionEl.style.display = (lights.length === 0 && !isEditMode) ? "none" : "";
  }

  container.innerHTML = lights.map(light => {
    const isOn = Boolean(light.state?.state);
    const hiddenClass = (isEditMode && isDeviceHidden(light.id)) ? "control-hidden-in-edit" : "";
    return `
      <div class="liquid-card ${isOn ? 'is-on' : ''} ${hiddenClass}" data-devid="${light.id}" data-category="light">
        ${getEditBadgeHtml(light.id)}
        <div class="card-top">
          <div class="card-icon-bubble">💡</div>
          <div class="liquid-switch ${isOn ? 'on' : ''}"></div>
        </div>
        <div class="card-title-group">
          <h4>${light.name}</h4>
          <span class="card-subtitle">${isOn ? 'ENCENDIDA' : 'Apagada'}</span>
        </div>
      </div>
    `;
  }).join("");

  container.querySelectorAll(".liquid-card").forEach(card => {
    card.addEventListener("click", () => {
      const devId = card.getAttribute("data-devid");
      if (isEditMode) {
        toggleDeviceVisibility(devId);
        return;
      }
      const light = deviceData.lights.find(l => l.id === devId);
      const nextState = !Boolean(light?.state?.state);
      if (light && light.state) light.state.state = nextState;
      renderAllDevices();
      sendDeviceCommand(devId, "switch_1", nextState);
    });
  });
}

function renderClimateGrid() {
  const container = document.getElementById("climate-grid");
  const sectionEl = document.getElementById("section-climate");
  if (!container || !deviceData.climate) return;

  const allClimate = [...(deviceData.climate || [])];
  const purDev = (deviceData.xiaomi || []).find(d => d.kind === "purifier");
  if (purDev && purDev.state && purDev.state.temperature !== undefined) {
    allClimate.push({
      id: "purifier_climate",
      name: "Purificador",
      state: {
        temperature: purDev.state.temperature,
        humidity: purDev.state.humidity,
        battery: "Xiaomi"
      }
    });
  }
  const climateList = isEditMode
    ? allClimate
    : allClimate.filter(c => !isDeviceHidden(c.id || ("climate_" + c.name)));

  if (sectionEl) {
    sectionEl.style.display = (climateList.length === 0 && !isEditMode) ? "none" : "";
  }

  container.innerHTML = climateList.map(c => {
    const cid = c.id || ("climate_" + c.name);
    const hiddenClass = (isEditMode && isDeviceHidden(cid)) ? "control-hidden-in-edit" : "";
    const temp = c.state?.temperature ?? "--";
    const hum = c.state?.humidity ?? "--";
    let bat = c.state?.battery ?? "--";
    if (bat === "high") bat = "Alta";
    else if (bat === "middle") bat = "Media";
    else if (bat === "low") bat = "Baja";
    else if (typeof bat === "number") bat = `${bat}%`;

    const shortName = (c.name || "Sensor").replace(/^(Higr[oó]metro|Sensor\s*Aire)\s*/i, "").trim() || c.name;
    const badgeText = c.state?.co2 !== undefined ? `CO₂ ${c.state.co2}` : `🔋 ${bat}`;
    const icon = c.state?.co2 !== undefined ? "🌬️" : "🌡️";
    return `
      <div class="liquid-card climate-vertical-card ${hiddenClass}" data-devid="${cid}" title="${c.name}" style="cursor: ${isEditMode ? 'pointer' : 'default'};">
        ${getEditBadgeHtml(cid, null, false)}
        <div class="climate-vert-name">${icon} ${shortName}</div>
        <div class="climate-vert-temp">${temp}<span style="font-size:0.78rem; font-weight:600;">°C</span></div>
        <div class="climate-vert-sub">
          <span class="climate-vert-pill">💧 ${hum}%</span>
          <span class="climate-vert-pill">${badgeText}</span>
          <span class="climate-vert-pill" style="color:var(--neon-cyan); font-weight:700;">📈 Gráfica ›</span>
        </div>
      </div>
    `;
  }).join("");

  if (isEditMode) {
    container.querySelectorAll(".liquid-card").forEach(card => {
      card.addEventListener("click", () => {
        toggleDeviceVisibility(card.getAttribute("data-devid"));
      });
    });
  } else {
    container.querySelectorAll(".liquid-card").forEach(card => {
      const devid = card.getAttribute("data-devid");
      if (devid === "energy_solar") {
        card.style.cursor = "pointer";
        card.addEventListener("click", () => {
          openSolarModal();
        });
      }
    });
    container.querySelectorAll(".climate-vertical-card").forEach(card => {
      card.style.cursor = "pointer";
      card.addEventListener("click", () => {
        openClimateHistoryModal();
      });
    });
  }
}

function renderEnergyGrid() {
  const container = document.getElementById("energy-grid");
  const sectionEl = document.getElementById("section-energy");
  if (!container) return;

  const solar = deviceData.solar?.state || {};
  const bat20v = deviceData.battery?.state || {};

  const showSolar = isEditMode || !isDeviceHidden("energy_solar");
  const showBat = isEditMode || !isDeviceHidden("energy_battery_20v");

  if (sectionEl) {
    sectionEl.style.display = (!showSolar && !showBat && !isEditMode) ? "none" : "";
  }

  let htmlParts = [];
  if (showSolar) {
    const hiddenClass = (isEditMode && isDeviceHidden("energy_solar")) ? "control-hidden-in-edit" : "";
    htmlParts.push(`
      <div class="liquid-card is-on ${hiddenClass}" data-devid="energy_solar" style="cursor: pointer;" title="Abrir detalles de producción solar">
        ${getEditBadgeHtml("energy_solar", null, false)}
        <div class="card-top">
          <div class="card-icon-bubble" style="background: rgba(217, 119, 6, 0.25); color: var(--neon-amber);">⚡</div>
          <span class="sub-metric-pill">Magnetotérmico Activo</span>
        </div>
        <div class="card-title-group">
          <h4>Paneles Solares Cocina/Tejado</h4>
          <div class="metric-row">
            <span class="metric-big" style="color: var(--neon-amber);">${solar.watts ?? 0}</span>
            <span class="metric-unit">W Generando</span>
          </div>
          <div class="sub-metrics">
            <span>Tensión: <b>${solar.volts ?? 230} V</b></span>
            <span>Corriente: <b>${solar.amps ?? 0} A</b></span>
          </div>
        </div>
      </div>
    `);
  }

  // Tarjeta de Ahorro y Autoconsumo justo debajo de Paneles Solares
  const esData = window.energySavingsData || null;
  const esMode = esData?.config?.mode || "auto";
  const esModeMeta = {
    auto: { label: "Autoconsumo Activo", bg: "rgba(16,185,129,0.20)", color: "#10b981" },
    paused: { label: "Pausado", bg: "rgba(245,158,11,0.20)", color: "#f59e0b" },
    vacation: { label: "Vacaciones", bg: "rgba(59,130,246,0.20)", color: "#3b82f6" }
  }[esMode] || { label: "Autoconsumo", bg: "rgba(16,185,129,0.20)", color: "#10b981" };
  const firstRule = (esData?.rules_status || []).find(r => r.enabled) || (esData?.rules_status || [])[0];
  const esSummaryLine = firstRule
    ? `${firstRule.icon || "⚡"} ${firstRule.name}: ${firstRule.status_label}`
    : "Pulsa para configurar reglas solares";
  const esSavedKwh = esData?.summary?.total_saved_kwh_today ?? 0;
  const esMeterTxt = esData?.telemetry?.meter_online ? "Doble pinza activa" : "Vía Hoymiles (listo para pinza)";
  const esShortMode = { auto: "Activo", paused: "Pausa", vacation: "Vacac." }[esMode] || "Activo";
  htmlParts.push(`
    <div class="liquid-card energy-savings-compact-card" data-devid="energy_savings" style="cursor:pointer; padding:0.52rem 0.68rem; gap:0.22rem; min-height:0;" title="Programar ahorro y autoconsumo inteligente">
      <div style="display:flex; align-items:center; justify-content:space-between; gap:0.35rem;">
        <div style="display:flex; align-items:center; gap:0.35rem; min-width:0;">
          <span style="font-size:0.95rem; line-height:1;">🌱</span>
          <span style="font-size:0.78rem; font-weight:700; color:var(--text-primary); white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">Ahorro Solar</span>
        </div>
        <span style="font-size:0.65rem; padding:0.12rem 0.42rem; border-radius:999px; background:${esModeMeta.bg}; color:${esModeMeta.color}; font-weight:700; white-space:nowrap;">${esShortMode}</span>
      </div>
      <div style="font-size:0.69rem; color:var(--text-secondary); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; line-height:1.2;">${esSummaryLine}</div>
      <div style="display:flex; align-items:center; justify-content:space-between; font-size:0.68rem; color:var(--text-secondary); margin-top:0.05rem;">
        <span>Hoy: <b>${esSavedKwh} kWh</b></span>
        <span style="color:#0284c7; font-weight:600;">Reglas ›</span>
      </div>
    </div>
  `);

  if (showBat) {
    const hiddenClass = (isEditMode && isDeviceHidden("energy_battery_20v")) ? "control-hidden-in-edit" : "";
    htmlParts.push(`
      <div class="liquid-card ${hiddenClass}" data-devid="energy_battery_20v" style="cursor: ${isEditMode ? 'pointer' : 'default'};">
        ${getEditBadgeHtml("energy_battery_20v", null, false)}
        <div class="card-top">
          <div class="card-icon-bubble">🔋</div>
          <span class="sub-metric-pill">${bat20v.voltage ?? 25.0} V</span>
        </div>
        <div class="card-title-group">
          <h4>Batería Smart 20 V / 4 Ah</h4>
          <div class="metric-row">
            <span class="metric-big">${bat20v.battery_percentage ?? 92}</span>
            <span class="metric-unit">% Carga</span>
          </div>
          <div class="sub-metrics">
            <span>Temp: <b>${bat20v.temperature ?? 19}°C</b></span>
            <span>Salud: Óptima</span>
          </div>
        </div>
      </div>
    `);
  }

  container.innerHTML = htmlParts.join("");

  if (isEditMode) {
    container.querySelectorAll(".liquid-card").forEach(card => {
      card.addEventListener("click", () => {
        toggleDeviceVisibility(card.getAttribute("data-devid"));
      });
    });
  } else {
    container.querySelectorAll(".liquid-card").forEach(card => {
      const devid = card.getAttribute("data-devid");
      if (devid === "energy_solar") {
        card.style.cursor = "pointer";
        card.setAttribute("title", "Abrir detalles de producción solar");
        card.addEventListener("click", () => {
          openSolarModal();
        });
      } else if (devid === "energy_savings") {
        card.style.cursor = "pointer";
        card.addEventListener("click", () => {
          openEnergySavingsModal();
        });
      }
    });
  }
}

function renderPlugsGrid() {
  const container = document.getElementById("plugs-grid");
  const sectionEl = document.getElementById("section-plugs");
  if (!container || !deviceData.plugs) return;

  const allPlugs = deviceData.plugs;
  const plugs = isEditMode ? allPlugs : allPlugs.filter(p => !isDeviceHidden(p.id));

  if (sectionEl) {
    sectionEl.style.display = (plugs.length === 0 && !isEditMode) ? "none" : "";
  }

  container.innerHTML = plugs.map(plug => {
    const isOn = Boolean(plug.state?.state);
    const hiddenClass = (isEditMode && isDeviceHidden(plug.id)) ? "control-hidden-in-edit" : "";
    return `
      <div class="liquid-card ${isOn ? 'plug-on' : ''} ${hiddenClass}" data-devid="${plug.id}">
        ${getEditBadgeHtml(plug.id)}
        <div class="card-top">
          <div class="card-icon-bubble">🔌</div>
          <div class="liquid-switch ${isOn ? 'on' : ''}"></div>
        </div>
        <div class="card-title-group">
          <h4>${plug.name}</h4>
          <span class="card-subtitle">${isOn ? 'CONECTADO (ON)' : 'Apagado'}</span>
        </div>
      </div>
    `;
  }).join("");

  container.querySelectorAll(".liquid-card").forEach(card => {
    card.addEventListener("click", () => {
      const devId = card.getAttribute("data-devid");
      if (isEditMode) {
        toggleDeviceVisibility(devId);
        return;
      }
      const plug = deviceData.plugs.find(p => p.id === devId);
      const nextState = !Boolean(plug?.state?.state);
      if (plug && plug.state) plug.state.state = nextState;
      renderAllDevices();
      sendDeviceCommand(devId, "switch_1", nextState);
    });
  });
}

function renderSecurityGrid() {
  const container = document.getElementById("security-grid");
  const sectionEl = document.getElementById("section-security");
  if (!container) return;

  const alarmMode = deviceData.security?.alarm?.state?.master_mode ?? "disarmed";
  const doorOpen = deviceData.security?.door?.state?.is_open ?? false;

  const showAlarm = isEditMode || !isDeviceHidden("security_alarm");
  const showDoor = isEditMode || !isDeviceHidden("security_door");
  const showAdguard = isEditMode || !isDeviceHidden("security_adguard");

  if (sectionEl) {
    sectionEl.style.display = (!showAlarm && !showDoor && !showAdguard && !isEditMode) ? "none" : "";
  }

  let htmlParts = [];
  if (showAlarm) {
    const hiddenClass = (isEditMode && isDeviceHidden("security_alarm")) ? "control-hidden-in-edit" : "";
    const isArmed = alarmMode !== "disarmed";
    const statusTxt = isArmed ? (alarmMode === "home" ? "En Casa" : "ARMADA") : "Desarmada";
    htmlParts.push(`
      <div class="liquid-card sec-horiz-card ${isArmed ? 'is-on' : ''} ${hiddenClass}" id="card-security-alarm" data-devid="security_alarm" style="cursor:pointer;" title="Pulsa para abrir el panel completo de Alarma, accesorios y log de eventos">
        ${getEditBadgeHtml("security_alarm", null, false)}
        <div class="sec-horiz-left">
          <div class="card-icon-bubble">🛡️</div>
          <div class="sec-horiz-info">
            <h4>Alarma Inteligente</h4>
            <div class="sec-horiz-sub" style="color:${isArmed ? '#ef4444' : '#10b981'}; font-weight:700;">${statusTxt} · <span style="color:var(--modal-text-muted); font-weight:500;">Accesorios & Log ›</span></div>
          </div>
        </div>
        <div class="sec-horiz-right">
          <button type="button" class="liquid-action-pill alarm-icon-btn alarm-btn-disarm ${!isArmed ? 'is-disarm-active' : ''}" id="btn-alarm-disarm" title="Desarmar alarma" aria-label="Desarmar">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 9.9-1"/></svg>
          </button>
          <button type="button" class="liquid-action-pill alarm-icon-btn alarm-btn-arm ${isArmed ? 'is-arm-active' : ''}" id="btn-alarm-arm" title="Armar alarma" aria-label="Armar">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
          </button>
        </div>
      </div>
    `);
  }

  if (showDoor) {
    const hiddenClass = (isEditMode && isDeviceHidden("security_door")) ? "control-hidden-in-edit" : "";
    htmlParts.push(`
      <div class="liquid-card sec-horiz-card ${doorOpen ? 'is-on' : ''} ${hiddenClass}" id="card-security-door" data-devid="security_door" style="cursor:pointer;" title="Pulsa para ver el esquema de accesos y seguridad">
        ${getEditBadgeHtml("security_door", null, false)}
        <div class="sec-horiz-left">
          <div class="card-icon-bubble">${doorOpen ? '🚪⚠️' : '🚪'}</div>
          <div class="sec-horiz-info">
            <h4>Puerta Principal</h4>
            <div class="sec-horiz-sub">Sensor Magnético · Entrada</div>
          </div>
        </div>
        <div class="sec-horiz-right">
          <span class="sub-metric-pill" style="${doorOpen ? 'color:#ef4444; border-color:rgba(239,68,68,0.45); background:rgba(239,68,68,0.12); font-weight:800;' : 'color:#10b981; border-color:rgba(16,185,129,0.4);'}">${doorOpen ? '¡ABIERTA!' : 'Cerrada'}</span>
        </div>
      </div>
    `);
  }

  if (showAdguard) {
    const hiddenClass = (isEditMode && isDeviceHidden("security_adguard")) ? "control-hidden-in-edit" : "";
    const ag = window.adguardStats || { online: false };
    const protOn = Boolean(ag.online && ag.protection_enabled);
    const totalQ = ag.online ? (ag.num_dns_queries ?? 0) : "--";
    const blockedQ = ag.online ? (ag.num_blocked_filtering ?? 0) : "--";
    const pctQ = ag.online ? (ag.block_pct ?? 0) : "--";
    htmlParts.push(`
      <div class="liquid-card sec-horiz-card ${protOn ? "is-on" : ""} ${hiddenClass}" id="card-security-adguard" data-devid="security_adguard" style="cursor:pointer;">
        ${getEditBadgeHtml("security_adguard", null, false)}
        <div class="sec-horiz-left">
          <div class="card-icon-bubble">🛡️</div>
          <div class="sec-horiz-info">
            <h4>AdGuard Home</h4>
            <div class="sec-horiz-sub"><b>${blockedQ} bloq. (${pctQ}%)</b> · ${totalQ} DNS</div>
          </div>
        </div>
        <div class="sec-horiz-right">
          <span class="sub-metric-pill" style="${protOn ? "color:#10b981; border-color:rgba(16,185,129,0.45);" : ""}">${ag.online ? (protOn ? "Activo ›" : "Pausado") : "Offline"}</span>
        </div>
      </div>
    `);
  }

  container.innerHTML = htmlParts.join("");

  if (isEditMode) {
    container.querySelectorAll(".liquid-card").forEach(card => {
      card.addEventListener("click", (e) => {
        e.stopPropagation();
        toggleDeviceVisibility(card.getAttribute("data-devid"));
      });
    });
    return;
  }

  document.getElementById("card-security-alarm")?.addEventListener("click", () => {
    openAlarmModal();
  });
  document.getElementById("card-security-door")?.addEventListener("click", () => {
    openAlarmModal();
  });
  document.getElementById("card-security-adguard")?.addEventListener("click", () => {
    openAdguardModal();
  });

  const btnDisarm = document.getElementById("btn-alarm-disarm");
  const btnArm = document.getElementById("btn-alarm-arm");
  const alarmDevId = deviceData.security?.alarm?.id;

  if (btnDisarm && alarmDevId) {
    btnDisarm.addEventListener("click", (e) => {
      e.stopPropagation();
      sendDeviceCommand(alarmDevId, "master_mode", "disarmed");
    });
  }
  if (btnArm && alarmDevId) {
    btnArm.addEventListener("click", (e) => {
      e.stopPropagation();
      sendDeviceCommand(alarmDevId, "master_mode", "arm");
    });
  }
}

async function sendDeviceCommand(devId, code, value) {
  try {
    await fetch("/api/devices/control", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ device_id: devId, code: code, value: value })
    });
  } catch (e) {
    console.error("Error sending device command:", e);
  }
}

// ========================================================
// 8. DOCK CONTROLS & FULLSCREEN DRAWER TOGGLE
// ========================================================
document.getElementById("dock-light-1")?.addEventListener("click", () => {
  const light = deviceData.lights?.find(l => l.id === "bf9abfe1a19f35a05ceej0");
  const next = !Boolean(light?.state?.state);
  if (light && light.state) light.state.state = next;
  renderAllDevices();
  sendDeviceCommand("bf9abfe1a19f35a05ceej0", "switch_1", next);
});

document.getElementById("dock-light-2")?.addEventListener("click", () => {
  const light = deviceData.lights?.find(l => l.id === "bf873ba4935f6abf954qsp");
  const next = !Boolean(light?.state?.state);
  if (light && light.state) light.state.state = next;
  renderAllDevices();
  sendDeviceCommand("bf873ba4935f6abf954qsp", "switch_1", next);
});

document.getElementById("dock-cameras-btn")?.addEventListener("click", () => {
  openCamerasModal();
});
document.getElementById("btn-open-cameras-modal")?.addEventListener("click", () => {
  closeDrawer();
  openCamerasModal();
});

const drawer = document.getElementById("controls-drawer");
const btnDrawer = document.getElementById("btn-drawer");
const btnDrawerClose = document.getElementById("drawer-close-btn");
const drawerBackdrop = document.getElementById("drawer-backdrop");

function openDrawer() {
  isDrawerOpen = true;
  drawer.classList.remove("hidden-drawer");
  fetchDevices();
  resetIdleTimer();
}

function closeDrawer() {
  isDrawerOpen = false;
  if (isEditMode) setEditMode(false);
  drawer.classList.add("hidden-drawer");
  resetIdleTimer();
}

if (btnDrawer) btnDrawer.addEventListener("click", openDrawer);
if (btnDrawerClose) btnDrawerClose.addEventListener("click", closeDrawer);
if (drawerBackdrop) drawerBackdrop.addEventListener("click", closeDrawer);

// Brightness & Dimmer Controls
const bSlider = document.getElementById("brightness-slider");
const bVal = document.getElementById("brightness-val");
const btnDim = document.getElementById("btn-dim");
let isDimmed = false;

if (bSlider && bVal) {
  bSlider.addEventListener("input", (e) => {
    const val = e.target.value;
    bVal.textContent = `${val}%`;
    fetch("/api/brightness", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ brightness: parseInt(val) })
    }).catch(() => {});
  });
}

if (btnDim) {
  btnDim.addEventListener("click", () => {
    isDimmed = !isDimmed;
    const targetBrightness = isDimmed ? 10 : 80;
    if (bSlider) bSlider.value = targetBrightness;
    if (bVal) bVal.textContent = `${targetBrightness}%`;
    fetch("/api/brightness", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ brightness: targetBrightness })
    }).catch(() => {});
  });
}

document.getElementById("btn-night-preset")?.addEventListener("click", () => {
  if (bSlider) bSlider.value = 10;
  if (bVal) bVal.textContent = "10%";
  fetch("/api/brightness", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ brightness: 10 })
  }).catch(() => {});
});

document.getElementById("btn-reload-photos")?.addEventListener("click", () => {
  showNextSlide();
});

// Auto-discovery Trigger
document.getElementById("btn-sync-devices")?.addEventListener("click", async () => {
  const btn = document.getElementById("btn-sync-devices");
  if (btn) btn.innerHTML = `<span>⏳</span> Buscando nuevos dispositivos...`;
  try {
    const res = await fetch("/api/devices/sync", { method: "POST" });
    const data = await res.json();
    if (btn) btn.innerHTML = `<span>✅</span> ¡${data.total_devices} Dispositivos Sincronizados!`;
    setTimeout(() => {
      if (btn) btn.innerHTML = `<span>🔄</span> Detectar Nuevos Tuya`;
    }, 3000);
    fetchDevices();
  } catch (e) {
    if (btn) btn.innerHTML = `<span>❌</span> Error al sincronizar`;
  }
});

// ========================================================
// 9. WEBSOCKET FOR LIVE SYNC, ASSISTANT & TOUCH FALLBACK
// ========================================================
let lastNativeInteractionTime = 0;
let lastAnyClickTime = 0;

window.addEventListener("click", (e) => {
  const now = Date.now();
  if (now - lastAnyClickTime < 320) {
    e.stopImmediatePropagation();
    e.preventDefault();
    return;
  }
  lastAnyClickTime = now;
  if (e.isTrusted) {
    lastNativeInteractionTime = now;
  }
}, true);

// Only native trusted click suppresses PHYSICAL_TAP_FALLBACK (so micro-drags on touchstart still tap)

function showTouchRipple(x, y) {
  const dot = document.createElement("div");
  dot.style.position = "fixed";
  dot.style.left = (x - 18) + "px";
  dot.style.top = (y - 18) + "px";
  dot.style.width = "36px";
  dot.style.height = "36px";
  dot.style.borderRadius = "50%";
  dot.style.background = "rgba(0, 229, 255, 0.75)";
  dot.style.boxShadow = "0 0 20px #00e5ff, inset 0 0 8px #ffffff";
  dot.style.zIndex = "99999";
  dot.style.pointerEvents = "none";
  dot.style.transition = "transform 0.4s ease, opacity 0.4s ease";
  document.body.appendChild(dot);
  setTimeout(() => {
    dot.style.transform = "scale(2.2)";
    dot.style.opacity = "0";
    setTimeout(() => dot.remove(), 400);
  }, 30);
}

function dispatchSyntheticTap(xPct, yPct) {
  resetIdleTimer();
  const x = xPct * window.innerWidth;
  const y = yPct * window.innerHeight;
  showTouchRipple(x, y);

  if (Date.now() - lastAnyClickTime < 320) return;

  const el = document.elementFromPoint(x, y);
  if (el) {
    const target = (el.closest) ? (el.closest("button, .liquid-card, .camera-card, .liquid-dock-btn, .liquid-pill, .liquid-action-pill, .camera-action-btn, .liquid-edit-btn, input, select, .liquid-close-btn, #drawer-close-btn") || el) : el;
    try {
      if (target && typeof target.click === "function") {
        target.click();
      } else {
        const evtClick = new MouseEvent('click', { bubbles: true, cancelable: true, clientX: x, clientY: y });
        el.dispatchEvent(evtClick);
      }
    } catch(e) {
      console.error("Click dispatch error:", e);
    }
  }
}

async function syncServerConfig() {
  try {
    const res = await fetch("/api/config");
    if (res.ok) {
      const cfg = await res.json();
      let changed = false;
      if (Array.isArray(cfg.hidden_devices)) {
        hiddenDevices = new Set(cfg.hidden_devices);
        localStorage.setItem("domos_hidden_devices", JSON.stringify(cfg.hidden_devices));
        changed = true;
      }
      if (cfg.layout_mode && ["rooms", "type", "compact"].includes(cfg.layout_mode)) {
        layoutMode = cfg.layout_mode;
        localStorage.setItem("domos_layout_mode", layoutMode);
        updateLayoutPresetButtons();
        changed = true;
      }
      if (cfg.device_rooms && typeof cfg.device_rooms === "object") {
        deviceRooms = cfg.device_rooms;
        localStorage.setItem("domos_device_rooms", JSON.stringify(deviceRooms));
        changed = true;
      }
      if (Array.isArray(cfg.custom_rooms)) {
        customRooms = cfg.custom_rooms;
        localStorage.setItem("domos_custom_rooms", JSON.stringify(customRooms));
        renderCustomRoomsList();
        changed = true;
      }
      if (Array.isArray(cfg.device_order)) {
        deviceOrder = cfg.device_order;
        localStorage.setItem("domos_device_order", JSON.stringify(deviceOrder));
        changed = true;
      }
      if (Array.isArray(cfg.favorite_devices)) {
        favoriteDevices = new Set(cfg.favorite_devices);
        localStorage.setItem("domos_favorite_devices", JSON.stringify(cfg.favorite_devices));
        changed = true;
      }
      if (cfg.carousel_mode && ["mixed", "online", "sd"].includes(cfg.carousel_mode) && cfg.carousel_mode !== carouselMode) {
        carouselMode = cfg.carousel_mode;
        localStorage.setItem("domos_carousel_mode", carouselMode);
        const sel = document.getElementById("carousel-mode-select");
        if (sel) sel.value = carouselMode;
        syncPhotoSourceModalUI();
        if (sdPhotoList.length > 0 || carouselMode === "online") {
          showNextSlide();
          startSlideshow();
        }
      }
      if (cfg.carousel_transition && ["auto", "blur", "black", "white"].includes(cfg.carousel_transition) && cfg.carousel_transition !== carouselTransition) {
        carouselTransition = cfg.carousel_transition;
        localStorage.setItem("domos_carousel_transition", carouselTransition);
        const transSel = document.getElementById("modal-slide-transition-select");
        if (transSel) transSel.value = carouselTransition;
      }
      if (changed) renderAllDevices();
    }
  } catch (e) {}
}
syncServerConfig();

function connectWebSocket() {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const ws = new WebSocket(`${protocol}//${window.location.host}/ws`);

  ws.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data);
      if (msg.type === "DEVICE_UPDATE") {
        if (msg.devices) {
          deviceData = msg.devices;
          renderAllDevices();
        }
      } else if (msg.type === "CONFIG_UPDATE") {
        if (msg.config && Array.isArray(msg.config.hidden_devices)) {
          hiddenDevices = new Set(msg.config.hidden_devices);
          localStorage.setItem("domos_hidden_devices", JSON.stringify(msg.config.hidden_devices));
          renderAllDevices(true);
        }
      } else if (msg.type === "ASSISTANT_STATE") {
        if (msg.state === "idle") {
          setTimeout(hideAssistant, 1200);
        } else {
          showAssistant(msg.state, msg.prompt, msg.reply);
        }
      } else if (msg.type === "OPEN_DRAWER") {
        openDrawer();
      } else if (msg.type === "CLOSE_DRAWER") {
        closeDrawer();
      } else if (msg.type === "SCROLL_DRAWER") {
        const body = document.querySelector(".liquid-panel-body");
        if (body) body.scrollTop = msg.top || 0;
      } else if (msg.type === "TOGGLE_THEME") {
        toggleTheme();
      } else if (msg.type === "CAMERA_LIVE") {
        if (msg.cameraId) requestCameraLive(msg.cameraId);
      } else if (msg.type === "CAMERA_STOP") {
        if (msg.cameraId) stopCameraLive(msg.cameraId);
      } else if (msg.type === "PHOTOS_UPDATED") {
        refreshSdPhotosSilently(msg.file);
      } else if (msg.type === "OPEN_MODAL") {
        fetch("/api/debug_log", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({got_modal: msg.modal, has_fn: typeof openAlarmDetailsModal})}).catch(()=>{});
        if (msg.modal === "alarm") openAlarmDetailsModal();
        else if (msg.modal === "photo") typeof openPhotoSourceModal === "function" && openPhotoSourceModal();
        else if (msg.modal === "solar") typeof openSolarModal === "function" && openSolarModal();
      } else if (msg.type === "REMOTE_CLICK") {
        dispatchSyntheticTap(msg.x, msg.y);
      } else if (msg.type === "PHYSICAL_TOUCH_POINT") {
        if (typeof isTouchTestOpen !== "undefined" && isTouchTestOpen) {
          paintTouchTestDot(msg.x, msg.y, "evdev");
        }
      } else if (msg.type === "RADIO_CONTROL") {
        handleRadioControlMsg(msg);
      } else if (msg.type === "VOLUME_OSD") {
        showVolumeOsd(msg.volume);
      } else if (msg.type === "VOLUME_SAFETY_LIMIT") {
        showVolumeOsd(msg.current || 70);
        openVolumeSafetyModal(msg.requested || 80);
      } else if (msg.type === "INCIDENTS_UPDATED") {
        updateIncidentBadges(msg.incidents || []);
      } else if (msg.type === "PHYSICAL_TAP_FALLBACK") {
        if (window.location.hostname !== "127.0.0.1" && window.location.hostname !== "localhost") {
          return;
        }
        if (typeof isTouchTestOpen !== "undefined" && isTouchTestOpen) {
          paintTouchTestDot(msg.x, msg.y, "evdev");
        }
        resetIdleTimer();
        setTimeout(() => {
          if (Date.now() - lastNativeInteractionTime < 450) {
            return;
          }
          dispatchSyntheticTap(msg.x, msg.y);
        }, 90);
      } else if (msg.type === "FAMILY_MESSAGE") {
        showFamilyMessage(msg.sender, msg.text, msg.timestamp);
      } else if (msg.type === "DOORBELL_ALERT") {
        triggerDoorbellAlert(msg.title, msg.stream_data || msg.stream_url, msg.cameraId, msg.ringing !== false);
      } else if (msg.type === "DOORBELL_CHIME_STATE") {
        setDoorbellSilenceBtnVisible(!!msg.ringing);
      } else if (msg.type === "AUDIO_VOLUMES_UPDATED") {
        applyAudioVolumesToUI(msg.volumes || {});
      } else if (msg.type === "ENERGY_SAVINGS_UPDATED") {
        window.energySavingsData = msg.data || null;
        if (typeof renderEnergyGrid === "function") renderEnergyGrid();
      } else if (msg.type === "DOCTOR_SPEAK_STATE") {
        doctorIsSpeaking = !!msg.speaking;
        const btn = document.getElementById("btn-doctor-speak");
        if (btn) {
          btn.disabled = false;
          btn.textContent = doctorIsSpeaking ? "⏹ Parar Lectura" : "🔊 Leer Informe";
        }
      }
    } catch (e) {
      console.error("WS Parse Error:", e);
    }
  };

  ws.onclose = () => {
    setTimeout(connectWebSocket, 3000);
  };
}
connectWebSocket();

// ========================================================
// 10. FAMILY MESSAGES & DOORBELL HANDLERS
// ========================================================
const msgModal = document.getElementById("message-modal");
function showFamilyMessage(sender, text, timestamp) {
  document.getElementById("message-sender").textContent = `Mensaje de ${sender || "Familia"}`;
  document.getElementById("message-text").textContent = text || "";
  document.getElementById("message-time").textContent = timestamp || new Date().toLocaleTimeString("es-ES", { hour: "2-digit", minute: "2-digit" });
  msgModal.classList.remove("hidden");
  fetch("/api/brightness", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ brightness: 100 })
  }).catch(() => {});
}

document.getElementById("message-dismiss-btn")?.addEventListener("click", () => {
  msgModal.classList.add("hidden");
});

const doorbellModal = document.getElementById("doorbell-modal");

function playDoorbellChime() {
  try {
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    if (!AudioCtx) return;
    const ctx = new AudioCtx();
    const notes = [
      { freq: 784.0, start: 0.0, dur: 0.38 },   // G5 (Ding)
      { freq: 659.25, start: 0.36, dur: 0.65 }  // E5 (Dong)
    ];
    notes.forEach(n => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = "triangle";
      osc.frequency.setValueAtTime(n.freq, ctx.currentTime + n.start);
      gain.gain.setValueAtTime(0.001, ctx.currentTime + n.start);
      gain.gain.exponentialRampToValueAtTime(0.45, ctx.currentTime + n.start + 0.03);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + n.start + n.dur);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(ctx.currentTime + n.start);
      osc.stop(ctx.currentTime + n.start + n.dur + 0.05);
    });
  } catch (e) {}
}

let doorbellChimeHideTimer = null;
let isDoorbellChimeActive = false;

function setDoorbellSilenceBtnVisible(visible) {
  isDoorbellChimeActive = !!visible;
  const btn = document.getElementById("btn-cam-fs-silence-chime");
  if (!btn) return;
  if (doorbellChimeHideTimer) {
    clearTimeout(doorbellChimeHideTimer);
    doorbellChimeHideTimer = null;
  }
  if (visible) {
    btn.classList.remove("hidden");
    btn.style.display = "inline-flex";
    btn.disabled = false;
    btn.textContent = "🔕 Silenciar Timbre";
    doorbellChimeHideTimer = setTimeout(() => {
      setDoorbellSilenceBtnVisible(false);
    }, 19000);
  } else {
    btn.classList.add("hidden");
    btn.style.display = "none";
  }
}

async function silenceDoorbellChime() {
  setDoorbellSilenceBtnVisible(false);
  try {
    await fetch("/api/doorbell/silence", { method: "POST" });
  } catch (e) {}
}

document.getElementById("btn-cam-fs-silence-chime")?.addEventListener("click", () => {
  silenceDoorbellChime();
});

function triggerDoorbellAlert(title, streamUrl, cameraId, ringing = true) {
  const camId = cameraId || "bf77eed8534deaf66f2xpj";
  openCameraFullscreen(camId, title || "🔔 ¡Timbre! Videoportero Exterior", true, streamUrl);
  if (ringing) {
    setDoorbellSilenceBtnVisible(true);
  }
}

document.getElementById("doorbell-dismiss-btn")?.addEventListener("click", () => {
  doorbellModal?.classList.add("hidden");
});

// ========================================================
// 11. ASUS BATTERY STATUS
// ========================================================
async function updateBattery() {
  try {
    const res = await fetch("/api/status");
    if (res.ok) {
      const data = await res.json();
      const rawCap = data.battery?.capacity ?? "--";
      const cap = typeof rawCap === "number" ? Math.min(100, Math.max(0, rawCap)) : rawCap;
      document.getElementById("battery-pct").textContent = `${cap}%`;
      const isCharging = data.battery?.status === "Charging" || data.battery?.status === "Full";
      const bEl = document.getElementById("battery-icon"); if (bEl) { bEl.className = isCharging ? 'neon-svg neon-amber' : 'neon-svg neon-emerald'; bEl.innerHTML = isCharging ? SVG_BOLT : SVG_BATTERY; }
    }
  } catch (e) {}
}
updateBattery();
setInterval(updateBattery, 30000);

// Initial device load
fetchDevices();
setInterval(fetchDevices, 15000);


// Auto-hide mouse cursor after 2s of mouse inactivity (or immediately on touch)
let cursorHideTimer = null;
function hideCursorNow() {
  document.body.classList.add("hide-cursor");
}
function showCursorBriefly() {
  document.body.classList.remove("hide-cursor");
  if (cursorHideTimer) clearTimeout(cursorHideTimer);
  cursorHideTimer = setTimeout(hideCursorNow, 2000);
}
window.addEventListener("mousemove", showCursorBriefly, { passive: true });
window.addEventListener("touchstart", hideCursorNow, { passive: true });
hideCursorNow();


// Reboot ASUS Kiosk button (2-tap safety confirmation)
let rebootConfirmTimer = null;
let rebootArmed = false;
document.getElementById("btn-reboot-device")?.addEventListener("click", async () => {
  const btn = document.getElementById("btn-reboot-device");
  if (!rebootArmed) {
    rebootArmed = true;
    if (btn) btn.innerHTML = '<span>⚠️</span> Confirmar Reinicio';
    if (rebootConfirmTimer) clearTimeout(rebootConfirmTimer);
    rebootConfirmTimer = setTimeout(() => {
      rebootArmed = false;
      if (btn) btn.innerHTML = '<span>🔄</span> Reiniciar';
    }, 5000);
    return;
  }
  rebootArmed = false;
  if (btn) btn.innerHTML = '<span>⏳</span> Reiniciando...';
  try {
    await fetch("/api/system/reboot", { method: "POST" });
  } catch (e) {}
});


// ========================================================
// 12. TOUCHSCREEN HARDWARE DIAGNOSTIC OVERLAY
// ========================================================
const touchOverlay = document.getElementById("touch-test-overlay");
const touchCanvas = document.getElementById("touch-test-canvas");
const touchCoordsEl = document.getElementById("touch-test-coords");
let isTouchTestOpen = false;

function drawTouchTestGrid() {
  if (!touchCanvas) return;
  touchCanvas.width = window.innerWidth;
  touchCanvas.height = window.innerHeight;
  const ctx = touchCanvas.getContext("2d");
  ctx.clearRect(0, 0, touchCanvas.width, touchCanvas.height);
  ctx.strokeStyle = "rgba(255, 255, 255, 0.12)";
  ctx.lineWidth = 1;
  for (let i = 1; i < 6; i++) {
    const x = (touchCanvas.width / 6) * i;
    ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, touchCanvas.height); ctx.stroke();
  }
  for (let j = 1; j < 4; j++) {
    const y = (touchCanvas.height / 4) * j;
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(touchCanvas.width, y); ctx.stroke();
  }
}

function paintTouchTestDot(xPct, yPct, source) {
  if (!isTouchTestOpen || !touchCanvas) return;
  const x = xPct * touchCanvas.width;
  const y = yPct * touchCanvas.height;
  const ctx = touchCanvas.getContext("2d");
  ctx.beginPath();
  ctx.arc(x, y, 10, 0, Math.PI * 2);
  ctx.fillStyle = source === "native" ? "rgba(16, 185, 129, 0.8)" : "rgba(0, 229, 255, 0.85)";
  ctx.fill();
  ctx.strokeStyle = "#ffffff";
  ctx.lineWidth = 2;
  ctx.stroke();
  if (touchCoordsEl) {
    touchCoordsEl.textContent = `Detectado: x=${Math.round(xPct * 100)}% (${Math.round(x)}px), y=${Math.round(yPct * 100)}% (${Math.round(y)}px)`;
  }
}

document.getElementById("btn-touch-test")?.addEventListener("click", () => {
  if (!touchOverlay) return;
  isTouchTestOpen = true;
  touchOverlay.classList.remove("hidden");
  touchOverlay.style.display = "flex";
  drawTouchTestGrid();
  if (touchCoordsEl) touchCoordsEl.textContent = "Toca o desliza por la pantalla...";
});

document.getElementById("btn-touch-test-clear")?.addEventListener("click", () => {
  drawTouchTestGrid();
  if (touchCoordsEl) touchCoordsEl.textContent = "Lienzo limpio. Toca para probar...";
});

document.getElementById("btn-touch-test-close")?.addEventListener("click", () => {
  isTouchTestOpen = false;
  if (touchOverlay) {
    touchOverlay.classList.add("hidden");
    touchOverlay.style.display = "none";
  }
});

if (touchOverlay) {
  touchOverlay.addEventListener("pointerdown", (e) => {
    if (e.target.closest("button")) return;
    paintTouchTestDot(e.clientX / window.innerWidth, e.clientY / window.innerHeight, "native");
  });
  touchOverlay.addEventListener("pointermove", (e) => {
    if (e.buttons > 0 || e.pointerType === "touch") {
      paintTouchTestDot(e.clientX / window.innerWidth, e.clientY / window.innerHeight, "native");
    }
  });
}


// ========================================================
// 13. MODAL DE CÁMARAS & PANTALLA COMPLETA (VIDEOPORTERO)
// ========================================================
const camerasModalEl = document.getElementById("cameras-modal");
const camFsModalEl = document.getElementById("camera-fullscreen-modal");
const camFsViewport = document.getElementById("cam-fs-viewport");
const camFsTitle = document.getElementById("cam-fs-title");
const camFsBadge = document.getElementById("cam-fs-badge");
const btnCamFsAudio = document.getElementById("btn-cam-fs-audio");
let fullscreenHls = null;
let fullscreenAudioEnabled = true;
let currentFullscreenCamId = null;

window.openCamerasModal = function() {
  if (!camerasModalEl) return;
  camerasModalEl.classList.remove("hidden");
  camerasModalEl.style.display = "flex";
  renderCamerasGrid(true);
  const statusEl = document.getElementById("cameras-modal-status");
  if (statusEl) statusEl.textContent = "Conectando todas automáticamente...";
  setTimeout(() => {
    connectAllCameras();
    if (statusEl) statusEl.textContent = "Toca cualquier cámara para Pantalla Completa";
  }, 150);
};

window.closeCamerasModal = function() {
  stopAllCameras();
  if (camerasModalEl) {
    camerasModalEl.classList.add("hidden");
    camerasModalEl.style.display = "none";
  }
};

document.getElementById("btn-cameras-modal-close")?.addEventListener("click", closeCamerasModal);
camerasModalEl?.addEventListener("click", (e) => {
  if (e.target === camerasModalEl) closeCamerasModal();
});

let doorbellAutoCloseTimer = null;

window.closeCameraFullscreen = function() {
  if (doorbellAutoCloseTimer) {
    clearTimeout(doorbellAutoCloseTimer);
    doorbellAutoCloseTimer = null;
  }
  if (isDoorbellChimeActive) {
    silenceDoorbellChime();
  } else {
    setDoorbellSilenceBtnVisible(false);
  }
  currentFullscreenCamId = null;
  if (fullscreenHls) {
    try { fullscreenHls.destroy(); } catch (e) {}
    fullscreenHls = null;
  }
  if (camFsViewport) camFsViewport.innerHTML = "";
  if (camFsModalEl) {
    camFsModalEl.classList.add("hidden");
    camFsModalEl.style.display = "none";
  }
};

document.getElementById("btn-cam-fs-close")?.addEventListener("click", closeCameraFullscreen);

btnCamFsAudio?.addEventListener("click", () => {
  fullscreenAudioEnabled = !fullscreenAudioEnabled;
  const vid = document.getElementById("cam-fs-video");
  if (vid) {
    vid.muted = !fullscreenAudioEnabled;
    if (fullscreenAudioEnabled) vid.volume = Math.max(0, Math.min(1, (window.domosAudioVolumes?.cameras ?? 85) / 100));
  }
  btnCamFsAudio.textContent = fullscreenAudioEnabled ? "🔊 Audio Activo" : "🔇 Audio Silenciado";
});

window.openCameraFullscreen = async function(camId, title, isDoorbellAlert = false, preloadedUrl = "") {
  if (!camFsModalEl || !camFsViewport) return;
  if (isDoorbellAlert && camFsModalEl.style.display === "flex" && currentFullscreenCamId === camId && fullscreenHls) {
    return;
  }
  currentFullscreenCamId = camId;
  if (fullscreenHls) {
    try { fullscreenHls.destroy(); } catch (e) {}
    fullscreenHls = null;
  }

  fullscreenAudioEnabled = true;
  if (btnCamFsAudio) btnCamFsAudio.textContent = "🔊 Audio Activo";
  if (camFsTitle) camFsTitle.textContent = title || "Cámara en Directo";
  if (doorbellAutoCloseTimer) {
    clearTimeout(doorbellAutoCloseTimer);
    doorbellAutoCloseTimer = null;
  }
  if (camFsBadge) {
    camFsBadge.textContent = isDoorbellAlert ? "🔔 TIMBRE ACTIVO · CIERRE AUTO 60s" : "PANTALLA COMPLETA";
    camFsBadge.style.background = isDoorbellAlert ? "rgba(239,68,68,0.28)" : "rgba(0,229,255,0.18)";
    camFsBadge.style.color = isDoorbellAlert ? "#fca5a5" : "#00e5ff";
  }
  if (isDoorbellAlert) {
    doorbellAutoCloseTimer = setTimeout(() => {
      if (camFsModalEl && camFsModalEl.style.display === "flex") {
        window.closeCameraFullscreen();
      }
    }, 60000);
  } else {
    setDoorbellSilenceBtnVisible(false);
  }

  camFsModalEl.classList.remove("hidden");
  camFsModalEl.style.display = "flex";
  camFsViewport.innerHTML = `<p style="color:#00e5ff; font-size:1.05rem;">Conectando señal en directo...</p>`;

  try {
    let streamData = (preloadedUrl && typeof preloadedUrl === "object")
      ? preloadedUrl
      : (preloadedUrl ? { success: true, mode: "hls", url: preloadedUrl } : null);

    if (!streamData) {
      const res = await fetch("/api/camera/stream/" + camId);
      const data = await res.json();
      if (data.success && (data.webrtc_url || data.url)) streamData = data;
    }

    if (!streamData) {
      camFsViewport.innerHTML = `<p style="color:#fbbf24;">No se pudo obtener el flujo en directo de esta cámara.</p>`;
      return;
    }

    camFsViewport.innerHTML = `<video id="cam-fs-video" autoplay playsinline controls style="width:100%; height:100%; object-fit:contain; background:#000;"></video>`;
    const vid = document.getElementById("cam-fs-video");
    vid.muted = !fullscreenAudioEnabled;
    vid.volume = Math.max(0, Math.min(1, (window.domosAudioVolumes?.cameras ?? 85) / 100));

    fullscreenHls = await attachLiveStream(vid, camId, streamData);
  } catch (e) {
    camFsViewport.innerHTML = `<p style="color:#f87171;">Error al conectar stream de cámara.</p>`;
  }
};


// --- Volume Safety Ceiling & Warning Modal (70% Protection) ---
let pendingHighVolumeTarget = 80;

function openVolumeSafetyModal(targetVol = 80) {
  pendingHighVolumeTarget = targetVol;
  const m = document.getElementById("volume-safety-modal");
  if (!m) return;
  m.classList.remove("hidden");
  m.style.display = "flex";
}

function closeVolumeSafetyModal() {
  const m = document.getElementById("volume-safety-modal");
  if (!m) return;
  m.classList.add("hidden");
  m.style.display = "none";
}

async function requestAudioVolumeChange(delta) {
  try {
    const res = await fetch("/api/audio/volume", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ delta })
    });
    const data = await res.json();
    if (data.limit_triggered) {
      openVolumeSafetyModal(data.requested || 80);
    }
  } catch (e) {}
}

async function confirmUnlockHighVolume() {
  try {
    await fetch("/api/audio/volume/unlock", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ unlocked: true, target_volume: pendingHighVolumeTarget })
    });
  } catch (e) {}
  closeVolumeSafetyModal();
}

document.getElementById("btn-cam-fs-vol-up")?.addEventListener("click", () => requestAudioVolumeChange("+10%"));
document.getElementById("btn-cam-fs-vol-down")?.addEventListener("click", () => requestAudioVolumeChange("-10%"));
document.getElementById("btn-vol-safety-keep")?.addEventListener("click", closeVolumeSafetyModal);
document.getElementById("btn-vol-safety-unlock")?.addEventListener("click", confirmUnlockHighVolume);
document.getElementById("volume-safety-modal")?.addEventListener("click", (e) => {
  if (e.target.id === "volume-safety-modal") closeVolumeSafetyModal();
});

// --- Volume OSD Animation ---
let volumeOsdTimer = null;
function showVolumeOsd(pct) {
  const osd = document.getElementById("volume-osd");
  const icon = document.getElementById("volume-osd-icon");
  const text = document.getElementById("volume-osd-text");
  const bar = document.getElementById("volume-osd-bar");
  if (!osd || !text || !bar) return;

  const val = typeof pct === "number" && !Number.isNaN(pct) ? Math.max(0, pct) : 0;
  if (icon) {
    if (val === 0) icon.textContent = "🔇";
    else if (val < 45) icon.textContent = "🔉";
    else if (val <= 70) icon.textContent = "🔊";
    else icon.textContent = "🔊⚠️";
  }
  text.textContent = `${val}%`;
  bar.style.width = `${Math.min(100, val)}%`;
  bar.style.background = val > 70
    ? "linear-gradient(90deg, #f59e0b, #ef4444)"
    : "linear-gradient(90deg, #00e5ff, #10b981)";

  osd.style.opacity = "1";
  osd.style.transform = "translateX(-50%) scale(1)";

  if (volumeOsdTimer) clearTimeout(volumeOsdTimer);
  volumeOsdTimer = setTimeout(() => {
    osd.style.opacity = "0";
    osd.style.transform = "translateX(-50%) scale(0.92)";
  }, 1800);
}

// ========================================================
// SYSTEM INCIDENTS & BATTERY/VOLTAGE ALERTS MODULE
// ========================================================
let currentIncidents = [];

function updateIncidentBadges(incidentsList) {
  currentIncidents = Array.isArray(incidentsList) ? incidentsList : [];
  const count = currentIncidents.length;
  const hudPill = document.getElementById("hud-incident-pill");
  const hudCount = document.getElementById("hud-incident-count");

  if (count > 0) {
    const label = count === 1 ? "1 aviso" : `${count} avisos`;
    if (hudPill && hudCount) {
      hudCount.textContent = label;
      hudPill.classList.remove("hidden");
      hudPill.style.display = "inline-flex";
    }
  } else {
    if (hudPill) {
      hudPill.classList.add("hidden");
      hudPill.style.display = "none";
    }
  }
}

async function fetchLiveIncidents() {
  try {
    const res = await fetch("/api/incidents");
    if (!res.ok) return;
    const data = await res.json();
    updateIncidentBadges(data.incidents || []);
  } catch (e) {}
}

async function openIncidentsModal() {
  const modal = document.getElementById("incidents-modal");
  const listContainer = document.getElementById("incidents-list-container");
  if (!modal || !listContainer) return;

  try {
    const res = await fetch("/api/incidents");
    if (res.ok) {
      const data = await res.json();
      updateIncidentBadges(data.incidents || []);
    }
  } catch (e) {}

  renderIncidentsList(listContainer);
  modal.classList.remove("hidden");
  modal.style.display = "flex";
}

function closeIncidentsModal() {
  const modal = document.getElementById("incidents-modal");
  if (!modal) return;
  modal.classList.add("hidden");
  modal.style.display = "none";
}

function renderIncidentsList(container) {
  if (!currentIncidents || currentIncidents.length === 0) {
    container.innerHTML = `
      <div style="text-align:center; padding:2.5rem 1rem; color:var(--modal-text-muted);">
        <div style="font-size:2.5rem; margin-bottom:0.5rem;">✅</div>
        <div style="font-size:1.05rem; font-weight:600; color:var(--modal-text);">Todo el sistema funciona con normalidad</div>
        <div style="font-size:0.85rem; margin-top:4px;">No hay avisos de batería baja ni anomalías de tensión eléctrica.</div>
      </div>
    `;
    return;
  }

  container.innerHTML = currentIncidents.map(inc => {
    const isCrit = inc.severity === "critical";
    const bg = isCrit ? "rgba(239,68,68,0.12)" : "rgba(245,158,11,0.12)";
    const border = isCrit ? "rgba(239,68,68,0.4)" : "rgba(245,158,11,0.4)";
    const badgeColor = isCrit ? "#ef4444" : "#f59e0b";
    const badgeText = isCrit ? "Crítica" : "Aviso";
    const icon = inc.icon || (inc.type && inc.type.includes("battery") ? "🔋" : (inc.type && inc.type.includes("volt") ? "⚡" : "⚠️"));

    return `
      <div class="domos-modal-subcard" style="padding:1.1rem 1.25rem; border-radius:18px; border:1px solid ${border}; background:${bg}; display:flex; flex-direction:column; gap:0.6rem;">
        <div style="display:flex; align-items:flex-start; justify-content:space-between; gap:0.75rem;">
          <div style="display:flex; align-items:center; gap:0.65rem;">
            <span style="font-size:1.6rem; line-height:1;">${icon}</span>
            <div>
              <div style="font-weight:700; font-size:1rem; color:var(--modal-text);">${inc.title || "Incidencia"}</div>
              <div style="font-size:0.78rem; color:var(--modal-text-muted);">${inc.source || "Sistema"} · ${inc.timestamp || ""}</div>
            </div>
          </div>
          <span style="padding:0.25rem 0.65rem; border-radius:9999px; font-size:0.75rem; font-weight:700; background:${badgeColor}22; color:${badgeColor}; border:1px solid ${badgeColor}66;">
            ${badgeText}
          </span>
        </div>
        <div style="font-size:0.9rem; line-height:1.45; color:var(--modal-text);">
          ${inc.description || ""}
        </div>
        <div style="display:flex; justify-content:flex-end; margin-top:0.25rem;">
          <button class="liquid-action-pill neutral" onclick="dismissIncident('${inc.id}')" style="font-size:0.8rem; padding:0.35rem 0.85rem; cursor:pointer;">
            ✓ Silenciar / Revisado
          </button>
        </div>
      </div>
    `;
  }).join("");
}

window.dismissIncident = async function(incId) {
  try {
    const res = await fetch("/api/incidents/resolve", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id: incId })
    });
    if (res.ok) {
      const data = await res.json();
      updateIncidentBadges(data.incidents || []);
      const listContainer = document.getElementById("incidents-list-container");
      if (listContainer) renderIncidentsList(listContainer);
    }
  } catch (e) {}
};

async function dismissAllIncidents() {
  try {
    const res = await fetch("/api/incidents/resolve", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({})
    });
    if (res.ok) {
      const data = await res.json();
      updateIncidentBadges(data.incidents || []);
      closeIncidentsModal();
    }
  } catch (e) {}
}

document.getElementById("hud-incident-pill")?.addEventListener("click", openIncidentsModal);
document.getElementById("standby-incident-badge")?.addEventListener("click", openIncidentsModal);
document.getElementById("btn-incidents-close")?.addEventListener("click", closeIncidentsModal);
document.getElementById("btn-incidents-clear-all")?.addEventListener("click", dismissAllIncidents);
document.getElementById("incidents-modal")?.addEventListener("click", (e) => {
  if (e.target.id === "incidents-modal") closeIncidentsModal();
});

// Periodic incident polling every 30 seconds
setInterval(fetchLiveIncidents, 30000);
setTimeout(fetchLiveIncidents, 2000);

// --- Natural Touchpad Two-Finger Scrolling ---
document.querySelectorAll(".liquid-panel-body").forEach((panel) => {
  panel.addEventListener("wheel", (e) => {
    if (e.ctrlKey || Math.abs(e.deltaY) < 0.5) return;
    e.preventDefault();
    panel.scrollTop -= e.deltaY;
  }, { passive: false });
});

// --- Photo Source Modal (from Top-Right Badge) ---
function syncPhotoSourceModalUI() {
  document.querySelectorAll(".photo-mode-opt").forEach(btn => {
    btn.classList.toggle("is-active", btn.dataset.mode === carouselMode);
  });
  const mainFolderSel = document.getElementById("photo-folder-select");
  const modalFolderSel = document.getElementById("modal-photo-folder-select");
  if (mainFolderSel && modalFolderSel) {
    modalFolderSel.innerHTML = mainFolderSel.innerHTML;
    modalFolderSel.value = mainFolderSel.value;
  }
  const transSel = document.getElementById("modal-slide-transition-select");
  if (transSel) {
    transSel.value = carouselTransition;
  }
}

async function openPhotoSourceModal() {
  const m = document.getElementById("photo-source-modal");
  if (!m) return;
  await loadFolders();
  syncPhotoSourceModalUI();
  m.classList.remove("hidden");
  m.style.display = "flex";
}
document.getElementById("hud-photo-badge")?.addEventListener("click", openPhotoSourceModal);

document.getElementById("btn-photo-modal-close")?.addEventListener("click", () => {
  const m = document.getElementById("photo-source-modal");
  if (m) { m.classList.add("hidden"); m.style.display = "none"; }
});
document.getElementById("photo-source-modal")?.addEventListener("click", (e) => {
  if (e.target.id === "photo-source-modal") {
    e.target.classList.add("hidden");
    e.target.style.display = "none";
  }
});

document.querySelectorAll(".photo-mode-opt").forEach(btn => {
  btn.addEventListener("click", () => {
    const newMode = btn.dataset.mode;
    if (!newMode) return;
    carouselMode = newMode;
    localStorage.setItem("domos_carousel_mode", carouselMode);
    const sel = document.getElementById("carousel-mode-select");
    if (sel) sel.value = newMode;
    fetch("/api/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ carousel_mode: carouselMode })
    }).catch(() => {});
    syncPhotoSourceModalUI();
    showNextSlide();
    startSlideshow();
  });
});

document.getElementById("modal-photo-folder-select")?.addEventListener("change", (e) => {
  const mainSel = document.getElementById("photo-folder-select");
  if (mainSel) {
    mainSel.value = e.target.value;
    mainSel.dispatchEvent(new Event("change"));
  }
});

// --- Weather Manual City Search ---
async function searchWeatherCity() {
  const inp = document.getElementById("wmodal-city-input");
  const resBox = document.getElementById("wmodal-city-results");
  if (!inp || !resBox) return;
  const q = (inp.value || "").trim();
  if (q.length < 2) return;
  resBox.style.display = "flex";
  resBox.innerHTML = `<span style="font-size:0.85rem; color:var(--modal-text-muted);">Buscando "${q}"...</span>`;
  try {
    const r = await fetch(`https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(q)}&count=5&language=es&format=json`);
    const d = await r.json();
    const list = d.results || [];
    if (!list.length) {
      resBox.innerHTML = `<span style="font-size:0.85rem; color:#fbbf24;">Sin resultados para "${q}".</span>`;
      return;
    }
    resBox.innerHTML = "";
    list.forEach(item => {
      const label = [item.name, item.admin2 || item.admin1, item.country].filter(Boolean).join(", ");
      const btn = document.createElement("button");
      btn.className = "liquid-action-pill";
      btn.style.cssText = "cursor:pointer; font-size:0.82rem; padding:0.4rem 0.75rem; background:rgba(255,255,255,0.1); color:var(--modal-text);";
      btn.textContent = "📍 " + label;
      btn.addEventListener("click", async () => {
        localStorage.setItem("domos_weather_loc", JSON.stringify({
          name: label,
          lat: item.latitude,
          lon: item.longitude
        }));
        resBox.style.display = "none";
        inp.value = "";
        await updateWeather();
        openWeatherModal();
      });
      resBox.appendChild(btn);
    });
  } catch (e) {
    resBox.innerHTML = `<span style="font-size:0.85rem; color:#f87171;">Error buscando localidad.</span>`;
  }
}

document.getElementById("wmodal-city-search-btn")?.addEventListener("click", searchWeatherCity);
document.getElementById("wmodal-city-input")?.addEventListener("keydown", (e) => {
  if (e.key === "Enter") searchWeatherCity();
});

// --- Solar Panels Detail Modal ---
function renderSolarModalContent(solar, battery, extra, power) {
  const body = document.getElementById("solar-modal-body");
  if (!body) return;
  const s = (solar && solar.state) || {};
  const b = (battery && battery.state) || {};
  const ex = extra || {};
  const p = power || {};

  const watts = s.watts !== undefined ? s.watts : "--";
  const volts = s.volts !== undefined ? s.volts : (p.devices && p.devices[0] ? p.devices[0].volts : "--");
  const amps = s.amps !== undefined ? s.amps : "--";
  const isProducing = Number(s.watts || 0) > 0;
  const statusLabel = isProducing ? "🟢 Produciendo" : (s.state ? "🟡 Standby (Listo)" : "🔴 Apagado");
  const totalKwh = typeof ex.total_forward_energy === "number"
    ? (ex.total_forward_energy / 100).toLocaleString("es-ES", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + " kWh"
    : "Calculando...";
  const faultText = ex.fault === 0 ? "✅ Sin fallos" : (ex.fault !== undefined ? `⚠️ Código ${ex.fault}` : "—");
  const breaker = ex.breaker_number || "—";
  const updated = s.updated_at ? new Date(s.updated_at).toLocaleTimeString("es-ES") : (p.updated_at || "—");

  // Power Consumption Metrics
  const isChint = Boolean(p.has_meter && (p.total_consumption_watts > 0 || (s.home_consumption_w && s.home_consumption_w > 0)));
  const totalConsW = typeof p.total_consumption_watts === "number" ? p.total_consumption_watts : 0;
  const solarW = typeof s.watts === "number" ? s.watts : 0;
  const netBalNum = typeof p.net_balance_watts === "number" ? p.net_balance_watts : (solarW - totalConsW);
  const isSurplus = netBalNum >= 0;
  const netBalText = `${Math.abs(Math.round(netBalNum))} W`;

  // Autoconsumo: Minimo entre lo generado y lo consumido
  const autoconsumoW = Math.max(0, Math.round(Math.min(solarW, totalConsW)));

  // Cobertura: % del consumo cubierto por solar
  const coberturaPct = totalConsW > 0 
    ? Math.min(100, Math.round((autoconsumoW / totalConsW) * 100)) + "%"
    : (solarW > 0 ? "100%" : "0%");

  const netLabel = isSurplus
    ? `+${netBalText} Excedente Inyectado a Red`
    : `${netBalText} Importación de Red`;
  const netColor = isSurplus ? "#10b981" : "#38bdf8";
  const consTitle = isChint ? "Consumo Vivienda (CHINT)" : "Consumo Monitorizado";
  const consSub = isChint ? "⚡ Medidor General Vivienda" : "Enchufes y Cargas";
  const chintStatus = isChint ? "🟢 En Línea (RS-485 Modbus)" : "🟡 Esperando Medidor (RS-485)";

  // Monitored Devices List
  const devList = (p.devices || []).map(d => {
    const dWatts = d.watts !== undefined ? `${d.watts} W` : "-- W";
    const statusPill = d.on 
      ? `<span style="font-size:0.72rem; padding:0.15rem 0.5rem; border-radius:999px; background:rgba(16,185,129,0.15); color:#10b981; border:1px solid rgba(16,185,129,0.3);">Activo</span>`
      : `<span style="font-size:0.72rem; padding:0.15rem 0.5rem; border-radius:999px; background:rgba(255,255,255,0.06); color:var(--modal-text-muted);">Apagado</span>`;
    return `
      <div class="domos-modal-subcard" style="padding:0.75rem 0.95rem; border-radius:14px; display:flex; justify-content:space-between; align-items:center;">
        <div>
          <div style="font-weight:700; font-size:0.9rem; color:var(--modal-text);">${d.name}</div>
          <div style="font-size:0.75rem; color:var(--modal-text-muted);">${d.volts} V · ${d.amps} A</div>
        </div>
        <div style="text-align:right; display:flex; flex-direction:column; align-items:flex-end; gap:0.2rem;">
          <div style="font-size:1.15rem; font-weight:800; color:#38bdf8;">${dWatts}</div>
          ${statusPill}
        </div>
      </div>
    `;
  }).join("") || `<p style="font-size:0.8rem; color:var(--modal-text-muted); margin:0;">No hay enchufes de medición disponibles en LAN.</p>`;

  body.innerHTML = `
    <!-- Fila 1: Generación Solar y Consumo -->
    <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(140px, 1fr)); gap:0.75rem;">
      <div class="domos-modal-subcard" style="padding:0.85rem; border-radius:16px;">
        <div style="font-size:0.74rem; color:var(--modal-text-muted); text-transform:uppercase; font-weight:600;">Generación Solar</div>
        <div style="font-size:1.55rem; font-weight:800; color:#fbbf24; margin-top:2px;">${watts} W</div>
        <div style="font-size:0.75rem; color:var(--modal-text-muted);">${statusLabel}</div>
      </div>
      <div class="domos-modal-subcard" style="padding:0.85rem; border-radius:16px;">
        <div style="font-size:0.74rem; color:var(--modal-text-muted); text-transform:uppercase; font-weight:600;">${consTitle}</div>
        <div style="font-size:1.55rem; font-weight:800; color:#38bdf8; margin-top:2px;">${totalConsW} W</div>
        <div style="font-size:0.75rem; color:${isChint ? '#10b981' : 'var(--modal-text-muted)'}; font-weight:${isChint ? '600' : 'normal'};">${consSub}</div>
      </div>
      <div class="domos-modal-subcard" style="padding:0.85rem; border-radius:16px;">
        <div style="font-size:0.74rem; color:var(--modal-text-muted); text-transform:uppercase; font-weight:600;">Energía Solar Total</div>
        <div style="font-size:1.35rem; font-weight:800; color:#10b981; margin-top:2px;">${totalKwh}</div>
        <div style="font-size:0.75rem; color:var(--modal-text-muted);">${faultText}</div>
      </div>
    </div>

    <!-- Desglose Microinversor Hoymiles -->
    ${(ex.port1_watts !== undefined || (s.port1 && s.port1.watts !== undefined)) ? `
    <div class="domos-modal-subcard" style="padding:0.85rem 1rem; border-radius:16px; background:rgba(251,191,36,0.04); border:1px solid rgba(251,191,36,0.25);">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.6rem;">
        <div style="font-size:0.75rem; color:#fbbf24; font-weight:700; text-transform:uppercase; letter-spacing:0.5px;">⚡ Microinversor Hoymiles (HMS)</div>
        <div style="font-size:0.72rem; color:var(--modal-text-muted);">S/N: <b>${ex.inverter_sn || s.inverter_sn || '1164749041'}</b> · Temp: <b>${ex.temperature ?? s.temperature ?? '--'} °C</b></div>
      </div>
      <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap:0.65rem;">
        <div class="domos-mini-stat">
          <div style="font-size:0.72rem; color:var(--modal-text-muted); font-weight:600;">PANEL 1</div>
          <div style="font-size:1.15rem; font-weight:800; color:#fbbf24; margin-top:2px;">${ex.port1_watts ?? s.port1?.watts ?? '--'} W</div>
          <div style="font-size:0.7rem; color:var(--modal-text-muted);">${ex.port1_volts ?? s.port1?.volts ?? '--'} V · ${ex.port1_amps ?? s.port1?.amps ?? '--'} A</div>
        </div>
        <div class="domos-mini-stat">
          <div style="font-size:0.72rem; color:var(--modal-text-muted); font-weight:600;">PANEL 2</div>
          <div style="font-size:1.15rem; font-weight:800; color:#fbbf24; margin-top:2px;">${ex.port2_watts ?? s.port2?.watts ?? '--'} W</div>
          <div style="font-size:0.7rem; color:var(--modal-text-muted);">${ex.port2_volts ?? s.port2?.volts ?? '--'} V · ${ex.port2_amps ?? s.port2?.amps ?? '--'} A</div>
        </div>
        ${(ex.port3_watts !== undefined || (s.port3 && s.port3.watts !== undefined)) ? `
        <div class="domos-mini-stat">
          <div style="font-size:0.72rem; color:var(--modal-text-muted); font-weight:600;">PANEL 3</div>
          <div style="font-size:1.15rem; font-weight:800; color:#fbbf24; margin-top:2px;">${ex.port3_watts ?? s.port3?.watts ?? '--'} W</div>
          <div style="font-size:0.7rem; color:var(--modal-text-muted);">${ex.port3_volts ?? s.port3?.volts ?? '--'} V · ${ex.port3_amps ?? s.port3?.amps ?? '--'} A</div>
        </div>
        <div class="domos-mini-stat">
          <div style="font-size:0.72rem; color:var(--modal-text-muted); font-weight:600;">PANEL 4</div>
          <div style="font-size:1.15rem; font-weight:800; color:#fbbf24; margin-top:2px;">${ex.port4_watts ?? s.port4?.watts ?? '--'} W</div>
          <div style="font-size:0.7rem; color:var(--modal-text-muted);">${ex.port4_volts ?? s.port4?.volts ?? '--'} V · ${ex.port4_amps ?? s.port4?.amps ?? '--'} A</div>
        </div>
        ` : ''}
      </div>
    </div>
    ` : ''}

    <!-- Sección Medidor General CHINT -->
    <div class="domos-modal-subcard" style="padding:0.85rem 1rem; border-radius:16px; background:rgba(16,185,129,0.04); border:1px solid rgba(16,185,129,0.25);">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.6rem;">
        <div style="font-size:0.75rem; color:#10b981; font-weight:700; text-transform:uppercase; letter-spacing:0.5px;">⚡ Contador de Red General (CHINT DDSU666)</div>
        <div style="font-size:0.72rem; color:var(--modal-text-muted);">${chintStatus}</div>
      </div>
      <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap:0.65rem;">
        <div class="domos-mini-stat">
          <div style="font-size:0.72rem; color:var(--modal-text-muted); font-weight:600;">FLUJO ACOMETIDA RED</div>
          <div style="font-size:1.15rem; font-weight:800; color:${isChint ? netColor : '#94a3b8'}; margin-top:2px;">${isChint ? (isSurplus ? '-' + netBalText : '+' + netBalText) : '-- W'}</div>
          <div style="font-size:0.7rem; color:var(--modal-text-muted);">${isChint ? (isSurplus ? 'Exportando a Red' : 'Importando de Red') : 'Sin lectura activa en DTU'}</div>
        </div>
        <div class="domos-mini-stat">
          <div style="font-size:0.72rem; color:var(--modal-text-muted); font-weight:600;">AUTOCONSUMO SOLAR</div>
          <div style="font-size:1.15rem; font-weight:800; color:#38bdf8; margin-top:2px;">${isChint ? autoconsumoW + ' W' : (solarW > 0 ? Math.round(solarW) + ' W (Est.)' : '0 W')}</div>
          <div style="font-size:0.7rem; color:var(--modal-text-muted);">${isChint ? 'Aprovechado en Directo' : 'Absorbido por la vivienda'}</div>
        </div>
        <div class="domos-mini-stat">
          <div style="font-size:0.72rem; color:var(--modal-text-muted); font-weight:600;">COBERTURA SOLAR</div>
          <div style="font-size:1.15rem; font-weight:800; color:#10b981; margin-top:2px;">${isChint ? coberturaPct : (solarW > 0 ? 'Cubriendo Cargas' : '0%')}</div>
          <div style="font-size:0.7rem; color:var(--modal-text-muted);">${isChint ? 'Autosuficiencia Actual' : 'Alimentando el hogar'}</div>
        </div>
      </div>
    </div>

    <!-- Fila 2: Balance Neto Hogar -->
    <div class="domos-modal-subcard" style="padding:0.95rem 1.15rem; border-radius:18px; display:flex; justify-content:space-between; align-items:center; background:linear-gradient(135deg, rgba(255,255,255,0.04), rgba(56,189,248,0.06)); border:1px solid rgba(56,189,248,0.25);">
      <div>
        <div style="font-size:0.75rem; color:var(--modal-text-muted); text-transform:uppercase; font-weight:600;">Balance Energético en Tiempo Real</div>
        <div style="font-size:1.25rem; font-weight:800; color:${isChint ? netColor : '#38bdf8'}; margin-top:2px;">${isChint ? netLabel : '⚡ ' + solarW + ' W Generación Solar'}</div>
        ${!isChint ? `<div style="font-size:0.72rem; color:var(--modal-text-muted); margin-top:2px;">Prioridad total a consumos de la casa antes de exportar a red</div>` : ''}
      </div>
      <button class="liquid-action-pill" id="btn-solar-to-schedules" style="font-size:0.78rem; padding:0.4rem 0.8rem; cursor:pointer; color:#38bdf8; border-color:rgba(56,189,248,0.4);">
        ⏱️ Programación
      </button>
    </div>

    <!-- Fila 3: Consumo Desglosado de Enchufes -->
    <div style="display:flex; flex-direction:column; gap:0.6rem;">
      <div style="font-size:0.82rem; font-weight:700; color:var(--modal-text); text-transform:uppercase; letter-spacing:0.5px;">Consumo de Enchufes Inteligentes (W)</div>
      <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(200px, 1fr)); gap:0.65rem;">
        ${devList}
      </div>
    </div>

    <!-- Fila 3.5: Gráfica de Consumo por Enchufe (Diario / Mensual / Anual) -->
    <div class="domos-modal-subcard" id="plug-power-chart-card" style="padding:0.95rem 1.15rem; border-radius:18px; display:flex; flex-direction:column; gap:0.65rem;">
      <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.5rem;">
        <div>
          <div id="plug-chart-title" style="font-size:0.86rem; font-weight:700; color:var(--modal-text);">📊 Evolución de Consumo por Enchufe (kWh)</div>
          <div id="plug-chart-subtitle" style="font-size:0.72rem; color:var(--modal-text-muted);">Cada curva representa un enchufe con medidor integrado</div>
        </div>
        <div class="plug-period-tabs" style="display:inline-flex; background:rgba(148,163,184,0.16); padding:3px; border-radius:11px; gap:3px;">
          <button type="button" class="plug-period-btn" data-period="daily">Diario</button>
          <button type="button" class="plug-period-btn" data-period="monthly">Mensual</button>
          <button type="button" class="plug-period-btn" data-period="yearly">Anual</button>
        </div>
      </div>
      <div id="plug-chart-legend" style="display:flex; flex-wrap:wrap; gap:0.4rem;"></div>
      <div id="plug-chart-svg-wrap" style="position:relative; width:100%; height:225px;">
        <p style="font-size:0.8rem; color:var(--modal-text-muted); margin:0;">Cargando curvas de consumo...</p>
      </div>
    </div>

    <!-- Fila 4: Red y Medidor -->
    <div style="padding:0.75rem 1rem; border-radius:14px; background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08); display:flex; justify-content:space-between; align-items:center;">
      <span style="font-size:0.78rem; color:var(--modal-text-muted);">Tensión de Red: <strong style="color:var(--modal-text);">${volts} V</strong> · Disyuntor: ${breaker}</span>
      <span style="font-size:0.75rem; color:var(--modal-text-muted);">Actualizado: ${updated}</span>
    </div>
  `;

  initPlugPowerChartControls();

  document.getElementById("btn-solar-to-schedules")?.addEventListener("click", () => {
    const sModal = document.getElementById("solar-modal");
    if (sModal) { sModal.classList.add("hidden"); sModal.style.display = "none"; }
    openSchedulesModal();
  });
}

async function openSolarModal() {
  const modal = document.getElementById("solar-modal");
  if (!modal) return;
  modal.classList.remove("hidden");
  modal.style.display = "flex";
  renderSolarModalContent({ state: deviceData.solar?.state }, { state: deviceData.battery?.state }, {}, {});
  try {
    const res = await fetch("/api/solar/details");
    if (res.ok) {
      const data = await res.json();
      renderSolarModalContent(data.solar, data.battery, data.extra, data.power);
    }
  } catch (e) {}
}

document.getElementById("hud-solar-pill")?.addEventListener("click", openSolarModal);
document.getElementById("btn-solar-modal-close")?.addEventListener("click", () => {
  const m = document.getElementById("solar-modal");
  if (m) { m.classList.add("hidden"); m.style.display = "none"; }
});
document.getElementById("solar-modal")?.addEventListener("click", (e) => {
  if (e.target.id === "solar-modal") {
    e.target.classList.add("hidden");
    e.target.style.display = "none";
  }
});

// --- Smart Plug Scheduling & Timers Modal ---
let selectedCountdownMins = 15;

function openSchedulesModal() {
  const modal = document.getElementById("schedules-modal");
  if (!modal) return;
  modal.classList.remove("hidden");
  modal.style.display = "flex";
  populateScheduleDeviceSelects();
  loadSchedulesList();
}

function closeSchedulesModal() {
  const modal = document.getElementById("schedules-modal");
  if (modal) {
    modal.classList.add("hidden");
    modal.style.display = "none";
  }
}

document.getElementById("btn-open-schedules")?.addEventListener("click", openSchedulesModal);
document.getElementById("btn-schedules-modal-close")?.addEventListener("click", closeSchedulesModal);
document.getElementById("schedules-modal")?.addEventListener("click", (e) => {
  if (e.target.id === "schedules-modal") closeSchedulesModal();
});

// Tab Switcher for Schedules Modal
document.getElementById("tab-btn-schedules-list")?.addEventListener("click", () => {
  document.getElementById("tab-btn-schedules-list").style.background = "rgba(56,189,248,0.2)";
  document.getElementById("tab-btn-schedules-list").style.borderColor = "#38bdf8";
  document.getElementById("tab-btn-schedules-list").style.color = "#fff";
  document.getElementById("tab-btn-schedules-countdown").style.background = "";
  document.getElementById("tab-btn-schedules-countdown").style.borderColor = "";
  document.getElementById("tab-btn-schedules-countdown").style.color = "";
  document.getElementById("tab-pane-schedules-list")?.classList.remove("hidden");
  document.getElementById("tab-pane-schedules-countdown")?.classList.add("hidden");
});

document.getElementById("tab-btn-schedules-countdown")?.addEventListener("click", () => {
  document.getElementById("tab-btn-schedules-countdown").style.background = "rgba(56,189,248,0.2)";
  document.getElementById("tab-btn-schedules-countdown").style.borderColor = "#38bdf8";
  document.getElementById("tab-btn-schedules-countdown").style.color = "#fff";
  document.getElementById("tab-btn-schedules-list").style.background = "";
  document.getElementById("tab-btn-schedules-list").style.borderColor = "";
  document.getElementById("tab-btn-schedules-list").style.color = "";
  document.getElementById("tab-pane-schedules-countdown")?.classList.remove("hidden");
  document.getElementById("tab-pane-schedules-list")?.classList.add("hidden");
});

function populateScheduleDeviceSelects() {
  const schSel = document.getElementById("sch-input-device");
  const cdSel = document.getElementById("countdown-device-select");
  if (!schSel && !cdSel) return;

  const options = [
    { id: "bf75842d28c31e9943g0wz", name: "Termo Eléctrico" },
    { id: "1728645494b97e138251", name: "Secatoallas" },
    { id: "bf2989a92a26b9381drtlg", name: "Cargador Domos (Asus)" },
    { id: "36074611d8f15bada4e6", name: "Regleta (Tomas 1-5)" },
    { id: "1000c0327f", name: "Altar (eWeLink)" },
    { id: "1000b0ef21", name: "Fuente (eWeLink)" },
    { id: "bf3aa35b1531ceffbezyrx", name: "Jardín" }
  ];

  // Also include any plugs from deviceData if available
  if (deviceData.plugs) {
    deviceData.plugs.forEach(p => {
      if (!options.some(o => o.id === p.id)) {
        options.push({ id: p.id, name: p.name || "Enchufe" });
      }
    });
  }

  const html = options.map(o => `<option value="${o.id}">${o.name}</option>`).join("");
  if (schSel) schSel.innerHTML = html;
  if (cdSel) cdSel.innerHTML = html;
}

// Collapsible Add Schedule Form
document.getElementById("btn-toggle-add-schedule")?.addEventListener("click", () => {
  const form = document.getElementById("form-add-schedule");
  if (form) form.classList.toggle("hidden");
});
document.getElementById("btn-cancel-add-schedule")?.addEventListener("click", () => {
  const form = document.getElementById("form-add-schedule");
  if (form) form.classList.add("hidden");
});

async function loadSchedulesList() {
  const container = document.getElementById("schedules-items-list");
  if (!container) return;
  try {
    const res = await fetch("/api/schedules");
    if (!res.ok) throw new Error("Error fetching schedules");
    const list = await res.json();
    renderSchedulesList(list);
  } catch (e) {
    container.innerHTML = `<p style="color:#f87171; font-size:0.85rem; margin:0;">Error cargando horarios: ${e.message}</p>`;
  }
}

function renderSchedulesList(schedules) {
  const container = document.getElementById("schedules-items-list");
  if (!container) return;
  if (!schedules || schedules.length === 0) {
    container.innerHTML = `<p style="color:var(--modal-text-muted); font-size:0.85rem; margin:0;">No hay horarios programados. Toca "➕ Nueva Regla" para añadir uno.</p>`;
    return;
  }

  container.innerHTML = schedules.map(s => {
    const isEnabled = s.enabled !== false;
    const actionBadge = s.action === "on" 
      ? `<span style="font-size:0.75rem; font-weight:700; color:#10b981;">🟢 Encender</span>`
      : `<span style="font-size:0.75rem; font-weight:700; color:#ef4444;">🔴 Apagar</span>`;
    const devName = s.device_name || s.name || "Dispositivo";

    return `
      <div class="domos-modal-subcard" style="padding:0.85rem 1.1rem; border-radius:16px; display:flex; justify-content:space-between; align-items:center; gap:0.75rem;">
        <div style="display:flex; align-items:center; gap:0.85rem;">
          <div style="font-size:1.45rem; font-weight:800; color:#38bdf8; min-width:65px;">${s.time}</div>
          <div>
            <div style="font-weight:700; font-size:0.92rem; color:var(--modal-text);">${s.name || devName}</div>
            <div style="font-size:0.75rem; color:var(--modal-text-muted); display:flex; align-items:center; gap:0.4rem; margin-top:2px;">
              ${actionBadge} · ${devName} · Diariamente
            </div>
          </div>
        </div>
        <div style="display:flex; align-items:center; gap:0.5rem;">
          <button class="liquid-action-pill btn-toggle-sch" data-id="${s.id}" style="font-size:0.75rem; padding:0.3rem 0.65rem; cursor:pointer; ${isEnabled ? 'border-color:#10b981; color:#10b981;' : 'border-color:var(--modal-input-border); color:var(--modal-text-muted);'}">
            ${isEnabled ? 'Activo' : 'Pausado'}
          </button>
          <button class="liquid-action-pill btn-delete-sch" data-id="${s.id}" style="font-size:0.75rem; padding:0.3rem 0.55rem; cursor:pointer; color:#ef4444; border-color:rgba(239,68,68,0.4);">
            🗑️
          </button>
        </div>
      </div>
    `;
  }).join("");

  // Attach toggle and delete listeners
  container.querySelectorAll(".btn-toggle-sch").forEach(btn => {
    btn.addEventListener("click", async (e) => {
      const id = e.currentTarget.dataset.id;
      try {
        await fetch(`/api/schedules/${id}/toggle`, { method: "POST" });
        loadSchedulesList();
      } catch (err) {}
    });
  });

  container.querySelectorAll(".btn-delete-sch").forEach(btn => {
    btn.addEventListener("click", async (e) => {
      const id = e.currentTarget.dataset.id;
      try {
        await fetch(`/api/schedules/${id}`, { method: "DELETE" });
        loadSchedulesList();
      } catch (err) {}
    });
  });
}

// Save new schedule
document.getElementById("btn-save-new-schedule")?.addEventListener("click", async () => {
  const devSel = document.getElementById("sch-input-device");
  const actSel = document.getElementById("sch-input-action");
  const timeInp = document.getElementById("sch-input-time");
  const nameInp = document.getElementById("sch-input-name");

  const devId = devSel ? devSel.value : "";
  const devName = devSel && devSel.selectedOptions[0] ? devSel.selectedOptions[0].text : "Dispositivo";
  const action = actSel ? actSel.value : "on";
  const timeVal = timeInp ? timeInp.value : "13:00";
  const customName = nameInp && nameInp.value.trim() ? nameInp.value.trim() : `${action === 'on' ? 'Encender' : 'Apagar'} ${devName}`;

  if (!devId || !timeVal) return;

  const newSchedule = {
    name: customName,
    device_id: devId,
    device_name: devName,
    code: "switch_1",
    action: action,
    time: timeVal,
    days: [1, 2, 3, 4, 5, 6, 7],
    enabled: true
  };

  try {
    await fetch("/api/schedules", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(newSchedule)
    });
    document.getElementById("form-add-schedule")?.classList.add("hidden");
    if (nameInp) nameInp.value = "";
    loadSchedulesList();
  } catch (err) {
    alert("Error guardando horario: " + err.message);
  }
});

// Countdown preset pill selection
document.querySelectorAll(".countdown-preset-pill").forEach(pill => {
  pill.addEventListener("click", (e) => {
    document.querySelectorAll(".countdown-preset-pill").forEach(p => p.classList.remove("active"));
    e.currentTarget.classList.add("active");
    selectedCountdownMins = parseInt(e.currentTarget.dataset.mins, 10) || 15;
  });
});

// Start Countdown Button
document.getElementById("btn-start-countdown")?.addEventListener("click", async () => {
  const devSel = document.getElementById("countdown-device-select");
  const actSel = document.getElementById("countdown-action-select");
  const feedback = document.getElementById("countdown-feedback");

  const devId = devSel ? devSel.value : "";
  const devName = devSel && devSel.selectedOptions[0] ? devSel.selectedOptions[0].text : "Dispositivo";
  const action = actSel ? actSel.value : "off";

  if (!devId) return;

  if (feedback) feedback.textContent = "Programando...";
  try {
    const res = await fetch("/api/devices/countdown", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        device_id: devId,
        minutes: selectedCountdownMins,
        action: action,
        code: "switch_1"
      })
    });
    const d = await res.json();
    if (feedback) {
      feedback.textContent = `✅ ${d.message || 'Temporizador iniciado'}`;
      setTimeout(() => { if (feedback) feedback.textContent = ""; }, 4000);
    }
  } catch (err) {
    if (feedback) feedback.textContent = `❌ Error: ${err.message}`;
  }
});

// --- Battery Health & Lifecycle Modal ---
async function openBatteryModal() {
  const modal = document.getElementById("battery-modal");
  if (!modal) return;
  modal.classList.remove("hidden");
  modal.style.display = "flex";

  try {
    const res = await fetch("/api/system/battery");
    if (res.ok) {
      const data = await res.json();
      renderBatteryModalContent(data);
    }
  } catch (e) {
    console.error("Error loading battery data:", e);
  }
}

function renderBatteryModalContent(data) {
  if (!data) return;
  const tel = data.telemetry || {};
  const stats = data.stats || {};
  const cycles = data.cycles || [];
  const curPhase = data.current_phase || {};

  const cap = tel.capacity ?? curPhase.current_pct ?? "--";
  const status = tel.status || (curPhase.type === "charge" ? "Charging" : "Discharging");
  const isCharging = status === "Charging" || curPhase.type === "charge";
  const health = tel.health_pct ?? 51.6;
  const power = tel.power_w ?? 4.5;
  const v = tel.voltage_v ?? 7.62;
  const i = tel.current_a ? Math.round(tel.current_a * 1000) : 587;
  const cyclesCount = tel.cycle_count ?? 401;
  const cf = tel.charge_full_mah ?? 2581;
  const cfd = tel.charge_full_design_mah ?? 5000;

  // Header status badge
  const badge = document.getElementById("bat-modal-status-badge");
  if (badge) {
    const phaseMin = curPhase.elapsed_min != null ? ` · Lleva ${curPhase.elapsed_min}m` : "";
    badge.textContent = isCharging ? `⚡ Cargando (30% ➔ 70%)${phaseMin}` : `🔋 Descargando (70% ➔ 30%)${phaseMin}`;
    badge.style.color = isCharging ? "#fbbf24" : "#10b981";
    badge.style.background = isCharging ? "rgba(251,191,36,0.15)" : "rgba(16,185,129,0.15)";
    badge.style.borderColor = isCharging ? "rgba(251,191,36,0.3)" : "rgba(16,185,129,0.3)";
  }

  // Cards
  const elLevel = document.getElementById("bat-modal-level");
  if (elLevel) elLevel.textContent = `${cap}%`;
  const elHealth = document.getElementById("bat-modal-health");
  if (elHealth) {
    elHealth.textContent = `${health}%`;
    elHealth.style.color = health >= 50 ? "#10b981" : (health >= 35 ? "#fbbf24" : "#f43f5e");
  }
  const elMah = document.getElementById("bat-modal-mah");
  if (elMah) elMah.textContent = `${cf.toLocaleString()} / ${cfd.toLocaleString()} mAh`;
  const elPower = document.getElementById("bat-modal-power");
  if (elPower) elPower.textContent = `${power} W`;
  const elVi = document.getElementById("bat-modal-vi");
  if (elVi) elVi.textContent = `${v} V · ${i} mA`;
  const elCycles = document.getElementById("bat-modal-cycles");
  if (elCycles) elCycles.textContent = String(cyclesCount);

  // Health bar & diag
  const bar = document.getElementById("bat-modal-health-bar");
  if (bar) {
    bar.style.width = `${Math.min(100, Math.max(5, health))}%`;
    bar.style.background = health >= 50 ? "linear-gradient(90deg, #10b981, #38bdf8)" : (health >= 35 ? "linear-gradient(90deg, #fbbf24, #f59e0b)" : "linear-gradient(90deg, #f43f5e, #e11d48)");
  }
  const diagBadge = document.getElementById("bat-modal-diag-badge");
  const diagText = document.getElementById("bat-modal-diag-text");
  if (diagBadge && diagText) {
    if (health >= 45) {
      diagBadge.textContent = "Estable y Segura";
      diagBadge.style.color = "#10b981";
      diagText.textContent = `La celda conserva ${cf.toLocaleString()} mAh de los ${cfd.toLocaleString()} mAh de fábrica (${health}% de salud). El ciclado automático en el rango seguro (30% - 70%) evita hinchamientos y prolonga la vida útil de las celdas.`;
    } else if (health >= 30) {
      diagBadge.textContent = "Desgaste Moderado";
      diagBadge.style.color = "#fbbf24";
      diagText.textContent = `Capacidad reducida (${cf.toLocaleString()} mAh). Pérdida de autonomía normal por ciclos de uso. La protección activa 30%-70% previene calentamiento y deformación.`;
    } else {
      diagBadge.textContent = "⚠️ Reemplazo Aconsejado";
      diagBadge.style.color = "#f43f5e";
      diagText.textContent = `Capacidad crítica por debajo del 30%. Se recomienda reemplazar la batería para evitar que las celdas se hinchen o pierdan estabilidad química.`;
    }
  }

  // Autonomy benchmarks
  const elDay = document.getElementById("bat-modal-avg-day");
  if (elDay) elDay.textContent = `~${stats.avg_discharge_day_min || 75} min`;
  const elNight = document.getElementById("bat-modal-avg-night");
  if (elNight) {
    const nm = stats.avg_discharge_night_min || 175;
    elNight.textContent = `~${Math.floor(nm/60)}h ${nm%60}m`;
  }
  const elChg = document.getElementById("bat-modal-avg-charge");
  if (elChg) elChg.textContent = `~${stats.avg_charge_min || 36} min`;

  // Visual Chart (SVG Bars)
  const chartBox = document.getElementById("bat-modal-chart");
  if (chartBox) {
    const chartCycles = cycles.slice(0, 16).reverse();
    if (chartCycles.length === 0) {
      chartBox.innerHTML = '<span style="font-size:0.8rem; color:var(--modal-text-muted); margin:auto;">Sin datos suficientes de ciclos todavía</span>';
    } else {
      const maxDur = Math.max(180, ...chartCycles.map(c => c.duration_min || 0));
      chartBox.innerHTML = chartCycles.map(c => {
        const d = c.duration_min || 0;
        const hPct = Math.max(14, Math.min(100, Math.round((d / maxDur) * 100)));
        let color = "#fbbf24";
        let icon = "⚡";
        let label = "Carga";
        if (c.type === "discharge") {
          if (c.mode === "night") { color = "#a78bfa"; icon = "🌙"; label = "Noche"; }
          else { color = "#10b981"; icon = "☀️"; label = "Día"; }
        }
        return `
          <div style="flex:1; min-width:28px; height:100%; display:flex; flex-direction:column; align-items:center; justify-content:flex-end; gap:3px;" title="${label}: ${d} min (${c.start_pct}% ➔ ${c.end_pct}%) [${c.start_time}]">
            <span style="font-size:0.65rem; color:var(--modal-text-muted); font-weight:700;">${d}m</span>
            <div style="width:100%; height:${hPct}%; max-height:85px; background:${color}; border-radius:6px; opacity:0.88; transition:height 0.4s ease;"></div>
            <span style="font-size:0.65rem;">${icon}</span>
          </div>
        `;
      }).join("");
    }
  }

  // Cycles Table
  const listEl = document.getElementById("bat-modal-cycles-list");
  if (listEl) {
    if (cycles.length === 0) {
      listEl.innerHTML = '<div style="font-size:0.8rem; color:var(--modal-text-muted);">Sin ciclos registrados todavía.</div>';
    } else {
      listEl.innerHTML = cycles.slice(0, 8).map(c => {
        const isC = c.type === "charge";
        const isN = c.mode === "night";
        const icon = isC ? "⚡" : (isN ? "🌙" : "☀️");
        const title = isC ? "Carga completa (30% ➔ 70%)" : (isN ? "Descarga nocturna (Pantalla apagada)" : "Descarga diurna (En uso activo)");
        const tagColor = isC ? "#fbbf24" : (isN ? "#a78bfa" : "#10b981");
        return `
          <div style="display:flex; align-items:center; justify-content:space-between; padding:0.45rem 0.65rem; background:rgba(255,255,255,0.03); border-radius:12px; font-size:0.8rem;">
            <div style="display:flex; align-items:center; gap:0.55rem;">
              <span>${icon}</span>
              <div>
                <div style="font-weight:600; color:var(--modal-text);">${title}</div>
                <div style="font-size:0.72rem; color:var(--modal-text-muted);">${c.start_time} · ${c.start_pct}% ➔ ${c.end_pct}%</div>
              </div>
            </div>
            <div style="font-weight:700; color:${tagColor};">${c.duration_min} min</div>
          </div>
        `;
      }).join("");
    }
  }
}

document.getElementById("battery-widget")?.addEventListener("click", openBatteryModal);
document.getElementById("btn-battery-modal-close")?.addEventListener("click", () => {
  const m = document.getElementById("battery-modal");
  if (m) { m.classList.add("hidden"); m.style.display = "none"; }
});
document.getElementById("battery-modal")?.addEventListener("click", (e) => {
  if (e.target.id === "battery-modal") {
    e.target.classList.add("hidden");
    e.target.style.display = "none";
  }
});

// ========================================================
// CLIMATE HISTORY & TEMPORAL EVOLUTION MODAL
// ========================================================
let climateHistoryCurrentMonth = null;
let climateHistoryCurrentMetric = "temperature";
let climateHistoryDisabledSensors = new Set();
let climateHistoryData = null;
let climateChartHoverIndex = null;

async function openClimateHistoryModal(initialMetric = null) {
  const modal = document.getElementById("climate-history-modal");
  if (!modal) return;
  modal.classList.remove("hidden");
  modal.style.display = "flex";

  if (initialMetric) climateHistoryCurrentMetric = initialMetric;

  if (!climateHistoryCurrentMonth) {
    const now = new Date();
    const y = now.getFullYear();
    const m = String(now.getMonth() + 1).padStart(2, "0");
    climateHistoryCurrentMonth = `${y}-${m}`;
  }

  syncClimateMonthYearSelects();
  await fetchAndRenderClimateHistory();
}

function closeClimateHistoryModal() {
  const modal = document.getElementById("climate-history-modal");
  if (!modal) return;
  modal.classList.add("hidden");
  modal.style.display = "none";
  climateChartHoverIndex = null;
  const tip = document.getElementById("climate-chart-tooltip");
  if (tip) tip.style.display = "none";
}

function syncClimateMonthYearSelects() {
  if (!climateHistoryCurrentMonth) return;
  const [y, m] = climateHistoryCurrentMonth.split("-");
  const monthSel = document.getElementById("climate-month-select");
  const yearSel = document.getElementById("climate-year-select");
  if (monthSel) monthSel.value = String(parseInt(m, 10));
  if (yearSel) yearSel.value = y;
}

async function fetchAndRenderClimateHistory() {
  try {
    const res = await fetch(`/api/climate/history?month=${climateHistoryCurrentMonth}&metric=${climateHistoryCurrentMetric}`);
    if (res.ok) {
      climateHistoryData = await res.json();
      renderClimateHistoryUI();
    }
  } catch (err) {
    console.error("Error loading climate history:", err);
  }
}

function renderClimateHistoryUI() {
  if (!climateHistoryData) return;

  const data = climateHistoryData;
  const unit = data.unit || "°C";
  const sensors = data.sensors || [];
  const points = data.points || [];

  // 1. Metric buttons styling
  document.querySelectorAll(".climate-metric-btn").forEach(btn => {
    const m = btn.getAttribute("data-metric");
    btn.classList.toggle("active", m === climateHistoryCurrentMetric);
    if (m === climateHistoryCurrentMetric) {
      btn.style.background = "rgba(6,182,212,0.22)";
      btn.style.color = "#38bdf8";
      btn.style.borderColor = "rgba(6,182,212,0.45)";
    } else {
      btn.style.background = "transparent";
      btn.style.color = "var(--modal-text-muted)";
      btn.style.borderColor = "transparent";
    }
  });

  // 2. Active header badge
  const monthNames = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"];
  const [yStr, mStr] = (data.selected_month || "2026-11").split("-");
  const mName = monthNames[parseInt(mStr, 10)] || mStr;
  const badgeEl = document.getElementById("climate-modal-active-badge");
  if (badgeEl) {
    const metricLabels = { temperature: "Temperatura", humidity: "Humedad Relativa", co2: "Calidad de Aire CO₂" };
    badgeEl.textContent = `${mName} ${yStr} · ${metricLabels[climateHistoryCurrentMetric] || "Clima"}`;
    badgeEl.style.background = "rgba(6, 182, 212, 0.28)";
    badgeEl.style.color = "#f0f9ff";
    badgeEl.style.borderColor = "rgba(6, 182, 212, 0.55)";
  }

  // 3. Sensor Legend (Interactive Toggles)
  const legendEl = document.getElementById("climate-modal-sensor-legend");
  if (legendEl) {
    legendEl.innerHTML = sensors.map(s => {
      const isDisabled = climateHistoryDisabledSensors.has(s.id);
      const cur = s.stats?.current != null ? `${s.stats.current} ${unit}` : "--";
      return `
        <div class="climate-sensor-pill-toggle ${isDisabled ? 'disabled' : ''}" data-sensorid="${s.id}" style="border-color:${isDisabled ? 'transparent' : s.color}44;">
          <span style="display:inline-block; width:9px; height:9px; border-radius:999px; background:${s.color}; box-shadow:0 0 6px ${s.color};"></span>
          <span>${s.name}</span>
          <span style="color:var(--modal-text-muted); font-weight:700;">(${cur})</span>
        </div>
      `;
    }).join("");

    legendEl.querySelectorAll(".climate-sensor-pill-toggle").forEach(pill => {
      pill.addEventListener("click", () => {
        const sid = pill.getAttribute("data-sensorid");
        if (climateHistoryDisabledSensors.has(sid)) {
          climateHistoryDisabledSensors.delete(sid);
        } else {
          const activeCount = sensors.filter(s => !climateHistoryDisabledSensors.has(s.id)).length;
          if (activeCount > 1) {
            climateHistoryDisabledSensors.add(sid);
          }
        }
        renderClimateHistoryUI();
      });
    });
  }

  // 4. Render Canvas Chart
  drawClimateChart();

  // 5. Stat Cards
  const statsEl = document.getElementById("climate-stats-grid");
  if (statsEl) {
    statsEl.innerHTML = sensors.map(s => {
      const isDisabled = climateHistoryDisabledSensors.has(s.id);
      const st = s.stats || {};
      const avg = st.avg != null ? `${st.avg} ${unit}` : "--";
      const max = st.max != null ? `${st.max} ${unit}` : "--";
      const min = st.min != null ? `${st.min} ${unit}` : "--";
      const cur = st.current != null ? `${st.current} ${unit}` : "--";

      return `
        <div class="domos-modal-subcard" style="padding:0.85rem 1rem; border-radius:16px; opacity:${isDisabled ? '0.4' : '1'}; transition:opacity 0.2s;">
          <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:4px;">
            <div style="display:flex; align-items:center; gap:0.4rem; font-weight:700; font-size:0.82rem; color:${s.color};">
              <span>${s.icon || '🌡️'}</span><span>${s.name}</span>
            </div>
            <span style="font-size:0.7rem; color:var(--modal-text-muted);">${s.room}</span>
          </div>
          <div style="font-size:1.4rem; font-weight:800; color:var(--modal-text); margin:2px 0;">${cur}</div>
          <div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:4px; margin-top:6px; padding-top:6px; border-top:1px solid var(--modal-subcard-border); font-size:0.7rem;">
            <div><span style="color:var(--modal-text-muted); display:block;">Media</span><b>${avg}</b></div>
            <div><span style="color:var(--modal-text-muted); display:block;">Máx</span><b style="color:#f43f5e;">${max}</b></div>
            <div><span style="color:var(--modal-text-muted); display:block;">Mín</span><b style="color:#38bdf8;">${min}</b></div>
          </div>
        </div>
      `;
    }).join("");
  }

  // 6. Comfort Diagnosis
  const comfortTitle = document.getElementById("climate-comfort-title");
  const comfortDesc = document.getElementById("climate-comfort-desc");
  if (comfortTitle && comfortDesc) {
    const indoorSensors = sensors.filter(s => s.id !== "exterior" && !climateHistoryDisabledSensors.has(s.id));
    if (climateHistoryCurrentMetric === "temperature") {
      const avgs = indoorSensors.map(s => s.stats?.avg).filter(v => v != null);
      const overallAvg = avgs.length ? (avgs.reduce((a, b) => a + b, 0) / avgs.length) : 21.0;
      if (overallAvg >= 20.0 && overallAvg <= 23.5) {
        comfortTitle.textContent = "Confort Térmico Óptimo (20°C - 23.5°C)";
        comfortDesc.textContent = `La temperatura media del hogar se sitúa en ${overallAvg.toFixed(1)}°C, con una oscilación suave y gran inercia térmica en todas las estancias. Ideal para ahorro energético y bienestar continuo.`;
      } else if (overallAvg < 20.0) {
        comfortTitle.textContent = "Ambiente Ligeramente Fresco";
        comfortDesc.textContent = `La temperatura media interior es de ${overallAvg.toFixed(1)}°C. Las estancias se mantienen por debajo del umbral de confort estándar.`;
      } else {
        comfortTitle.textContent = "Ambiente Cálido";
        comfortDesc.textContent = `La temperatura media interior es de ${overallAvg.toFixed(1)}°C.`;
      }
    } else if (climateHistoryCurrentMetric === "humidity") {
      const hums = indoorSensors.map(s => s.stats?.avg).filter(v => v != null);
      const overallHum = hums.length ? (hums.reduce((a, b) => a + b, 0) / hums.length) : 62;
      if (overallHum >= 45 && overallHum <= 65) {
        comfortTitle.textContent = "Humedad Relativa Saludable (45% - 65%)";
        comfortDesc.textContent = `Nivel medio del ${overallHum.toFixed(0)}%. Previene sequedad en mucosas y evita condensaciones en paredes y ventanas.`;
      } else if (overallHum > 65) {
        comfortTitle.textContent = "Humedad Elevada (> 65%)";
        comfortDesc.textContent = `Promedio del ${overallHum.toFixed(0)}%. Se recomienda activar el deshumidificador inteligente de Tuya para acelerar el secado del ambiente.`;
      } else {
        comfortTitle.textContent = "Ambiente Seco (< 45%)";
        comfortDesc.textContent = `Promedio del ${overallHum.toFixed(0)}%. Podría ser conveniente ventilar suavemente o humidificar.`;
      }
    } else {
      comfortTitle.textContent = "Calidad del Aire y Concentración de CO₂";
      comfortDesc.textContent = `El sensor de aire registra concentraciones controladas de CO₂ en sótano y zonas habitadas (media en valores seguros por debajo de 800 ppm).`;
    }
  }
}

function drawClimateChart(hoverIndex = climateChartHoverIndex) {
  const canvas = document.getElementById("climate-chart-canvas");
  if (!canvas || !climateHistoryData) return;

  const ctx = canvas.getContext("2d");
  const data = climateHistoryData;
  const sensors = (data.sensors || []).filter(s => !climateHistoryDisabledSensors.has(s.id));
  const points = data.points || [];
  const unit = data.unit || "°C";

  // Handle Retina resolution
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  const w = rect.width || 760;
  const h = rect.height || 260;
  canvas.width = Math.round(w * dpr);
  canvas.height = Math.round(h * dpr);
  ctx.scale(dpr, dpr);

  ctx.clearRect(0, 0, w, h);

  if (points.length === 0 || sensors.length === 0) {
    ctx.fillStyle = "rgba(255, 255, 255, 0.4)";
    ctx.font = "14px system-ui, sans-serif";
    ctx.textAlign = "center";
    ctx.fillText("Sin datos registrados para los sensores y fechas seleccionadas", w / 2, h / 2);
    return;
  }

  // Calculate Global Bounds
  let minVal = Infinity;
  let maxVal = -Infinity;

  points.forEach(pt => {
    sensors.forEach(s => {
      const v = pt.values?.[s.id];
      if (v != null) {
        if (v < minVal) minVal = v;
        if (v > maxVal) maxVal = v;
      }
    });
  });

  if (!isFinite(minVal) || !isFinite(maxVal)) {
    minVal = 18; maxVal = 26;
  }

  const span = Math.max(1.0, maxVal - minVal);
  const yMin = Math.floor(minVal - (span * 0.12));
  const yMax = Math.ceil(maxVal + (span * 0.12));

  const padLeft = 45;
  const padRight = 18;
  const padTop = 22;
  const padBottom = 32;

  const plotW = w - padLeft - padRight;
  const plotH = h - padTop - padBottom;

  const getX = (idx) => padLeft + (idx / Math.max(1, points.length - 1)) * plotW;
  const getY = (val) => padTop + plotH - ((val - yMin) / (yMax - yMin)) * plotH;

  // Horizontal Grid Lines & Y Ticks (5 lines)
  const numYTicks = 5;
  ctx.lineWidth = 1;
  ctx.textAlign = "right";
  ctx.textBaseline = "middle";
  ctx.font = "11px system-ui, sans-serif";

  for (let i = 0; i <= numYTicks; i++) {
    const val = yMin + ((yMax - yMin) * (i / numYTicks));
    const yPos = getY(val);

    ctx.strokeStyle = "rgba(255, 255, 255, 0.08)";
    ctx.beginPath();
    ctx.moveTo(padLeft, yPos);
    ctx.lineTo(w - padRight, yPos);
    ctx.stroke();

    ctx.fillStyle = "rgba(255, 255, 255, 0.45)";
    const formattedVal = (climateHistoryCurrentMetric === "co2" || unit === "%") ? Math.round(val) : val.toFixed(1);
    ctx.fillText(`${formattedVal}${unit}`, padLeft - 6, yPos);
  }

  // X Axis Ticks (Days of Month)
  ctx.textAlign = "center";
  ctx.textBaseline = "top";
  ctx.fillStyle = "rgba(255, 255, 255, 0.45)";
  const stepX = Math.max(1, Math.floor(points.length / 7));
  for (let i = 0; i < points.length; i += stepX) {
    const pt = points[i];
    const xPos = getX(i);
    const dayLabel = `Día ${pt.day}`;
    ctx.fillText(dayLabel, xPos, h - padBottom + 8);
  }

  // Draw Sensor Lines
  sensors.forEach(s => {
    ctx.save();
    ctx.strokeStyle = s.color;
    ctx.fillStyle = s.color;
    ctx.lineWidth = 2.4;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.shadowColor = s.color;
    ctx.shadowBlur = 5;

    ctx.beginPath();
    let started = false;

    points.forEach((pt, idx) => {
      const v = pt.values?.[s.id];
      if (v != null) {
        const px = getX(idx);
        const py = getY(v);
        if (!started) {
          ctx.moveTo(px, py);
          started = true;
        } else {
          ctx.lineTo(px, py);
        }
      }
    });
    ctx.stroke();
    ctx.restore();
  });

  // Hover Cursor & Highlight
  const tip = document.getElementById("climate-chart-tooltip");
  if (hoverIndex != null && hoverIndex >= 0 && hoverIndex < points.length) {
    const pt = points[hoverIndex];
    const cursorX = getX(hoverIndex);

    ctx.save();
    ctx.strokeStyle = "rgba(255, 255, 255, 0.45)";
    ctx.lineWidth = 1.2;
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(cursorX, padTop);
    ctx.lineTo(cursorX, h - padBottom);
    ctx.stroke();
    ctx.restore();

    let tipRows = [];
    sensors.forEach(s => {
      const v = pt.values?.[s.id];
      if (v != null) {
        const py = getY(v);
        ctx.save();
        ctx.fillStyle = s.color;
        ctx.strokeStyle = "#ffffff";
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(cursorX, py, 4.5, 0, Math.PI * 2);
        ctx.fill();
        ctx.stroke();
        ctx.restore();

        tipRows.push(`
          <div style="display:flex; align-items:center; justify-content:space-between; gap:12px; margin-top:3px;">
            <span style="display:flex; align-items:center; gap:5px; color:${s.color};">
              <span style="width:7px; height:7px; border-radius:999px; background:${s.color}; display:inline-block;"></span>
              ${s.name}
            </span>
            <b>${v} ${unit}</b>
          </div>
        `);
      }
    });

    if (tip && tipRows.length > 0) {
      tip.style.display = "block";
      tip.innerHTML = `
        <div style="font-weight:700; color:var(--neon-cyan); margin-bottom:4px; font-size:0.75rem; border-bottom:1px solid rgba(255,255,255,0.12); padding-bottom:3px;">
          📅 ${pt.label}
        </div>
        ${tipRows.join("")}
      `;

      const tipW = tip.offsetWidth || 150;
      let leftPos = cursorX + 12;
      if (leftPos + tipW > w - 10) {
        leftPos = cursorX - tipW - 12;
      }
      tip.style.left = `${Math.max(10, leftPos)}px`;
      tip.style.top = `${padTop + 10}px`;
    }
  } else {
    if (tip) tip.style.display = "none";
  }
}

// Controls & Listeners
document.getElementById("btn-open-climate-history")?.addEventListener("click", () => openClimateHistoryModal());
document.getElementById("btn-climate-modal-close")?.addEventListener("click", closeClimateHistoryModal);
document.getElementById("climate-history-modal")?.addEventListener("click", (e) => {
  if (e.target.id === "climate-history-modal") closeClimateHistoryModal();
});

document.querySelectorAll(".climate-metric-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    const metric = btn.getAttribute("data-metric");
    if (metric && metric !== climateHistoryCurrentMetric) {
      climateHistoryCurrentMetric = metric;
      climateHistoryDisabledSensors.clear();
      fetchAndRenderClimateHistory();
    }
  });
});

const climMonthSel = document.getElementById("climate-month-select");
const climYearSel = document.getElementById("climate-year-select");

function handleClimateDateChange() {
  const m = climMonthSel?.value || "11";
  const y = climYearSel?.value || "2026";
  climateHistoryCurrentMonth = `${y}-${String(m).padStart(2, "0")}`;
  fetchAndRenderClimateHistory();
}

climMonthSel?.addEventListener("change", handleClimateDateChange);
climYearSel?.addEventListener("change", handleClimateDateChange);

document.getElementById("climate-prev-month")?.addEventListener("click", () => {
  let m = parseInt(climMonthSel.value, 10) - 1;
  let y = parseInt(climYearSel.value, 10);
  if (m < 1) { m = 12; y -= 1; }
  climMonthSel.value = String(m);
  climYearSel.value = String(y);
  handleClimateDateChange();
});

document.getElementById("climate-next-month")?.addEventListener("click", () => {
  let m = parseInt(climMonthSel.value, 10) + 1;
  let y = parseInt(climYearSel.value, 10);
  if (m > 12) { m = 1; y += 1; }
  climMonthSel.value = String(m);
  climYearSel.value = String(y);
  handleClimateDateChange();
});

document.getElementById("climate-today-btn")?.addEventListener("click", () => {
  const n = new Date();
  climMonthSel.value = String(n.getMonth() + 1);
  climYearSel.value = String(n.getFullYear());
  handleClimateDateChange();
});

// Canvas interactive pointer tracking
const climChartWrap = document.getElementById("climate-chart-wrapper");
if (climChartWrap) {
  function handlePointerMove(e) {
    if (!climateHistoryData || !climateHistoryData.points?.length) return;
    const canvas = document.getElementById("climate-chart-canvas");
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const clientX = e.touches ? e.touches[0].clientX : e.clientX;
    const padLeft = 45;
    const padRight = 18;
    const plotW = rect.width - padLeft - padRight;
    const relX = clientX - rect.left - padLeft;
    const pct = Math.max(0, Math.min(1, relX / plotW));
    const idx = Math.round(pct * (climateHistoryData.points.length - 1));
    climateChartHoverIndex = idx;
    drawClimateChart(idx);
  }

  climChartWrap.addEventListener("mousemove", handlePointerMove);
  climChartWrap.addEventListener("touchmove", handlePointerMove, { passive: true });
  climChartWrap.addEventListener("mouseleave", () => {
    climateChartHoverIndex = null;
    drawClimateChart(null);
  });
  climChartWrap.addEventListener("touchend", () => {
    climateChartHoverIndex = null;
    drawClimateChart(null);
  });
}

window.addEventListener("resize", () => {
  const modal = document.getElementById("climate-history-modal");
  if (modal && !modal.classList.contains("hidden") && modal.style.display !== "none") {
    drawClimateChart();
  }
});

// --- Slide Interval Selector ---
const modalIntervalSel = document.getElementById("modal-slide-interval-select");
if (modalIntervalSel) {
  modalIntervalSel.value = String(slideIntervalSec);
  modalIntervalSel.addEventListener("change", (e) => {
    slideIntervalSec = parseInt(e.target.value, 10) || 60;
    localStorage.setItem("domos_slide_interval_sec", String(slideIntervalSec));
    fetch("/api/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ slide_interval_sec: slideIntervalSec })
    }).catch(() => {});
    startSlideshow();
  });
}

// --- Carousel Transition Selector ---
const modalTransitionSel = document.getElementById("modal-slide-transition-select");
if (modalTransitionSel) {
  modalTransitionSel.value = carouselTransition;
  modalTransitionSel.addEventListener("change", (e) => {
    carouselTransition = e.target.value;
    localStorage.setItem("domos_carousel_transition", carouselTransition);
    fetch("/api/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ carousel_transition: carouselTransition })
    }).catch(() => {});
    showNextSlide();
  });
}

// --- Radio Player & Modal (10 National Stations) ---
const RADIO_STATIONS = [
  { id: "cadena100", name: "Cadena 100", genre: "Éxitos Pop", icon: "🎵", url: "https://cadena100-streamers-mp3.flumotion.com/cope/cadena100.mp3" },
  { id: "europafm", name: "Europa FM", genre: "Pop & Actualidad", icon: "🎧", url: "https://atres-live.europafm.com/live/europafm/bitrate_1.m3u8" },
  { id: "radioplaneta", name: "Radio Planeta", genre: "Música & Entretenimiento", icon: "🪐", url: "https://radioplaneta.emitironline.com/radio" },
  { id: "locafm", name: "Loca FM", genre: "Dance & Electrónica", icon: "⚡", url: "https://s02.fjperezdj.com:8066/live" },
  { id: "los40", name: "LOS40", genre: "Top Hits España", icon: "🔥", url: "https://playerservices.streamtheworld.com/api/livestream-redirect/LOS40.mp3" },
  { id: "cadenaser", name: "Cadena SER", genre: "Noticias & Deportes", icon: "🎙️", url: "https://playerservices.streamtheworld.com/api/livestream-redirect/CADENASER.mp3" },
  { id: "cope", name: "COPE", genre: "Actualidad & Opinión", icon: "📻", url: "https://net1-cope-rrcast.flumotion.com/cope/net1.mp3" },
  { id: "ondacero", name: "Onda Cero", genre: "Magazines & Noticias", icon: "🌊", url: "https://atres-live.ondacero.es/live/ondacero/bitrate_1.m3u8" },
  { id: "radio3", name: "RNE Radio 3", genre: "Indie & Cultura", icon: "🎸", url: "https://rtvelivestream.rtve.es/rtvesec/rne/rne_r3_main.m3u8" },
  { id: "kissfm", name: "Kiss FM", genre: "Clásicos 80s-2000s", icon: "💋", url: "https://bbkissfm.kissfmradio.cires21.com/bbkissfm.mp3" },
  { id: "chillout", name: "Antenne Chillout", genre: "Chillout & Lounge", icon: "🛋️", url: "https://s6-webradio.antenne.de/chillout" },
  { id: "groovesalad", name: "SomaFM Groove Salad", genre: "Lo-Fi & Ambient", icon: "🌙", url: "https://hls.somafm.com/hls//gs-surround/program.m3u8" }
];

let currentRadioId = null;
let radioHls = null;
let radioOutputTarget = (window.location.hostname === "127.0.0.1" || window.location.hostname === "localhost") ? "domos" : "domos";

window.setRadioOutputTarget = function(target) {
  radioOutputTarget = target || "domos";
  document.querySelectorAll(".radio-target-btn").forEach(btn => {
    const active = btn.getAttribute("data-target") === radioOutputTarget;
    btn.style.background = active ? "rgba(14,165,233,0.25)" : "";
    btn.style.borderColor = active ? "#38bdf8" : "";
    btn.style.fontWeight = active ? "700" : "";
  });
};

function renderRadioGrid() {
  const grid = document.getElementById("radio-stations-grid");
  if (!grid) return;
  grid.innerHTML = RADIO_STATIONS.map(st => {
    const active = currentRadioId === st.id;
    return `
      <button class="liquid-action-pill radio-station-btn ${active ? 'is-active-station' : ''}" data-radio-id="${st.id}" style="
        cursor:pointer; display:flex; align-items:center; gap:0.75rem; padding:0.9rem 1rem;
        border-radius:18px; text-align:left; justify-content:flex-start;
        background:${active ? 'rgba(14,165,233,0.28)' : 'var(--modal-subcard-bg)'};
        border:1px solid ${active ? '#38bdf8' : 'var(--modal-subcard-border)'};
        color:var(--modal-text);
      ">
        <span style="font-size:1.65rem; line-height:1;">${st.icon}</span>
        <div style="min-width:0;">
          <div style="font-weight:700; font-size:0.98rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${st.name}</div>
          <div style="font-size:0.76rem; color:${active ? '#0284c7' : 'var(--modal-text-muted)'};">${active ? "🔊 Reproduciendo" : st.genre}</div>
        </div>
      </button>
    `;
  }).join("");

  grid.querySelectorAll(".radio-station-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const sid = btn.getAttribute("data-radio-id");
      if (currentRadioId === sid) stopRadio();
      else playRadioStation(sid);
    });
  });
}

function stopRadio() {
  fetch("/api/radio/stop", { method: "POST" }).catch(() => {});
  currentRadioId = null;
  const np = document.getElementById("radio-now-playing");
  if (np) np.textContent = "Selecciona una emisora para escuchar";
  document.getElementById("dock-radio-btn")?.classList.remove("is-on");
  renderRadioGrid();
}

function playRadioStation(stationId) {
  const st = RADIO_STATIONS.find(s => s.id === stationId) || RADIO_STATIONS[0];
  if (!st) return;

  currentRadioId = st.id;
  const np = document.getElementById("radio-now-playing");
  if (np) np.textContent = "🔊 Conectando " + st.name + " en Altavoz Asus...";
  document.getElementById("dock-radio-btn")?.classList.add("is-on");
  renderRadioGrid();

  fetch("/api/radio/play", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url: st.url, station: st.name, target: radioOutputTarget || "domos" })
  }).then(res => res.json()).then(data => {
    if (data.status === "error") {
      currentRadioId = null;
      document.getElementById("dock-radio-btn")?.classList.remove("is-on");
      renderRadioGrid();
      if (np) {
        np.style.color = "#ef4444";
        np.textContent = `❌ Error en stream (${st.name}): ${data.error || "Sin señal de audio"}`;
      }
      return;
    }
    if (np) {
      np.style.color = "";
      const mv = data.master_volume;
      const rv = data.radio_volume;
      const lowVolWarn = (typeof mv === "number" && mv <= 25) || (typeof rv === "number" && rv <= 10)
        ? ` · ⚠️ Volumen bajo (General ${mv ?? "--"}% / Radio ${rv ?? "--"}%)`
        : "";
      const stPrefix = data.stream_verified ? "🔊 En directo" : "⏳ Conectando stream";
      np.textContent = `${stPrefix}: ${st.name} · ${st.genre || ""}${lowVolWarn}`;
    }
  }).catch(() => {
    currentRadioId = null;
    document.getElementById("dock-radio-btn")?.classList.remove("is-on");
    renderRadioGrid();
    if (np) {
      np.style.color = "#ef4444";
      np.textContent = "⚠️ Error de red conectando con el servidor de audio DOMOS";
    }
  });
}

// --- Real Audio-Reactive Radio VU Meter (/ws/radio-vu) ---
let radioVuWs = null;
function initRadioVuBars() {
  const container = document.getElementById("radio-vumeter");
  if (!container || container.children.length === 16) return;
  container.innerHTML = Array.from({ length: 16 }, () =>
    '<div class="vu-bar" style="flex:1; height:12%; min-height:4px; border-radius:4px 4px 2px 2px; background:linear-gradient(180deg, #38bdf8, #10b981); transition:height 0.06s linear;"></div>'
  ).join("");
}

function startRadioVuMeter() {
  initRadioVuBars();
  stopRadioVuMeter();
  const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
  try {
    radioVuWs = new WebSocket(`${proto}//${window.location.host}/ws/radio-vu`);
    radioVuWs.onmessage = (ev) => {
      const container = document.getElementById("radio-vumeter");
      if (!container) return;
      const levels = JSON.parse(ev.data);
      const bars = container.children;
      for (let i = 0; i < Math.min(bars.length, levels.length); i++) {
        const h = Math.max(8, levels[i]);
        bars[i].style.height = h + "%";
        bars[i].style.background = h > 80
          ? "linear-gradient(180deg, #f59e0b, #10b981)"
          : "linear-gradient(180deg, #38bdf8, #10b981)";
      }
    };
  } catch (e) {}
}

function stopRadioVuMeter() {
  if (radioVuWs) {
    try { radioVuWs.close(); } catch (e) {}
    radioVuWs = null;
  }
  const container = document.getElementById("radio-vumeter");
  if (container) {
    Array.from(container.children).forEach(b => { b.style.height = "10%"; });
  }
}

function openRadioModal() {
  const m = document.getElementById("radio-modal");
  if (!m) return;
  renderRadioGrid();
  m.classList.remove("hidden");
  m.style.display = "flex";
  startRadioVuMeter();
}

function handleRadioControlMsg(msg) {
  if (msg.action === "stop") stopRadio();
  else if (msg.action === "play") { openRadioModal(); playRadioStation(msg.station || "cadena100"); }
  else if (msg.action === "open") openRadioModal();
}

document.getElementById("dock-radio-btn")?.addEventListener("click", openRadioModal);
document.getElementById("btn-radio-modal-close")?.addEventListener("click", () => {
  const m = document.getElementById("radio-modal");
  if (m) { m.classList.add("hidden"); m.style.display = "none"; }
  stopRadioVuMeter();
});
document.getElementById("radio-modal")?.addEventListener("click", (e) => {
  if (e.target.id === "radio-modal") {
    e.target.classList.add("hidden");
    e.target.style.display = "none";
    stopRadioVuMeter();
  }
});
document.getElementById("btn-radio-stop")?.addEventListener("click", stopRadio);
document.getElementById("btn-radio-vol-up")?.addEventListener("click", () => requestAudioVolumeChange("+10%"));
document.getElementById("btn-radio-vol-down")?.addEventListener("click", () => requestAudioVolumeChange("-10%"));


function renderAcGrid() {
  const container = document.getElementById("ac-grid");
  const sectionEl = document.getElementById("section-ac");
  if (!container) return;
  const acList = deviceData.ac || [];
  if (sectionEl) sectionEl.style.display = acList.length === 0 ? "none" : "";
  if (acList.length === 0) { container.innerHTML = ""; return; }

  const modeLabels = { cold: "❄️ Frío", hot: "🔥 Calor", auto: "✨ Auto", wind: "💨 Vent.", wet: "💧 Seco" };
  container.innerHTML = acList.map(ac => {
    const isOn = Boolean(ac.state?.state);
    const tSet = ac.state?.temp_set ?? 23;
    const tCur = ac.state?.temp_current ?? "--";
    const mode = ac.state?.mode || "cold";
    return `
      <div class="liquid-card ${isOn ? "is-on" : ""}" data-devid="${ac.id}">
        <div class="card-top">
          <div class="card-icon-bubble">❄️</div>
          <button class="liquid-action-pill ac-power-btn" data-id="${ac.id}" data-on="${isOn ? "1" : "0"}" style="cursor:pointer; padding:0.35rem 0.75rem; font-size:0.8rem; background:${isOn ? "rgba(14,165,233,0.28)" : "var(--modal-subcard-bg)"}; border-color:${isOn ? "#38bdf8" : "var(--modal-subcard-border)"};">
            ${isOn ? "Encendido" : "Apagado"}
          </button>
        </div>
        <div class="card-title-group">
          <h4>${ac.name}</h4>
          <div class="metric-row" style="align-items:center; justify-content:space-between; margin-top:4px;">
            <div>
              <span class="metric-big">${tSet}</span><span class="metric-unit">°C</span>
              <div style="font-size:0.75rem; color:var(--modal-text-muted);">Ambiente: ${tCur}°C</div>
            </div>
            <div style="display:flex; gap:0.35rem;">
              <button class="liquid-action-pill ac-temp-btn" data-id="${ac.id}" data-temp="${Math.max(16, tSet - 1)}" style="cursor:pointer; min-width:34px; padding:0.3rem 0.55rem;">−</button>
              <button class="liquid-action-pill ac-temp-btn" data-id="${ac.id}" data-temp="${Math.min(30, tSet + 1)}" style="cursor:pointer; min-width:34px; padding:0.3rem 0.55rem;">+</button>
            </div>
          </div>
          <div style="display:flex; flex-wrap:wrap; gap:0.3rem; margin-top:0.55rem;">
            ${Object.entries(modeLabels).map(([k, lbl]) => `
              <button class="liquid-action-pill ac-mode-btn" data-id="${ac.id}" data-mode="${k}" style="cursor:pointer; padding:0.24rem 0.5rem; font-size:0.74rem; ${mode === k ? "background:rgba(14,165,233,0.28); border-color:#38bdf8; font-weight:700;" : ""}">${lbl}</button>
            `).join("")}
          </div>
        </div>
      </div>
    `;
  }).join("");

  container.querySelectorAll(".ac-power-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const id = btn.getAttribute("data-id");
      const next = btn.getAttribute("data-on") !== "1";
      sendDeviceCommand(id, "switch", next);
    });
  });
  container.querySelectorAll(".ac-temp-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const id = btn.getAttribute("data-id");
      const t = Math.round(Number(btn.getAttribute("data-temp")) * 10);
      sendDeviceCommand(id, "temp_set", t);
    });
  });
  container.querySelectorAll(".ac-mode-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const id = btn.getAttribute("data-id");
      const m = btn.getAttribute("data-mode");
      sendDeviceCommand(id, "mode", m);
    });
  });
}

function renderIrGrid() {
  const container = document.getElementById("ir-grid");
  const sectionEl = document.getElementById("section-ir");
  if (!container) return;
  const irList = deviceData.ir || [];
  if (sectionEl) sectionEl.style.display = irList.length === 0 ? "none" : "";
  if (irList.length === 0) { container.innerHTML = ""; return; }

  container.innerHTML = irList.map(ir => {
    const isTv = ir.type === "infrared_tv";
    const keys = isTv
      ? [["Power", "⏻ Power"], ["Volume-", "🔉 -"], ["Volume+", "🔊 +"], ["Channel-", "CH -"], ["Channel+", "CH +"], ["OK", "OK"], ["Back", "↩️ Atrás"], ["Home", "🏠 Home"]]
      : [["PowerToggle", "💡 Encender / Apagar"]];
    return `
      <div class="liquid-card" data-devid="${ir.id}">
        <div class="card-top">
          <div class="card-icon-bubble">${isTv ? "📺" : "💡"}</div>
          <span class="sub-metric-pill">IR</span>
        </div>
        <div class="card-title-group">
          <h4>${ir.name}</h4>
          <div style="display:flex; flex-wrap:wrap; gap:0.35rem; margin-top:0.55rem;">
            ${keys.map(([code, lbl]) => `
              <button class="liquid-action-pill ir-key-btn" data-id="${ir.id}" data-code="${code}" style="cursor:pointer; padding:0.28rem 0.55rem; font-size:0.76rem;">${lbl}</button>
            `).join("")}
          </div>
        </div>
      </div>
    `;
  }).join("");

  container.querySelectorAll(".ir-key-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      sendDeviceCommand(btn.getAttribute("data-id"), btn.getAttribute("data-code"), btn.getAttribute("data-code"));
    });
  });
}


// Poweroff Kiosk button (2-tap safety confirmation)
let poweroffConfirmTimer = null;
let poweroffArmed = false;
document.getElementById("btn-poweroff-device")?.addEventListener("click", async () => {
  const btn = document.getElementById("btn-poweroff-device");
  if (!poweroffArmed) {
    poweroffArmed = true;
    if (btn) btn.innerHTML = '<span>⚠️</span> Confirmar Apagado';
    if (poweroffConfirmTimer) clearTimeout(poweroffConfirmTimer);
    poweroffConfirmTimer = setTimeout(() => {
      poweroffArmed = false;
      if (btn) btn.innerHTML = '<span>⏻</span> Apagar';
    }, 5000);
    return;
  }
  poweroffArmed = false;
  if (btn) btn.innerHTML = '<span>⏳</span> Apagando...';
  try {
    await fetch("/api/system/poweroff", { method: "POST" });
  } catch (e) {}
});


async function sendXiaomiCommand(devId, action, value = null) {
  try {
    const res = await fetch("/api/xiaomi/control", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ device_id: devId, action, value })
    });
    if (res.ok) {
      const data = await res.json();
      if (data.devices) {
        deviceData = data.devices;
        renderAllDevices();
      }
    }
  } catch (e) { console.error("Xiaomi cmd err:", e); }
}

function renderXiaomiGrid() {
  const container = document.getElementById("xiaomi-grid");
  const sectionEl = document.getElementById("section-xiaomi");
  if (!container) return;
  const list = deviceData.xiaomi || [];
  if (sectionEl) sectionEl.style.display = list.length === 0 ? "none" : "";
  if (list.length === 0) { container.innerHTML = ""; return; }

  container.innerHTML = list.map(dev => {
    const st = dev.state || {};
    if (dev.kind === "purifier") {
      const isOn = Boolean(st.is_on);
      const aqi = st.aqi ?? "--";
      const temp = st.temperature ?? "--";
      const hum = st.humidity ?? "--";
      const flt = st.filter_life ?? "--";
      const mode = (st.mode || "auto").toLowerCase();
      return `
        <div class="liquid-card ${isOn ? "is-on" : ""}" data-devid="${dev.id}">
          <div class="card-top">
            <div class="card-icon-bubble">🌀</div>
            <button class="liquid-action-pill xm-pur-power" data-id="${dev.id}" data-on="${isOn ? "1" : "0"}" style="cursor:pointer; padding:0.35rem 0.75rem; font-size:0.8rem; background:${isOn ? "rgba(16,185,129,0.25)" : "var(--modal-subcard-bg)"}; border-color:${isOn ? "#34d399" : "var(--modal-subcard-border)"};">
              ${isOn ? "Encendido" : "Apagado"}
            </button>
          </div>
          <div class="card-title-group">
            <h4>${dev.name}</h4>
            <div class="metric-row" style="margin-top:4px;">
              <span class="metric-big">${aqi}</span>
              <span class="metric-unit">PM2.5</span>
            </div>
            <div class="sub-metrics">
              <span>${temp}°C · ${hum}%</span>
              <span>Filtro: <b>${flt}%</b></span>
            </div>
            <div style="display:flex; flex-wrap:wrap; gap:0.3rem; margin-top:0.55rem;">
              ${[["auto","✨ Auto"],["silent","🌙 Noche"],["favorite","⚡ Fav"]].map(([m, lbl]) => `
                <button class="liquid-action-pill xm-pur-mode" data-id="${dev.id}" data-mode="${m}" style="cursor:pointer; padding:0.24rem 0.55rem; font-size:0.75rem; ${isOn && mode === m ? "background:rgba(16,185,129,0.25); border-color:#34d399; font-weight:700;" : ""}">${lbl}</button>
              `).join("")}
            </div>
          </div>
        </div>
      `;
    } else {
      const isCleaning = Boolean(st.is_cleaning);
      const bat = st.battery ?? "--";
      const stText = st.status_text || "Conectado";
      return `
        <div class="liquid-card ${isCleaning ? "is-on" : ""}" data-devid="${dev.id}">
          <div class="card-top">
            <div class="card-icon-bubble">🤖</div>
            <span class="sub-metric-pill">🔋 ${bat}%</span>
          </div>
          <div class="card-title-group">
            <h4>${dev.name}</h4>
            <div style="font-size:0.95rem; font-weight:700; margin:4px 0; color:${isCleaning ? "#38bdf8" : "var(--modal-text)"};">${stText}</div>
            <div style="display:flex; flex-wrap:wrap; gap:0.35rem; margin-top:0.55rem;">
              <button class="liquid-action-pill xm-vac-act" data-id="${dev.id}" data-act="start" style="cursor:pointer; padding:0.3rem 0.65rem; font-size:0.78rem; ${isCleaning ? "background:rgba(14,165,233,0.28); border-color:#38bdf8;" : ""}">▶ Limpiar</button>
              <button class="liquid-action-pill xm-vac-act" data-id="${dev.id}" data-act="pause" style="cursor:pointer; padding:0.3rem 0.65rem; font-size:0.78rem;">⏸ Pausar</button>
              <button class="liquid-action-pill xm-vac-act" data-id="${dev.id}" data-act="home" style="cursor:pointer; padding:0.3rem 0.65rem; font-size:0.78rem;">🏠 Base</button>
            </div>
          </div>
        </div>
      `;
    }
  }).join("");

  container.querySelectorAll(".xm-pur-power").forEach(btn => {
    btn.addEventListener("click", () => sendXiaomiCommand(btn.getAttribute("data-id"), "power", btn.getAttribute("data-on") !== "1"));
  });
  container.querySelectorAll(".xm-pur-mode").forEach(btn => {
    btn.addEventListener("click", () => sendXiaomiCommand(btn.getAttribute("data-id"), "mode", btn.getAttribute("data-mode")));
  });
  container.querySelectorAll(".xm-vac-act").forEach(btn => {
    btn.addEventListener("click", () => sendXiaomiCommand(btn.getAttribute("data-id"), btn.getAttribute("data-act")));
  });
}


// ========================================================
// UNIFIED CONTROL CARDS & ROOM / COMPACT / TYPE VIEWS
// ========================================================
function buildControlCardHtml(item) {
  const { kind, dev } = item;
  const hiddenClass = (isEditMode && isDeviceHidden(dev.id)) ? "control-hidden-in-edit" : "";
  const badgeHtml = getEditBadgeHtml(dev.id, dev, true);

  if (kind === "light") {
    const isOn = Boolean(dev.state?.state);
    return `
      <div class="liquid-card liquid-card-compact ${isOn ? "is-on" : ""} ${hiddenClass}" data-devid="${dev.id}" data-kind="light">
        ${badgeHtml}
        <div class="card-top">
          <div class="card-icon-bubble">💡</div>
          <div class="liquid-switch ${isOn ? "on" : ""}"></div>
        </div>
        <div class="card-title-group">
          <h4>${dev.name}</h4>
          <span class="card-subtitle">${isOn ? "ENCENDIDA" : "Apagada"}</span>
        </div>
      </div>`;
  }

  if (kind === "plug") {
    const switchesMap = dev.state?.switches;
    const switchEntries = (switchesMap && typeof switchesMap === "object") ? Object.entries(switchesMap) : [];
    if (switchEntries.length > 1) {
      const onCount = switchEntries.filter(([, val]) => Boolean(val)).length;
      const anyOn = onCount > 0;
      const total = switchEntries.length;
      return `
        <div class="liquid-card liquid-card-wide ${anyOn ? "plug-on" : ""} ${hiddenClass}" data-devid="${dev.id}" data-kind="plug" data-multistrip="1">
          ${badgeHtml}
          <div class="card-top">
            <div class="card-icon-bubble">🔌</div>
            <span class="sub-metric-pill">${anyOn ? `${onCount}/${total} ON` : "Todo apagado"}</span>
          </div>
          <div class="card-title-group">
            <h4>${dev.name}</h4>
            <div class="strip-outlets-row">
              ${switchEntries.map(([swCode, swVal]) => {
                const idx = swCode.split("_")[1];
                const lbl = (total === 5 && idx === "5") ? "USB" : `Toma ${idx}`;
                const active = Boolean(swVal);
                return `
                  <button class="liquid-action-pill strip-outlet-btn ${active ? "is-on" : ""}" data-id="${dev.id}" data-code="${swCode}" data-on="${active ? "1" : "0"}">
                    <span class="strip-dot"></span>${lbl}
                  </button>`;
              }).join("")}
            </div>
          </div>
        </div>`;
    }
    const isOn = Boolean(dev.state?.state);
    return `
      <div class="liquid-card liquid-card-compact ${isOn ? "plug-on" : ""} ${hiddenClass}" data-devid="${dev.id}" data-kind="plug">
        ${badgeHtml}
        <div class="card-top">
          <div class="card-icon-bubble">🔌</div>
          <div class="liquid-switch ${isOn ? "on" : ""}"></div>
        </div>
        <div class="card-title-group">
          <h4>${dev.name}</h4>
          <span class="card-subtitle">${isOn ? "CONECTADO (ON)" : "Apagado"}</span>
        </div>
      </div>`;
  }

  if (kind === "ac") {
    const isOn = Boolean(dev.state?.state);
    const tSet = dev.state?.temp_set ?? 23;
    const tCur = dev.state?.temp_current ?? "--";
    const mode = dev.state?.mode || "cold";
    const modeLabels = { cold: "❄️ Frío", hot: "🔥 Calor", auto: "✨ Auto", wind: "💨 Vent.", wet: "💧 Seco" };
    return `
      <div class="liquid-card liquid-card-wide ${isOn ? "is-on" : ""} ${hiddenClass}" data-devid="${dev.id}" data-kind="ac">
        ${badgeHtml}
        <div class="card-top">
          <div class="card-icon-bubble">❄️</div>
          <button class="liquid-action-pill ac-power-btn" data-id="${dev.id}" data-on="${isOn ? "1" : "0"}" style="cursor:pointer; padding:0.35rem 0.75rem; font-size:0.8rem; background:${isOn ? "rgba(14,165,233,0.28)" : "var(--modal-subcard-bg)"}; border-color:${isOn ? "#38bdf8" : "var(--modal-subcard-border)"};">
            ${isOn ? "Encendido" : "Apagado"}
          </button>
        </div>
        <div class="card-title-group">
          <h4>${dev.name}</h4>
          <div class="metric-row" style="align-items:center; justify-content:space-between; margin-top:4px;">
            <div>
              <span class="metric-big">${tSet}</span><span class="metric-unit">°C</span>
              <div style="font-size:0.75rem; color:var(--modal-text-muted);">Ambiente: ${tCur}°C</div>
            </div>
            <div style="display:flex; gap:0.35rem;">
              <button class="liquid-action-pill ac-temp-btn" data-id="${dev.id}" data-temp="${Math.max(16, tSet - 1)}" style="cursor:pointer; min-width:34px; padding:0.3rem 0.55rem;">−</button>
              <button class="liquid-action-pill ac-temp-btn" data-id="${dev.id}" data-temp="${Math.min(30, tSet + 1)}" style="cursor:pointer; min-width:34px; padding:0.3rem 0.55rem;">+</button>
            </div>
          </div>
          <div style="display:flex; flex-wrap:wrap; gap:0.3rem; margin-top:0.55rem;">
            ${Object.entries(modeLabels).map(([k, lbl]) => `
              <button class="liquid-action-pill ac-mode-btn" data-id="${dev.id}" data-mode="${k}" style="cursor:pointer; padding:0.24rem 0.5rem; font-size:0.74rem; ${mode === k ? "background:rgba(14,165,233,0.28); border-color:#38bdf8; font-weight:700;" : ""}">${lbl}</button>
            `).join("")}
          </div>
        </div>
      </div>`;
  }

  if (kind === "ir") {
    const isTv = dev.type === "infrared_tv";
    const keys = isTv
      ? [["Power", "⏻ Power"], ["Volume-", "🔉 -"], ["Volume+", "🔊 +"], ["Channel-", "CH -"], ["Channel+", "CH +"], ["OK", "OK"], ["Back", "↩️ Atrás"], ["Home", "🏠 Home"]]
      : [["PowerToggle", "💡 Encender / Apagar"]];
    return `
      <div class="liquid-card liquid-card-wide ${hiddenClass}" data-devid="${dev.id}" data-kind="ir">
        ${badgeHtml}
        <div class="card-top">
          <div class="card-icon-bubble">${isTv ? "📺" : "💡"}</div>
          <span class="sub-metric-pill">IR</span>
        </div>
        <div class="card-title-group">
          <h4>${dev.name}</h4>
          <div style="display:flex; flex-wrap:wrap; gap:0.35rem; margin-top:0.55rem;">
            ${keys.map(([code, lbl]) => `
              <button class="liquid-action-pill ir-key-btn" data-id="${dev.id}" data-code="${code}" style="cursor:pointer; padding:0.28rem 0.55rem; font-size:0.76rem;">${lbl}</button>
            `).join("")}
          </div>
        </div>
      </div>`;
  }

  if (kind === "xiaomi") {
    const st = dev.state || {};
    if (dev.kind === "purifier") {
      const isOn = Boolean(st.is_on);
      const aqi = st.aqi ?? "--";
      const temp = st.temperature ?? "--";
      const hum = st.humidity ?? "--";
      const flt = st.filter_life ?? "--";
      const mode = (st.mode || "auto").toLowerCase();
      return `
        <div class="liquid-card liquid-card-wide ${isOn ? "is-on" : ""} ${hiddenClass}" data-devid="${dev.id}" data-kind="xiaomi">
          ${badgeHtml}
          <div class="card-top">
            <div class="card-icon-bubble">🌀</div>
            <button class="liquid-action-pill xm-pur-power" data-id="${dev.id}" data-on="${isOn ? "1" : "0"}" style="cursor:pointer; padding:0.35rem 0.75rem; font-size:0.8rem; background:${isOn ? "rgba(16,185,129,0.25)" : "var(--modal-subcard-bg)"}; border-color:${isOn ? "#34d399" : "var(--modal-subcard-border)"};">
              ${isOn ? "Encendido" : "Apagado"}
            </button>
          </div>
          <div class="card-title-group">
            <h4>${dev.name}</h4>
            <div class="metric-row" style="margin-top:4px;">
              <span class="metric-big">${aqi}</span>
              <span class="metric-unit">PM2.5</span>
            </div>
            <div class="sub-metrics">
              <span>${temp}°C · ${hum}%</span>
              <span>Filtro: <b>${flt}%</b></span>
            </div>
            <div style="display:flex; flex-wrap:wrap; gap:0.3rem; margin-top:0.55rem;">
              ${[["auto","✨ Auto"],["silent","🌙 Noche"],["favorite","⚡ Fav"]].map(([m, lbl]) => `
                <button class="liquid-action-pill xm-pur-mode" data-id="${dev.id}" data-mode="${m}" style="cursor:pointer; padding:0.24rem 0.55rem; font-size:0.75rem; ${isOn && mode === m ? "background:rgba(16,185,129,0.25); border-color:#34d399; font-weight:700;" : ""}">${lbl}</button>
              `).join("")}
            </div>
          </div>
        </div>`;
    } else {
      const isCleaning = Boolean(st.is_cleaning);
      const bat = st.battery ?? "--";
      const stText = st.status_text || "Conectado";
      return `
        <div class="liquid-card liquid-card-wide ${isCleaning ? "is-on" : ""} ${hiddenClass}" data-devid="${dev.id}" data-kind="xiaomi">
          ${badgeHtml}
          <div class="card-top">
            <div class="card-icon-bubble">🤖</div>
            <span class="sub-metric-pill">🔋 ${bat}%</span>
          </div>
          <div class="card-title-group">
            <h4>${dev.name}</h4>
            <div style="font-size:0.95rem; font-weight:700; margin:4px 0; color:${isCleaning ? "#38bdf8" : "var(--modal-text)"};">${stText}</div>
            <div style="display:flex; flex-wrap:wrap; gap:0.35rem; margin-top:0.55rem;">
              <button class="liquid-action-pill xm-vac-act" data-id="${dev.id}" data-act="start" style="cursor:pointer; padding:0.3rem 0.65rem; font-size:0.78rem; ${isCleaning ? "background:rgba(14,165,233,0.28); border-color:#38bdf8;" : ""}">▶ Limpiar</button>
              <button class="liquid-action-pill xm-vac-act" data-id="${dev.id}" data-act="pause" style="cursor:pointer; padding:0.3rem 0.65rem; font-size:0.78rem;">⏸ Pausar</button>
              <button class="liquid-action-pill xm-vac-act" data-id="${dev.id}" data-act="home" style="cursor:pointer; padding:0.3rem 0.65rem; font-size:0.78rem;">🏠 Base</button>
            </div>
          </div>
        </div>`;
    }
  }
  return "";
}

function bindControlCardEvents(rootEl) {
  if (!rootEl) return;

  rootEl.querySelectorAll(".edit-fav-btn").forEach(btn => {
    ["mousedown", "touchstart"].forEach(evt => btn.addEventListener(evt, e => e.stopPropagation()));
    btn.addEventListener("click", e => {
      e.stopPropagation();
      toggleDeviceFavorite(btn.getAttribute("data-devid"));
    });
  });

  rootEl.querySelectorAll(".edit-move-btn").forEach(btn => {
    ["mousedown", "touchstart"].forEach(evt => btn.addEventListener(evt, e => e.stopPropagation()));
    btn.addEventListener("click", e => {
      e.stopPropagation();
      const devId = btn.getAttribute("data-devid");
      const delta = Number(btn.getAttribute("data-delta") || "0");
      const grid = btn.closest(".liquid-grid");
      const scopeIds = grid
        ? Array.from(grid.querySelectorAll(".liquid-card[data-devid]")).map(c => c.getAttribute("data-devid"))
        : [];
      moveDeviceOrder(devId, delta, scopeIds);
    });
  });

  rootEl.querySelectorAll(".edit-room-select").forEach(sel => {
    ["click", "mousedown", "touchstart"].forEach(evt => {
      sel.addEventListener(evt, e => e.stopPropagation());
    });
    sel.addEventListener("change", e => {
      e.stopPropagation();
      setDeviceRoom(sel.getAttribute("data-devid"), e.target.value);
    });
  });

  rootEl.querySelectorAll(".liquid-card[data-devid]").forEach(card => {
    card.addEventListener("click", () => {
      const devId = card.getAttribute("data-devid");
      const kind = card.getAttribute("data-kind");
      if (isEditMode) {
        toggleDeviceVisibility(devId);
        return;
      }
      if (kind === "light") {
        const light = (deviceData.lights || []).find(l => l.id === devId);
        const nextState = !Boolean(light?.state?.state);
        if (light && light.state) light.state.state = nextState;
        renderAllDevices();
        sendDeviceCommand(devId, "switch_1", nextState);
      } else if (kind === "plug") {
        if (card.getAttribute("data-multistrip") === "1") return;
        const plug = (deviceData.plugs || []).find(p => p.id === devId);
        const nextState = !Boolean(plug?.state?.state);
        if (plug && plug.state) plug.state.state = nextState;
        renderAllDevices();
        sendDeviceCommand(devId, "switch_1", nextState);
      }
    });
  });

  rootEl.querySelectorAll(".strip-outlet-btn").forEach(btn => {
    btn.addEventListener("click", e => {
      e.stopPropagation();
      if (isEditMode) return;
      const devId = btn.getAttribute("data-id");
      const code = btn.getAttribute("data-code");
      const nextState = btn.getAttribute("data-on") !== "1";
      const plug = (deviceData.plugs || []).find(p => p.id === devId);
      if (plug?.state?.switches) {
        plug.state.switches[code] = nextState;
        plug.state.state = Object.values(plug.state.switches).some(Boolean);
      }
      renderAllDevices();
      sendDeviceCommand(devId, code, nextState);
    });
  });

  rootEl.querySelectorAll(".ac-power-btn").forEach(btn => {
    btn.addEventListener("click", e => {
      e.stopPropagation();
      if (isEditMode) return;
      sendDeviceCommand(btn.getAttribute("data-id"), "switch", btn.getAttribute("data-on") !== "1");
    });
  });
  rootEl.querySelectorAll(".ac-temp-btn").forEach(btn => {
    btn.addEventListener("click", e => {
      e.stopPropagation();
      if (isEditMode) return;
      sendDeviceCommand(btn.getAttribute("data-id"), "temp_set", Math.round(Number(btn.getAttribute("data-temp")) * 10));
    });
  });
  rootEl.querySelectorAll(".ac-mode-btn").forEach(btn => {
    btn.addEventListener("click", e => {
      e.stopPropagation();
      if (isEditMode) return;
      sendDeviceCommand(btn.getAttribute("data-id"), "mode", btn.getAttribute("data-mode"));
    });
  });
  rootEl.querySelectorAll(".ir-key-btn").forEach(btn => {
    btn.addEventListener("click", e => {
      e.stopPropagation();
      if (isEditMode) return;
      sendDeviceCommand(btn.getAttribute("data-id"), btn.getAttribute("data-code"), btn.getAttribute("data-code"));
    });
  });
  rootEl.querySelectorAll(".xm-pur-power").forEach(btn => {
    btn.addEventListener("click", e => {
      e.stopPropagation();
      if (isEditMode) return;
      sendXiaomiCommand(btn.getAttribute("data-id"), "power", btn.getAttribute("data-on") !== "1");
    });
  });
  rootEl.querySelectorAll(".xm-pur-mode").forEach(btn => {
    btn.addEventListener("click", e => {
      e.stopPropagation();
      if (isEditMode) return;
      sendXiaomiCommand(btn.getAttribute("data-id"), "mode", btn.getAttribute("data-mode"));
    });
  });
  rootEl.querySelectorAll(".xm-vac-act").forEach(btn => {
    btn.addEventListener("click", e => {
      e.stopPropagation();
      if (isEditMode) return;
      sendXiaomiCommand(btn.getAttribute("data-id"), btn.getAttribute("data-act"));
    });
  });
}

function getAllControlItems() {
  const items = [];
  (deviceData.lights || []).forEach(dev => items.push({ kind: "light", dev }));
  (deviceData.ac || []).forEach(dev => items.push({ kind: "ac", dev }));
  (deviceData.plugs || []).forEach(dev => items.push({ kind: "plug", dev }));
  (deviceData.xiaomi || []).forEach(dev => items.push({ kind: "xiaomi", dev }));
  (deviceData.ir || []).forEach(dev => items.push({ kind: "ir", dev }));
  const filtered = isEditMode ? items : items.filter(i => !isDeviceHidden(i.dev.id));
  return sortByDeviceOrder(filtered);
}

function renderRoomsView() {
  const container = document.getElementById("rooms-container");
  if (!container) return;
  const items = getAllControlItems();
  const favItems = items.filter(i => isDeviceFavorite(i.dev.id));

  let favHtml = "";
  if (favItems.length > 0) {
    favHtml = `
      <div class="room-group-block favorites-group-block" data-room="favorites">
        <div class="room-group-header">
          <div class="room-group-title"><span>⭐</span><span>Favoritos</span></div>
          <span class="room-group-count">${favItems.length} ${favItems.length === 1 ? "equipo" : "equipos"}</span>
        </div>
        <div class="liquid-grid" style="grid-template-columns: repeat(4, minmax(0, 1fr));">
          ${favItems.map(buildControlCardHtml).join("")}
        </div>
      </div>`;
  }

  const byRoom = {};
  const rooms = getAllRooms();
  rooms.forEach(r => { byRoom[r.id] = []; });
  items.forEach(item => {
    const rid = getDeviceRoom(item.dev);
    (byRoom[rid] || byRoom.exterior).push(item);
  });

  const blocks = [];
  rooms.forEach(r => {
    const list = byRoom[r.id] || [];
    if (list.length === 0 && !isEditMode) return;
    const weight = list.reduce((acc, it) => acc + (["ac", "ir", "xiaomi"].includes(it.kind) ? 2 : 1), 1.5);
    const html = `
      <div class="room-group-block" data-room="${r.id}">
        <div class="room-group-header">
          <div class="room-group-title"><span>${r.icon}</span><span>${r.label}</span></div>
          <span class="room-group-count">${list.length} ${list.length === 1 ? "equipo" : "equipos"}</span>
        </div>
        <div class="liquid-grid">
          ${list.map(buildControlCardHtml).join("")}
        </div>
      </div>`;
    blocks.push({ html, weight });
  });

  // Balance room blocks into 2 tight vertical columns (no empty gap under shorter rooms)
  const colLeft = [];
  const colRight = [];
  let wLeft = 0;
  let wRight = 0;
  blocks.forEach(b => {
    if (wLeft <= wRight) {
      colLeft.push(b.html);
      wLeft += b.weight;
    } else {
      colRight.push(b.html);
      wRight += b.weight;
    }
  });

  container.classList.remove("rooms-mosaic-columns");
  container.innerHTML = favHtml + `
    <div class="rooms-mosaic-columns">
      <div class="rooms-masonry-col">${colLeft.join("")}</div>
      <div class="rooms-masonry-col">${colRight.join("")}</div>
    </div>`;

  bindControlCardEvents(container);
}

function renderCompactView() {
  const container = document.getElementById("compact-grid");
  if (!container) return;
  const items = getAllControlItems();
  container.innerHTML = items.map(buildControlCardHtml).join("");
  bindControlCardEvents(container);
}

function renderTypeGrid(containerId, sectionId, rawList, kind) {
  const container = document.getElementById(containerId);
  const sectionEl = document.getElementById(sectionId);
  if (!container) return;
  const all = rawList || [];
  const list = sortByDeviceOrder(isEditMode ? all : all.filter(d => !isDeviceHidden(d.id)));
  if (sectionEl) sectionEl.style.display = (list.length === 0 && !isEditMode) ? "none" : "";
  if (list.length === 0) { container.innerHTML = ""; return; }
  container.innerHTML = list.map(dev => buildControlCardHtml({ kind, dev })).join("");
  bindControlCardEvents(container);
}

function renderControlViews() {
  const secRooms = document.getElementById("section-rooms");
  const secCompact = document.getElementById("section-compact");
  const typeIds = ["section-lights", "section-ac", "section-plugs", "section-xiaomi", "section-ir"];

  if (layoutMode === "rooms") {
    if (secRooms) secRooms.style.display = "";
    if (secCompact) secCompact.style.display = "none";
    typeIds.forEach(id => { const el = document.getElementById(id); if (el) el.style.display = "none"; });
    renderRoomsView();
  } else if (layoutMode === "compact") {
    if (secRooms) secRooms.style.display = "none";
    if (secCompact) secCompact.style.display = "";
    typeIds.forEach(id => { const el = document.getElementById(id); if (el) el.style.display = "none"; });
    renderCompactView();
  } else {
    if (secRooms) secRooms.style.display = "none";
    if (secCompact) secCompact.style.display = "none";
    renderTypeGrid("lights-grid", "section-lights", deviceData.lights, "light");
    renderTypeGrid("ac-grid", "section-ac", deviceData.ac, "ac");
    renderTypeGrid("plugs-grid", "section-plugs", deviceData.plugs, "plug");
    renderTypeGrid("xiaomi-grid", "section-xiaomi", deviceData.xiaomi, "xiaomi");
    renderTypeGrid("ir-grid", "section-ir", deviceData.ir, "ir");
  }
}

// Settings toggle & layout preset bindings
document.getElementById("btn-toggle-settings")?.addEventListener("click", (e) => {
  e.stopPropagation();
  const panel = document.getElementById("drawer-settings-panel");
  const btn = document.getElementById("btn-toggle-settings");
  const body = document.querySelector(".liquid-panel-body");
  if (panel) {
    const isHidden = panel.classList.toggle("hidden");
    btn?.classList.toggle("active", !isHidden);
    if (!isHidden) {
      renderCustomRoomsList();
      if (body) body.scrollTo({ top: 0, behavior: "smooth" });
    }
  }
});

// Built-in Glass On-Screen Keyboard (OSK)
let oskTargetInput = null;
let oskShift = true;
let oskValue = "";

function renderOskKeys() {
  const container = document.getElementById("osk-keys-container");
  if (!container) return;
  const rows = [
    ["1","2","3","4","5","6","7","8","9","0"],
    ["q","w","e","r","t","y","u","i","o","p"],
    ["a","s","d","f","g","h","j","k","l","ñ"],
    ["SHIFT","z","x","c","v","b","n","m","BKSP"]
  ];
  container.innerHTML = rows.map(row => `
    <div class="osk-row">
      ${row.map(k => {
        if (k === "SHIFT") return `<button type="button" class="osk-key osk-key-wide ${oskShift ? "osk-key-accent" : ""}" data-osk="SHIFT">⇧</button>`;
        if (k === "BKSP") return `<button type="button" class="osk-key osk-key-wide" data-osk="BKSP">⌫</button>`;
        const disp = oskShift ? k.toUpperCase() : k;
        return `<button type="button" class="osk-key" data-osk="${disp}">${disp}</button>`;
      }).join("")}
    </div>
  `).join("") + `
    <div class="osk-row">
      <button type="button" class="osk-key osk-key-space" data-osk="SPACE">Espacio</button>
      <button type="button" class="osk-key osk-key-wide osk-key-accent" data-osk="ENTER">✓ Aceptar</button>
    </div>
  `;

  container.querySelectorAll("[data-osk]").forEach(btn => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const key = btn.getAttribute("data-osk");
      if (key === "SHIFT") {
        oskShift = !oskShift;
        renderOskKeys();
        return;
      }
      if (key === "BKSP") {
        oskValue = oskValue.slice(0, -1);
      } else if (key === "SPACE") {
        oskValue += " ";
        oskShift = true;
      } else if (key === "ENTER") {
        if (oskTargetInput) oskTargetInput.value = oskValue;
        closeOsk();
        return;
      } else {
        oskValue += key;
        if (oskShift && oskValue.length === 1) oskShift = false;
      }
      const prev = document.getElementById("osk-preview-input");
      if (prev) prev.value = oskValue;
      if (oskTargetInput) oskTargetInput.value = oskValue;
      renderOskKeys();
    });
  });
}

function openOsk(inputEl) {
  oskTargetInput = inputEl;
  oskValue = inputEl?.value || "";
  oskShift = oskValue.length === 0;
  const prev = document.getElementById("osk-preview-input");
  if (prev) prev.value = oskValue;
  renderOskKeys();
  document.getElementById("domos-osk-overlay")?.classList.remove("hidden");
}

function closeOsk() {
  document.getElementById("domos-osk-overlay")?.classList.add("hidden");
  oskTargetInput = null;
}

document.getElementById("osk-clear-btn")?.addEventListener("click", () => {
  oskValue = "";
  oskShift = true;
  const prev = document.getElementById("osk-preview-input");
  if (prev) prev.value = "";
  if (oskTargetInput) oskTargetInput.value = "";
  renderOskKeys();
});
document.getElementById("osk-cancel-btn")?.addEventListener("click", closeOsk);
document.getElementById("domos-osk-overlay")?.addEventListener("click", (e) => {
  if (e.target.id === "domos-osk-overlay") closeOsk();
});

const newRoomInput = document.getElementById("new-room-name-input");
newRoomInput?.addEventListener("click", () => openOsk(newRoomInput));
document.getElementById("btn-add-custom-room")?.addEventListener("click", () => {
  const inp = document.getElementById("new-room-name-input");
  const emo = document.getElementById("new-room-emoji")?.value || "🏠";
  if (inp && inp.value.trim()) {
    addCustomRoom(inp.value.trim(), emo);
    inp.value = "";
  } else if (inp) {
    openOsk(inp);
  }
});

renderCustomRoomsList();

document.querySelectorAll(".layout-preset-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    setLayoutMode(btn.getAttribute("data-layout"));
  });
});

updateLayoutPresetButtons();


// ========================================================
// ADGUARD HOME MONITOR & EXTENDED MODAL
// ========================================================
window.adguardStats = null;

async function fetchAdguardStats() {
  try {
    const res = await fetch("/api/adguard/stats");
    if (res.ok) {
      window.adguardStats = await res.json();
      renderSecurityGrid();
      const modal = document.getElementById("adguard-modal");
      if (modal && !modal.classList.contains("hidden")) {
        renderAdguardModalBody();
      }
    }
  } catch (e) {}
}

function renderAdguardModalBody() {
  const body = document.getElementById("adguard-modal-body");
  if (!body) return;
  const ag = window.adguardStats;
  if (!ag || !ag.online) {
    body.innerHTML = `<div class="domos-subcard" style="padding:1rem; border-radius:16px;">No se pudo conectar con AdGuard Home (<code>127.0.0.1:3000</code>).</div>`;
    return;
  }

  const protOn = Boolean(ag.protection_enabled);
  const topBlocked = (ag.top_blocked_domains || []).map(item => {
    const [dom, cnt] = Object.entries(item)[0] || ["-", 0];
    return `<div style="display:flex; justify-content:space-between; font-size:0.84rem; padding:0.28rem 0; border-bottom:1px solid var(--modal-subcard-border);"><span style="overflow:hidden; text-overflow:ellipsis; white-space:nowrap; max-width:75%;">${dom}</span><b>${cnt}</b></div>`;
  }).join("") || `<div style="font-size:0.82rem; color:var(--modal-text-muted);">Sin bloqueos recientes</div>`;

  const topClients = (ag.top_clients || []).map(item => {
    const [cli, cnt] = Object.entries(item)[0] || ["-", 0];
    return `<div style="display:flex; justify-content:space-between; font-size:0.84rem; padding:0.28rem 0; border-bottom:1px solid var(--modal-subcard-border);"><span>${cli}</span><b>${cnt}</b></div>`;
  }).join("") || `<div style="font-size:0.82rem; color:var(--modal-text-muted);">Sin clientes aún</div>`;

  body.innerHTML = `
    <div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:0.65rem;">
      <div style="display:flex; align-items:center; gap:0.5rem;">
        <span class="sub-metric-pill" style="${protOn ? "color:#10b981; border-color:rgba(16,185,129,0.5);" : "color:#f59e0b; border-color:rgba(245,158,11,0.5);"}">
          ${protOn ? "● Protección Activa" : "● Protección Pausada"}
        </span>
        <span style="font-size:0.8rem; color:var(--modal-text-muted);">AdGuard ${ag.version || ""} · Latencia ${ag.avg_processing_ms ?? 0} ms</span>
      </div>
      <button type="button" id="btn-adguard-toggle-prot" class="liquid-action-pill" style="cursor:pointer; font-weight:700; ${protOn ? "border-color:rgba(245,158,11,0.55); color:#f59e0b;" : "border-color:rgba(16,185,129,0.55); color:#10b981;"}">
        ${protOn ? "⏸ Pausar Filtro" : "▶ Activar Filtro"}
      </button>
    </div>

    <div style="display:grid; grid-template-columns:repeat(4, minmax(0, 1fr)); gap:0.6rem;">
      <div class="domos-subcard" style="padding:0.75rem; border-radius:14px;">
        <div style="font-size:0.75rem; color:var(--modal-text-muted);">Consultas DNS</div>
        <div style="font-size:1.35rem; font-weight:800;">${ag.num_dns_queries ?? 0}</div>
      </div>
      <div class="domos-subcard" style="padding:0.75rem; border-radius:14px;">
        <div style="font-size:0.75rem; color:var(--modal-text-muted);">Bloqueados</div>
        <div style="font-size:1.35rem; font-weight:800; color:#f97316;">${ag.num_blocked_filtering ?? 0}</div>
      </div>
      <div class="domos-subcard" style="padding:0.75rem; border-radius:14px;">
        <div style="font-size:0.75rem; color:var(--modal-text-muted);">% Bloqueo</div>
        <div style="font-size:1.35rem; font-weight:800; color:#38bdf8;">${ag.block_pct ?? 0}%</div>
      </div>
      <div class="domos-subcard" style="padding:0.75rem; border-radius:14px;">
        <div style="font-size:0.75rem; color:var(--modal-text-muted);">Malware / Phish</div>
        <div style="font-size:1.35rem; font-weight:800; color:#ef4444;">${ag.num_malware_blocked ?? 0}</div>
      </div>
    </div>

    <div style="display:grid; grid-template-columns:1fr 1fr; gap:0.85rem;">
      <div class="domos-subcard" style="padding:0.85rem; border-radius:16px;">
        <div style="font-size:0.85rem; font-weight:700; margin-bottom:0.45rem;">🚫 Dominios más bloqueados</div>
        ${topBlocked}
      </div>
      <div class="domos-subcard" style="padding:0.85rem; border-radius:16px;">
        <div style="font-size:0.85rem; font-weight:700; margin-bottom:0.45rem;">📱 Clientes más activos</div>
        ${topClients}
      </div>
    </div>
  `;

  document.getElementById("btn-adguard-toggle-prot")?.addEventListener("click", async () => {
    const res = await fetch("/api/adguard/toggle", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ enabled: !protOn })
    });
    if (res.ok) {
      window.adguardStats = await res.json();
      renderSecurityGrid();
      renderAdguardModalBody();
    }
  });
}

function openAdguardModal() {
  const modal = document.getElementById("adguard-modal");
  if (!modal) return;
  modal.classList.remove("hidden");
  modal.style.display = "flex";
  renderAdguardModalBody();
  fetchAdguardStats();
}

function closeAdguardModal() {
  const modal = document.getElementById("adguard-modal");
  if (!modal) return;
  modal.classList.add("hidden");
  modal.style.display = "none";
}

document.getElementById("btn-adguard-modal-close")?.addEventListener("click", closeAdguardModal);
document.getElementById("adguard-modal")?.addEventListener("click", (e) => {
  if (e.target.id === "adguard-modal") closeAdguardModal();
});

fetchAdguardStats();
setInterval(fetchAdguardStats, 20000);


// ========================================================
// FAMILY CALENDAR & ICS SYNC + FULLSCREEN MONTH MODAL
// ========================================================
let calendarEvents = [];
let calendarIcsSources = [];
const _calNow = new Date();
let calViewYear = _calNow.getFullYear();
let calViewMonth = _calNow.getMonth(); // 0-11
let calSelectedDate = `${_calNow.getFullYear()}-${String(_calNow.getMonth() + 1).padStart(2, "0")}-${String(_calNow.getDate()).padStart(2, "0")}`;

function formatYmd(y, m0, d) {
  return `${y}-${String(m0 + 1).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
}

async function fetchCalendarData() {
  try {
    const [evRes, srcRes] = await Promise.all([
      fetch("/api/calendar"),
      fetch("/api/calendar/sources")
    ]);
    if (evRes.ok) calendarEvents = await evRes.json();
    if (srcRes.ok) {
      const sData = await srcRes.json();
      calendarIcsSources = sData.sources || [];
    }
    renderHudCalendarPill();
    const modal = document.getElementById("calendar-modal");
    if (modal && !modal.classList.contains("hidden")) {
      renderCalendarModal();
    }
  } catch (e) {}
}

function renderHudCalendarPill() {
  const el = document.getElementById("hud-calendar-text");
  if (!el) return;
  const now = new Date();
  const todayStr = formatYmd(now.getFullYear(), now.getMonth(), now.getDate());
  const todayEvs = calendarEvents.filter(e => e.date === todayStr);
  if (todayEvs.length > 0) {
    el.textContent = `Hoy: ${todayEvs[0].title}${todayEvs.length > 1 ? ` (+${todayEvs.length - 1})` : ""}`;
    return;
  }
  const upcoming = calendarEvents.find(e => (e.date || "") > todayStr);
  if (upcoming) {
    const parts = (upcoming.date || "").split("-");
    const shortD = parts.length === 3 ? `${parts[2]}/${parts[1]}` : upcoming.date;
    el.textContent = `Próximo (${shortD}): ${upcoming.title}`;
  } else {
    el.textContent = "Calendario · Sin eventos";
  }
}

function renderCalendarSourcesList() {
  const el = document.getElementById("cal-ics-sources-list");
  if (!el) return;
  el.innerHTML = (calendarIcsSources || []).map((s, idx) => `
    <span class="custom-room-chip">
      <span>🔗 ${s.name || "ICS"}</span>
      <button type="button" class="custom-room-del-btn cal-del-ics-btn" data-idx="${idx}" title="Eliminar calendario">×</button>
    </span>
  `).join("") || `<span style="font-size:0.78rem; color:var(--modal-text-muted);">No hay calendarios .ics externos añadidos todavía.</span>`;

  el.querySelectorAll(".cal-del-ics-btn").forEach(btn => {
    btn.addEventListener("click", async () => {
      const idx = Number(btn.getAttribute("data-idx"));
      const next = calendarIcsSources.filter((_, i) => i !== idx);
      const res = await fetch("/api/calendar/sources", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sources: next })
      });
      if (res.ok) {
        const d = await res.json();
        calendarIcsSources = d.sources || [];
        calendarEvents = d.events || [];
        renderCalendarSourcesList();
        renderCalendarModal();
        renderHudCalendarPill();
      }
    });
  });
}

function eventMatchesDate(ev, dateStr) {
  if (!ev || !ev.date || !dateStr) return false;
  if (ev.date === dateStr) return true;
  return ev.repeat === "yearly" && ev.date.slice(5, 10) === dateStr.slice(5, 10);
}

function renderCalendarDayDetail() {
  const bar = document.getElementById("cal-day-detail-bar");
  if (!bar) return;
  const list = calendarEvents.filter(e => eventMatchesDate(e, calSelectedDate));
  if (list.length === 0) {
    bar.innerHTML = `<strong>${calSelectedDate}:</strong> <span style="color:var(--modal-text-muted);">Sin hitos o eventos para este día.</span>`;
    return;
  }
  bar.innerHTML = `<strong>${calSelectedDate}:</strong> ` + list.map(ev => {
    const timeBadge = ev.reminder_time ? `🕒 ${ev.reminder_time} ` : "";
    const delBtn = ev.type !== "ics" ? `<button type="button" class="custom-room-del-btn cal-del-ev-btn" data-evid="${ev.id}" title="Eliminar hito">×</button>` : "";
    return `<span class="custom-room-chip">${timeBadge}${ev.title} <small style="opacity:0.7;">(${ev.source || "Domos"})</small>${delBtn}</span>`;
  }).join("");

  bar.querySelectorAll(".cal-del-ev-btn").forEach(btn => {
    btn.addEventListener("click", async () => {
      const id = btn.getAttribute("data-evid");
      await fetch(`/api/calendar/${encodeURIComponent(id)}`, { method: "DELETE" });
      await fetchCalendarData();
    });
  });
}

function renderCalendarModal() {
  const lbl = document.getElementById("cal-month-label");
  const grid = document.getElementById("cal-grid-days");
  if (!lbl || !grid) return;

  const firstDay = new Date(calViewYear, calViewMonth, 1);
  lbl.textContent = firstDay.toLocaleDateString("es-ES", { month: "long", year: "numeric" });

  // Monday = 0 .. Sunday = 6
  const startOffset = (firstDay.getDay() + 6) % 7;
  const daysInMonth = new Date(calViewYear, calViewMonth + 1, 0).getDate();
  const prevMonthDays = new Date(calViewYear, calViewMonth, 0).getDate();

  const now = new Date();
  const todayStr = formatYmd(now.getFullYear(), now.getMonth(), now.getDate());

  const byDate = {};
  const yearsVisible = [calViewYear - 1, calViewYear, calViewYear + 1];
  calendarEvents.forEach(ev => {
    if (!ev.date) return;
    if (ev.repeat === "yearly" && ev.date.length >= 10) {
      const mmdd = ev.date.slice(5, 10);
      yearsVisible.forEach(yr => {
        const dKey = `${yr}-${mmdd}`;
        if (!byDate[dKey]) byDate[dKey] = [];
        byDate[dKey].push(ev);
      });
    } else {
      if (!byDate[ev.date]) byDate[ev.date] = [];
      byDate[ev.date].push(ev);
    }
  });

  const cells = [];
  for (let i = 0; i < 42; i++) {
    let y = calViewYear, m = calViewMonth, d = 1, isOther = false;
    if (i < startOffset) {
      isOther = true;
      d = prevMonthDays - startOffset + i + 1;
      m = calViewMonth - 1;
      if (m < 0) { m = 11; y -= 1; }
    } else if (i >= startOffset + daysInMonth) {
      isOther = true;
      d = i - (startOffset + daysInMonth) + 1;
      m = calViewMonth + 1;
      if (m > 11) { m = 0; y += 1; }
    } else {
      d = i - startOffset + 1;
    }

    const ymd = formatYmd(y, m, d);
    const dayEvs = byDate[ymd] || [];
    const cls = [
      "cal-day-cell",
      isOther ? "is-other-month" : "",
      ymd === todayStr ? "is-today" : "",
      ymd === calSelectedDate ? "is-selected" : ""
    ].filter(Boolean).join(" ");

    const chips = dayEvs.slice(0, 3).map(ev => {
      const evCls = ev.type === "ics" ? "is-ics" : (ev.type === "birthday" ? "is-birthday" : "");
      const icon = ev.type === "birthday" ? "🎂 " : (ev.type === "ics" ? "🔗 " : "• ");
      return `<div class="cal-event-chip ${evCls}" title="${ev.title}">${icon}${ev.title}</div>`;
    }).join("") + (dayEvs.length > 3 ? `<div style="font-size:0.66rem; font-weight:700; color:var(--modal-text-muted);">+${dayEvs.length - 3} más</div>` : "");

    cells.push(`
      <div class="${cls}" data-ymd="${ymd}">
        <div class="cal-day-num">${d}</div>
        <div class="cal-day-events">${chips}</div>
      </div>
    `);
  }

  grid.innerHTML = cells.join("");
  grid.querySelectorAll(".cal-day-cell").forEach(cell => {
    cell.addEventListener("click", () => {
      calSelectedDate = cell.getAttribute("data-ymd");
      const dInp = document.getElementById("cal-new-date-input");
      if (dInp) dInp.value = calSelectedDate;
      renderCalendarModal();
    });
  });

  renderCalendarDayDetail();
  renderCalendarSourcesList();
}

function openCalendarModal() {
  const modal = document.getElementById("calendar-modal");
  if (!modal) return;
  modal.classList.remove("hidden");
  modal.style.display = "flex";
  const dInp = document.getElementById("cal-new-date-input");
  if (dInp && !dInp.value) dInp.value = calSelectedDate;
  renderCalendarModal();
  fetchCalendarData();
}

function closeCalendarModal() {
  const modal = document.getElementById("calendar-modal");
  if (!modal) return;
  modal.classList.add("hidden");
  modal.style.display = "none";
}

document.getElementById("hud-calendar-pill")?.addEventListener("click", openCalendarModal);
document.getElementById("clock-touch-target")?.addEventListener("click", (e) => {
  if (e.target.closest("#standby-incident-badge")) return;
  openCalendarModal();
});
document.getElementById("clock-time")?.addEventListener("click", openCalendarModal);
document.getElementById("clock-date")?.addEventListener("click", openCalendarModal);
document.getElementById("btn-calendar-modal-close")?.addEventListener("click", closeCalendarModal);
document.getElementById("calendar-modal")?.addEventListener("click", (e) => {
  if (e.target.id === "calendar-modal") closeCalendarModal();
});

document.getElementById("cal-prev-month")?.addEventListener("click", () => {
  calViewMonth -= 1;
  if (calViewMonth < 0) { calViewMonth = 11; calViewYear -= 1; }
  renderCalendarModal();
});
document.getElementById("cal-next-month")?.addEventListener("click", () => {
  calViewMonth += 1;
  if (calViewMonth > 11) { calViewMonth = 0; calViewYear += 1; }
  renderCalendarModal();
});
document.getElementById("cal-today-btn")?.addEventListener("click", () => {
  const n = new Date();
  calViewYear = n.getFullYear();
  calViewMonth = n.getMonth();
  calSelectedDate = formatYmd(calViewYear, calViewMonth, n.getDate());
  renderCalendarModal();
});

document.getElementById("cal-btn-toggle-add")?.addEventListener("click", () => {
  document.getElementById("cal-add-panel")?.classList.toggle("hidden");
  document.getElementById("cal-ics-panel")?.classList.add("hidden");
});
document.getElementById("cal-btn-toggle-ics")?.addEventListener("click", () => {
  document.getElementById("cal-ics-panel")?.classList.toggle("hidden");
  document.getElementById("cal-add-panel")?.classList.add("hidden");
  renderCalendarSourcesList();
});

const calNewTitleInp = document.getElementById("cal-new-title-input");
calNewTitleInp?.addEventListener("click", () => openOsk(calNewTitleInp));
const calIcsNameInp = document.getElementById("cal-ics-name-input");
calIcsNameInp?.addEventListener("click", () => openOsk(calIcsNameInp));

document.getElementById("cal-save-event-btn")?.addEventListener("click", async () => {
  const title = calNewTitleInp?.value?.trim();
  const dateVal = document.getElementById("cal-new-date-input")?.value || calSelectedDate;
  const timeVal = document.getElementById("cal-new-time-input")?.value || "09:00";
  if (!title) { openOsk(calNewTitleInp); return; }
  await fetch("/api/calendar", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, date: dateVal, type: "event", reminder_time: timeVal })
  });
  calNewTitleInp.value = "";
  document.getElementById("cal-add-panel")?.classList.add("hidden");
  await fetchCalendarData();
});

document.getElementById("cal-add-ics-btn")?.addEventListener("click", async () => {
  const name = calIcsNameInp?.value?.trim() || "Calendario";
  const url = document.getElementById("cal-ics-url-input")?.value?.trim();
  if (!url) return;
  const next = [...calendarIcsSources, { name, url }];
  const res = await fetch("/api/calendar/sources", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sources: next })
  });
  if (res.ok) {
    const d = await res.json();
    calendarIcsSources = d.sources || [];
    calendarEvents = d.events || [];
    if (calIcsNameInp) calIcsNameInp.value = "";
    const uInp = document.getElementById("cal-ics-url-input");
    if (uInp) uInp.value = "";
    renderCalendarSourcesList();
    renderCalendarModal();
    renderHudCalendarPill();
  }
});

fetchCalendarData();
setInterval(fetchCalendarData, 60000);

async function refreshSdPhotosSilently(newestFile) {
  try {
    const res = await fetch("/api/photos");
    if (!res.ok) return;
    const data = await res.json();
    const list = data.photos || [];
    if (list.length > 0) {
      sdPhotoList = list;
      if (newestFile) {
        const matchIdx = sdPhotoList.findIndex(u => u.endsWith("/" + newestFile));
        if (matchIdx >= 0) {
          currentPhotoIndex = (matchIdx - 1 + sdPhotoList.length) % sdPhotoList.length;
          showNextSlide();
        }
      }
    }
  } catch (e) {}
}
setInterval(() => refreshSdPhotosSilently(null), 120000);

// --- Alarm & Security Details Modal ---
async function openAlarmDetailsModal() {
  fetch("/api/debug_log", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({in_openAlarmDetailsModal: true, has_modal_el: Boolean(document.getElementById("alarm-details-modal"))})}).catch(()=>{});
  const modal = document.getElementById("alarm-details-modal");
  if (!modal) return;
  modal.classList.remove("hidden");
  modal.style.display = "flex";

  const body = document.getElementById("alarm-modal-body");
  if (body) {
    body.innerHTML = `
      <div style="display:flex; justify-content:center; align-items:center; padding:2.5rem 0; gap:0.75rem; color:var(--modal-text-muted);">
        <div class="kiosk-spinner" style="width:24px; height:24px; border:3px solid rgba(56,189,248,0.2); border-top-color:#38bdf8; border-radius:50%; animation:spin 0.8s linear infinite;"></div>
        <span>Consultando diagnóstico y baterías de seguridad...</span>
      </div>
    `;
  }

  try {
    const res = await fetch("/api/security/details");
    if (!res.ok) throw new Error("HTTP " + res.status);
    const data = await res.json();
    renderAlarmModalContent(data);
  } catch (e) {
    fetch("/api/debug_log", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({modal_err: e.message, stack: e.stack})}).catch(()=>{});
    if (body) {
      body.innerHTML = `
        <div style="padding:1.5rem; text-align:center; color:#f87171; background:rgba(239,68,68,0.1); border-radius:18px;">
          <p style="margin:0; font-weight:600;">No se pudo conectar con el servicio de seguridad (${e.message})</p>
        </div>
      `;
    }
  }
}

function renderAlarmModalContent(data) {
  const body = document.getElementById("alarm-modal-body");
  if (!body) return;

  const mode = data.alarm_mode || "disarmed";
  const sec = data.security_devices || {};
  const lowBats = data.low_battery_warnings || [];
  const inventory = data.battery_inventory || [];

  let modeBadge = `<span style="background:rgba(16,185,129,0.2); color:#34d399; padding:0.35rem 0.85rem; border-radius:999px; font-weight:700; font-size:0.88rem; border:1px solid rgba(16,185,129,0.4);">DESARMADA</span>`;
  if (mode === "arm") {
    modeBadge = `<span style="background:rgba(239,68,68,0.25); color:#f87171; padding:0.35rem 0.85rem; border-radius:999px; font-weight:700; font-size:0.88rem; border:1px solid rgba(239,68,68,0.5);">🚨 TOTALMENTE ARMADA</span>`;
  } else if (mode === "home") {
    modeBadge = `<span style="background:rgba(245,158,11,0.25); color:#fbbf24; padding:0.35rem 0.85rem; border-radius:999px; font-weight:700; font-size:0.88rem; border:1px solid rgba(245,158,11,0.5);">🏠 ARMADA EN CASA</span>`;
  }

  // Low battery banner
  let lowBatHtml = "";
  if (lowBats.length > 0) {
    const itemsList = lowBats.map(b => `
      <li style="margin:0.25rem 0; font-size:0.86rem; color:#fca5a5;">
        <strong>${b.name}</strong>: ${b.alarm_state === 'low_battery' ? '⚠️ Advertencia de batería baja emitida por el dispositivo' : 'Batería agotada/crítica (' + b.battery + '%)'}
      </li>
    `).join("");

    lowBatHtml = `
      <div style="background:rgba(239,68,68,0.12); border:1px solid rgba(239,68,68,0.35); border-radius:18px; padding:0.9rem 1.15rem;">
        <div style="display:flex; align-items:center; gap:0.5rem; font-weight:700; color:#f87171; font-size:0.95rem; margin-bottom:0.4rem;">
          <span>⚠️ Aviso de Mantenimiento de Batería</span>
        </div>
        <ul style="margin:0; padding-left:1.2rem;">${itemsList}</ul>
      </div>
    `;
  }

  const door = sec.door || {};
  const doorSt = door.state || {};
  const lock = sec.lock || {};
  const lockSt = lock.state || {};
  const motion = sec.motion || {};
  const motionSt = motion.state || {};
  const pir = sec.pir || {};
  const pirSt = pir.state || {};
  const smoke = sec.smoke_co || {};
  const smokeSt = smoke.state || {};
  const vib = sec.vibration || {};
  const vibSt = vib.state || {};

  function batBadge(val) {
    if (val === undefined || val === null) return `<span style="color:var(--modal-text-muted);">--</span>`;
    if (typeof val === "number") {
      const col = val > 50 ? "#34d399" : (val > 25 ? "#fbbf24" : "#f87171");
      return `<span style="font-weight:700; color:${col};">${val}%</span>`;
    }
    const s = String(val).toLowerCase();
    if (s.includes("high") || s.includes("alta")) return `<span style="color:#34d399; font-weight:700;">Alta</span>`;
    if (s.includes("middle") || s.includes("media") || s.includes("normal")) return `<span style="color:#38bdf8; font-weight:700;">Normal</span>`;
    if (s.includes("low") || s.includes("baja")) return `<span style="color:#f87171; font-weight:700;">Baja ⚠️</span>`;
    return `<span style="font-weight:600;">${val}</span>`;
  }

  body.innerHTML = `
    <div style="background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.1); border-radius:20px; padding:1.1rem 1.25rem; display:flex; flex-direction:column; gap:0.9rem;">
      <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.6rem;">
        <div>
          <div style="font-size:0.8rem; color:var(--modal-text-muted); font-weight:600; text-transform:uppercase; letter-spacing:0.04em;">Central de Alarma Tuya</div>
          <div style="font-size:1.15rem; font-weight:700; margin-top:0.2rem; display:flex; align-items:center; gap:0.6rem;">
            ${data.alarm_name} ${modeBadge}
          </div>
        </div>
        <div style="font-size:0.85rem; color:var(--modal-text-muted);">
          Batería Central: <strong>${data.alarm_battery}%</strong>
        </div>
      </div>
      
      <div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:0.6rem;">
        <button id="btn-alarm-disarm" class="liquid-action-pill" style="justify-content:center; padding:0.7rem; font-size:0.88rem; font-weight:700; cursor:pointer; background:${mode === 'disarmed' ? 'rgba(16,185,129,0.25)' : 'rgba(255,255,255,0.06)'}; border-color:${mode === 'disarmed' ? '#10b981' : 'rgba(255,255,255,0.12)'}; color:${mode === 'disarmed' ? '#34d399' : '#fff'};">
          🔓 Desarmar
        </button>
        <button id="btn-alarm-home" class="liquid-action-pill" style="justify-content:center; padding:0.7rem; font-size:0.88rem; font-weight:700; cursor:pointer; background:${mode === 'home' ? 'rgba(245,158,11,0.25)' : 'rgba(255,255,255,0.06)'}; border-color:${mode === 'home' ? '#f59e0b' : 'rgba(255,255,255,0.12)'}; color:${mode === 'home' ? '#fbbf24' : '#fff'};">
          🏠 En Casa
        </button>
        <button id="btn-alarm-arm" class="liquid-action-pill" style="justify-content:center; padding:0.7rem; font-size:0.88rem; font-weight:700; cursor:pointer; background:${mode === 'arm' ? 'rgba(239,68,68,0.25)' : 'rgba(255,255,255,0.06)'}; border-color:${mode === 'arm' ? '#ef4444' : 'rgba(255,255,255,0.12)'}; color:${mode === 'arm' ? '#f87171' : '#fff'};">
          🚨 Armar Todo
        </button>
      </div>
    </div>

    ${lowBatHtml}

    <div style="display:flex; flex-direction:column; gap:0.6rem;">
      <div style="font-size:0.85rem; font-weight:700; color:var(--modal-text-muted); text-transform:uppercase; letter-spacing:0.04em;">Sensores y Detectores</div>
      
      <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(260px, 1fr)); gap:0.75rem;">
        <div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08); border-radius:16px; padding:0.85rem 1rem; display:flex; justify-content:space-between; align-items:center;">
          <div>
            <div style="font-size:0.92rem; font-weight:600;">🚪 Puerta Principal</div>
            <div style="font-size:0.8rem; color:${doorSt.is_open ? '#f87171' : '#34d399'}; font-weight:600; margin-top:0.2rem;">
              ${doorSt.is_open ? '¡ABIERTA!' : 'Cerrada / Asegurada'}
            </div>
          </div>
          <div style="text-align:right; font-size:0.8rem; color:var(--modal-text-muted);">
            Batería<br>${batBadge(doorSt.battery)}
          </div>
        </div>

        <div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08); border-radius:16px; padding:0.85rem 1rem; display:flex; justify-content:space-between; align-items:center;">
          <div>
            <div style="font-size:0.92rem; font-weight:600;">🔐 Cerradura Inteligente</div>
            <div style="font-size:0.8rem; color:${lockSt.alarm_lock === 'low_battery' ? '#fbbf24' : '#34d399'}; font-weight:600; margin-top:0.2rem;">
              ${lockSt.alarm_lock === 'low_battery' ? '⚠️ Aviso de Pila' : 'Cerrojo Normal'}
            </div>
          </div>
          <div style="text-align:right; font-size:0.8rem; color:var(--modal-text-muted);">
            Batería<br>${batBadge(lockSt.battery_state || lockSt.battery)}
          </div>
        </div>

        <div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08); border-radius:16px; padding:0.85rem 1rem; display:flex; justify-content:space-between; align-items:center;">
          <div>
            <div style="font-size:0.92rem; font-weight:600;">🌿 Sensor Movimiento Patio</div>
            <div style="font-size:0.8rem; color:#38bdf8; font-weight:600; margin-top:0.2rem;">
              PIR Activo (Vigilancia)
            </div>
          </div>
          <div style="text-align:right; font-size:0.8rem; color:var(--modal-text-muted);">
            Batería<br>${batBadge(motionSt.battery)}
          </div>
        </div>

        <div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08); border-radius:16px; padding:0.85rem 1rem; display:flex; justify-content:space-between; align-items:center;">
          <div>
            <div style="font-size:0.92rem; font-weight:600;">👀 Sensor PIR Interior</div>
            <div style="font-size:0.8rem; color:#38bdf8; font-weight:600; margin-top:0.2rem;">
              Sensor Infrarrojo
            </div>
          </div>
          <div style="text-align:right; font-size:0.8rem; color:var(--modal-text-muted);">
            Batería<br>${batBadge(pirSt.battery)}
          </div>
        </div>

        <div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08); border-radius:16px; padding:0.85rem 1rem; display:flex; justify-content:space-between; align-items:center;">
          <div>
            <div style="font-size:0.92rem; font-weight:600;">🍳 Detector Humo y CO Cocina</div>
            <div style="font-size:0.8rem; color:${smokeSt.is_alarm ? '#f87171' : '#34d399'}; font-weight:600; margin-top:0.2rem;">
              ${smokeSt.is_alarm ? '🚨 ¡ALARMA HUMO/CO!' : 'Seguro (CO: ' + (smokeSt.co_ppm || 0) + ' ppm)'}
            </div>
          </div>
          <div style="text-align:right; font-size:0.8rem; color:var(--modal-text-muted);">
            Batería<br>${batBadge(smokeSt.battery)}
          </div>
        </div>

        <div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08); border-radius:16px; padding:0.85rem 1rem; display:flex; justify-content:space-between; align-items:center;">
          <div>
            <div style="font-size:0.92rem; font-weight:600;">🪟 Sensor Vibración Ventana</div>
            <div style="font-size:0.8rem; color:#34d399; font-weight:600; margin-top:0.2rem;">
              Sin vibración / Normal
            </div>
          </div>
          <div style="text-align:right; font-size:0.8rem; color:var(--modal-text-muted);">
            Batería<br>${batBadge(vibSt.battery)}
          </div>
        </div>
      </div>
    </div>

    <div style="display:flex; flex-direction:column; gap:0.6rem;">
      <div style="font-size:0.85rem; font-weight:700; color:var(--modal-text-muted); text-transform:uppercase; letter-spacing:0.04em;">Nivel de Baterías de Todos los Dispositivos</div>
      <div style="background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.06); border-radius:18px; padding:0.75rem 1rem; display:flex; flex-direction:column; gap:0.55rem;">
        ${inventory.map(item => `
          <div style="display:flex; justify-content:space-between; align-items:center; padding:0.35rem 0; border-bottom:1px solid rgba(255,255,255,0.04);">
            <div style="display:flex; align-items:center; gap:0.6rem;">
              <span style="font-size:0.9rem;">${item.category === 'security' ? '🛡️' : (item.category === 'climate' ? '🌡️' : '🔋')}</span>
              <span style="font-size:0.86rem; font-weight:600;">${item.name}</span>
            </div>
            <div style="display:flex; align-items:center; gap:0.75rem;">
              <span style="font-size:0.78rem; color:var(--modal-text-muted);">${item.status_text || ''}</span>
              ${batBadge(item.battery)}
            </div>
          </div>
        `).join("")}
      </div>
    </div>
  `;

  const alarmId = data.alarm_id || "64326051e8db8480acc0";
  async function sendAlarmMode(newMode) {
    try {
      await fetch("/api/devices/control", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ device_id: alarmId, code: "master_mode", value: newMode })
      });
      setTimeout(openAlarmDetailsModal, 800);
    } catch (e) {
      alert("Error al enviar orden a la alarma: " + e.message);
    }
  }

  document.getElementById("btn-alarm-disarm")?.addEventListener("click", () => sendAlarmMode("disarmed"));
  document.getElementById("btn-alarm-home")?.addEventListener("click", () => sendAlarmMode("home"));
  document.getElementById("btn-alarm-arm")?.addEventListener("click", () => sendAlarmMode("arm"));
}

document.getElementById("hud-alarm-pill")?.addEventListener("click", openAlarmModal);
document.getElementById("hud-door-pill")?.addEventListener("click", openAlarmModal);
document.getElementById("btn-alarm-modal-close")?.addEventListener("click", () => {
  const m = document.getElementById("alarm-details-modal");
  if (m) { m.classList.add("hidden"); m.style.display = "none"; }
});
document.getElementById("alarm-details-modal")?.addEventListener("click", (e) => {
  if (e.target.id === "alarm-details-modal") {
    e.target.classList.add("hidden");
    e.target.style.display = "none";
  }
});

// --- Mac & Remote Photo Drag-and-Drop Upload ---
function wirePhotoUploadZone() {
  const dropZone = document.getElementById("drop-photo-zone");
  const fileInput = document.getElementById("modal-photo-file-input");
  const statusEl = document.getElementById("photo-upload-status");
  if (!dropZone || !fileInput) return;

  dropZone.addEventListener("click", () => fileInput.click());

  dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.style.borderColor = "#38bdf8";
    dropZone.style.background = "rgba(56,189,248,0.15)";
  });

  dropZone.addEventListener("dragleave", () => {
    dropZone.style.borderColor = "rgba(56,189,248,0.4)";
    dropZone.style.background = "rgba(56,189,248,0.05)";
  });

  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.style.borderColor = "rgba(56,189,248,0.4)";
    dropZone.style.background = "rgba(56,189,248,0.05)";
    if (e.dataTransfer && e.dataTransfer.files.length > 0) {
      handlePhotoUpload(e.dataTransfer.files);
    }
  });

  fileInput.addEventListener("change", () => {
    if (fileInput.files.length > 0) {
      handlePhotoUpload(fileInput.files);
    }
  });

  async function handlePhotoUpload(files) {
    if (!statusEl) return;
    statusEl.style.display = "block";
    statusEl.style.background = "rgba(56,189,248,0.15)";
    statusEl.style.color = "#38bdf8";
    statusEl.textContent = `Subiendo ${files.length} foto(s) a la SD...`;

    let successCount = 0;
    let failCount = 0;

    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      statusEl.textContent = `Subiendo foto ${i + 1} de ${files.length} (${file.name})...`;
      const formData = new FormData();
      formData.append("file", file);
      formData.append("folder", "Images");

      try {
        const res = await fetch("/api/sd/upload", {
          method: "POST",
          body: formData
        });
        if (res.ok) successCount++;
        else failCount++;
      } catch (err) {
        failCount++;
      }
    }

    if (failCount === 0) {
      statusEl.style.background = "rgba(16,185,129,0.2)";
      statusEl.style.color = "#34d399";
      statusEl.textContent = `✅ ¡${successCount} foto(s) subidas con éxito a la SD!`;
    } else {
      statusEl.style.background = "rgba(245,158,11,0.2)";
      statusEl.style.color = "#fbbf24";
      statusEl.textContent = `Subidas: ${successCount} | Fallos: ${failCount}`;
    }

    setTimeout(() => {
      if (typeof fetchPhotosList === "function") fetchPhotosList();
      fileInput.value = "";
    }, 1500);
  }
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", wirePhotoUploadZone);
} else {
  wirePhotoUploadZone();
}



// ========================================================
// AIR QUALITY & OUTDOOR POLLEN MODULE (29720)
// ========================================================
let latestAirQualityData = null;

async function fetchAirQualityData() {
  try {
    const res = await fetch("/api/air/quality");
    if (res.ok) {
      latestAirQualityData = await res.json();
      renderAirQualityGrid();
      updateIndoorAirHud();
    }
  } catch (e) {
    console.error("Error fetching air quality:", e);
  }
}

function updateIndoorAirHud() {
  const airGrid = document.getElementById("hud-air-rooms-grid");
  const airBadge = document.getElementById("hud-air-badge");
  if (!latestAirQualityData) return;

  const d = latestAirQualityData;
  const ev = d.evaluation || {};
  const ind = d.indoor || {};
  const pur = ind.purifier || {};
  const sot = ind.sotano || {};
  const coc = ind.cocina || {};
  const out = d.outdoor || {};

  if (airBadge) {
    airBadge.textContent = ev.badge || "Excelente 🟢";
    airBadge.style.color = ev.badge_color || "#10b981";
    airBadge.style.borderColor = `${ev.badge_color || "#10b981"}55`;
    airBadge.style.background = `${ev.badge_color || "#10b981"}22`;
  }

  if (airGrid) {
    const sotCo2 = (sot.co2 !== undefined && sot.co2 > 10) ? `${sot.co2} ppm` : `Nivel ${sot.co2 ?? 1} (Óptimo)`;
    airGrid.innerHTML = `
      <div class="hud-room-item" title="Salón: ${pur.aqi ?? '--'} µg/m³ PM2.5 (Calidad ${pur.quality_label || 'Buena'})">
        <span class="hud-room-name">🌀 Salón</span>
        <span class="hud-room-val">${pur.aqi ?? '--'} <span style="font-size:0.68rem; color:#38bdf8;">PM2.5</span></span>
      </div>
      <div class="hud-room-item" title="Sótano: CO₂ ${sotCo2}">
        <span class="hud-room-name">🌬️ Sótano</span>
        <span class="hud-room-val"><span style="font-size:0.75rem; color:#a855f7;">${sotCo2}</span></span>
      </div>
      <div class="hud-room-item" title="Cocina: Monóxido ${coc.co_ppm ?? 0} ppm, Humo Seguro">
        <span class="hud-room-name">🍳 Cocina</span>
        <span class="hud-room-val">${coc.co_ppm ?? 0} ppm <span style="font-size:0.68rem; color:#10b981;">Humo OK</span></span>
      </div>
      <div class="hud-room-item" title="Exterior 29720 (Rincón de la Victoria): Polen ${out.pollen_total ?? 0.5} gr/m³ (${out.pollen_level || 'Bajo'}), EAQI ${out.european_aqi ?? 25}">
        <span class="hud-room-name">🌿 Ext. 29720</span>
        <span class="hud-room-val">${out.pollen_total ?? 0.5} gr/m³ <span style="font-size:0.68rem; color:#10b981;">Polen Bajo</span></span>
      </div>
    `;
  }
}

function renderAirQualityGrid() {
  const container = document.getElementById("air-quality-grid");
  if (!container) return;
  if (!latestAirQualityData) {
    container.innerHTML = `<div class="liquid-card"><p style="color:var(--modal-text-muted); margin:0; font-size:0.8rem;">Cargando análisis de aire...</p></div>`;
    return;
  }

  const d = latestAirQualityData;
  const ev = d.evaluation || {};
  const ind = d.indoor || {};
  const pur = ind.purifier || {};
  const sot = ind.sotano || {};
  const coc = ind.cocina || {};
  const out = d.outdoor || {};

  const sotCo2 = (sot.co2 !== undefined && sot.co2 > 10) ? `${sot.co2} ppm` : `Nivel ${sot.co2 ?? 2}`;

  const sotCo2Short = (sot.co2 !== undefined && sot.co2 > 10) ? `${sot.co2}` : `${sot.co2 ?? 2}`;
  container.innerHTML = `
    <div class="liquid-card air-quality-card" id="card-air-quality-main" style="cursor:pointer; padding:0.68rem 0.78rem; gap:0.38rem;" title="Pulsa para ver análisis de calidad del aire, polen y control de purificador">
      <div style="display:flex; justify-content:space-between; align-items:center; gap:0.4rem;">
        <span style="font-size:0.72rem; font-weight:700; padding:0.14rem 0.5rem; border-radius:999px; background:rgba(16,185,129,0.18); color:${ev.badge_color || '#10b981'}; border:1px solid ${ev.badge_color || '#10b981'}44;">${ev.badge || 'Excelente 🟢'}</span>
        <span style="font-size:0.72rem; font-weight:700; color:var(--neon-cyan); white-space:nowrap;">Detalle & Polen ›</span>
      </div>
      <div style="font-size:0.82rem; font-weight:700; color:var(--modal-text); line-height:1.15; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${ev.headline || 'Aire Saludable & Pureza Óptima'}</div>

      <!-- 3 Habitaciones compactas -->
      <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:0.3rem;">
        <div style="background:rgba(255,255,255,0.04); padding:0.3rem 0.25rem; border-radius:10px; border:1px solid var(--modal-subcard-border); text-align:center;">
          <div style="font-size:0.64rem; color:var(--modal-text-muted);">🌀 Salón</div>
          <div style="font-size:0.86rem; font-weight:800; color:#38bdf8; line-height:1.15;">${pur.aqi ?? '--'}</div>
          <div style="font-size:0.61rem; color:${pur.quality_color || '#10b981'}; font-weight:700;">PM2.5 · ${pur.quality_label || 'Buena'}</div>
        </div>
        <div style="background:rgba(255,255,255,0.04); padding:0.3rem 0.25rem; border-radius:10px; border:1px solid var(--modal-subcard-border); text-align:center;">
          <div style="font-size:0.64rem; color:var(--modal-text-muted);">🌬️ Sótano</div>
          <div style="font-size:0.86rem; font-weight:800; color:#a855f7; line-height:1.15;">${sotCo2Short}</div>
          <div style="font-size:0.61rem; color:${sot.quality_color || '#10b981'}; font-weight:700;">ppm CO₂</div>
        </div>
        <div style="background:rgba(255,255,255,0.04); padding:0.3rem 0.25rem; border-radius:10px; border:1px solid var(--modal-subcard-border); text-align:center;">
          <div style="font-size:0.64rem; color:var(--modal-text-muted);">🍳 Cocina</div>
          <div style="font-size:0.86rem; font-weight:800; color:#10b981; line-height:1.15;">${coc.co_ppm ?? 0}</div>
          <div style="font-size:0.61rem; color:#10b981; font-weight:700;">ppm CO · OK</div>
        </div>
      </div>

      <!-- Exterior 29720 Polen compacto -->
      <div style="display:flex; justify-content:space-between; align-items:center; gap:0.35rem; background:rgba(56,189,248,0.08); padding:0.3rem 0.5rem; border-radius:10px; border:1px solid rgba(56,189,248,0.22); font-size:0.68rem; line-height:1.2;">
        <span style="color:var(--modal-text);">🌤️ <b>29720:</b> EAQI ${out.european_aqi ?? 25} · ${out.pm2_5 ?? 3.6} PM</span>
        <span style="color:${out.pollen_color || '#10b981'}; font-weight:700; white-space:nowrap;">Polen ${out.pollen_total ?? 0.5} (${out.pollen_level || 'Bajo'})</span>
      </div>
    </div>
  `;

  document.getElementById("card-air-quality-main")?.addEventListener("click", openAirQualityModal);
}

function openAirQualityModal() {
  const modal = document.getElementById("air-quality-modal");
  if (!modal) return;
  modal.classList.remove("hidden");
  modal.style.display = "flex";
  renderAirQualityModalContent();
}

function closeAirQualityModal() {
  const modal = document.getElementById("air-quality-modal");
  if (modal) {
    modal.classList.add("hidden");
    modal.style.display = "none";
  }
}

function renderAirQualityModalContent() {
  const body = document.getElementById("air-modal-body");
  const badge = document.getElementById("air-modal-badge");
  if (!body || !latestAirQualityData) return;

  const d = latestAirQualityData;
  const ev = d.evaluation || {};
  const ind = d.indoor || {};
  const pur = ind.purifier || {};
  const sot = ind.sotano || {};
  const coc = ind.cocina || {};
  const out = d.outdoor || {};
  const pb = out.pollen_breakdown || {};

  if (badge) {
    badge.textContent = ev.badge || "Excelente 🟢";
    badge.style.color = ev.badge_color || "#10b981";
    badge.style.borderColor = `${ev.badge_color || "#10b981"}55`;
    badge.style.background = `${ev.badge_color || "#10b981"}22`;
  }

  const sotCo2 = (sot.co2 !== undefined && sot.co2 > 10) ? `${sot.co2} ppm` : `Nivel ${sot.co2 ?? 2}`;
  const isPurOn = Boolean(pur.is_on);
  const purMode = (pur.mode || "auto").toLowerCase();

  body.innerHTML = `
    <!-- 1. Diagnóstico Inteligente del Aire -->
    <div class="domos-modal-subcard" style="padding:1rem 1.25rem; border-radius:18px; background:linear-gradient(135deg, rgba(16,185,129,0.12), rgba(56,189,248,0.06)); border:1px solid rgba(16,185,129,0.35);">
      <div style="display:flex; align-items:center; gap:0.6rem; margin-bottom:0.35rem;">
        <span style="font-size:1.3rem;">🍃</span>
        <h4 style="margin:0; font-size:1.05rem; color:var(--modal-text);">${ev.headline || "Calidad del Aire Interior & Exterior"}</h4>
      </div>
      <p style="margin:0; font-size:0.86rem; color:var(--modal-text); line-height:1.45;">${ev.summary || ""}</p>
    </div>

    <!-- 2. Detalle Interior por Estancias -->
    <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(240px, 1fr)); gap:0.75rem;">
      <!-- Salón: Purificador Xiaomi -->
      <div class="domos-modal-subcard" style="padding:0.95rem 1.15rem; border-radius:18px; display:flex; flex-direction:column; gap:0.55rem;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <div style="display:flex; align-items:center; gap:0.4rem; font-weight:700; font-size:0.92rem;">
            <span>🌀</span><span>Salón (Purificador)</span>
          </div>
          <button type="button" class="liquid-action-pill btn-modal-pur-power" data-id="${pur.id}" data-on="${isPurOn ? "1" : "0"}" style="cursor:pointer; padding:0.25rem 0.65rem; font-size:0.76rem; background:${isPurOn ? "rgba(16,185,129,0.25)" : "rgba(255,255,255,0.06)"}; border-color:${isPurOn ? "#10b981" : "var(--modal-subcard-border)"};">
            ${isPurOn ? "Encendido" : "Apagado"}
          </button>
        </div>
        <div style="display:flex; justify-content:space-between; align-items:baseline;">
          <div>
            <span style="font-size:1.7rem; font-weight:800; color:#38bdf8;">${pur.aqi ?? '--'}</span>
            <span style="font-size:0.78rem; color:var(--modal-text-muted); font-weight:600;">µg/m³ PM2.5</span>
          </div>
          <span style="font-size:0.8rem; font-weight:700; color:${pur.quality_color || '#10b981'};">${pur.quality_label || 'Buena'}</span>
        </div>
        <div style="font-size:0.78rem; color:var(--modal-text-muted); display:flex; justify-content:space-between;">
          <span>🌡️ ${pur.temperature ?? '--'}°C · 💧 ${pur.humidity ?? '--'}%</span>
          <span>Filtro: <b>${pur.filter_life ?? '--'}%</b></span>
        </div>
        <!-- Selectores de Modo del Purificador -->
        <div style="display:flex; gap:0.35rem; margin-top:0.2rem;">
          <button type="button" class="liquid-action-pill btn-modal-pur-mode" data-id="${pur.id}" data-mode="auto" style="flex:1; cursor:pointer; padding:0.28rem; font-size:0.75rem; ${isPurOn && purMode === "auto" ? "background:rgba(56,189,248,0.25); border-color:#38bdf8; font-weight:700;" : ""}">✨ Auto</button>
          <button type="button" class="liquid-action-pill btn-modal-pur-mode" data-id="${pur.id}" data-mode="silent" style="flex:1; cursor:pointer; padding:0.28rem; font-size:0.75rem; ${isPurOn && purMode === "silent" ? "background:rgba(56,189,248,0.25); border-color:#38bdf8; font-weight:700;" : ""}">🌙 Noche</button>
          <button type="button" class="liquid-action-pill btn-modal-pur-mode" data-id="${pur.id}" data-mode="favorite" style="flex:1; cursor:pointer; padding:0.28rem; font-size:0.75rem; ${isPurOn && purMode === "favorite" ? "background:rgba(56,189,248,0.25); border-color:#38bdf8; font-weight:700;" : ""}">⚡ Potente</button>
        </div>
        <!-- Automatización Purificador por PM2.5 -->
        <div style="margin-top:0.35rem; padding:0.45rem 0.6rem; border-radius:12px; background:rgba(16,185,129,0.08); border:1px solid rgba(16,185,129,0.25); display:flex; flex-direction:column; gap:0.22rem;">
          <div style="display:flex; justify-content:space-between; align-items:center; gap:0.4rem;">
            <span style="font-size:0.74rem; font-weight:700; color:var(--modal-text);">🤖 Auto-Purificación</span>
            <button type="button" id="btn-toggle-air-auto" onclick="toggleAirPurifierAuto()" class="liquid-action-pill" style="cursor:pointer; padding:0.14rem 0.55rem; font-size:0.7rem; font-weight:700; background:${(d.air_auto?.config?.enabled !== false) ? 'rgba(16,185,129,0.24)' : 'rgba(148,163,184,0.20)'}; border-color:${(d.air_auto?.config?.enabled !== false) ? '#10b981' : 'var(--modal-subcard-border)'}; color:${(d.air_auto?.config?.enabled !== false) ? '#047857' : 'var(--modal-text-muted)'};">
              ${(d.air_auto?.config?.enabled !== false) ? 'Activa' : 'Pausada'}
            </button>
          </div>
          <div style="font-size:0.68rem; color:var(--modal-text-muted); line-height:1.25;">
            ON ≥ ${d.air_auto?.config?.on_pm25 ?? 35} PM2.5 · OFF ≤ ${d.air_auto?.config?.off_pm25 ?? 15} PM2.5 · 🌙 Noche 23–08h
          </div>
          <div style="font-size:0.69rem; color:var(--modal-text); font-weight:600;">${d.air_auto?.status_text || 'Supervisando PM2.5'}</div>
        </div>
      </div>

      <!-- Sótano: AirBox -->
      <div class="domos-modal-subcard" style="padding:0.95rem 1.15rem; border-radius:18px; display:flex; flex-direction:column; gap:0.55rem;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <div style="display:flex; align-items:center; gap:0.4rem; font-weight:700; font-size:0.92rem;">
            <span>🌬️</span><span>Sótano (AirBox)</span>
          </div>
          <span style="font-size:0.72rem; padding:0.2rem 0.5rem; border-radius:999px; background:rgba(168,85,247,0.18); color:#a855f7; border:1px solid rgba(168,85,247,0.35);">CO₂ / VOC</span>
        </div>
        <div style="display:flex; justify-content:space-between; align-items:baseline;">
          <div>
            <span style="font-size:1.7rem; font-weight:800; color:#a855f7;">${sotCo2}</span>
          </div>
          <span style="font-size:0.8rem; font-weight:700; color:${sot.quality_color || '#10b981'};">Aire Saludable</span>
        </div>
        <div style="font-size:0.78rem; color:var(--modal-text-muted); display:flex; justify-content:space-between;">
          <span>🌡️ ${sot.temperature ?? '--'}°C · 💧 ${sot.humidity ?? '--'}%</span>
          <span>Compuestos VOC: <b style="color:#10b981;">Limpio</b></span>
        </div>
        <div style="margin-top:auto; font-size:0.73rem; color:var(--modal-text-muted); line-height:1.25;">
          Monitorización continua por red local para prevención de concentración de CO₂.
        </div>
      </div>

      <!-- Cocina: Detector Humo y CO -->
      <div class="domos-modal-subcard" style="padding:0.95rem 1.15rem; border-radius:18px; display:flex; flex-direction:column; gap:0.55rem;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <div style="display:flex; align-items:center; gap:0.4rem; font-weight:700; font-size:0.92rem;">
            <span>🍳</span><span>Cocina (Humo & CO)</span>
          </div>
          <span style="font-size:0.72rem; padding:0.2rem 0.5rem; border-radius:999px; background:rgba(16,185,129,0.18); color:#10b981; border:1px solid rgba(16,185,129,0.35);">Seguridad</span>
        </div>
        <div style="display:flex; justify-content:space-between; align-items:baseline;">
          <div>
            <span style="font-size:1.7rem; font-weight:800; color:#10b981;">${coc.co_ppm ?? 0}</span>
            <span style="font-size:0.78rem; color:var(--modal-text-muted); font-weight:600;">ppm CO</span>
          </div>
          <span style="font-size:0.8rem; font-weight:700; color:#10b981;">Despejado 🛡️</span>
        </div>
        <div style="font-size:0.78rem; color:var(--modal-text-muted); display:flex; justify-content:space-between;">
          <span>Detector de Humo: <b style="color:#10b981;">Normal</b></span>
          <span>Batería: <b>OK</b></span>
        </div>
        <div style="margin-top:auto; font-size:0.73rem; color:var(--modal-text-muted); line-height:1.25;">
          Sin riesgos de combustión incompleta ni humos detectados en zona de cocina.
        </div>
      </div>
    </div>

    <!-- 3. Entorno Exterior & Niveles de Polen (CP 29720 - Rincón de la Victoria) -->
    <div class="domos-modal-subcard" style="padding:1rem 1.25rem; border-radius:18px; display:flex; flex-direction:column; gap:0.75rem;">
      <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.5rem;">
        <div>
          <div style="font-weight:700; font-size:0.95rem; color:var(--modal-text); display:flex; align-items:center; gap:0.4rem;">
            <span>🌿</span><span>Polen y Calidad Exterior · Código Postal 29720</span>
          </div>
          <div style="font-size:0.75rem; color:var(--modal-text-muted);">Estación meteorológica y ambiental de Rincón de la Victoria / Málaga</div>
        </div>
        <span style="font-size:0.8rem; font-weight:700; padding:0.25rem 0.65rem; border-radius:999px; background:rgba(56,189,248,0.18); color:#38bdf8; border:1px solid rgba(56,189,248,0.35);">EAQI ${out.european_aqi ?? 25} (Excelente)</span>
      </div>

      <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(130px, 1fr)); gap:0.5rem;">
        <div style="background:rgba(255,255,255,0.03); padding:0.6rem 0.75rem; border-radius:12px; border:1px solid var(--modal-subcard-border); text-align:center;">
          <div style="font-size:0.7rem; color:var(--modal-text-muted);">🌾 Gramíneas</div>
          <div style="font-size:1.1rem; font-weight:800; color:#10b981;">${pb.grass ?? 0} <span style="font-size:0.65rem;">gr/m³</span></div>
          <div style="font-size:0.65rem; color:var(--modal-text-muted);">Nulo</div>
        </div>
        <div style="background:rgba(255,255,255,0.03); padding:0.6rem 0.75rem; border-radius:12px; border:1px solid var(--modal-subcard-border); text-align:center;">
          <div style="font-size:0.7rem; color:var(--modal-text-muted);">🫒 Olivo</div>
          <div style="font-size:1.1rem; font-weight:800; color:#10b981;">${pb.olive ?? 0} <span style="font-size:0.65rem;">gr/m³</span></div>
          <div style="font-size:0.65rem; color:var(--modal-text-muted);">Nulo</div>
        </div>
        <div style="background:rgba(255,255,255,0.03); padding:0.6rem 0.75rem; border-radius:12px; border:1px solid var(--modal-subcard-border); text-align:center;">
          <div style="font-size:0.7rem; color:var(--modal-text-muted);">🌱 Artemisia</div>
          <div style="font-size:1.1rem; font-weight:800; color:#38bdf8;">${pb.mugwort ?? 0.5} <span style="font-size:0.65rem;">gr/m³</span></div>
          <div style="font-size:0.65rem; color:var(--modal-text-muted);">Muy bajo</div>
        </div>
        <div style="background:rgba(255,255,255,0.03); padding:0.6rem 0.75rem; border-radius:12px; border:1px solid var(--modal-subcard-border); text-align:center;">
          <div style="font-size:0.7rem; color:var(--modal-text-muted);">🌲 Abedul / Aliso</div>
          <div style="font-size:1.1rem; font-weight:800; color:#10b981;">${(pb.birch || 0) + (pb.alder || 0)} <span style="font-size:0.65rem;">gr/m³</span></div>
          <div style="font-size:0.65rem; color:var(--modal-text-muted);">Nulo</div>
        </div>
        <div style="background:rgba(255,255,255,0.03); padding:0.6rem 0.75rem; border-radius:12px; border:1px solid var(--modal-subcard-border); text-align:center;">
          <div style="font-size:0.7rem; color:var(--modal-text-muted);">💨 PM2.5 Exterior</div>
          <div style="font-size:1.1rem; font-weight:800; color:#38bdf8;">${out.pm2_5 ?? 3.6} <span style="font-size:0.65rem;">µg/m³</span></div>
          <div style="font-size:0.65rem; color:var(--modal-text-muted);">Limpio</div>
        </div>
      </div>
    </div>

    <!-- 4. Acceso directo a Gráficas Históricas -->
    <div style="display:flex; justify-content:flex-end; gap:0.6rem;">
      <button type="button" id="btn-air-to-co2-chart" class="liquid-action-pill" style="cursor:pointer; padding:0.5rem 1rem; font-weight:700; color:#a855f7; border-color:rgba(168,85,247,0.4);">
        📈 Ver Evolución Histórica de CO₂
      </button>
      <button type="button" id="btn-air-to-pm-chart" class="liquid-action-pill" style="cursor:pointer; padding:0.5rem 1rem; font-weight:700; color:#38bdf8; border-color:rgba(56,189,248,0.4);">
        📈 Ver Evolución de Partículas PM2.5
      </button>
    </div>
  `;

  // Attach controls
  body.querySelectorAll(".btn-modal-pur-power").forEach(btn => {
    btn.addEventListener("click", async () => {
      const id = btn.getAttribute("data-id");
      const turnOn = btn.getAttribute("data-on") !== "1";
      await sendXiaomiCommand(id, "power", turnOn);
      await fetchAirQualityData();
      renderAirQualityModalContent();
    });
  });

  body.querySelectorAll(".btn-modal-pur-mode").forEach(btn => {
    btn.addEventListener("click", async () => {
      const id = btn.getAttribute("data-id");
      const mode = btn.getAttribute("data-mode");
      await sendXiaomiCommand(id, "mode", mode);
      await fetchAirQualityData();
      renderAirQualityModalContent();
    });
  });

  document.getElementById("btn-air-to-co2-chart")?.addEventListener("click", () => {
    closeAirQualityModal();
    openClimateHistoryModal("co2");
  });

  document.getElementById("btn-air-to-pm-chart")?.addEventListener("click", () => {
    closeAirQualityModal();
    openClimateHistoryModal("pm25");
  });
}

// Event Listeners for Air Quality Modal
document.getElementById("btn-open-air-modal")?.addEventListener("click", openAirQualityModal);
document.getElementById("btn-air-modal-close")?.addEventListener("click", closeAirQualityModal);
document.getElementById("hud-air-pill")?.addEventListener("click", openAirQualityModal);
document.getElementById("air-quality-modal")?.addEventListener("click", (e) => {
  if (e.target.id === "air-quality-modal") closeAirQualityModal();
});

// Periodic fetch for Air Quality
setInterval(fetchAirQualityData, 30000);
setTimeout(fetchAirQualityData, 1000);


document.getElementById("hud-indoor-climate-card")?.addEventListener("click", () => openClimateHistoryModal());
document.getElementById("hud-air-quality-card")?.addEventListener("click", openAirQualityModal);


window.closeAirQualityModal = function() {
  const modal = document.getElementById("air-quality-modal");
  if (modal) {
    modal.classList.add("hidden");
    modal.style.display = "none";
  }
};

window.openAirQualityModal = openAirQualityModal;

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    closeAirQualityModal();
  }
});



// ========================================================
// SMART PLUG POWER CONSUMPTION CHART (DAILY / MONTHLY / YEARLY)
// ========================================================
let plugChartPeriod = "daily";
let plugChartHidden = new Set();
let plugChartDataCache = null;

function initPlugPowerChartControls() {
  document.querySelectorAll(".plug-period-btn").forEach(btn => {
    const per = btn.getAttribute("data-period");
    btn.classList.toggle("active", per === plugChartPeriod);
    btn.addEventListener("click", () => {
      plugChartPeriod = per;
      document.querySelectorAll(".plug-period-btn").forEach(b => {
        b.classList.toggle("active", b.getAttribute("data-period") === plugChartPeriod);
      });
      loadAndRenderPlugPowerChart(plugChartPeriod);
    });
  });
  loadAndRenderPlugPowerChart(plugChartPeriod);
}

async function loadAndRenderPlugPowerChart(period = "daily") {
  const wrap = document.getElementById("plug-chart-svg-wrap");
  if (!wrap) return;
  try {
    const res = await fetch(`/api/power/history?period=${encodeURIComponent(period)}`);
    if (!res.ok) return;
    plugChartDataCache = await res.json();
    renderPlugPowerChartSvg(plugChartDataCache);
  } catch (e) {
    console.error("Error loading power history:", e);
  }
}

function _buildSmoothPath(coords) {
  if (!coords.length) return "";
  if (coords.length === 1) return `M ${coords[0].x.toFixed(1)} ${coords[0].y.toFixed(1)}`;
  let d = `M ${coords[0].x.toFixed(1)} ${coords[0].y.toFixed(1)}`;
  for (let i = 0; i < coords.length - 1; i++) {
    const p0 = coords[i === 0 ? i : i - 1];
    const p1 = coords[i];
    const p2 = coords[i + 1];
    const p3 = coords[i + 2 < coords.length ? i + 2 : i + 1];
    const cp1x = p1.x + (p2.x - p0.x) / 6;
    const cp1y = p1.y + (p2.y - p0.y) / 6;
    const cp2x = p2.x - (p3.x - p1.x) / 6;
    const cp2y = p2.y - (p3.y - p1.y) / 6;
    d += ` C ${cp1x.toFixed(1)} ${cp1y.toFixed(1)}, ${cp2x.toFixed(1)} ${cp2y.toFixed(1)}, ${p2.x.toFixed(1)} ${p2.y.toFixed(1)}`;
  }
  return d;
}

function renderPlugPowerChartSvg(data) {
  const wrap = document.getElementById("plug-chart-svg-wrap");
  const legendEl = document.getElementById("plug-chart-legend");
  const titleEl = document.getElementById("plug-chart-title");
  const subEl = document.getElementById("plug-chart-subtitle");
  if (!wrap || !data) return;

  if (titleEl) titleEl.textContent = `📊 ${data.title || "Consumo por Enchufe (kWh)"}`;
  if (subEl) subEl.textContent = `Total periodo: ${data.grand_total_kwh ?? 0} kWh · Pulsa un dispositivo para ocultar/mostrar su curva`;

  const series = data.series || [];
  const points = data.points || [];

  // Interactive color-coded legend
  if (legendEl) {
    legendEl.innerHTML = series.map(s => {
      const hidden = plugChartHidden.has(s.key);
      return `
        <button type="button" class="plug-legend-chip ${hidden ? "is-hidden" : ""}" data-key="${s.key}" style="display:inline-flex; align-items:center; gap:0.35rem; padding:0.24rem 0.6rem; border-radius:999px; font-size:0.73rem; font-weight:700; cursor:pointer; border:1px solid ${hidden ? "rgba(148,163,184,0.3)" : s.color + "66"}; background:${hidden ? "transparent" : s.color + "1c"}; color:var(--modal-text); opacity:${hidden ? "0.45" : "1"}; transition:all 0.15s;">
          <span style="width:9px; height:9px; border-radius:50%; background:${s.color}; display:inline-block; flex-shrink:0;"></span>
          <span>${s.name}</span>
          <span style="color:${s.color}; font-weight:800;">${s.total_kwh} kWh</span>
        </button>
      `;
    }).join("");

    legendEl.querySelectorAll(".plug-legend-chip").forEach(chip => {
      chip.addEventListener("click", () => {
        const k = chip.getAttribute("data-key");
        if (plugChartHidden.has(k)) plugChartHidden.delete(k);
        else plugChartHidden.add(k);
        renderPlugPowerChartSvg(plugChartDataCache);
      });
    });
  }

  const activeSeries = series.filter(s => !plugChartHidden.has(s.key));
  const W = 740, H = 220;
  const padL = 48, padR = 16, padT = 16, padB = 30;
  const plotW = W - padL - padR;
  const plotH = H - padT - padB;

  let maxVal = 0.1;
  points.forEach(pt => {
    activeSeries.forEach(s => {
      const v = Number(pt.values?.[s.key] || 0);
      if (v > maxVal) maxVal = v;
    });
  });
  // Nice rounded ceiling
  const yMax = maxVal <= 0.5 ? Math.ceil(maxVal * 10) / 10 : (maxVal <= 5 ? Math.ceil(maxVal * 2) / 2 : Math.ceil(maxVal / 5) * 5);
  const n = Math.max(1, points.length);
  const xAt = (i) => padL + (n === 1 ? plotW / 2 : (i / (n - 1)) * plotW);
  const yAt = (v) => padT + plotH - (Math.max(0, v) / yMax) * plotH;

  // Gridlines + Y labels
  const gridSteps = 4;
  let gridHtml = "";
  for (let g = 0; g <= gridSteps; g++) {
    const val = (yMax / gridSteps) * g;
    const y = yAt(val);
    const lbl = yMax < 2 ? val.toFixed(2) : (yMax < 10 ? val.toFixed(1) : Math.round(val));
    gridHtml += `
      <line x1="${padL}" y1="${y.toFixed(1)}" x2="${W - padR}" y2="${y.toFixed(1)}" stroke="rgba(148,163,184,0.22)" stroke-dasharray="${g === 0 ? "" : "3,4"}" />
      <text x="${padL - 7}" y="${(y + 3.5).toFixed(1)}" text-anchor="end" font-size="10.5" fill="var(--modal-text-muted)">${lbl}</text>
    `;
  }

  // X labels
  const stepX = n > 16 ? 3 : (n > 10 ? 2 : 1);
  let xLabelsHtml = "";
  for (let i = 0; i < n; i++) {
    if (i % stepX === 0 || i === n - 1) {
      const lbl = points[i].short || points[i].label;
      xLabelsHtml += `<text x="${xAt(i).toFixed(1)}" y="${H - 8}" text-anchor="middle" font-size="10.5" fill="var(--modal-text-muted)">${lbl}</text>`;
    }
  }

  // Series defs + smooth curves + area gradients
  let defsHtml = "";
  let pathsHtml = "";
  activeSeries.forEach((s, idx) => {
    const gradId = `plugGrad_${s.key}_${idx}`;
    defsHtml += `
      <linearGradient id="${gradId}" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="${s.color}" stop-opacity="0.24" />
        <stop offset="100%" stop-color="${s.color}" stop-opacity="0.01" />
      </linearGradient>
    `;
    const coords = points.map((pt, i) => ({
      x: xAt(i),
      y: Math.min(padT + plotH, Math.max(padT, yAt(Number(pt.values?.[s.key] || 0))))
    }));
    const lineD = _buildSmoothPath(coords);
    const areaD = `${lineD} L ${coords[coords.length - 1].x.toFixed(1)} ${(padT + plotH).toFixed(1)} L ${coords[0].x.toFixed(1)} ${(padT + plotH).toFixed(1)} Z`;
    pathsHtml += `
      <path d="${areaD}" fill="url(#${gradId})" />
      <path d="${lineD}" fill="none" stroke="${s.color}" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" />
    `;
  });

  wrap.innerHTML = `
    <svg id="plug-power-svg" viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" style="width:100%; height:100%; display:block; overflow:visible;">
      <defs>${defsHtml}</defs>
      ${gridHtml}
      ${xLabelsHtml}
      ${pathsHtml}
      <line id="plug-hover-line" x1="0" y1="${padT}" x2="0" y2="${padT + plotH}" stroke="rgba(148,163,184,0.65)" stroke-width="1.2" stroke-dasharray="3,3" style="display:none;" />
      <g id="plug-hover-dots"></g>
      <rect id="plug-hover-zone" x="${padL}" y="${padT}" width="${plotW}" height="${plotH}" fill="transparent" style="cursor:crosshair;" />
    </svg>
    <div id="plug-hover-tooltip" style="display:none; position:absolute; top:8px; left:60px; pointer-events:none; background:rgba(15,23,42,0.92); color:#f8fafc; border:1px solid rgba(255,255,255,0.18); border-radius:12px; padding:0.5rem 0.7rem; font-size:0.74rem; box-shadow:0 10px 28px rgba(0,0,0,0.35); z-index:20; min-width:165px;"></div>
  `;

  const zone = document.getElementById("plug-hover-zone");
  const vLine = document.getElementById("plug-hover-line");
  const dotsG = document.getElementById("plug-hover-dots");
  const tip = document.getElementById("plug-hover-tooltip");

  const handleMove = (clientX) => {
    const svg = document.getElementById("plug-power-svg");
    if (!svg || !points.length) return;
    const rect = svg.getBoundingClientRect();
    const relX = ((clientX - rect.left) / rect.width) * W;
    const ratio = Math.max(0, Math.min(1, (relX - padL) / plotW));
    const idx = Math.round(ratio * (n - 1));
    const pt = points[idx];
    if (!pt) return;

    const cx = xAt(idx);
    vLine.setAttribute("x1", cx.toFixed(1));
    vLine.setAttribute("x2", cx.toFixed(1));
    vLine.style.display = "block";

    let dotsSvg = "";
    let rowsHtml = "";
    let tot = 0;
    activeSeries.forEach(s => {
      const v = Number(pt.values?.[s.key] || 0);
      tot += v;
      const cy = Math.min(padT + plotH, Math.max(padT, yAt(v)));
      dotsSvg += `<circle cx="${cx.toFixed(1)}" cy="${cy.toFixed(1)}" r="4.2" fill="${s.color}" stroke="#ffffff" stroke-width="1.5" />`;
      rowsHtml += `
        <div style="display:flex; justify-content:space-between; align-items:center; gap:0.75rem; margin-top:2px;">
          <span style="display:inline-flex; align-items:center; gap:0.3rem;"><span style="width:7px; height:7px; border-radius:50%; background:${s.color};"></span>${s.name}</span>
          <strong>${v.toFixed(v < 1 ? 3 : 2)} kWh</strong>
        </div>
      `;
    });
    dotsG.innerHTML = dotsSvg;

    tip.innerHTML = `
      <div style="font-weight:700; margin-bottom:4px; border-bottom:1px solid rgba(255,255,255,0.14); padding-bottom:3px; display:flex; justify-content:space-between;">
        <span>${pt.label}</span>
        <span style="color:#7dd3fc;">${tot.toFixed(2)} kWh</span>
      </div>
      ${rowsHtml}
    `;
    tip.style.display = "block";
    const pctLeft = (cx / W) * 100;
    if (pctLeft > 58) {
      tip.style.left = "auto";
      tip.style.right = `${Math.max(4, 100 - pctLeft + 3).toFixed(1)}%`;
    } else {
      tip.style.right = "auto";
      tip.style.left = `${Math.min(72, pctLeft + 3).toFixed(1)}%`;
    }
  };

  const hideTip = () => {
    if (vLine) vLine.style.display = "none";
    if (dotsG) dotsG.innerHTML = "";
    if (tip) tip.style.display = "none";
  };

  zone?.addEventListener("mousemove", (e) => handleMove(e.clientX));
  zone?.addEventListener("touchstart", (e) => { if (e.touches[0]) handleMove(e.touches[0].clientX); }, { passive: true });
  zone?.addEventListener("touchmove", (e) => { if (e.touches[0]) handleMove(e.touches[0].clientX); }, { passive: true });
  zone?.addEventListener("mouseleave", hideTip);
}



// ========================================================
// ALARM & SECURITY ACCESSORIES DETAIL MODAL
// ========================================================
async function openAlarmModal() {
  const modal = document.getElementById("security-alarm-modal");
  if (!modal) return;
  modal.classList.remove("hidden");
  modal.style.display = "flex";
  const body = document.getElementById("security-alarm-modal-body");
  if (body && !body.dataset.loaded) {
    body.innerHTML = `<p style="color:var(--modal-text-muted); margin:0;">Cargando estado de la centralita, sensores y log de eventos...</p>`;
  }
  try {
    const res = await fetch("/api/security/alarm/details");
    if (res.ok) {
      const data = await res.json();
      renderAlarmModalContent(data);
    }
  } catch (e) {
    console.error("Error loading alarm details:", e);
  }
}

function closeAlarmModal() {
  const modal = document.getElementById("security-alarm-modal");
  if (modal) {
    modal.classList.add("hidden");
    modal.style.display = "none";
  }
}
window.openAlarmModal = openAlarmModal;
window.closeAlarmModal = closeAlarmModal;

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") closeAlarmModal();
});

function renderAlarmModalContent(data) {
  const body = document.getElementById("security-alarm-modal-body");
  const badge = document.getElementById("security-alarm-modal-badge");
  if (!body || !data) return;
  body.dataset.loaded = "1";

  const al = data.alarm || {};
  const zones = data.zones || [];
  const accessories = data.accessories || [];
  const events = data.events || [];
  const mode = al.master_mode || "disarmed";

  if (badge) {
    badge.textContent = al.mode_label || "Desarmada";
    badge.style.color = al.mode_color || "#10b981";
    badge.style.borderColor = `${al.mode_color || "#10b981"}55`;
    badge.style.background = `${al.mode_color || "#10b981"}20`;
  }

  const batColor = (st) => st === "critical" ? "#ef4444" : (st === "warning" ? "#f59e0b" : "#10b981");

  // 1. Visual 2x2 Zone Distribution Map
  const zonesHtml = zones.map(z => {
    const borderCol = z.has_alert ? "rgba(239,68,68,0.45)" : "rgba(16,185,129,0.32)";
    const itemsHtml = (z.accessories || []).map(a => {
      const dotCol = a.alert ? "#ef4444" : (a.battery?.status === "critical" ? "#ef4444" : "#10b981");
      const bCol = batColor(a.battery?.status);
      return `
        <div style="display:flex; justify-content:space-between; align-items:center; gap:0.4rem; padding:0.38rem 0.55rem; border-radius:10px; background:rgba(148,163,184,0.1); border:1px solid rgba(148,163,184,0.2);">
          <div style="display:flex; align-items:center; gap:0.35rem; min-width:0;">
            <span style="width:8px; height:8px; border-radius:50%; background:${dotCol}; flex-shrink:0;"></span>
            <span style="font-size:0.78rem; font-weight:700; color:var(--modal-text); white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${a.icon} ${a.name}</span>
          </div>
          <div style="display:flex; align-items:center; gap:0.4rem; flex-shrink:0;">
            <span style="font-size:0.72rem; font-weight:700; color:${a.alert ? '#ef4444' : 'var(--modal-text-muted)'};">${a.state_label}</span>
            <span style="font-size:0.7rem; font-weight:800; color:${bCol};">🔋 ${a.battery?.label ?? '--'}</span>
          </div>
        </div>
      `;
    }).join("");
    return `
      <div class="domos-modal-subcard" style="padding:0.8rem 0.95rem; border-radius:16px; border:1px solid ${borderCol}; display:flex; flex-direction:column; gap:0.45rem;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <div style="font-size:0.84rem; font-weight:800; color:var(--modal-text);">${z.icon} ${z.title}</div>
          <span style="font-size:0.68rem; font-weight:700; color:${z.has_alert ? '#ef4444' : '#10b981'};">${z.has_alert ? '⚠️ Revisar' : '● OK'}</span>
        </div>
        <div style="font-size:0.7rem; color:var(--modal-text-muted); margin-top:-4px;">${z.desc}</div>
        <div style="display:flex; flex-direction:column; gap:0.35rem;">${itemsHtml}</div>
      </div>
    `;
  }).join("");

  // 2. Accessories Battery & Health Bars
  const accRowsHtml = accessories.map(a => {
    const pct = a.battery?.pct ?? 80;
    const bCol = batColor(a.battery?.status);
    return `
      <div style="display:flex; align-items:center; justify-content:space-between; gap:0.75rem; padding:0.45rem 0.65rem; border-radius:12px; background:rgba(148,163,184,0.08); border:1px solid rgba(148,163,184,0.18);">
        <div style="display:flex; align-items:center; gap:0.5rem; min-width:0; flex:1;">
          <span style="font-size:1.1rem;">${a.icon}</span>
          <div style="min-width:0;">
            <div style="font-size:0.82rem; font-weight:700; color:var(--modal-text);">${a.name} <span style="font-weight:500; font-size:0.72rem; color:var(--modal-text-muted);">· ${a.zone}</span></div>
            <div style="font-size:0.72rem; color:${a.alert ? '#ef4444' : 'var(--modal-text-muted)'}; font-weight:${a.alert ? '700' : '500'};">${a.state_label} · ${a.protocol}</div>
          </div>
        </div>
        <div style="display:flex; align-items:center; gap:0.5rem; width:130px; flex-shrink:0;">
          <div style="flex:1; height:7px; border-radius:999px; background:rgba(148,163,184,0.25); overflow:hidden;">
            <div style="width:${Math.max(6, Math.min(100, pct))}%; height:100%; background:${bCol}; border-radius:999px;"></div>
          </div>
          <span style="font-size:0.75rem; font-weight:800; color:${bCol}; min-width:36px; text-align:right;">${a.battery?.label ?? '--'}</span>
        </div>
      </div>
    `;
  }).join("");

  // 3. Chronological Event Log
  const eventsHtml = events.map(ev => {
    const evCol = ev.severity === "critical" ? "#ef4444" : (ev.severity === "warning" ? "#f59e0b" : "#38bdf8");
    return `
      <div style="display:flex; align-items:flex-start; justify-content:space-between; gap:0.75rem; padding:0.45rem 0.65rem; border-radius:10px; background:rgba(148,163,184,0.07); border-left:3px solid ${evCol};">
        <div style="display:flex; gap:0.45rem; align-items:flex-start;">
          <span>${ev.icon || '🛡️'}</span>
          <div>
            <div style="font-size:0.8rem; font-weight:700; color:var(--modal-text);">${ev.title} <span style="font-weight:500; font-size:0.72rem; color:var(--modal-text-muted);">(${ev.source})</span></div>
            <div style="font-size:0.72rem; color:var(--modal-text-muted);">${ev.detail || ''}</div>
          </div>
        </div>
        <span style="font-size:0.7rem; color:var(--modal-text-muted); white-space:nowrap;">${ev.ts || ''}</span>
      </div>
    `;
  }).join("") || `<p style="font-size:0.78rem; color:var(--modal-text-muted); margin:0;">Sin eventos registrados todavía.</p>`;

  body.innerHTML = `
    <!-- Panel Superior: Estado Centralita + Controles de Armado -->
    <div class="domos-modal-subcard" style="padding:0.95rem 1.2rem; border-radius:18px; display:flex; flex-wrap:wrap; align-items:center; justify-content:space-between; gap:0.85rem; border:1px solid ${al.mode_color || '#10b981'}44;">
      <div>
        <div style="font-size:0.72rem; font-weight:700; text-transform:uppercase; color:var(--modal-text-muted);">Estado Centralita (${al.ip || 'LAN'})</div>
        <div style="font-size:1.3rem; font-weight:800; color:${al.mode_color || '#10b981'}; margin-top:2px;">🛡️ ${al.mode_label || 'Desarmada'}</div>
        <div style="font-size:0.75rem; color:var(--modal-text-muted); margin-top:2px;">
          🔋 Batería respaldo: <b>${al.battery?.label ?? '100%'}</b> · Conexión: <b>LAN local</b>${al.alarm_msg_text ? ` · Último aviso: <b>${al.alarm_msg_text}</b>` : ''}
        </div>
      </div>
      <div style="display:flex; gap:0.45rem; flex-wrap:wrap;">
        <button type="button" class="liquid-action-pill btn-alarm-mode-cmd alarm-btn-disarm ${mode === 'disarmed' ? 'is-disarm-active' : ''}" data-mode="disarmed" style="cursor:pointer; padding:0.45rem 0.95rem; font-size:0.82rem; font-weight:700;">🔓 Desarmar</button>
        <button type="button" class="liquid-action-pill btn-alarm-mode-cmd alarm-btn-home ${mode === 'home' ? 'is-home-active' : ''}" data-mode="home" style="cursor:pointer; padding:0.45rem 0.95rem; font-size:0.82rem; font-weight:700;">🏠 En Casa</button>
        <button type="button" class="liquid-action-pill btn-alarm-mode-cmd alarm-btn-arm ${mode === 'arm' ? 'is-arm-active' : ''}" data-mode="arm" style="cursor:pointer; padding:0.45rem 0.95rem; font-size:0.82rem; font-weight:700;">🔒 Armar Total</button>
      </div>
    </div>

    <!-- Esquema de Distribución por Zonas -->
    <div>
      <div style="font-size:0.78rem; font-weight:700; text-transform:uppercase; letter-spacing:0.04em; color:var(--modal-text-muted); margin-bottom:0.5rem;">🗺️ Esquema de Distribución de Sensores por Zonas</div>
      <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(290px, 1fr)); gap:0.65rem;">
        ${zonesHtml}
      </div>
    </div>

    <!-- Estado de Carga de Pilas de Accesorios -->
    <div class="domos-modal-subcard" style="padding:0.9rem 1.1rem; border-radius:18px; display:flex; flex-direction:column; gap:0.5rem;">
      <div style="font-size:0.78rem; font-weight:700; text-transform:uppercase; letter-spacing:0.04em; color:var(--modal-text-muted);">🔋 Estado y Carga de Pilas de Accesorios (${accessories.length})</div>
      <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(300px, 1fr)); gap:0.45rem;">
        ${accRowsHtml}
      </div>
    </div>

    <!-- Log de Eventos -->
    <div class="domos-modal-subcard" style="padding:0.9rem 1.1rem; border-radius:18px; display:flex; flex-direction:column; gap:0.45rem;">
      <div style="font-size:0.78rem; font-weight:700; text-transform:uppercase; letter-spacing:0.04em; color:var(--modal-text-muted);">📋 Registro de Eventos de Seguridad</div>
      <div style="display:flex; flex-direction:column; gap:0.35rem; max-height:190px; overflow-y:auto;">
        ${eventsHtml}
      </div>
    </div>
  `;

  body.querySelectorAll(".btn-alarm-mode-cmd").forEach(btn => {
    btn.addEventListener("click", async () => {
      const m = btn.getAttribute("data-mode");
      await sendDeviceCommand(al.id || "64326051e8db8480acc0", "master_mode", m);
      setTimeout(openAlarmModal, 600);
    });
  });
}


// ========================================================
// ENERGY SAVINGS / SMART AUTOCONSUMO MODAL & API
// ========================================================
window.energySavingsData = null;

async function fetchEnergySavings(renderModal = false) {
  try {
    const res = await fetch("/api/energy/savings");
    if (res.ok) {
      window.energySavingsData = await res.json();
      if (typeof renderEnergyGrid === "function") renderEnergyGrid();
      if (renderModal) renderEnergySavingsModalBody();
    }
  } catch (e) {}
}

window.openEnergySavingsModal = async function() {
  const modal = document.getElementById("energy-savings-modal");
  if (!modal) return;
  modal.classList.remove("hidden");
  modal.style.display = "flex";
  await fetchEnergySavings(true);
};

window.closeEnergySavingsModal = function() {
  const modal = document.getElementById("energy-savings-modal");
  if (!modal) return;
  modal.classList.add("hidden");
  modal.style.display = "none";
};

window.setEnergySavingsMode = async function(mode) {
  try {
    const res = await fetch("/api/energy/savings/mode", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mode })
    });
    if (res.ok) {
      window.energySavingsData = await res.json();
      if (typeof renderEnergyGrid === "function") renderEnergyGrid();
      renderEnergySavingsModalBody();
    }
  } catch (e) {}
};

function renderEnergySavingsModalBody() {
  const body = document.getElementById("energy-savings-modal-body");
  const badge = document.getElementById("esav-modal-badge");
  const d = window.energySavingsData;
  if (!body || !d) return;

  const cfg = d.config || { mode: "auto", source: "auto", rules: [] };
  const tel = d.telemetry || {};
  const statuses = Object.fromEntries((d.rules_status || []).map(x => [x.id, x]));
  const sum = d.summary || {};

  if (badge) {
    const map = {
      auto: ["Autoconsumo Activo", "rgba(16,185,129,0.16)", "#10b981"],
      paused: ["Pausado (Manual)", "rgba(245,158,11,0.18)", "#f59e0b"],
      vacation: ["Modo Vacaciones", "rgba(59,130,246,0.18)", "#3b82f6"]
    };
    const [txt, bg, col] = map[cfg.mode] || map.auto;
    badge.textContent = txt;
    badge.style.background = bg;
    badge.style.color = col;
    badge.style.borderColor = col;
  }

  const meterChip = tel.meter_online
    ? `<span style="color:#10b981; font-weight:700;">● Doble pinza online (${tel.net_surplus_w ?? 0} W excedente)</span>`
    : `<span style="color:#f59e0b; font-weight:600;">○ Doble pinza en espera · Usando generación Hoymiles</span>`;

  const rulesHtml = (cfg.rules || []).map((r, idx) => {
    const st = statuses[r.id] || {};
    return `
      <div class="esav-rule-card" data-rule-idx="${idx}" data-rule-id="${r.id}">
        <div style="display:flex; flex-wrap:wrap; align-items:center; justify-content:space-between; gap:0.5rem;">
          <div style="display:flex; align-items:center; gap:0.5rem;">
            <span style="font-size:1.2rem;">${r.icon || "⚡"}</span>
            <strong style="font-size:0.95rem; color:var(--modal-text);">${r.name}</strong>
            <span class="sub-metric-pill" style="font-size:0.72rem;">Prioridad ${r.priority}</span>
            <span class="sub-metric-pill" style="font-size:0.72rem; background:${st.is_on ? 'rgba(16,185,129,0.18)' : 'rgba(148,163,184,0.18)'}; color:${st.is_on ? '#10b981' : 'var(--modal-text-muted)'};">${st.status_label || "En espera"}</span>
          </div>
          <label style="display:flex; align-items:center; gap:0.4rem; cursor:pointer; font-size:0.84rem; font-weight:700; color:var(--modal-text);">
            <input type="checkbox" class="esav-enabled" ${r.enabled ? "checked" : ""} style="width:18px; height:18px; accent-color:#10b981;">
            Regla activa
          </label>
        </div>

        <div class="esav-fields-grid">
          <div class="esav-field">
            <label>Encender ≥ (W)</label>
            <input type="number" class="esav-on-w" min="50" max="5000" step="50" value="${r.on_threshold_w}">
          </div>
          <div class="esav-field">
            <label>Apagar &lt; (W) (Histéresis)</label>
            <input type="number" class="esav-off-w" min="0" max="4900" step="50" value="${r.off_threshold_w}">
          </div>
          <div class="esav-field">
            <label>Espera encendido (min)</label>
            <input type="number" class="esav-sustain-on" min="0" max="60" value="${r.sustain_on_min}">
          </div>
          <div class="esav-field">
            <label>Anti-nubes apagado (min)</label>
            <input type="number" class="esav-sustain-off" min="0" max="60" value="${r.sustain_off_min}">
          </div>
          <div class="esav-field">
            <label>Mínimo encendido (min)</label>
            <input type="number" class="esav-min-on" min="0" max="120" value="${r.min_on_min}">
          </div>
          <div class="esav-field">
            <label>Máximo diario (min)</label>
            <input type="number" class="esav-max-daily" min="10" max="720" value="${r.max_daily_min}">
          </div>
          <div class="esav-field">
            <label>Horario inicio</label>
            <input type="time" class="esav-time-start" value="${r.time_start || "10:00"}">
          </div>
          <div class="esav-field">
            <label>Horario fin</label>
            <input type="time" class="esav-time-end" value="${r.time_end || "18:30"}">
          </div>
          <div class="esav-field">
            <label>Presencia / Casa</label>
            <select class="esav-presence">
              <option value="any" ${r.presence_condition === "any" ? "selected" : ""}>Siempre (cualquier estado)</option>
              <option value="away_only" ${r.presence_condition === "away_only" ? "selected" : ""}>Solo ausente (Alarma armada)</option>
              <option value="home_only" ${r.presence_condition === "home_only" ? "selected" : ""}>Solo en casa (Desarmada)</option>
            </select>
          </div>
          <div class="esav-field">
            <label>Prioridad cascada</label>
            <input type="number" class="esav-priority" min="1" max="10" value="${r.priority}">
          </div>
        </div>

        <label style="display:flex; align-items:center; gap:0.45rem; font-size:0.8rem; color:var(--modal-text-muted); cursor:pointer;">
          <input type="checkbox" class="esav-auto-cutoff" ${r.auto_cutoff_idle ? "checked" : ""} style="width:16px; height:16px; accent-color:#0ea5e9;">
          Auto-apagar y ceder excedente al terminar de calentar (&lt; ${r.idle_watts || 35} W durante ${r.idle_cutoff_min || 10} min)
        </label>
      </div>
    `;
  }).join("");

  const histHtml = (d.history || []).length
    ? (d.history || []).slice(0, 8).map(h => `
        <div style="display:flex; justify-content:space-between; gap:0.75rem; font-size:0.78rem; padding:0.32rem 0; border-bottom:1px solid var(--modal-subcard-border);">
          <span>${h.icon || "🌱"} <b>${h.device}</b> · ${h.action} — <span style="color:var(--modal-text-muted);">${h.detail}</span></span>
          <span style="color:var(--modal-text-muted); white-space:nowrap;">${h.ts}</span>
        </div>
      `).join("")
    : `<div style="font-size:0.8rem; color:var(--modal-text-muted);">Sin actuaciones automáticas todavía hoy.</div>`;

  body.innerHTML = `
    <!-- Barra de modo rápido y origen de medida -->
    <div class="domos-modal-subcard" style="padding:0.85rem 1rem; border-radius:16px; display:flex; flex-direction:column; gap:0.7rem;">
      <div style="display:flex; flex-wrap:wrap; align-items:center; justify-content:space-between; gap:0.6rem;">
        <div style="display:flex; flex-wrap:wrap; gap:0.45rem;">
          <button type="button" class="esav-mode-btn ${cfg.mode === "auto" ? "active-auto" : ""}" onclick="setEnergySavingsMode('auto')">☀️ Autoconsumo</button>
          <button type="button" class="esav-mode-btn ${cfg.mode === "paused" ? "active-paused" : ""}" onclick="setEnergySavingsMode('paused')">⏸️ Pausa / Manual</button>
          <button type="button" class="esav-mode-btn ${cfg.mode === "vacation" ? "active-vacation" : ""}" onclick="setEnergySavingsMode('vacation')">✈️ Vacaciones</button>
        </div>
        <div style="display:flex; align-items:center; gap:0.5rem;">
          <span style="font-size:0.78rem; color:var(--modal-text-muted);">Origen:</span>
          <select id="esav-source-select" class="domos-modal-input" style="padding:0.35rem 0.65rem; border-radius:10px; font-size:0.8rem; font-weight:600;">
            <option value="auto" ${cfg.source === "auto" ? "selected" : ""}>🔄 Automático (Doble Pinza / Hoymiles)</option>
            <option value="solar_gen" ${cfg.source === "solar_gen" ? "selected" : ""}>☀️ Generación Solar (Hoymiles)</option>
            <option value="net_surplus" ${cfg.source === "net_surplus" ? "selected" : ""}>⚡ Excedente Neto (Doble Pinza)</option>
          </select>
        </div>
      </div>
      <div style="display:flex; flex-wrap:wrap; align-items:center; justify-content:space-between; gap:0.5rem; font-size:0.79rem; padding-top:0.45rem; border-top:1px solid var(--modal-subcard-border);">
        <div>${meterChip}</div>
        <div style="display:flex; flex-wrap:wrap; gap:0.75rem;">
          <span>🏠 Casa: <b>${tel.is_away ? "Ausente (Armada)" : "En casa"}</b></span>
          <span>🌱 Ahorro hoy: <b>${sum.total_saved_kwh_today ?? 0} kWh</b></span>
        </div>
      </div>
      <div style="display:grid; grid-template-columns:repeat(4, minmax(0, 1fr)); gap:0.45rem;">
        <div style="padding:0.42rem 0.55rem; border-radius:12px; background:rgba(245,158,11,0.10); border:1px solid rgba(245,158,11,0.25); text-align:center;">
          <div style="font-size:0.68rem; color:var(--modal-text-muted);">☀️ Generación Solar</div>
          <div style="font-size:0.96rem; font-weight:800; color:#d97706;">${tel.solar_w ?? 0} W</div>
        </div>
        <div style="padding:0.42rem 0.55rem; border-radius:12px; background:rgba(99,102,241,0.10); border:1px solid rgba(99,102,241,0.25); text-align:center;">
          <div style="font-size:0.68rem; color:var(--modal-text-muted);">🏠 Consumo Hogar</div>
          <div style="font-size:0.96rem; font-weight:800; color:#6366f1;">${tel.meter_online ? `${tel.home_load_w ?? 0} W` : "— W"}</div>
        </div>
        <div style="padding:0.42rem 0.55rem; border-radius:12px; background:rgba(14,165,233,0.10); border:1px solid rgba(14,165,233,0.25); text-align:center;">
          <div style="font-size:0.68rem; color:var(--modal-text-muted);">🔌 Flujo Red</div>
          <div style="font-size:0.96rem; font-weight:800; color:${(tel.grid_w ?? 0) < 0 ? '#10b981' : '#0284c7'};">${tel.meter_online ? `${(tel.grid_w ?? 0) < 0 ? 'Export ' + Math.abs(tel.grid_w) : 'Import ' + (tel.grid_w ?? 0)} W` : "Esperando pinza"}</div>
        </div>
        <div style="padding:0.42rem 0.55rem; border-radius:12px; background:rgba(16,185,129,0.12); border:1px solid rgba(16,185,129,0.30); text-align:center;">
          <div style="font-size:0.68rem; color:var(--modal-text-muted);">⚡ Excedente Útil</div>
          <div style="font-size:0.96rem; font-weight:800; color:#10b981;">${tel.base_avail_w ?? 0} W</div>
        </div>
      </div>
    </div>

    <!-- Asesor Agua Caliente / Termosifón (preparado para válvulas Tuya) -->
    ${d.hot_water ? `
      <div class="domos-modal-subcard" style="padding:0.75rem 1rem; border-radius:16px; border-left:4px solid ${d.hot_water.badge_color || '#f59e0b'}; display:flex; flex-wrap:wrap; align-items:center; justify-content:space-between; gap:0.5rem;">
        <div>
          <div style="font-size:0.84rem; font-weight:700; color:var(--modal-text);">🚿 Agua Caliente (Termosifón): ${d.hot_water.recommended_label}</div>
          <div style="font-size:0.75rem; color:var(--modal-text-muted); margin-top:2px;">${d.hot_water.reason}</div>
        </div>
        <span class="sub-metric-pill" style="font-size:0.72rem;">${d.hot_water.valves_configured ? "✅ 2 Válvulas Tuya vinculadas" : "🔧 Listo para 2 válvulas Tuya"}</span>
      </div>
    ` : ""}

    <!-- Reglas configurables por dispositivo -->
    ${rulesHtml}

    <!-- Registro de decisiones -->
    <div class="domos-modal-subcard" style="padding:0.8rem 1rem; border-radius:16px;">
      <div style="font-size:0.82rem; font-weight:700; margin-bottom:0.45rem; color:var(--modal-text);">📋 Registro de actuaciones de ahorro</div>
      ${histHtml}
    </div>
  `;
}

window.saveEnergySavingsRules = async function() {
  const d = window.energySavingsData;
  if (!d) return;
  const btn = document.getElementById("btn-esav-save");
  const srcEl = document.getElementById("esav-source-select");
  const cards = document.querySelectorAll("#energy-savings-modal-body .esav-rule-card");
  const updatedRules = (d.config?.rules || []).map((orig, idx) => {
    const card = cards[idx];
    if (!card) return orig;
    return {
      ...orig,
      enabled: !!card.querySelector(".esav-enabled")?.checked,
      priority: parseInt(card.querySelector(".esav-priority")?.value, 10) || orig.priority,
      on_threshold_w: parseInt(card.querySelector(".esav-on-w")?.value, 10) || orig.on_threshold_w,
      off_threshold_w: parseInt(card.querySelector(".esav-off-w")?.value, 10) || orig.off_threshold_w,
      sustain_on_min: parseInt(card.querySelector(".esav-sustain-on")?.value, 10) || 0,
      sustain_off_min: parseInt(card.querySelector(".esav-sustain-off")?.value, 10) || 0,
      min_on_min: parseInt(card.querySelector(".esav-min-on")?.value, 10) || 0,
      max_daily_min: parseInt(card.querySelector(".esav-max-daily")?.value, 10) || 180,
      time_start: card.querySelector(".esav-time-start")?.value || "10:00",
      time_end: card.querySelector(".esav-time-end")?.value || "18:30",
      presence_condition: card.querySelector(".esav-presence")?.value || "any",
      auto_cutoff_idle: !!card.querySelector(".esav-auto-cutoff")?.checked
    };
  });

  if (btn) btn.textContent = "⏳ Guardando...";
  try {
    const res = await fetch("/api/energy/savings/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        mode: d.config?.mode || "auto",
        source: srcEl ? srcEl.value : (d.config?.source || "auto"),
        rules: updatedRules
      })
    });
    if (res.ok) {
      window.energySavingsData = await res.json();
      if (typeof renderEnergyGrid === "function") renderEnergyGrid();
      renderEnergySavingsModalBody();
      if (btn) btn.textContent = "✅ Guardado";
      setTimeout(() => { if (btn) btn.textContent = "💾 Guardar Reglas"; }, 2200);
    }
  } catch (e) {
    if (btn) btn.textContent = "💾 Guardar Reglas";
  }
};

fetchEnergySavings(false);
setInterval(() => fetchEnergySavings(false), 30000);


// ========================================================
// AUTOMATIC & MANUAL BACKUPS MODAL
// ========================================================
window.openBackupsModal = async function() {
  const modal = document.getElementById("backups-modal");
  if (!modal) return;
  modal.classList.remove("hidden");
  modal.style.display = "flex";
  await loadBackupsList();
};

window.closeBackupsModal = function() {
  const modal = document.getElementById("backups-modal");
  if (!modal) return;
  modal.classList.add("hidden");
  modal.style.display = "none";
};

async function loadBackupsList() {
  const body = document.getElementById("backups-modal-body");
  if (!body) return;
  try {
    const res = await fetch("/api/system/backups");
    const d = await res.json();
    const sdBadge = d.sd_mounted
      ? `<span style="color:#10b981; font-weight:700;">● Espejo SD activo (${d.sd_dir})</span>`
      : `<span style="color:#f59e0b; font-weight:600;">○ Solo almacenamiento interno</span>`;
    const rows = (d.backups || []).length
      ? d.backups.map(b => `
          <div style="display:flex; align-items:center; justify-content:space-between; gap:0.65rem; padding:0.55rem 0.75rem; border-radius:12px; background:var(--modal-subcard-bg); border:1px solid var(--modal-subcard-border);">
            <div style="min-width:0;">
              <div style="font-size:0.82rem; font-weight:700; color:var(--modal-text); white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${b.filename}</div>
              <div style="font-size:0.74rem; color:var(--modal-text-muted);">${b.date} · ${b.size_kb} KB ${b.sd_mirrored ? "· ✅ Copiado en SD" : ""}</div>
            </div>
            <a href="/api/system/backup/download/${encodeURIComponent(b.filename)}" class="liquid-action-pill" style="text-decoration:none; font-size:0.76rem; padding:0.28rem 0.65rem; white-space:nowrap;">⬇️ Descargar</a>
          </div>
        `).join("")
      : `<div style="font-size:0.82rem; color:var(--modal-text-muted); text-align:center;">Aún no hay copias guardadas. Pulsa "Crear Copia Ahora".</div>`;

    body.innerHTML = `
      <div class="domos-modal-subcard" style="padding:0.75rem 0.95rem; border-radius:14px; font-size:0.8rem; display:flex; flex-direction:column; gap:0.35rem;">
        <div>🕒 <b>Programación:</b> ${d.schedule || "Diario 04:00"}</div>
        <div>💾 ${sdBadge}</div>
        <div style="color:var(--modal-text-muted); font-size:0.74rem;">Incluye toda la configuración (*.json), credenciales Tuya/Hoymiles, historiales, scripts y servicios systemd.</div>
      </div>
      <div style="display:flex; flex-direction:column; gap:0.45rem;">${rows}</div>
    `;
  } catch (e) {
    body.innerHTML = `<p style="color:#ef4444;">Error al consultar las copias de seguridad.</p>`;
  }
}

window.triggerManualBackup = async function() {
  const btn = document.getElementById("btn-run-backup-now");
  if (btn) { btn.disabled = true; btn.textContent = "⏳ Creando..."; }
  try {
    const res = await fetch("/api/system/backup", { method: "POST" });
    if (res.ok) {
      await loadBackupsList();
      if (btn) btn.textContent = "✅ Copia creada";
      setTimeout(() => { if (btn) { btn.disabled = false; btn.textContent = "💾 Crear Copia Ahora"; } }, 2200);
      return;
    }
  } catch (e) {}
  if (btn) { btn.disabled = false; btn.textContent = "💾 Crear Copia Ahora"; }
};


window.toggleAirPurifierAuto = async function() {
  const curEnabled = latestAirQualityData?.air_auto?.config?.enabled !== false;
  try {
    const res = await fetch("/api/air/auto", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ enabled: !curEnabled })
    });
    if (res.ok) {
      const updated = await res.json();
      if (latestAirQualityData) latestAirQualityData.air_auto = updated;
      renderAirQualityModalContent();
    }
  } catch (e) {}
};


// ========================================================
// GOOGLE CAST SPEAKERS & MULTI-ROOM INTERCOM MODAL
// ========================================================
let castSelectedTarget = "all";

window.openCastModal = async function() {
  const modal = document.getElementById("cast-modal");
  if (!modal) return;
  modal.classList.remove("hidden");
  modal.style.display = "flex";
  await loadCastModalBody();
};

window.closeCastModal = function() {
  const modal = document.getElementById("cast-modal");
  if (!modal) return;
  modal.classList.add("hidden");
  modal.style.display = "none";
};

window.selectCastIntercomTarget = function(target) {
  castSelectedTarget = target;
  document.querySelectorAll(".cast-target-pill").forEach(b => {
    const act = b.getAttribute("data-ct") === target;
    b.style.background = act ? "rgba(14,165,233,0.25)" : "";
    b.style.borderColor = act ? "#38bdf8" : "";
    b.style.fontWeight = act ? "700" : "";
  });
};

window.sendCastAnnouncement = async function(customText) {
  const input = document.getElementById("cast-announce-input");
  const statusEl = document.getElementById("cast-announce-status");
  const text = (customText || input?.value || "").trim();
  if (!text) return;
  if (statusEl) statusEl.textContent = "⏳ Enviando aviso de voz...";
  try {
    const res = await fetch("/api/cast/announce", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ targets: castSelectedTarget, text })
    });
    const d = await res.json();
    if (statusEl) statusEl.textContent = d.success ? `✅ Anunciado en ${castSelectedTarget === "all" ? "todos los altavoces" : castSelectedTarget}` : `⚠️ ${d.error || "No se pudo reproducir"}`;
    if (!customText && input) input.value = "";
  } catch (e) {
    if (statusEl) statusEl.textContent = "⚠️ Error de red";
  }
};

window.toggleCastDoorbellSetting = async function(key, val, speakerId = null) {
  const payload = speakerId ? { speaker_doorbell: { [speakerId]: !!val } } : { [key]: !!val };
  try {
    await fetch("/api/cast/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    await loadCastModalBody();
  } catch (e) {}
};

async function loadCastModalBody() {
  const body = document.getElementById("cast-modal-body");
  if (!body) return;
  try {
    const res = await fetch("/api/cast/speakers");
    const d = await res.json();
    const sps = d.speakers || [];
    const targetPills = [
      { id: "all", label: "🏠 Todos (3)" },
      ...sps.map(s => ({ id: s.id, label: `${s.icon || "🔊"} ${s.name}` }))
    ].map(t => `
      <button type="button" class="liquid-action-pill cast-target-pill" data-ct="${t.id}" onclick="selectCastIntercomTarget('${t.id}')" style="cursor:pointer; font-size:0.78rem; padding:0.28rem 0.65rem; ${castSelectedTarget === t.id ? 'background:rgba(14,165,233,0.25); border-color:#38bdf8; font-weight:700;' : ''}">${t.label}</button>
    `).join("");

    const spRows = sps.map(s => `
      <div style="display:flex; align-items:center; justify-content:space-between; padding:0.55rem 0.75rem; border-radius:12px; background:var(--modal-subcard-bg); border:1px solid var(--modal-subcard-border);">
        <div>
          <div style="font-size:0.86rem; font-weight:700; color:var(--modal-text);">${s.icon || "🔊"} ${s.name} <span style="font-size:0.74rem; font-weight:500; color:var(--modal-text-muted);">(${s.model})</span></div>
          <div style="font-size:0.72rem; color:var(--modal-text-muted);">LAN ${s.host}:${s.port}</div>
        </div>
        <label style="display:flex; align-items:center; gap:0.35rem; font-size:0.78rem; cursor:pointer; color:var(--modal-text);">
          <input type="checkbox" ${s.doorbell_enabled ? "checked" : ""} onchange="toggleCastDoorbellSetting(null, this.checked, '${s.id}')" style="width:16px; height:16px; accent-color:#10b981;">
          🔔 Timbre
        </label>
      </div>
    `).join("");

    body.innerHTML = `
      <!-- Intercomunicador -->
      <div class="domos-modal-subcard" style="padding:0.85rem 1rem; border-radius:16px; display:flex; flex-direction:column; gap:0.6rem;">
        <div style="font-size:0.86rem; font-weight:700; color:var(--modal-text);">📢 Intercomunicador Familiar (Voz Piper)</div>
        <div style="display:flex; flex-wrap:wrap; gap:0.35rem;">${targetPills}</div>
        <div style="display:flex; gap:0.45rem;">
          <input id="cast-announce-input" type="text" class="domos-modal-input" placeholder="Escribe un aviso para anunciar por voz..." style="flex:1; padding:0.48rem 0.75rem; border-radius:12px; font-size:0.84rem;" onkeydown="if(event.key==='Enter') sendCastAnnouncement()">
          <button type="button" class="liquid-action-pill" onclick="sendCastAnnouncement()" style="cursor:pointer; background:rgba(14,165,233,0.25); border-color:#38bdf8; font-weight:700;">📣 Anunciar</button>
        </div>
        <div style="display:flex; flex-wrap:wrap; gap:0.35rem;">
          <button type="button" class="liquid-action-pill" onclick="sendCastAnnouncement('¡La comida está lista en la mesa!')" style="cursor:pointer; font-size:0.75rem; padding:0.25rem 0.6rem;">🍽️ ¡A comer!</button>
          <button type="button" class="liquid-action-pill" onclick="sendCastAnnouncement('¡La cena está lista!')" style="cursor:pointer; font-size:0.75rem; padding:0.25rem 0.6rem;">🌙 ¡A cenar!</button>
          <button type="button" class="liquid-action-pill" onclick="sendCastAnnouncement('¿Podéis venir un momento al salón?')" style="cursor:pointer; font-size:0.75rem; padding:0.25rem 0.6rem;">👋 Venid al salón</button>
          <button type="button" class="liquid-action-pill" onclick="sendCastAnnouncement('Atención, alguien está llamando al videoportero.')" style="cursor:pointer; font-size:0.75rem; padding:0.25rem 0.6rem;">🔔 Probar timbre</button>
        </div>
        <div id="cast-announce-status" style="font-size:0.76rem; color:var(--modal-text-muted); min-height:1rem;"></div>
      </div>

      <!-- Configuración de Timbre Multi-habitación -->
      <div class="domos-modal-subcard" style="padding:0.85rem 1rem; border-radius:16px; display:flex; flex-direction:column; gap:0.55rem;">
        <div style="display:flex; flex-wrap:wrap; align-items:center; justify-content:space-between; gap:0.5rem;">
          <div style="font-size:0.86rem; font-weight:700; color:var(--modal-text);">🔔 Timbre Videoportero en Altavoces Google</div>
          <label style="display:flex; align-items:center; gap:0.35rem; font-size:0.8rem; font-weight:700; cursor:pointer;">
            <input type="checkbox" ${d.doorbell_cast_enabled ? "checked" : ""} onchange="toggleCastDoorbellSetting('doorbell_cast_enabled', this.checked)" style="width:17px; height:17px; accent-color:#10b981;">
            Activado
          </label>
        </div>
        <label style="display:flex; align-items:center; gap:0.4rem; font-size:0.76rem; color:var(--modal-text-muted); cursor:pointer;">
          <input type="checkbox" ${d.quiet_night_dormitorio ? "checked" : ""} onchange="toggleCastDoorbellSetting('quiet_night_dormitorio', this.checked)" style="width:15px; height:15px; accent-color:#0ea5e9;">
          🌙 Silenciar Dormitorio 1 por la noche (23:00–08:00)
        </label>
        <div style="display:flex; flex-direction:column; gap:0.4rem;">${spRows}</div>
      </div>
    `;
  } catch (e) {
    body.innerHTML = `<p style="color:#ef4444;">Error cargando altavoces Google.</p>`;
  }
}


// ========================================================
// DOCTOR DOMOS MODAL (Nightly Hybrid Auditor + Gemini AI + Auto-Heal)
// ========================================================
window.openDoctorModal = async function() {
  const modal = document.getElementById("doctor-modal");
  if (!modal) return;
  modal.classList.remove("hidden");
  modal.style.display = "flex";
  await loadDoctorReport();
};

let doctorIsSpeaking = false;

window.toggleDoctorSpeak = async function() {
  const btn = document.getElementById("btn-doctor-speak");
  if (doctorIsSpeaking) {
    doctorIsSpeaking = false;
    if (btn) btn.textContent = "🔊 Leer Informe";
    try { await fetch("/api/doctor/speak/stop", { method: "POST" }); } catch (e) {}
    return;
  }
  if (btn) { btn.disabled = true; btn.textContent = "⏳ Generando voz..."; }
  try {
    const res = await fetch("/api/doctor/speak", { method: "POST" });
    const d = await res.json();
    if (d.success) {
      doctorIsSpeaking = true;
      if (btn) { btn.disabled = false; btn.textContent = "⏹ Parar Lectura"; }
      setTimeout(() => {
        if (doctorIsSpeaking) {
          doctorIsSpeaking = false;
          if (btn) btn.textContent = "🔊 Leer Informe";
        }
      }, 45000);
      return;
    }
  } catch (e) {}
  if (btn) { btn.disabled = false; btn.textContent = "🔊 Leer Informe"; }
};

window.closeDoctorModal = function() {
  if (doctorIsSpeaking) {
    doctorIsSpeaking = false;
    const btn = document.getElementById("btn-doctor-speak");
    if (btn) btn.textContent = "🔊 Leer Informe";
    fetch("/api/doctor/speak/stop", { method: "POST" }).catch(() => {});
  }
  const modal = document.getElementById("doctor-modal");
  if (!modal) return;
  modal.classList.add("hidden");
  modal.style.display = "none";
};

async function loadDoctorReport() {
  const body = document.getElementById("doctor-modal-body");
  if (!body) return;
  try {
    const res = await fetch("/api/doctor/report");
    const d = await res.json();
    renderDoctorModalBody(d);
  } catch (e) {
    body.innerHTML = `<p style="color:#ef4444;">Error al cargar el informe de Doctor DOMOS.</p>`;
  }
}

window.runDoctorNow = async function() {
  const btn = document.getElementById("btn-run-doctor-now");
  if (btn) { btn.disabled = true; btn.textContent = "⏳ Analizando..."; }
  try {
    const res = await fetch("/api/doctor/run", { method: "POST" });
    if (res.ok) {
      const d = await res.json();
      renderDoctorModalBody(d);
    }
  } catch (e) {}
  if (btn) { btn.disabled = false; btn.textContent = "🩺 Diagnosticar Ahora"; }
};

window.saveDoctorSettings = async function() {
  const autoHeal = !!document.getElementById("doctor-auto-heal-chk")?.checked;
  const statusEl = document.getElementById("doctor-cfg-status");
  try {
    const res = await fetch("/api/doctor/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ auto_heal_enabled: autoHeal })
    });
    if (res.ok && statusEl) {
      statusEl.textContent = "✅ Guardado";
      setTimeout(() => { statusEl.textContent = ""; }, 2000);
    }
  } catch (e) {}
};

function renderDoctorModalBody(data) {
  const body = document.getElementById("doctor-modal-body");
  const badge = document.getElementById("doctor-score-badge");
  if (!body || !data) return;
  const rep = data.report || {};
  const cfg = data.config || {};
  const score = rep.health_score ?? 100;
  const scCol = score >= 85 ? "#10b981" : (score >= 65 ? "#f59e0b" : "#ef4444");

  if (badge) {
    badge.textContent = `${score} / 100 · ${score >= 85 ? "Óptimo" : (score >= 65 ? "Atención" : "Crítico")}`;
    badge.style.color = scCol;
    badge.style.borderColor = scCol;
    badge.style.background = `${scCol}22`;
  }

  const ai = rep.ai || {};
  const checksHtml = (rep.checks || []).map(c => {
    const col = c.status === "ok" ? "#10b981" : (c.status === "warning" ? "#f59e0b" : "#ef4444");
    const lbl = c.status === "ok" ? "OK" : (c.status === "warning" ? "Aviso" : "Crítico");
    return `
      <div style="padding:0.65rem 0.8rem; border-radius:14px; background:var(--modal-subcard-bg); border:1px solid var(--modal-subcard-border); border-left:4px solid ${col};">
        <div style="display:flex; justify-content:space-between; align-items:center; gap:0.4rem;">
          <span style="font-size:0.84rem; font-weight:700; color:var(--modal-text);">${c.icon || "🔹"} ${c.name}</span>
          <span style="font-size:0.7rem; font-weight:700; color:${col};">${lbl}</span>
        </div>
        <div style="font-size:0.75rem; color:var(--modal-text-muted); margin-top:3px;">${c.summary}</div>
      </div>
    `;
  }).join("");

  const actionsHtml = (rep.actions_taken || []).length
    ? rep.actions_taken.map(a => `<div style="font-size:0.79rem; padding:0.25rem 0;">${a}</div>`).join("")
    : `<div style="font-size:0.78rem; color:var(--modal-text-muted);">No fue necesaria ninguna auto-reparación en el último chequeo.</div>`;

  const recsHtml = (rep.recommendations || []).map(r => `<li style="margin:0.2rem 0; font-size:0.8rem; color:var(--modal-text);">${r}</li>`).join("");

  body.innerHTML = `
    <!-- Análisis IA / Resumen Ejecutivo -->
    <div class="domos-modal-subcard" style="padding:0.9rem 1.05rem; border-radius:16px; background:linear-gradient(135deg, rgba(139,92,246,0.12), rgba(14,165,233,0.08)); border:1px solid rgba(139,92,246,0.32);">
      <div style="display:flex; justify-content:space-between; align-items:center; gap:0.5rem; margin-bottom:0.4rem;">
        <span style="font-size:0.88rem; font-weight:700; color:var(--modal-text);">🧠 ${ai.used ? `Análisis Gemini (${ai.model})` : "Resumen Doctor DOMOS (Local)"}</span>
        <span style="font-size:0.73rem; color:var(--modal-text-muted);">Último chequeo: ${rep.timestamp || "--"} · Nocturno ${cfg.nightly_time || "03:30"}</span>
      </div>
      <div style="font-size:0.83rem; color:var(--modal-text); line-height:1.45; white-space:pre-line;">${(ai.text || "").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/\*\*(.+?)\*\*/g,"<b>$1</b>")}</div>
      ${ai.error ? `<div style="font-size:0.74rem; color:#f59e0b; margin-top:0.35rem;">⚠️ Gemini: ${ai.error}</div>` : ""}
    </div>

    <!-- Subsistemas (7 tarjetas) -->
    <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(230px, 1fr)); gap:0.55rem;">
      ${checksHtml}
    </div>

    <!-- Recomendaciones y Auto-Reparaciones -->
    <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(280px, 1fr)); gap:0.7rem;">
      <div class="domos-modal-subcard" style="padding:0.8rem 0.95rem; border-radius:16px;">
        <div style="font-size:0.84rem; font-weight:700; margin-bottom:0.35rem; color:var(--modal-text);">💡 Recomendaciones</div>
        <ul style="margin:0; padding-left:1.15rem;">${recsHtml}</ul>
      </div>
      <div class="domos-modal-subcard" style="padding:0.8rem 0.95rem; border-radius:16px;">
        <div style="font-size:0.84rem; font-weight:700; margin-bottom:0.35rem; color:var(--modal-text);">🛠️ Acciones Seguras Ejecutadas</div>
        ${actionsHtml}
      </div>
    </div>

    <!-- Auto-reparación segura -->
    <div class="domos-modal-subcard" style="padding:0.75rem 1rem; border-radius:16px; display:flex; flex-wrap:wrap; align-items:center; justify-content:space-between; gap:0.5rem;">
      <label style="display:flex; align-items:center; gap:0.45rem; font-size:0.82rem; font-weight:700; cursor:pointer; color:var(--modal-text);">
        <input type="checkbox" id="doctor-auto-heal-chk" ${cfg.auto_heal_enabled ? "checked" : ""} onchange="saveDoctorSettings()" style="width:17px; height:17px; accent-color:#8b5cf6;">
        🛠️ Auto-reparación segura activa (servicios caídos, backups atrasados, purificador en PM2.5 crítico)
      </label>
      <span id="doctor-cfg-status" style="font-size:0.74rem; color:#10b981; font-weight:600;"></span>
    </div>
  `;
}


// ========================================================
// SD CARD FILE MANAGER (Strictly /media/storage inside Photo Source Modal)
// ========================================================
let sdFmCurrentPath = "Images";
let sdFmParentPath = "";
let sdFmAllFolders = [""];

window.switchPhotoModalTab = function(tab) {
  const tabCfg = document.getElementById("photo-modal-tab-cfg");
  const tabSd = document.getElementById("photo-modal-tab-sd");
  const btnCfg = document.getElementById("btn-photo-tab-cfg");
  const btnSd = document.getElementById("btn-photo-tab-sd");
  const isSd = tab === "sd";
  if (tabCfg) tabCfg.style.display = isSd ? "none" : "flex";
  if (tabSd) tabSd.style.display = isSd ? "flex" : "none";
  if (btnCfg) {
    btnCfg.style.background = !isSd ? "rgba(14,165,233,0.22)" : "";
    btnCfg.style.borderColor = !isSd ? "#38bdf8" : "";
    btnCfg.style.fontWeight = !isSd ? "700" : "";
  }
  if (btnSd) {
    btnSd.style.background = isSd ? "rgba(14,165,233,0.22)" : "";
    btnSd.style.borderColor = isSd ? "#38bdf8" : "";
    btnSd.style.fontWeight = isSd ? "700" : "";
  }
  if (isSd) loadSdFileManager(sdFmCurrentPath);
};

function setSdFmStatus(msg, isErr = false) {
  const el = document.getElementById("sd-fm-status");
  if (!el) return;
  if (!msg) { el.style.display = "none"; return; }
  el.style.display = "block";
  el.style.background = isErr ? "rgba(239,68,68,0.16)" : "rgba(16,185,129,0.16)";
  el.style.color = isErr ? "#dc2626" : "#047857";
  el.textContent = msg;
  setTimeout(() => { el.style.display = "none"; }, 3500);
}

window.sdFmGoUp = function() {
  if (sdFmParentPath !== null && sdFmParentPath !== undefined) {
    loadSdFileManager(sdFmParentPath);
  }
};

window.loadSdFileManager = async function(path = "") {
  const listEl = document.getElementById("sd-fm-list");
  const crumbEl = document.getElementById("sd-fm-breadcrumb");
  const upBtn = document.getElementById("btn-sd-fm-up");
  if (!listEl) return;
  try {
    const res = await fetch(`/api/sd/list?path=${encodeURIComponent(path)}`);
    const d = await res.json();
    if (!res.ok) {
      if (path !== "") return loadSdFileManager("");
      listEl.innerHTML = `<p style="color:#ef4444; font-size:0.82rem;">${d.error || "Error accediendo a la SD"}</p>`;
      return;
    }
    sdFmCurrentPath = d.path || "";
    sdFmParentPath = d.parent;
    sdFmAllFolders = d.all_folders || [""];

    if (crumbEl) crumbEl.textContent = `📁 SD / ${sdFmCurrentPath || "(Raíz)"}`;
    if (upBtn) upBtn.style.display = sdFmParentPath !== null ? "inline-flex" : "none";

    const folderOptions = sdFmAllFolders.map(f => `<option value="${f.replace(/"/g, "&quot;")}">${f ? "📁 " + f : "📁 (Raíz SD)"}</option>`).join("");

    const folderRows = (d.folders || []).map(f => {
      const safeP = f.path.replace(/'/g, "\'");
      return `
        <div style="display:flex; align-items:center; justify-content:space-between; gap:0.5rem; padding:0.5rem 0.7rem; border-radius:12px; background:var(--modal-subcard-bg); border:1px solid var(--modal-subcard-border);">
          <div onclick="loadSdFileManager('${safeP}')" style="display:flex; align-items:center; gap:0.55rem; cursor:pointer; flex:1; min-width:0;">
            <span style="font-size:1.2rem;">📁</span>
            <div style="min-width:0;">
              <div style="font-size:0.84rem; font-weight:700; color:var(--modal-text); white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${f.name}</div>
              <div style="font-size:0.71rem; color:var(--modal-text-muted);">${f.items} elemento(s)</div>
            </div>
          </div>
          <div style="display:flex; gap:0.3rem;">
            <button type="button" class="liquid-action-pill" onclick="loadSdFileManager('${safeP}')" style="cursor:pointer; font-size:0.72rem; padding:0.2rem 0.5rem;">Abrir</button>
            ${f.items === 0 ? `<button type="button" class="liquid-action-pill" onclick="sdFmDelete('${safeP}', '${f.name.replace(/'/g, "\'")}')" style="cursor:pointer; font-size:0.72rem; padding:0.2rem 0.45rem; border-color:rgba(239,68,68,0.45); color:#dc2626;">🗑️</button>` : ""}
          </div>
        </div>
      `;
    }).join("");

    const fileRows = (d.files || []).map((f, idx) => {
      const safeP = f.path.replace(/'/g, "\'");
      const safeName = f.name.replace(/'/g, "\'");
      const thumb = f.is_image
        ? `<img src="/api/sd/thumb?path=${encodeURIComponent(f.path)}" loading="lazy" style="width:42px; height:42px; object-fit:cover; border-radius:8px; border:1px solid var(--modal-subcard-border); flex-shrink:0;">`
        : `<span style="width:42px; height:42px; display:flex; align-items:center; justify-content:center; font-size:1.25rem; flex-shrink:0;">📄</span>`;
      return `
        <div style="display:flex; flex-direction:column; gap:0.35rem; padding:0.45rem 0.65rem; border-radius:12px; background:var(--modal-subcard-bg); border:1px solid var(--modal-subcard-border);">
          <div style="display:flex; align-items:center; justify-content:space-between; gap:0.55rem;">
            <div style="display:flex; align-items:center; gap:0.55rem; min-width:0; flex:1;">
              ${thumb}
              <div style="min-width:0;">
                <div style="font-size:0.81rem; font-weight:600; color:var(--modal-text); white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${f.name}</div>
                <div style="font-size:0.7rem; color:var(--modal-text-muted);">${f.size_kb} KB</div>
              </div>
            </div>
            <div style="display:flex; gap:0.3rem; flex-shrink:0;">
              <button type="button" class="liquid-action-pill" onclick="sdFmToggleMoveRow(${idx})" style="cursor:pointer; font-size:0.72rem; padding:0.22rem 0.5rem;">📦 Mover</button>
              <button type="button" class="liquid-action-pill" onclick="sdFmDelete('${safeP}', '${safeName}')" style="cursor:pointer; font-size:0.72rem; padding:0.22rem 0.48rem; border-color:rgba(239,68,68,0.45); color:#dc2626;">🗑️</button>
            </div>
          </div>
          <div id="sd-move-row-${idx}" style="display:none; align-items:center; gap:0.35rem; padding-top:0.25rem; border-top:1px solid var(--modal-subcard-border);">
            <select id="sd-move-sel-${idx}" class="domos-modal-input" style="flex:1; padding:0.28rem 0.5rem; border-radius:8px; font-size:0.76rem;">${folderOptions}</select>
            <button type="button" class="liquid-action-pill" onclick="sdFmConfirmMove('${safeP}', ${idx})" style="cursor:pointer; font-size:0.73rem; padding:0.24rem 0.55rem; background:rgba(16,185,129,0.22); border-color:#10b981; color:#047857; font-weight:700;">✓ Mover aquí</button>
          </div>
        </div>
      `;
    }).join("");

    listEl.innerHTML = (folderRows + fileRows) || `<p style="color:var(--modal-text-muted); text-align:center; font-size:0.82rem;">Esta carpeta está vacía.</p>`;
  } catch (e) {
    listEl.innerHTML = `<p style="color:#ef4444; font-size:0.82rem;">Error de red al leer la SD.</p>`;
  }
};

window.sdFmToggleMoveRow = function(idx) {
  const row = document.getElementById(`sd-move-row-${idx}`);
  if (!row) return;
  row.style.display = row.style.display === "flex" ? "none" : "flex";
};

window.sdFmConfirmMove = async function(srcPath, idx) {
  const sel = document.getElementById(`sd-move-sel-${idx}`);
  if (!sel) return;
  try {
    const res = await fetch("/api/sd/move", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ src: srcPath, dst_dir: sel.value })
    });
    const d = await res.json();
    if (res.ok && d.success) {
      setSdFmStatus(`✅ Movido a ${sel.value || "(Raíz SD)"}`);
      loadSdFileManager(sdFmCurrentPath);
      if (typeof loadPhotoFolders === "function") loadPhotoFolders();
    } else {
      setSdFmStatus(`⚠️ ${d.error || "No se pudo mover"}`, true);
    }
  } catch (e) {
    setSdFmStatus("⚠️ Error de red al mover", true);
  }
};

window.sdFmDelete = async function(targetPath, label) {
  if (!window.confirm(`¿Borrar "${label}" de la tarjeta SD? Esta acción no se puede deshacer.`)) return;
  try {
    const res = await fetch("/api/sd/delete", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path: targetPath })
    });
    const d = await res.json();
    if (res.ok && d.success) {
      setSdFmStatus(`🗑️ "${label}" borrado de la SD`);
      loadSdFileManager(sdFmCurrentPath);
      if (typeof loadPhotoFolders === "function") loadPhotoFolders();
    } else {
      setSdFmStatus(`⚠️ ${d.error || "No se pudo borrar"}`, true);
    }
  } catch (e) {
    setSdFmStatus("⚠️ Error de red al borrar", true);
  }
};

window.sdFmCreateFolder = async function() {
  const name = window.prompt("Nombre de la nueva carpeta en la tarjeta SD:");
  if (!name || !name.trim()) return;
  try {
    const res = await fetch("/api/sd/mkdir", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path: sdFmCurrentPath, name: name.trim() })
    });
    const d = await res.json();
    if (res.ok && d.success) {
      setSdFmStatus(`📁 Carpeta "${name.trim()}" creada`);
      loadSdFileManager(sdFmCurrentPath);
      if (typeof loadPhotoFolders === "function") loadPhotoFolders();
    } else {
      setSdFmStatus(`⚠️ ${d.error || "No se pudo crear"}`, true);
    }
  } catch (e) {
    setSdFmStatus("⚠️ Error de red", true);
  }
};


// ========================================================
// ANTI-BURN-IN: AUTO-CLOSE ALL MODALS & DRAWER AFTER 2 MIN IDLE
// ========================================================
const MODAL_IDLE_CLOSE_MS = 120000; // 2 minutos sin interacción
let modalIdleCloseTimer = null;

function closeAllModalsAndReturnToKiosk() {
  // Call dedicated close handlers where available (stops streams/TTS cleanly, keeps Radio audio playing)
  try { if (typeof closeCameraFullscreen === "function") closeCameraFullscreen(); } catch (e) {}
  try { if (typeof closeDoctorModal === "function") closeDoctorModal(); } catch (e) {}
  try { if (typeof closeCastModal === "function") closeCastModal(); } catch (e) {}
  try { if (typeof closeBackupsModal === "function") closeBackupsModal(); } catch (e) {}
  try { if (typeof closeEnergySavingsModal === "function") closeEnergySavingsModal(); } catch (e) {}
  try { if (typeof closeAlarmModal === "function") closeAlarmModal(); } catch (e) {}
  try { if (typeof closeAirQualityModal === "function") closeAirQualityModal(); } catch (e) {}

  // Hide any remaining open modal backdrops
  const modalIds = [
    "weather-modal", "photo-source-modal", "alarm-details-modal", "security-alarm-modal",
    "air-quality-modal", "energy-savings-modal", "backups-modal", "cast-modal", "doctor-modal",
    "calendar-modal", "radio-modal", "cameras-modal", "solar-modal", "climate-history-modal",
    "incidents-modal", "schedules-modal", "adguard-modal", "message-modal", "volume-safety-modal"
  ];
  modalIds.forEach(id => {
    const el = document.getElementById(id);
    if (el && (el.style.display === "flex" || el.style.display === "block" || !el.classList.contains("hidden"))) {
      el.classList.add("hidden");
      el.style.display = "none";
    }
  });

  // Close settings panel & Control Center drawer to return to photo carousel
  const settingsPanel = document.getElementById("drawer-settings-panel");
  if (settingsPanel) settingsPanel.classList.add("hidden");
  const drawer = document.getElementById("control-drawer");
  if (drawer && drawer.classList.contains("open")) {
    drawer.classList.remove("open");
  }
}

function resetModalIdleCloseTimer() {
  if (modalIdleCloseTimer) clearTimeout(modalIdleCloseTimer);
  modalIdleCloseTimer = setTimeout(() => {
    closeAllModalsAndReturnToKiosk();
  }, MODAL_IDLE_CLOSE_MS);
}

["pointerdown", "touchstart", "click", "scroll", "keydown", "input", "change"].forEach(ev => {
  window.addEventListener(ev, resetModalIdleCloseTimer, { passive: true, capture: true });
});
resetModalIdleCloseTimer();


// ========================================================
// INDEPENDENT AUDIO VOLUME MIXER (General, Radio, Doorbell, Cameras)
// ========================================================
window.domosAudioVolumes = { master: 70, radio: 75, doorbell: 85, cameras: 85 };
let audioVolDebounceTimers = {};

function applyAudioVolumesToUI(vols) {
  if (!vols) return;
  window.domosAudioVolumes = { ...window.domosAudioVolumes, ...vols };
  ["master", "radio", "doorbell", "cameras"].forEach(ch => {
    const val = window.domosAudioVolumes[ch];
    if (typeof val !== "number") return;
    const slider = document.getElementById(`vol-${ch}-slider`);
    const badge = document.getElementById(`vol-${ch}-val`);
    if (slider) slider.value = val;
    if (badge) badge.textContent = `${val}%`;
  });
  const camVid = document.getElementById("cam-fs-video");
  if (camVid && !camVid.muted) {
    camVid.volume = Math.max(0, Math.min(1, (window.domosAudioVolumes.cameras ?? 85) / 100));
  }
  const radioEl = document.getElementById("radio-audio-player") || window.radioAudio;
  if (radioEl && typeof radioEl.volume === "number") {
    radioEl.volume = Math.max(0, Math.min(1, (window.domosAudioVolumes.radio ?? 75) / 100));
  }
}

async function loadAudioVolumes() {
  try {
    const res = await fetch("/api/audio/volumes");
    if (res.ok) {
      const data = await res.json();
      if (data.volumes) applyAudioVolumesToUI(data.volumes);
    }
  } catch (e) {}
}

function pushAudioVolumeChannel(channel, value) {
  const num = Math.max(0, Math.min(100, parseInt(value, 10) || 0));
  window.domosAudioVolumes[channel] = num;
  const badge = document.getElementById(`vol-${channel}-val`);
  if (badge) badge.textContent = `${num}%`;
  if (channel === "cameras") {
    const camVid = document.getElementById("cam-fs-video");
    if (camVid && !camVid.muted) camVid.volume = num / 100;
  }
  if (audioVolDebounceTimers[channel]) clearTimeout(audioVolDebounceTimers[channel]);
  audioVolDebounceTimers[channel] = setTimeout(async () => {
    try {
      await fetch("/api/audio/volumes", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ [channel]: num })
      });
    } catch (e) {}
  }, 120);
}

["master", "radio", "doorbell", "cameras"].forEach(ch => {
  const slider = document.getElementById(`vol-${ch}-slider`);
  if (slider) {
    slider.addEventListener("input", (e) => pushAudioVolumeChannel(ch, e.target.value));
    slider.addEventListener("change", (e) => pushAudioVolumeChannel(ch, e.target.value));
  }
});

document.getElementById("btn-test-doorbell-chime")?.addEventListener("click", async () => {
  const btn = document.getElementById("btn-test-doorbell-chime");
  if (btn) btn.textContent = "🔔 Sonando...";
  try {
    await fetch("/api/doorbell/test_chime", { method: "POST" });
  } catch (e) {}
  setTimeout(() => {
    if (btn) btn.textContent = "🔊 Probar";
  }, 3400);
});

document.getElementById("btn-toggle-settings")?.addEventListener("click", () => {
  setTimeout(loadAudioVolumes, 120);
});

loadAudioVolumes();

import threading
import re
import urllib.request
import urllib.parse
import tuya_service
import xiaomi_service
import ewelink_service
import climate_logger
import power_logger
import energy_savings
import backup_domos
import cast_service
import doctor_domos
import time
import datetime
import os
import glob
import json
import asyncio
import subprocess
from pathlib import Path
from typing import List, Set
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
import shutil

app = FastAPI(title="DomosKiosk")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ACTIVE_SOCKETS: Set[WebSocket] = set()

CONFIG_FILE = Path("/opt/domoskiosk/kiosk_config.json")
SD_STORAGE = Path("/media/storage")
FALLBACK_DIR = Path("/opt/domoskiosk/photos_fallback")
INCIDENTS_FILE = Path("/opt/domoskiosk/incidents.json")
CALENDAR_FILE = Path("/opt/domoskiosk/family_calendar.json")
SHARED_PHOTO_DIR = Path("/media/storage/Imagenes/Compartidas")

def get_kiosk_config():
    default_cfg = {
        "photo_folder": "Imagenes",
        "carousel_mode": "mixed",  # "sd", "online", "mixed"
        "theme": "light",          # "light" (default) or "dark"
        "hidden_devices": []       # List of hidden device/control IDs
    }
    if CONFIG_FILE.exists():
        try:
            saved = json.loads(CONFIG_FILE.read_text())
            default_cfg.update(saved)
        except Exception:
            pass
    return default_cfg

def save_kiosk_config(new_vals: dict):
    cfg = get_kiosk_config()
    cfg.update(new_vals)
    try:
        CONFIG_FILE.write_text(json.dumps(cfg, indent=2))
    except Exception as e:
        print("Error saving config:", e)
    return cfg

def get_battery_info():
    hist_file = Path("/opt/domoskiosk/battery_history.json")
    if hist_file.exists():
        try:
            hdata = json.loads(hist_file.read_text())
            if hdata.get("telemetry"):
                t = dict(hdata["telemetry"])
                if "capacity" in t and isinstance(t["capacity"], (int, float)):
                    t["capacity"] = min(100, max(0, int(t["capacity"])))
                return t
        except Exception:
            pass

    bat_path = Path("/sys/class/power_supply/BATC")
    if not bat_path.exists():
        bats = list(Path("/sys/class/power_supply").glob("BAT*"))
        bat_path = bats[0] if bats else None
    
    if bat_path and bat_path.exists():
        try:
            raw_cap = int((bat_path / "capacity").read_text().strip())
            cap = min(100, max(0, raw_cap))
            status = (bat_path / "status").read_text().strip()
            v_now = int((bat_path / "voltage_now").read_text().strip()) if (bat_path / "voltage_now").exists() else 7600000
            i_now = int((bat_path / "current_now").read_text().strip()) if (bat_path / "current_now").exists() else 500000
            cf = int((bat_path / "charge_full").read_text().strip()) if (bat_path / "charge_full").exists() else 2581000
            cfd = int((bat_path / "charge_full_design").read_text().strip()) if (bat_path / "charge_full_design").exists() else 5000000
            cycles = int((bat_path / "cycle_count").read_text().strip()) if (bat_path / "cycle_count").exists() else 401
            health = round((cf / cfd) * 100, 1) if cfd > 0 else 51.6
            power = round((v_now * abs(i_now)) / 1e12, 2)
            return {
                "capacity": cap,
                "status": status,
                "health_pct": health,
                "voltage_v": round(v_now / 1e6, 2),
                "power_w": power,
                "cycle_count": cycles,
                "charge_full_mah": round(cf / 1000),
                "charge_full_design_mah": round(cfd / 1000)
            }
        except Exception:
            pass
    return {"capacity": 100, "status": "Unknown", "health_pct": 51.6, "power_w": 4.5}

def get_brightness():
    try:
        out = subprocess.check_output(["brightnessctl", "get"], text=True).strip()
        max_b = subprocess.check_output(["brightnessctl", "max"], text=True).strip()
        pct = int(round(int(out) / int(max_b) * 100))
        return pct
    except Exception:
        return 80

def set_brightness(pct: int):
    try:
        pct = max(5, min(100, pct))
        subprocess.run(["brightnessctl", "set", f"{pct}%"], check=True)
        return True
    except Exception:
        return False

@app.get("/api/config")
async def api_get_config():
    return get_kiosk_config()

@app.post("/api/config")
async def api_set_config(request: Request):
    data = await request.json()
    cfg = save_kiosk_config(data)
    payload = json.dumps({"type": "CONFIG_UPDATE", "config": cfg})
    for ws in list(ACTIVE_SOCKETS):
        try:
            await ws.send_text(payload)
        except Exception:
            pass
    return {"status": "updated", "config": cfg}


DOMOS_REMOTE_KEY = os.environ.get("DOMOS_REMOTE_KEY", "domos_bc1a70aa4324bde9eb1a4cea1f79c52b5a43964f")
NTFY_TUNNEL_TOPIC = "domos_ep_94a7c2e1b8f03d5a"
_last_published_tunnel = ""

try:
    if not Path("/tmp/domos_voice_arm").exists():
        Path("/tmp/domos_voice_arm").write_text("0.0")
except Exception:
    pass

def _get_current_tunnel_url() -> str:
    global _last_published_tunnel
    log_p = Path("/var/log/domos_tunnel.log")
    if not log_p.exists():
        return _last_published_tunnel
    try:
        import re
        txt = log_p.read_text(errors="ignore")
        matches = re.findall(r"https://[a-z0-9-]+\.trycloudflare\.com", txt)
        if matches:
            latest = matches[-1]
            if latest != _last_published_tunnel:
                _last_published_tunnel = latest
                def _pub(u):
                    try:
                        req = urllib.request.Request(
                            f"https://ntfy.sh/{NTFY_TUNNEL_TOPIC}",
                            data=u.encode("utf-8"),
                            method="POST"
                        )
                        urllib.request.urlopen(req, timeout=5).read()
                    except Exception:
                        pass
                import threading
                threading.Thread(target=_pub, args=(latest,), daemon=True).start()
            return latest
    except Exception:
        pass
    return _last_published_tunnel

@app.middleware("http")
async def no_cache_static_middleware(request: Request, call_next):
    response = await call_next(request)
    path = request.url.path
    if path == "/" or path.endswith((".html", ".js", ".css")):
        response.headers["Cache-Control"] = "no-cache, must-revalidate"
    return response

@app.middleware("http")
async def remote_tunnel_auth_middleware(request: Request, call_next):
    # Local LAN requests do not carry Cf-Connecting-Ip header
    cf_ip = request.headers.get("cf-connecting-ip")
    if cf_ip:
        key_hdr = request.headers.get("x-domos-key", "")
        key_q = request.query_params.get("domos_key", "")
        key_cookie = request.cookies.get("domos_key", "")
        if DOMOS_REMOTE_KEY not in (key_hdr, key_q, key_cookie):
            return JSONResponse({"error": "Acceso externo protegido por Domos"}, status_code=403)
        response = await call_next(request)
        if key_q == DOMOS_REMOTE_KEY and key_cookie != DOMOS_REMOTE_KEY:
            response.set_cookie("domos_key", DOMOS_REMOTE_KEY, max_age=31536000, httponly=True, samesite="lax")
        return response
    return await call_next(request)

@app.get("/api/status")
async def api_status():
    cfg = get_kiosk_config()
    target_folder = SD_STORAGE / cfg.get("photo_folder", "Imagenes")
    active_inc = compute_system_incidents()
    return {
        "battery": get_battery_info(),
        "brightness": get_brightness(),
        "photo_dir_exists": target_folder.exists(),
        "tunnel_url": _get_current_tunnel_url(),
        "config": cfg,
        "incidents_count": len(active_inc),
        "has_incidents": len(active_inc) > 0,
        "incidents": active_inc
    }

@app.get("/api/system/battery")
async def api_system_battery():
    hist_file = Path("/opt/domoskiosk/battery_history.json")
    if hist_file.exists():
        try:
            return json.loads(hist_file.read_text())
        except Exception:
            pass
    bat = get_battery_info()
    return {
        "telemetry": bat,
        "current_phase": {
            "type": "discharge" if bat.get("status") == "Discharging" else "charge",
            "current_pct": bat.get("capacity", 50),
            "start_pct": 70 if bat.get("status") == "Discharging" else 30,
            "elapsed_min": 25
        },
        "stats": {
            "avg_charge_min": 35,
            "avg_discharge_day_min": 75,
            "avg_discharge_night_min": 175,
            "total_cycles_recorded": 18
        },
        "cycles": []
    }


@app.get("/api/power/history")
async def api_power_history(period: str = "daily"):
    try:
        if period not in ("daily", "monthly", "yearly"):
            period = "daily"
        data = await asyncio.to_thread(power_logger.get_power_history, period)
        return data
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/climate/history")
async def api_climate_history(month: str = None, metric: str = "temperature"):
    try:
        data = await asyncio.to_thread(climate_logger.get_climate_history, month, metric)
        return data
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

_last_outdoor_air_cache = None
_last_outdoor_air_time = 0.0

def _get_outdoor_air_sync():
    global _last_outdoor_air_cache, _last_outdoor_air_time
    now = time.time()
    if _last_outdoor_air_cache and (now - _last_outdoor_air_time) < 600.0:
        return _last_outdoor_air_cache

    url = "https://air-quality-api.open-meteo.com/v1/air-quality?latitude=36.7167&longitude=-4.2833&current=european_aqi,pm10,pm2_5,ozone,dust,alder_pollen,birch_pollen,grass_pollen,mugwort_pollen,olive_pollen,ragweed_pollen"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "DomosKiosk/4.1"})
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read().decode())
            cur = data.get("current", {})
            eaqi = cur.get("european_aqi", 25)
            pm25 = cur.get("pm2_5", 3.6)
            pm10 = cur.get("pm10", 7.1)
            dust = cur.get("dust", 0.0)
            ozone = cur.get("ozone", 56.0)

            p_grass = cur.get("grass_pollen", 0.0) or 0.0
            p_olive = cur.get("olive_pollen", 0.0) or 0.0
            p_mug = cur.get("mugwort_pollen", 0.0) or 0.0
            p_alder = cur.get("alder_pollen", 0.0) or 0.0
            p_birch = cur.get("birch_pollen", 0.0) or 0.0
            p_rag = cur.get("ragweed_pollen", 0.0) or 0.0
            p_total = round(p_grass + p_olive + p_mug + p_alder + p_birch + p_rag, 1)

            if p_total < 2.0:
                p_level = "Muy Bajo"
                p_color = "#10b981"
            elif p_total < 10.0:
                p_level = "Bajo"
                p_color = "#38bdf8"
            elif p_total < 30.0:
                p_level = "Moderado"
                p_color = "#f59e0b"
            else:
                p_level = "Alto"
                p_color = "#ef4444"

            if eaqi <= 25:
                aqi_lbl = "Excelente"
                aqi_col = "#10b981"
            elif eaqi <= 50:
                aqi_lbl = "Bueno"
                aqi_col = "#38bdf8"
            elif eaqi <= 75:
                aqi_lbl = "Moderado"
                aqi_col = "#f59e0b"
            else:
                aqi_lbl = "Deficiente"
                aqi_col = "#ef4444"

            out = {
                "location": "Rincón de la Victoria (29720)",
                "european_aqi": eaqi,
                "aqi_label": aqi_lbl,
                "aqi_color": aqi_col,
                "pm2_5": pm25,
                "pm10": pm10,
                "dust": dust,
                "ozone": ozone,
                "pollen_total": p_total,
                "pollen_level": p_level,
                "pollen_color": p_color,
                "pollen_breakdown": {
                    "grass": p_grass,
                    "olive": p_olive,
                    "mugwort": p_mug,
                    "alder": p_alder,
                    "birch": p_birch,
                    "ragweed": p_rag
                }
            }
            _last_outdoor_air_cache = out
            _last_outdoor_air_time = now
            return out
    except Exception as e:
        if _last_outdoor_air_cache:
            return _last_outdoor_air_cache
        return {
            "location": "Rincón de la Victoria (29720)",
            "european_aqi": 25,
            "aqi_label": "Bueno",
            "aqi_color": "#10b981",
            "pm2_5": 3.6,
            "pm10": 7.1,
            "dust": 0.0,
            "ozone": 56.0,
            "pollen_total": 0.5,
            "pollen_level": "Muy Bajo",
            "pollen_color": "#10b981",
            "pollen_breakdown": {"grass": 0.0, "olive": 0.0, "mugwort": 0.5}
        }


SECURITY_EVENTS_FILE = Path("/opt/domoskiosk/security_events.json")
_last_sec_snapshot = {}

def _load_security_events():
    if SECURITY_EVENTS_FILE.exists():
        try:
            data = json.loads(SECURITY_EVENTS_FILE.read_text())
            if isinstance(data, list):
                return data
        except Exception:
            pass
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    initial = [
        {
            "ts": now_str,
            "icon": "🛡️",
            "source": "Centralita Alarma",
            "title": "Supervisión activa",
            "detail": "Conexión local LAN (192.168.1.14) y sensores vinculados operativos.",
            "severity": "info"
        }
    ]
    try:
        SECURITY_EVENTS_FILE.write_text(json.dumps(initial, indent=2, ensure_ascii=False))
    except Exception:
        pass
    return initial

def _append_security_event(source: str, title: str, detail: str, severity: str = "info", icon: str = "🛡️"):
    try:
        evts = _load_security_events()
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        # Avoid exact consecutive duplicate within same minute
        if evts and evts[0].get("title") == title and evts[0].get("source") == source and evts[0].get("ts") == now_str:
            return
        evts.insert(0, {
            "ts": now_str,
            "icon": icon,
            "source": source,
            "title": title,
            "detail": detail,
            "severity": severity
        })
        SECURITY_EVENTS_FILE.write_text(json.dumps(evts[:40], indent=2, ensure_ascii=False))
    except Exception:
        pass

def _normalize_battery(val):
    if val is None or val == "--":
        return {"label": "--", "pct": None, "status": "ok"}
    try:
        pct = int(val)
        st = "critical" if pct <= 15 else ("warning" if pct <= 30 else "ok")
        return {"label": f"{pct}%", "pct": pct, "status": st}
    except (ValueError, TypeError):
        s = str(val).lower().strip()
        if s in ("high", "alta", "full", "normal"):
            return {"label": "Alta", "pct": 95, "status": "ok"}
        if s in ("middle", "medium", "media"):
            return {"label": "Media", "pct": 55, "status": "warning"}
        if s in ("low", "baja", "lower", "empty"):
            return {"label": "Baja", "pct": 12, "status": "critical"}
        return {"label": str(val), "pct": 80, "status": "ok"}

@app.get("/api/security/alarm/details")
async def api_security_alarm_details():
    global _last_sec_snapshot
    tuya_struct = tuya_service.service.get_structured_devices()
    sec = tuya_struct.get("security", {})
    all_states = tuya_service.service.states

    alarm_dev = sec.get("alarm") or {}
    ast = alarm_dev.get("state") or all_states.get("64326051e8db8480acc0") or {}
    mode = str(ast.get("master_mode", "disarmed")).lower()
    mode_map = {
        "disarmed": ("Desarmada", "#10b981"),
        "arm": ("Armada Total", "#ef4444"),
        "home": ("Armada En Casa", "#f59e0b"),
        "sos": ("¡EMERGENCIA SOS!", "#ef4444"),
    }
    mode_label, mode_color = mode_map.get(mode, (mode.upper(), "#38bdf8"))
    alarm_bat = _normalize_battery(ast.get("battery", 100))

    door_st = (sec.get("door") or {}).get("state") or all_states.get("bf216abd6b1934fa11rl63") or {}
    lock_st = (sec.get("lock") or {}).get("state") or all_states.get("bf20349qicjyoh2g") or {}
    pir_st = (sec.get("pir") or {}).get("state") or all_states.get("bfe5e0eee875e23682hlez") or {}
    vib_st = (sec.get("vibration") or {}).get("state") or all_states.get("bf3f3e9f42a2a9101extac") or {}
    patio_st = (sec.get("motion") or {}).get("state") or all_states.get("bf452117db5ebe4eadwctr") or {}
    smoke_st = (sec.get("smoke_co") or {}).get("state") or all_states.get("bf736f7cfc729a8d8cb7eo") or {}

    door_open = bool(door_st.get("is_open", False))
    patio_pir = str(patio_st.get("pir", "none")).lower() in ("pir", "true", "1", "motion")
    int_pir = str(pir_st.get("pir", "none")).lower() in ("pir", "true", "1", "motion")
    vib_alert = str(vib_st.get("vibration", "normal")).lower() not in ("normal", "none", "")
    smoke_alarm = bool(smoke_st.get("is_alarm", False))

    # Detect live transitions to log real events
    snap = {"mode": mode, "door": door_open, "patio": patio_pir, "smoke": smoke_alarm}
    if _last_sec_snapshot:
        if snap["mode"] != _last_sec_snapshot.get("mode"):
            _append_security_event("Alarma", f"Modo cambiado a {mode_label}", "Estado de la centralita actualizado.", "warning" if mode != "disarmed" else "info", "🛡️")
        if snap["door"] != _last_sec_snapshot.get("door"):
            _append_security_event("Puerta Principal", "Puerta ABIERTA" if door_open else "Puerta cerrada", "Cambio detectado por sensor magnético.", "warning" if door_open else "info", "🚪")
        if snap["smoke"] and not _last_sec_snapshot.get("smoke"):
            _append_security_event("Cocina", "¡Alerta de Humo o CO!", "Activación en detector de cocina.", "critical", "🔥")
    _last_sec_snapshot = snap

    accessories = [
        {
            "id": "bf216abd6b1934fa11rl63",
            "name": "Puerta Principal",
            "zone": "Entrada",
            "icon": "🚪",
            "state_label": "¡ABIERTA!" if door_open else "Cerrada",
            "alert": door_open,
            "battery": _normalize_battery(door_st.get("battery", "high")),
            "protocol": "Wi-Fi / Smart Life",
        },
        {
            "id": "bf20349qicjyoh2g",
            "name": "Cerradura Inteligente",
            "zone": "Entrada",
            "icon": "🔐",
            "state_label": "Operativa",
            "alert": False,
            "battery": _normalize_battery(lock_st.get("battery", "high")),
            "protocol": "Zigbee LAN",
        },
        {
            "id": "bfe5e0eee875e23682hlez",
            "name": "Sensor Movimiento PIR",
            "zone": "Interior",
            "icon": "👁️",
            "state_label": "Movimiento" if int_pir else "Sin movimiento",
            "alert": int_pir,
            "battery": _normalize_battery(pir_st.get("battery", 74)),
            "protocol": "Wi-Fi / Tuya",
        },
        {
            "id": "bf3f3e9f42a2a9101extac",
            "name": "Vibración Ventana",
            "zone": "Interior",
            "icon": "🪟",
            "state_label": "Vibración" if vib_alert else "Reposo",
            "alert": vib_alert,
            "battery": _normalize_battery(vib_st.get("battery", 90)),
            "protocol": "Wi-Fi / Tuya",
        },
        {
            "id": "bf452117db5ebe4eadwctr",
            "name": "Sensor Patio",
            "zone": "Exterior / Patio",
            "icon": "🌿",
            "state_label": "Movimiento" if patio_pir else "Reposo",
            "alert": patio_pir,
            "battery": _normalize_battery(patio_st.get("battery", 9)),
            "protocol": "Zigbee / Smart Life",
        },
        {
            "id": "bf736f7cfc729a8d8cb7eo",
            "name": "Detector Humo y CO",
            "zone": "Cocina",
            "icon": "🍳",
            "state_label": "¡ALARMA!" if smoke_alarm else f"Seguro · CO {smoke_st.get('co_ppm', 0)} ppm",
            "alert": smoke_alarm,
            "battery": _normalize_battery(smoke_st.get("battery", 100)),
            "protocol": "Wi-Fi / Tuya",
        },
    ]

    zones_order = [
        {"key": "Entrada", "icon": "🚪", "title": "Zona Entrada", "desc": "Acceso principal y cerradura"},
        {"key": "Interior", "icon": "🛋️", "title": "Zona Interior", "desc": "Presencia y perímetro ventana"},
        {"key": "Exterior / Patio", "icon": "🌿", "title": "Zona Exterior / Patio", "desc": "Detección perimetral exterior"},
        {"key": "Cocina", "icon": "🍳", "title": "Zona Cocina", "desc": "Seguridad humo y monóxido (CO)"},
    ]
    zones = []
    for z in zones_order:
        z_acc = [a for a in accessories if a["zone"] == z["key"]]
        has_crit = any(a["alert"] or a["battery"]["status"] == "critical" for a in z_acc)
        zones.append({**z, "accessories": z_acc, "has_alert": has_crit})

    events = _load_security_events()
    # Include centralita last alarm_msg if present and not already logged
    alarm_msg_txt = str(ast.get("alarm_msg_text") or "").strip()
    if alarm_msg_txt and not any(alarm_msg_txt in (e.get("detail") or "") for e in events):
        _append_security_event("Centralita Alarma", "Último aviso de centralita", alarm_msg_txt, "info", "📢")
        events = _load_security_events()

    return {
        "alarm": {
            "id": "64326051e8db8480acc0",
            "name": "Alarma Inteligente",
            "master_mode": mode,
            "mode_label": mode_label,
            "mode_color": mode_color,
            "battery": alarm_bat,
            "online": bool(ast.get("online", True)),
            "ip": "192.168.1.14",
            "alarm_msg_text": alarm_msg_txt,
            "updated_at": ast.get("updated_at")
        },
        "zones": zones,
        "accessories": accessories,
        "events": events[:15]
    }

@app.get("/api/air/quality")
async def api_air_quality():
    outdoor = await asyncio.to_thread(_get_outdoor_air_sync)
    
    # 1. Xiaomi Purifier
    purifier_state = {}
    try:
        xm_devs = xiaomi_service.service.get_devices()
        for d in xm_devs:
            if d.get("kind") == "purifier":
                purifier_state = d
                break
    except Exception:
        pass
    
    pst = purifier_state.get("state") or {}
    aqi_val = pst.get("aqi", 34)
    pur_is_on = pst.get("is_on", True)
    pur_mode = pst.get("mode", "auto")
    pur_temp = pst.get("temperature", 21.5)
    pur_hum = pst.get("humidity", 69)
    pur_filter = pst.get("filter_life", 35)

    # 2. Sótano AirBox
    tuya_struct = tuya_service.service.get_structured_devices()
    sotano_dev = None
    for c in tuya_struct.get("climate", []):
        if "aire" in (c.get("name") or "").lower() or c.get("id") == "bf3aa055b420138596m0cs":
            sotano_dev = c
            break
    
    sst = (sotano_dev.get("state") or {}) if sotano_dev else {}
    co2_val = sst.get("co2", 368)
    sot_temp = sst.get("temperature", 21.7)
    sot_hum = sst.get("humidity", 66)
    sot_voc = "Limpio"

    # 3. Cocina Smoke/CO
    smoke_co_dev = tuya_struct.get("security", {}).get("smoke_co")
    cst = (smoke_co_dev.get("state") or {}) if smoke_co_dev else {}
    co_ppm = cst.get("co_ppm", 0)
    smoke_st = cst.get("smoke_status", "normal")
    is_alarm = cst.get("is_alarm", False)

    # 4. Qualitative Synthesis
    if is_alarm or smoke_st == "alarm" or co_ppm > 25:
        headline = "¡Alerta Crítica en Cocina!"
        badge = "Alerta 🔴"
        badge_color = "#ef4444"
        summary = f"Detección anómala en cocina (Humo: {smoke_st}, Monóxido: {co_ppm} ppm). Ventile de inmediato y revise fogones/horno."
    elif co2_val > 1000 or aqi_val > 50:
        headline = "Calidad del Aire Moderada"
        badge = "Aviso 🟡"
        badge_color = "#f59e0b"
        summary = f"Valores elevados en alguna estancia (Salón: {aqi_val} PM2.5, Sótano: {co2_val} ppm CO₂). Se recomienda mantener activo el purificador o airear."
    else:
        headline = "Aire Saludable & Pureza Óptima"
        badge = "Excelente 🟢"
        badge_color = "#10b981"
        summary = f"Ambiente interior fresco y seguro. Partículas en salón controladas ({aqi_val} PM2.5), CO₂ en sótano óptimo ({co2_val} ppm) y monóxido nulo ({co_ppm} ppm). Exterior 29720 con aire limpio (EAQI {outdoor.get('european_aqi')}) y polen casi nulo ({outdoor.get('pollen_total')} gr/m³)."

    return {
        "evaluation": {
            "headline": headline,
            "badge": badge,
            "badge_color": badge_color,
            "summary": summary
        },
        "indoor": {
            "purifier": {
                "id": purifier_state.get("id", "314954236"),
                "name": "Purificador Salón",
                "room": "Salón",
                "online": pst.get("online", True),
                "is_on": pur_is_on,
                "mode": pur_mode,
                "aqi": aqi_val,
                "temperature": pur_temp,
                "humidity": pur_hum,
                "filter_life": pur_filter,
                "quality_label": "Buena" if aqi_val <= 35 else ("Moderada" if aqi_val <= 75 else "Deficiente"),
                "quality_color": "#10b981" if aqi_val <= 35 else ("#f59e0b" if aqi_val <= 75 else "#ef4444")
            },
            "sotano": {
                "id": "bf3aa055b420138596m0cs",
                "name": "Sensor Aire Sótano",
                "room": "Sótano",
                "co2": co2_val,
                "voc": sot_voc,
                "temperature": sot_temp,
                "humidity": sot_hum,
                "quality_label": "Excelente" if co2_val < 700 else ("Aceptable" if co2_val < 1000 else "Ventilar"),
                "quality_color": "#10b981" if co2_val < 700 else ("#f59e0b" if co2_val < 1000 else "#ef4444")
            },
            "cocina": {
                "id": "bf736f7cfc729a8d8cb7eo",
                "name": "Detector Humo & CO",
                "room": "Cocina",
                "co_ppm": co_ppm,
                "smoke_status": "Seguro" if smoke_st == "normal" else "Alerta",
                "is_alarm": is_alarm,
                "quality_label": "Seguro" if co_ppm == 0 and not is_alarm else "¡Alerta!",
                "quality_color": "#10b981" if co_ppm == 0 and not is_alarm else "#ef4444"
            }
        },
        "outdoor": outdoor,
        "air_auto": _get_air_auto_snapshot()
    }



# =========================================================
# AUTOMATIC AIR PURIFIER CONTROLLER (Xiaomi Purifier 314954236)
# =========================================================
AIR_AUTO_CONFIG_FILE = Path("/opt/domoskiosk/air_auto_config.json")
PURIFIER_DEV_ID = "314954236"
AIR_AUTO_DEFAULT = {
    "enabled": True,
    "on_pm25": 35,
    "off_pm25": 15,
    "sustain_on_min": 2,
    "sustain_off_min": 5,
    "min_on_min": 10,
    "night_start_hour": 23,
    "night_end_hour": 8,
}
_air_auto_rt = {
    "high_since": None,
    "low_since": None,
    "on_since": None,
    "auto_started": False,
    "last_action": None,
    "status_text": "Supervisando calidad del aire",
}

def load_air_auto_config() -> dict:
    cfg = dict(AIR_AUTO_DEFAULT)
    if AIR_AUTO_CONFIG_FILE.exists():
        try:
            saved = json.loads(AIR_AUTO_CONFIG_FILE.read_text())
            if isinstance(saved, dict):
                cfg.update(saved)
        except Exception:
            pass
    else:
        try:
            AIR_AUTO_CONFIG_FILE.write_text(json.dumps(cfg, indent=2))
        except Exception:
            pass
    return cfg

def save_air_auto_config(cfg: dict) -> dict:
    clean = dict(AIR_AUTO_DEFAULT)
    clean.update(cfg or {})
    clean["enabled"] = bool(clean.get("enabled", True))
    clean["on_pm25"] = max(15, min(150, int(clean.get("on_pm25", 35))))
    clean["off_pm25"] = max(5, min(clean["on_pm25"] - 5, int(clean.get("off_pm25", 15))))
    clean["sustain_on_min"] = max(0, min(30, int(clean.get("sustain_on_min", 2))))
    clean["sustain_off_min"] = max(1, min(30, int(clean.get("sustain_off_min", 5))))
    clean["min_on_min"] = max(1, min(60, int(clean.get("min_on_min", 10))))
    try:
        AIR_AUTO_CONFIG_FILE.write_text(json.dumps(clean, indent=2))
    except Exception:
        pass
    return clean

def _get_air_auto_snapshot() -> dict:
    cfg = load_air_auto_config()
    return {
        "config": cfg,
        "status_text": _air_auto_rt.get("status_text") or "Supervisando",
        "auto_started": bool(_air_auto_rt.get("auto_started")),
        "last_action": _air_auto_rt.get("last_action"),
    }

@app.get("/api/air/auto")
async def api_get_air_auto():
    return {"success": True, **_get_air_auto_snapshot()}

@app.post("/api/air/auto")
async def api_set_air_auto(request: Request):
    data = await request.json()
    cur = load_air_auto_config()
    cur.update(data)
    saved = save_air_auto_config(cur)
    if not saved["enabled"]:
        _air_auto_rt["high_since"] = None
        _air_auto_rt["low_since"] = None
        _air_auto_rt["status_text"] = "Pausada (control manual)"
    else:
        _air_auto_rt["status_text"] = "Activa · Supervisando PM2.5"
    return {"success": True, **_get_air_auto_snapshot()}

def _evaluate_air_purifier_auto():
    cfg = load_air_auto_config()
    if not cfg.get("enabled", True):
        _air_auto_rt["status_text"] = "Pausada (control manual)"
        return
    xm = getattr(xiaomi_service, "service", None)
    if xm is None:
        return
    pur = (xm.states or {}).get(PURIFIER_DEV_ID)
    if not isinstance(pur, dict) or not pur.get("online", True):
        _air_auto_rt["status_text"] = "Purificador sin conexión"
        return
    aqi = pur.get("aqi")
    if aqi is None:
        return
    try:
        pm25 = float(aqi)
    except Exception:
        return

    is_on = bool(pur.get("is_on", False))
    now = time.time()
    hour = datetime.datetime.now().hour
    is_night = hour >= int(cfg.get("night_start_hour", 23)) or hour < int(cfg.get("night_end_hour", 8))

    on_th = float(cfg["on_pm25"])
    off_th = float(cfg["off_pm25"])
    sus_on = float(cfg["sustain_on_min"])
    sus_off = float(cfg["sustain_off_min"])
    min_on = float(cfg["min_on_min"])

    if not is_on:
        _air_auto_rt["on_since"] = None
        _air_auto_rt["low_since"] = None
        _air_auto_rt["auto_started"] = False
        if pm25 >= on_th:
            if _air_auto_rt["high_since"] is None:
                _air_auto_rt["high_since"] = now
            elapsed_min = (now - _air_auto_rt["high_since"]) / 60.0
            if elapsed_min >= sus_on:
                target_mode = "silent" if is_night else "auto"
                xm.send_command(PURIFIER_DEV_ID, "power", True)
                xm.send_command(PURIFIER_DEV_ID, "mode", target_mode)
                _air_auto_rt["on_since"] = now
                _air_auto_rt["high_since"] = None
                _air_auto_rt["auto_started"] = True
                _air_auto_rt["last_action"] = f"Encendido ({target_mode}) a {int(pm25)} PM2.5 ({datetime.datetime.now():%H:%M})"
                _air_auto_rt["status_text"] = f"Purificando ({int(pm25)} → ≤{int(off_th)} PM2.5)"
                print(f"[AIR_AUTO] Purificador ON ({target_mode}): PM2.5={int(pm25)} >= {int(on_th)} durante {int(sus_on)} min", flush=True)
            else:
                rem_s = max(1, int((sus_on - elapsed_min) * 60))
                _air_auto_rt["status_text"] = f"Aire cargado ({int(pm25)} PM2.5) · Activa en {rem_s}s"
        else:
            _air_auto_rt["high_since"] = None
            _air_auto_rt["status_text"] = f"En espera · Aire limpio ({int(pm25)}/{int(on_th)} PM2.5)"
    else:
        _air_auto_rt["high_since"] = None
        if _air_auto_rt["on_since"] is None:
            _air_auto_rt["on_since"] = now
        on_elapsed = (now - _air_auto_rt["on_since"]) / 60.0
        if pm25 <= off_th:
            if _air_auto_rt["low_since"] is None:
                _air_auto_rt["low_since"] = now
            low_elapsed = (now - _air_auto_rt["low_since"]) / 60.0
            if on_elapsed >= min_on and low_elapsed >= sus_off:
                xm.send_command(PURIFIER_DEV_ID, "power", False)
                _air_auto_rt["on_since"] = None
                _air_auto_rt["low_since"] = None
                _air_auto_rt["auto_started"] = False
                _air_auto_rt["last_action"] = f"Apagado al limpiar ({int(pm25)} PM2.5, {datetime.datetime.now():%H:%M})"
                _air_auto_rt["status_text"] = f"Apagado · Aire limpio ({int(pm25)} PM2.5)"
                print(f"[AIR_AUTO] Purificador OFF: PM2.5={int(pm25)} <= {int(off_th)} durante {int(sus_off)} min", flush=True)
            else:
                rem_m = max(1, int(max(min_on - on_elapsed, sus_off - low_elapsed)))
                _air_auto_rt["status_text"] = f"Nivel seguro ({int(pm25)} PM2.5) · Apaga en ~{rem_m} min"
        else:
            _air_auto_rt["low_since"] = None
            _air_auto_rt["status_text"] = f"Purificando ({int(pm25)} → ≤{int(off_th)} PM2.5)"

async def air_purifier_auto_loop():
    await asyncio.sleep(15.0)
    print("[AIR_AUTO] Background Xiaomi Purifier auto-controller started (ON >=35 PM2.5, OFF <=15 PM2.5)", flush=True)
    while True:
        try:
            await asyncio.to_thread(_evaluate_air_purifier_auto)
        except Exception as e:
            print(f"[AIR_AUTO] Loop error: {e}", flush=True)
        await asyncio.sleep(30.0)

@app.on_event("startup")
async def start_air_purifier_auto_loop():
    asyncio.create_task(air_purifier_auto_loop())

@app.post("/api/brightness")
async def api_set_brightness(request: Request):
    data = await request.json()
    pct = data.get("brightness", 80)
    success = set_brightness(pct)
    return {"success": success, "brightness": pct}

# =========================================================
# SD CARD FILE MANAGER (Strictly sandboxed to /media/storage)
# =========================================================
SD_PROTECTED_NAMES = {"domos_backups", "System Volume Information", ".Spotlight-V100", ".Trashes", ".fseventsd", "MapData"}
SD_IMG_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}

def _safe_sd_path(rel_path: str) -> Path:
    root = SD_STORAGE.resolve()
    clean = str(rel_path or "").strip().lstrip("/")
    target = (root / clean).resolve()
    if target != root and not target.is_relative_to(root):
        raise ValueError("Path outside SD card")
    # Block protected top-level system/backup folders
    try:
        rel_parts = target.relative_to(root).parts
        if rel_parts and rel_parts[0] in SD_PROTECTED_NAMES:
            raise ValueError("Protected folder")
    except ValueError:
        raise
    return target

def _all_sd_folders() -> list:
    root = SD_STORAGE.resolve()
    out = [""]
    if not root.exists():
        return out
    for dirpath, dirnames, _ in os.walk(root):
        dp = Path(dirpath).resolve()
        # Prune hidden & protected dirs
        dirnames[:] = sorted(
            d for d in dirnames
            if not d.startswith(".") and not (dp == root and d in SD_PROTECTED_NAMES)
        )
        for d in dirnames:
            rel = str((dp / d).relative_to(root))
            out.append(rel)
    return out

@app.get("/api/sd/list")
async def api_sd_list(path: str = ""):
    if not SD_STORAGE.exists() or not SD_STORAGE.is_dir():
        return JSONResponse({"error": "Tarjeta SD no montada"}, status_code=404)
    try:
        target = _safe_sd_path(path)
        if not target.exists() or not target.is_dir():
            return JSONResponse({"error": "Carpeta no encontrada"}, status_code=404)
        root = SD_STORAGE.resolve()
        rel_cur = "" if target == root else str(target.relative_to(root))
        parent_rel = None if target == root else ("" if target.parent == root else str(target.parent.relative_to(root)))

        folders = []
        files = []
        for entry in sorted(target.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
            if entry.name.startswith(".") or entry.name.startswith("._"):
                continue
            if target == root and entry.name in SD_PROTECTED_NAMES:
                continue
            rel_entry = str(entry.relative_to(root))
            if entry.is_dir():
                try:
                    cnt = sum(1 for _ in entry.iterdir() if not _.name.startswith("."))
                except Exception:
                    cnt = 0
                folders.append({"name": entry.name, "path": rel_entry, "items": cnt})
            elif entry.is_file():
                st = entry.stat()
                is_img = entry.suffix.lower() in SD_IMG_EXTS
                files.append({
                    "name": entry.name,
                    "path": rel_entry,
                    "size_kb": round(st.st_size / 1024.0, 1),
                    "is_image": is_img,
                })
        return {
            "success": True,
            "path": rel_cur,
            "parent": parent_rel,
            "folders": folders,
            "files": files,
            "all_folders": _all_sd_folders(),
        }
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)

SD_THUMB_CACHE = Path("/tmp/domos_sd_thumbs")

def _make_sd_thumb(target: Path) -> Path:
    import hashlib
    from PIL import Image, ImageOps
    SD_THUMB_CACHE.mkdir(parents=True, exist_ok=True)
    st = target.stat()
    key = hashlib.md5(f"{target}:{st.st_mtime}:{st.st_size}".encode()).hexdigest()
    out = SD_THUMB_CACHE / f"{key}.jpg"
    if out.exists():
        return out
    with Image.open(target) as im:
        im = ImageOps.exif_transpose(im)
        im = im.convert("RGB")
        im.thumbnail((120, 120))
        im.save(out, format="JPEG", quality=72, optimize=True)
    return out

@app.get("/api/sd/thumb")
async def api_sd_thumb(path: str = ""):
    try:
        target = _safe_sd_path(path)
        if not target.exists() or not target.is_file() or target.suffix.lower() not in SD_IMG_EXTS:
            return Response(status_code=404)
        thumb = await asyncio.to_thread(_make_sd_thumb, target)
        return FileResponse(
            str(thumb),
            media_type="image/jpeg",
            headers={"Cache-Control": "public, max-age=86400"},
        )
    except Exception:
        return Response(status_code=400)

@app.post("/api/sd/mkdir")
async def api_sd_mkdir(request: Request):
    data = await request.json()
    base = str(data.get("path") or "")
    name = str(data.get("name") or "").strip()
    if not name or "/" in name or chr(92) in name or name in (".", "..") or name.startswith(".") or name in SD_PROTECTED_NAMES:
        return JSONResponse({"error": "Nombre de carpeta no válido"}, status_code=400)
    try:
        parent = _safe_sd_path(base)
        new_dir = _safe_sd_path(f"{base}/{name}" if base else name)
        new_dir.mkdir(parents=False, exist_ok=True)
        return {"success": True, "path": str(new_dir.relative_to(SD_STORAGE.resolve()))}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)

@app.post("/api/sd/move")
async def api_sd_move(request: Request):
    data = await request.json()
    src_rel = str(data.get("src") or "").strip()
    dst_dir_rel = str(data.get("dst_dir") or "").strip()
    if not src_rel:
        return JSONResponse({"error": "Origen requerido"}, status_code=400)
    try:
        src = _safe_sd_path(src_rel)
        dst_dir = _safe_sd_path(dst_dir_rel)
        if src == SD_STORAGE.resolve() or not src.exists():
            return JSONResponse({"error": "Archivo no encontrado"}, status_code=404)
        if not dst_dir.exists() or not dst_dir.is_dir():
            return JSONResponse({"error": "Carpeta destino no encontrada"}, status_code=404)
        dst = dst_dir / src.name
        if dst.resolve() == src.resolve():
            return {"success": True, "moved_to": dst_dir_rel}
        if dst.exists():
            stem, suf = src.stem, src.suffix
            dst = dst_dir / f"{stem}_{int(time.time())}{suf}"
        shutil.move(str(src), str(dst))
        return {"success": True, "moved_to": str(dst.relative_to(SD_STORAGE.resolve()))}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)

@app.post("/api/sd/delete")
async def api_sd_delete(request: Request):
    data = await request.json()
    rel = str(data.get("path") or "").strip()
    if not rel:
        return JSONResponse({"error": "Ruta requerida"}, status_code=400)
    try:
        target = _safe_sd_path(rel)
        if target == SD_STORAGE.resolve() or not target.exists():
            return JSONResponse({"error": "Elemento no encontrado"}, status_code=404)
        if target.is_dir():
            # Only allow deleting empty directories for safety
            if any(not x.name.startswith(".") for x in target.iterdir()):
                return JSONResponse({"error": "La carpeta no está vacía. Vacíala primero para borrarla."}, status_code=400)
            shutil.rmtree(target)
        else:
            target.unlink()
        return {"success": True, "deleted": rel}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)

@app.get("/api/photos/folders")
async def api_photos_folders():
    folders = []
    exts = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
    ignored = {"System Volume Information", "MapData", "Music"}

    if SD_STORAGE.exists() and SD_STORAGE.is_dir():
        try:
            for d in sorted(SD_STORAGE.iterdir(), key=lambda x: x.name.lower()):
                if not d.is_dir() or d.name.startswith(".") or d.name in ignored:
                    continue
                c_direct = sum(1 for f in d.iterdir() if f.is_file() and not f.name.startswith(".") and f.suffix.lower() in exts)
                c_total = sum(1 for f in d.rglob("*") if f.is_file() and not f.name.startswith(".") and f.suffix.lower() in exts)
                if c_total > 0 or d.name in {"Imagenes", "Images", "Fotos"}:
                    folders.append({
                        "id": d.name,
                        "name": f"📁 {d.name} ({c_total})",
                        "path": d.name,
                        "count": c_total
                    })
                for sub in sorted(d.iterdir(), key=lambda x: x.name.lower()):
                    if sub.is_dir() and not sub.name.startswith("."):
                        sub_c = sum(1 for f in sub.rglob("*") if f.is_file() and not f.name.startswith(".") and f.suffix.lower() in exts)
                        if sub_c > 0:
                            folders.append({
                                "id": f"{d.name}/{sub.name}",
                                "name": f"  ↳ {sub.name} ({sub_c})",
                                "path": f"{d.name}/{sub.name}",
                                "count": sub_c
                            })
        except Exception as e:
            print("Folder scan error:", e)

    current = get_kiosk_config().get("photo_folder", "Images")
    return {"folders": folders, "current": current}

@app.post("/api/photos/folder")
async def api_set_photo_folder(request: Request):
    data = await request.json()
    folder = data.get("folder", "Imagenes")
    save_kiosk_config({"photo_folder": folder})
    return {"status": "folder_changed", "folder": folder}

@app.get("/api/photos")
async def api_photos():
    cfg = get_kiosk_config()
    folder_rel = cfg.get("photo_folder", "Imagenes")
    target_dir = SD_STORAGE / folder_rel if folder_rel else SD_STORAGE
    exts = (".jpg", ".jpeg", ".png", ".webp", ".JPG", ".JPEG", ".PNG")
    photos = []
    
    # 1. Search in user SD Card target directory
    if target_dir.exists() and target_dir.is_dir():
        for ext in exts:
            for p in target_dir.rglob(f"*{ext}"):
                if not p.name.startswith("."):
                    rel = p.relative_to(SD_STORAGE)
                    photos.append(f"/photo_file/{rel}")
                    
    # 2. If no photos found, check fallback
    if not photos and FALLBACK_DIR.exists():
        for ext in exts:
            for p in FALLBACK_DIR.glob(f"*{ext}"):
                photos.append(f"/fallback_file/{p.name}")
                
    return {
        "photos": photos,
        "folder": folder_rel,
        "count": len(photos)
    }


# ========================================================
# SANDBOXED SD CARD FILE API (STRICTLY /media/storage ONLY)
# ========================================================
def _resolve_sd_path(rel_path: str = "") -> Path:
    base = SD_STORAGE.resolve()
    clean = (rel_path or "").lstrip("/").strip()
    target = (base / clean).resolve()
    target.relative_to(base)  # raises ValueError if path escapes /media/storage
    return target

@app.get("/api/sd/files")
async def sd_list_files(path: str = ""):
    try:
        target = _resolve_sd_path(path)
    except ValueError:
        return JSONResponse({"error": "Acceso denegado fuera de la tarjeta SD"}, status_code=403)
    if not target.exists() or not target.is_dir():
        return JSONResponse({"error": "Carpeta no encontrada"}, status_code=404)
    items = []
    for entry in sorted(target.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
        if entry.name.startswith(".") or entry.name == "System Volume Information":
            continue
        stat = entry.stat()
        items.append({
            "name": entry.name,
            "path": str(entry.relative_to(SD_STORAGE.resolve())),
            "is_dir": entry.is_dir(),
            "size": 0 if entry.is_dir() else stat.st_size,
            "mtime": int(stat.st_mtime),
        })
    return {"path": str(target.relative_to(SD_STORAGE.resolve())).replace(".", ""), "items": items}

@app.post("/api/sd/mkdir")
async def sd_mkdir(request: Request):
    data = await request.json()
    rel = data.get("path", "")
    try:
        target = _resolve_sd_path(rel)
    except ValueError:
        return JSONResponse({"error": "Acceso denegado fuera de la tarjeta SD"}, status_code=403)
    target.mkdir(parents=True, exist_ok=True)
    return {"status": "created", "path": str(target.relative_to(SD_STORAGE.resolve()))}

@app.post("/api/sd/upload")
async def sd_upload(file: UploadFile = File(...), folder: str = Form("Images")):
    try:
        dest_dir = _resolve_sd_path(folder)
    except ValueError:
        return JSONResponse({"error": "Acceso denegado fuera de la tarjeta SD"}, status_code=403)
    dest_dir.mkdir(parents=True, exist_ok=True)
    safe_name = Path(file.filename or f"upload_{int(time.time())}").name
    dest = (dest_dir / safe_name).resolve()
    dest.relative_to(SD_STORAGE.resolve())
    content = await file.read()
    dest.write_bytes(content)
    payload = json.dumps({"type": "PHOTOS_UPDATED", "folder": folder, "file": safe_name})
    for ws in list(ACTIVE_SOCKETS):
        try:
            await ws.send_text(payload)
        except Exception:
            pass
    return {
        "status": "uploaded",
        "name": safe_name,
        "path": str(dest.relative_to(SD_STORAGE.resolve())),
        "size": len(content),
    }

@app.get("/api/sd/download")
async def sd_download(path: str):
    try:
        target = _resolve_sd_path(path)
    except ValueError:
        return JSONResponse({"error": "Acceso denegado fuera de la tarjeta SD"}, status_code=403)
    if not target.exists() or not target.is_file():
        return JSONResponse({"error": "Archivo no encontrado"}, status_code=404)
    return FileResponse(target, filename=target.name)

@app.delete("/api/sd/file")
async def sd_delete(path: str):
    try:
        target = _resolve_sd_path(path)
    except ValueError:
        return JSONResponse({"error": "Acceso denegado fuera de la tarjeta SD"}, status_code=403)
    if target == SD_STORAGE.resolve():
        return JSONResponse({"error": "No se puede eliminar la raíz de la SD"}, status_code=403)
    if target.is_file():
        target.unlink()
        return {"status": "deleted"}
    return JSONResponse({"error": "Archivo no encontrado"}, status_code=404)

@app.get("/photo_file/{file_path:path}")
async def get_photo(file_path: str):
    full_path = (SD_STORAGE / file_path).resolve()
    # Path traversal protection
    try:
        full_path.relative_to(SD_STORAGE.resolve())
    except ValueError:
        return JSONResponse({"error": "Forbidden"}, status_code=403)
        
    if full_path.exists() and full_path.is_file():
        return FileResponse(full_path)
    return JSONResponse({"error": "Not found"}, status_code=404)

@app.get("/fallback_file/{file_path:path}")
async def get_fallback(file_path: str):
    full_path = FALLBACK_DIR / file_path
    if full_path.exists() and full_path.is_file():
        return FileResponse(full_path)
    return JSONResponse({"error": "Not found"}, status_code=404)

@app.post("/api/assistant/state")
async def set_assistant_state(request: Request):
    data = await request.json()
    state = data.get("state", "idle")  # "listening", "processing", "speaking", "idle"
    prompt = data.get("prompt", "")
    reply = data.get("reply", "")
    
    # Wake screen if assistant speaks or listens
    if state in ("listening", "speaking", "processing"):
        set_brightness(80)

    payload = json.dumps({
        "type": "ASSISTANT_STATE",
        "state": state,
        "prompt": prompt,
        "reply": reply
    })
    for ws in list(ACTIVE_SOCKETS):
        try:
            await ws.send_text(payload)
        except Exception:
            pass
    return {"status": "ok", "state": state}

@app.post("/api/doorbell/trigger")
async def trigger_doorbell(request: Request):
    data = await request.json() if request.headers.get("content-type") == "application/json" else {}
    title = data.get("title", "¡Alguien está en la puerta!")
    stream_url = data.get("stream_url", "")
    
    set_brightness(100)
    
    payload = json.dumps({
        "type": "DOORBELL_ALERT",
        "title": title,
        "stream_url": stream_url,
        "timestamp": data.get("timestamp", "")
    })
    
    dead_sockets = set()
    for ws in ACTIVE_SOCKETS:
        try:
            await ws.send_text(payload)
        except Exception:
            dead_sockets.add(ws)
    for ws in dead_sockets:
        ACTIVE_SOCKETS.discard(ws)
        
    return {"status": "broadcast_sent", "clients": len(ACTIVE_SOCKETS)}

@app.post("/api/doorbell/dismiss")
async def dismiss_doorbell():
    payload = json.dumps({"type": "DOORBELL_DISMISS"})
    for ws in list(ACTIVE_SOCKETS):
        try:
            await ws.send_text(payload)
        except Exception:
            pass
    return {"status": "dismissed"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    ACTIVE_SOCKETS.add(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Broadcast to all connected sockets
            for ws in list(ACTIVE_SOCKETS):
                try:
                    await ws.send_text(data)
                except Exception:
                    pass
    except WebSocketDisconnect:
        ACTIVE_SOCKETS.discard(websocket)
    except Exception:
        ACTIVE_SOCKETS.discard(websocket)

@app.post("/api/message/send")
async def send_family_message(request: Request):
    data = await request.json()
    sender = data.get("sender", "Papá")
    text = data.get("text", "")
    speak = data.get("speak", True)
    
    set_brightness(100)
    
    payload = json.dumps({
        "type": "FAMILY_MESSAGE",
        "sender": sender,
        "text": text,
        "timestamp": data.get("timestamp", "")
    })
    
    for ws in list(ACTIVE_SOCKETS):
        try:
            await ws.send_text(payload)
        except Exception:
            pass
            
    if speak and text:
        try:
            msg_to_speak = f"Mensaje de {sender}: {text}"
            subprocess.Popen(["espeak-ng", "-v", "es-es", "-s", "145", msg_to_speak])
        except Exception as e:
            print("TTS Error:", e)
            
    return {"status": "sent", "sender": sender, "text": text}

@app.post("/api/presence/wake")
async def wake_screen(request: Request = None):
    seconds = 180
    if request:
        try:
            data = await request.json()
            seconds = data.get("seconds", 180)
        except Exception:
            pass
    Path("/tmp/domos_wake_trigger").write_text(str(seconds))
    return {"status": "wake_triggered", "seconds": seconds}

@app.get("/api/presence/status")
async def presence_status():
    status_file = Path("/tmp/domos_presence_status.json")
    if status_file.exists():
        try:
            return json.loads(status_file.read_text())
        except Exception:
            pass
    return {"status": "unknown"}

@app.post("/api/photos/upload")
async def upload_photo(file: UploadFile = File(...), sender: str = Form("Familia")):
    try:
        SHARED_PHOTO_DIR.mkdir(parents=True, exist_ok=True)
        safe_name = f"{int(time.time())}_{file.filename}"
        dest_path = SHARED_PHOTO_DIR / safe_name
        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        set_brightness(100)
        
        payload = json.dumps({
            "type": "NEW_PHOTO",
            "sender": sender,
            "url": f"/photo_file/Imagenes/Compartidas/{safe_name}"
        })
        for ws in list(ACTIVE_SOCKETS):
            try:
                await ws.send_text(payload)
            except Exception:
                pass
                
        return {"status": "uploaded", "file": safe_name}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

DISMISSED_INCIDENTS_CACHE = {}  # {inc_id: timestamp_dismissed}

_INCIDENT_STATE_TRACKERS = {
    "door_open_since": None,
    "termo_on_since": None,
    "secatoallas_on_since": None,
}

def compute_system_incidents():
    active = []
    now_ts = time.time()
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    # Read persistent/logged incidents from incidents.json
    logged_unresolved = []
    if INCIDENTS_FILE.exists():
        try:
            stored = json.loads(INCIDENTS_FILE.read_text())
            for inc in stored:
                if not inc.get("resolved", False):
                    inc_id = inc.get("id")
                    if now_ts - DISMISSED_INCIDENTS_CACHE.get(inc_id, 0) > 43200:  # 12h
                        logged_unresolved.append(inc)
        except Exception:
            pass

    active.extend(logged_unresolved)

    # Read live states from /tmp/domos_tuya_states.json & devices.json
    states_file = Path("/tmp/domos_tuya_states.json")
    devs_file = Path("/opt/domoskiosk/devices.json")
    states = {}
    devs = {}
    if states_file.exists():
        try:
            states = json.loads(states_file.read_text())
        except Exception:
            pass
    if devs_file.exists():
        try:
            devs = json.loads(devs_file.read_text())
        except Exception:
            pass

    # 1. Batería baja en sensores a pilas y accesorios de alarma (deduplicado)
    seen_bat_names = set()
    for dev_id, st in states.items():
        if not isinstance(st, dict):
            continue
        # Skip mirrored duplicate ID for Higrómetro Salón
        if dev_id == "bf29b1a036ad20f17079pv" and "bf9cba82aabe945f4fc8q9" in states:
            continue
        dinfo = devs.get(dev_id, {})
        name = dinfo.get("name", dev_id)
        norm_name = name.strip().lower()
        if norm_name in seen_bat_names:
            continue
        cat = str(dinfo.get("category", "")).lower()
        name_lower = name.lower()

        # Ignore portable power tool batteries (Parkside/Lidl Smart X20V, dcb, taladro)
        if cat == "dcb" or "smart 20" in name_lower or "taladro" in name_lower or "batería smart" in name_lower:
            continue

        bat_val = st.get("battery")
        if bat_val is None:
            bat_val = st.get("battery_percentage")
        if bat_val is None:
            bat_val = st.get("battery_state")

        if bat_val is not None:
            inc_id = f"bat_{dev_id}"
            if now_ts - DISMISSED_INCIDENTS_CACHE.get(inc_id, 0) < 43200:
                continue

            try:
                pct = int(bat_val)
                if pct <= 20:
                    seen_bat_names.add(norm_name)
                    sev = "critical" if pct <= 10 else "warning"
                    active.append({
                        "id": inc_id,
                        "type": "battery_low",
                        "category": "battery",
                        "source": name,
                        "severity": sev,
                        "title": f"Batería baja: {name}",
                        "description": f"Nivel de batería al {pct}%. Conviene cambiar o recargar las pilas pronto.",
                        "value": f"{pct}%",
                        "icon": "🔋",
                        "timestamp": now_str,
                        "resolved": False
                    })
            except (ValueError, TypeError):
                sval = str(bat_val).lower().strip()
                if sval in ("low", "lower", "empty", "alarm", "bat_low", "die"):
                    seen_bat_names.add(norm_name)
                    active.append({
                        "id": inc_id,
                        "type": "battery_low",
                        "category": "battery",
                        "source": name,
                        "severity": "warning",
                        "title": f"Batería baja: {name}",
                        "description": f"El sensor reporta estado de batería baja ('{sval}'). Sustituir pilas.",
                        "value": sval,
                        "icon": "🔋",
                        "timestamp": now_str,
                        "resolved": False
                    })


    # 1b. Avisos de batería baja en accesorios RF vinculados al panel de Alarma
    alarm_st = states.get("64326051e8db8480acc0") or {}
    alarm_msg_txt = str(alarm_st.get("alarm_msg_text") or "").strip()
    if alarm_msg_txt and any(w in alarm_msg_txt.lower() for w in ("bater", "pila", "low bat", "battery")):
        inc_id = "bat_alarm_rf_accessory"
        if now_ts - DISMISSED_INCIDENTS_CACHE.get(inc_id, 0) >= 43200:
            active.append({
                "id": inc_id,
                "type": "battery_low",
                "category": "battery",
                "source": "Accesorio Alarma",
                "severity": "warning",
                "title": f"Batería baja en accesorio de Alarma",
                "description": f"El panel de alarma reporta: '{alarm_msg_txt}'. Revisa las pilas del sensor.",
                "value": "Baja",
                "icon": "🔋",
                "timestamp": now_str,
                "resolved": False
            })

    # 2. Anomalías de tensión eléctrica en la red (< 180V o > 255V)
    for dev_id, st in states.items():
        if not isinstance(st, dict):
            continue
        dinfo = devs.get(dev_id, {})
        name = dinfo.get("name", dev_id)
        cat = str(dinfo.get("category", "")).lower()
        name_lower = name.lower()

        # Ignore portable power tool batteries (Parkside/Lidl Smart X20V, dcb, taladro)
        if cat == "dcb" or "smart 20" in name_lower or "taladro" in name_lower or "batería smart" in name_lower:
            continue
        if "bater" in name.lower() or "battery" in name.lower():
            continue

        volt_val = st.get("volts") if st.get("volts") is not None else st.get("voltage")
        if volt_val is not None:
            try:
                v = float(volt_val)
                inc_id_low = f"volt_low_{dev_id}"
                inc_id_high = f"volt_high_{dev_id}"

                if 100.0 < v < 180.0:
                    if now_ts - DISMISSED_INCIDENTS_CACHE.get(inc_id_low, 0) > 43200:
                        active.append({
                            "id": inc_id_low,
                            "type": "voltage_low",
                            "category": "grid",
                            "source": name,
                            "severity": "critical" if v < 170.0 else "warning",
                            "title": "Caída de tensión en red eléctrica",
                            "description": f"{name} detecta una tensión anormal de {v:.1f} V (límite seguro: 180 V). Posible bajada de suministro en el barrio.",
                            "value": f"{v:.1f} V",
                            "icon": "⚡",
                            "timestamp": now_str,
                            "resolved": False
                        })
                elif v > 255.0:
                    if now_ts - DISMISSED_INCIDENTS_CACHE.get(inc_id_high, 0) > 43200:
                        active.append({
                            "id": inc_id_high,
                            "type": "voltage_high",
                            "category": "grid",
                            "source": name,
                            "severity": "warning",
                            "title": "Sobretensión en red eléctrica",
                            "description": f"{name} detecta sobretensión de {v:.1f} V (límite recomendado: 255 V).",
                            "value": f"{v:.1f} V",
                            "icon": "⚡",
                            "timestamp": now_str,
                            "resolved": False
                        })
            except (ValueError, TypeError):
                pass

    # 3. Supervisión de Batería y Salud de la Tablet Domos (Casos Extremos)
    try:
        bat_info = get_battery_info()
        tab_pct = bat_info.get("capacity") if bat_info.get("capacity") is not None else bat_info.get("percent")
        status = bat_info.get("status", "Discharging")
        health = bat_info.get("health_pct", 51.6)

        # 3.1 Nivel Crítico (<= 15%): Posible corte de luz, enchufe apagado o desconectado
        if tab_pct is not None and tab_pct <= 15:
            inc_id_crit = "tablet_domos_battery_critical"
            if now_ts - DISMISSED_INCIDENTS_CACHE.get(inc_id_crit, 0) > 43200:
                active.append({
                    "id": inc_id_crit,
                    "type": "tablet_battery",
                    "category": "system",
                    "source": "Tablet Domos",
                    "severity": "critical",
                    "title": "Batería crítica en Domos (≤ 15%)",
                    "description": f"La tablet central está al {tab_pct}% de batería y no ha entrado en carga. Comprueba el enchufe o el suministro eléctrico.",
                    "value": f"{tab_pct}%",
                    "icon": "🪫",
                    "timestamp": now_str,
                    "resolved": False
                })

        # 3.2 Alerta de Degradación Severa / Prevención de Hinchado (< 30% de salud)
        if health is not None and health < 30.0:
            inc_id_degrade = "tablet_domos_battery_degraded"
            if now_ts - DISMISSED_INCIDENTS_CACHE.get(inc_id_degrade, 0) > 86400: # 24h
                active.append({
                    "id": inc_id_degrade,
                    "type": "tablet_health",
                    "category": "system",
                    "source": "Batería Domos",
                    "severity": "critical",
                    "title": "Degradación crítica de batería",
                    "description": f"La salud de la celda de litio ha caído al {health}%. Se aconseja cambiar la batería de forma preventiva para evitar deformación o hinchamiento.",
                    "value": f"{health}% salud",
                    "icon": "⚠️",
                    "timestamp": now_str,
                    "resolved": False
                })

        # 3.3 Colapso de Autonomía Nocturna (< 60 min con pantalla apagada) o Carga Atascada (> 90 min cargando)
        hist_file = Path("/opt/domoskiosk/battery_history.json")
        if hist_file.exists():
            try:
                hdata = json.loads(hist_file.read_text())
                night_avg = hdata.get("stats", {}).get("avg_discharge_night_min", 170)
                if night_avg < 60:
                    inc_id_night = "tablet_domos_night_collapse"
                    if now_ts - DISMISSED_INCIDENTS_CACHE.get(inc_id_night, 0) > 86400:
                        active.append({
                            "id": inc_id_night,
                            "type": "tablet_autonomy",
                            "category": "system",
                            "source": "Batería Domos",
                            "severity": "warning",
                            "title": "Pérdida acelerada de retención",
                            "description": f"La descarga nocturna (con pantalla apagada) dura menos de 1 hora ({night_avg} min). Posible fuga interna o degradación acelerada.",
                            "value": f"{night_avg} min noche",
                            "icon": "🌙",
                            "timestamp": now_str,
                            "resolved": False
                        })

                cur_phase = hdata.get("current_phase", {})
                if (cur_phase.get("type") == "charge"
                    and cur_phase.get("elapsed_min", 0) > 90
                    and cur_phase.get("current_pct", 0) < 70
                    and bat.get("status") == "Charging"
                    and bat.get("voltage_v", 0) < 8.3):
                    inc_id_stall = "tablet_domos_charge_stall"
                    if now_ts - DISMISSED_INCIDENTS_CACHE.get(inc_id_stall, 0) > 43200:
                        active.append({
                            "id": inc_id_stall,
                            "type": "tablet_charge",
                            "category": "system",
                            "source": "Cargador Domos",
                            "severity": "warning",
                            "title": "Carga de batería anormalmente lenta",
                            "description": f"La batería lleva {cur_phase.get('elapsed_min')} min cargando sin llegar al 70%. Comprueba el cable microUSB o el cargador.",
                            "value": f">{cur_phase.get('elapsed_min')} min",
                            "icon": "🔌",
                            "timestamp": now_str,
                            "resolved": False
                        })
            except Exception:
                pass
    except Exception:
        pass

    # 4. Alerta Crítica de Humo o Monóxido de Carbono (Cocina)
    try:
        tuya_devs = tuya_service.service.get_structured_devices()
        smoke_dev = tuya_devs.get("security", {}).get("smoke_co")
        if smoke_dev:
            st = smoke_dev.get("state", {})
            if st.get("is_alarm") or st.get("smoke_status") == "alarm" or st.get("co_status") == "alarm" or st.get("co_ppm", 0) >= 50:
                active.append({
                    "id": "kitchen_smoke_co_alarm",
                    "type": "safety_alarm",
                    "category": "security",
                    "source": "Cocina",
                    "severity": "critical",
                    "title": "¡Alerta de Humo o Monóxido en Cocina!",
                    "description": f"El detector ha disparado una alarma de humo o nivel de CO ({st.get('co_ppm', 0)} ppm). Comprueba la cocina y ventila.",
                    "value": f"CO: {st.get('co_ppm', 0)} ppm",
                    "icon": "🔥",
                    "timestamp": now_str,
                    "resolved": False
                })
    except Exception:
        pass

    # 5. Seguridad: Puerta Principal abierta demasiado tiempo (>= 5 min) o abierta con Alarma Armada
    try:
        door_st = states.get("bf216abd6b1934fa11rl63") or {}
        door_open = bool(door_st.get("door_open") or door_st.get("doorcontact_state") is True)
        alarm_mode = str(alarm_st.get("master_mode") or "disarmed").lower()
        alarm_is_armed = alarm_mode in ("armed", "arm", "away")
        if door_open:
            if _INCIDENT_STATE_TRACKERS["door_open_since"] is None:
                _INCIDENT_STATE_TRACKERS["door_open_since"] = now_ts
            open_min = int((now_ts - _INCIDENT_STATE_TRACKERS["door_open_since"]) / 60.0)
            if alarm_is_armed:
                active.append({
                    "id": "sec_door_open_while_armed",
                    "type": "security_breach",
                    "category": "security",
                    "source": "Puerta Principal",
                    "severity": "critical",
                    "title": "¡Puerta abierta con Alarma Armada!",
                    "description": "La Puerta Principal está abierta mientras la alarma se encuentra armada. Revisa las cámaras.",
                    "value": "ABIERTA",
                    "icon": "🚨",
                    "timestamp": now_str,
                    "resolved": False
                })
            elif open_min >= 5 and (now_ts - DISMISSED_INCIDENTS_CACHE.get("sec_door_open_long", 0) > 1800):
                active.append({
                    "id": "sec_door_open_long",
                    "type": "door_open_long",
                    "category": "security",
                    "source": "Puerta Principal",
                    "severity": "warning",
                    "title": f"Puerta Principal abierta ({open_min} min)",
                    "description": f"La puerta de entrada lleva {open_min} minutos abierta de forma continua.",
                    "value": f"{open_min} min",
                    "icon": "🚪",
                    "timestamp": now_str,
                    "resolved": False
                })
        else:
            _INCIDENT_STATE_TRACKERS["door_open_since"] = None
    except Exception:
        pass

    # 6. Seguridad: Alarma disparada / intrusión / sabotaje
    try:
        al_state = str(alarm_st.get("alarm_state") or "").lower()
        al_txt_low = alarm_msg_txt.lower()
        if al_state == "alarm" or any(w in al_txt_low for w in ("intrus", "sabotaj", "tamper", "sos", "sirena", "dispar")):
            inc_id = "sec_alarm_triggered"
            if now_ts - DISMISSED_INCIDENTS_CACHE.get(inc_id, 0) > 3600:
                active.append({
                    "id": inc_id,
                    "type": "alarm_triggered",
                    "category": "security",
                    "source": "Alarma Hogar",
                    "severity": "critical",
                    "title": "¡Evento crítico en Alarma Hogar!",
                    "description": f"El panel de alarma reporta: '{alarm_msg_txt or al_state}'. Comprueba el historial de seguridad.",
                    "value": "ALARMA",
                    "icon": "🚨",
                    "timestamp": now_str,
                    "resolved": False
                })
    except Exception:
        pass

    # 7. Calidad del Aire Interior y Exterior (CO2 Sótano, CH2O, PM2.5 Salón, Polen 29720)
    try:
        sot_st = states.get("bf3aa055b420138596m0cs") or {}
        co2_val = sot_st.get("co2")
        if co2_val is not None:
            try:
                co2_num = float(co2_val)
                if co2_num >= 1000 and (now_ts - DISMISSED_INCIDENTS_CACHE.get("air_sotano_co2", 0) > 7200):
                    sev = "critical" if co2_num >= 1500 else "warning"
                    active.append({
                        "id": "air_sotano_co2",
                        "type": "air_co2_high",
                        "category": "air",
                        "source": "Sótano",
                        "severity": sev,
                        "title": f"CO₂ elevado en Sótano ({int(co2_num)} ppm)",
                        "description": "Conviene ventilar el sótano para renovar el aire (recomendado < 1000 ppm).",
                        "value": f"{int(co2_num)} ppm",
                        "icon": "🌬️",
                        "timestamp": now_str,
                        "resolved": False
                    })
            except Exception:
                pass
        ch2o_val = sot_st.get("ch2o")
        if ch2o_val is not None:
            try:
                ch2o_num = float(ch2o_val)
                if ch2o_num >= 1.0:
                    ch2o_num = ch2o_num / 1000.0  # Tuya raw CH2O integer is in ug/m3 (e.g. 2 -> 0.002 mg/m3)
                if ch2o_num >= 0.08 and (now_ts - DISMISSED_INCIDENTS_CACHE.get("air_sotano_ch2o", 0) > 7200):
                    active.append({
                        "id": "air_sotano_ch2o",
                        "type": "air_ch2o_high",
                        "category": "air",
                        "source": "Sótano",
                        "severity": "warning",
                        "title": f"Formaldehído elevado en Sótano ({ch2o_num:.2f} mg/m³)",
                        "description": "Nivel por encima del umbral confortable (0,08 mg/m³). Se recomienda ventilar.",
                        "value": f"{ch2o_num:.2f}",
                        "icon": "🧪",
                        "timestamp": now_str,
                        "resolved": False
                    })
            except Exception:
                pass

        # PM2.5 Purificador Xiaomi Salón
        xm_st = getattr(xiaomi_service, "service", None)
        if xm_st is not None:
            pur_st = (xm_st.states or {}).get("314954236") or {}
            pm25 = pur_st.get("aqi")
            if pm25 is not None:
                try:
                    pm_num = float(pm25)
                    if pm_num >= 35 and (now_ts - DISMISSED_INCIDENTS_CACHE.get("air_salon_pm25", 0) > 7200):
                        active.append({
                            "id": "air_salon_pm25",
                            "type": "air_pm25_high",
                            "category": "air",
                            "source": "Salón (Purificador)",
                            "severity": "critical" if pm_num >= 75 else "warning",
                            "title": f"Partículas PM2.5 altas en Salón ({int(pm_num)})",
                            "description": "Calidad del aire interior cargada. Conviene activar o subir el purificador Xiaomi.",
                            "value": f"{int(pm_num)} PM2.5",
                            "icon": "🌫️",
                            "timestamp": now_str,
                            "resolved": False
                        })
                except Exception:
                    pass

        # Polen exterior elevado (desde caché Open-Meteo si disponible)
        out_cache = globals().get("_outdoor_air_cache") or {}
        out_data = out_cache.get("data") or {}
        pollen_lvl = str(out_data.get("pollen_level") or "").lower()
        if any(w in pollen_lvl for w in ("alto", "muy alto", "elevado")):
            if now_ts - DISMISSED_INCIDENTS_CACHE.get("air_outdoor_pollen", 0) > 43200:
                active.append({
                    "id": "air_outdoor_pollen",
                    "type": "pollen_high",
                    "category": "air",
                    "source": "Exterior (29720)",
                    "severity": "warning",
                    "title": f"Nivel de polen {out_data.get('pollen_level')} en exterior",
                    "description": f"Concentración total de {out_data.get('pollen_total', '--')} gr/m³ en Rincón de la Victoria. Evita ventilar en horas punta si hay alergias.",
                    "value": f"{out_data.get('pollen_total', '--')} gr/m³",
                    "icon": "🌿",
                    "timestamp": now_str,
                    "resolved": False
                })
    except Exception:
        pass

    # 8. Confort interior: Humedad muy alta (>= 78%) o Temperatura extrema (< 15°C o > 29°C)
    try:
        for cid, cname in [
            ("bf9cba82aabe945f4fc8q9", "Salón"),
            ("bf2d1d67a6677da71c58y5", "Dormitorio"),
            ("bf3aa055b420138596m0cs", "Sótano"),
        ]:
            cst = states.get(cid) or {}
            hum = cst.get("humidity")
            temp = cst.get("temperature")
            if hum is not None:
                try:
                    h_num = float(hum)
                    inc_h = f"hum_high_{cid}"
                    if h_num >= 78 and (now_ts - DISMISSED_INCIDENTS_CACHE.get(inc_h, 0) > 21600):
                        active.append({
                            "id": inc_h,
                            "type": "humidity_high",
                            "category": "climate",
                            "source": cname,
                            "severity": "warning",
                            "title": f"Humedad elevada en {cname} ({int(h_num)}%)",
                            "description": f"Humedad superior al 78% en {cname}. Riesgo de condensación; conviene ventilar o deshumidificar.",
                            "value": f"{int(h_num)}%",
                            "icon": "💧",
                            "timestamp": now_str,
                            "resolved": False
                        })
                except Exception:
                    pass
            if temp is not None:
                try:
                    t_num = float(temp)
                    inc_t = f"temp_ext_{cid}"
                    if (t_num < 15.0 or t_num > 29.5) and (now_ts - DISMISSED_INCIDENTS_CACHE.get(inc_t, 0) > 21600):
                        active.append({
                            "id": inc_t,
                            "type": "temp_extreme",
                            "category": "climate",
                            "source": cname,
                            "severity": "warning",
                            "title": f"Temperatura extrema en {cname} ({t_num:.1f}°C)",
                            "description": f"La temperatura en {cname} está fuera del rango confortable (15–29,5 °C).",
                            "value": f"{t_num:.1f}°C",
                            "icon": "🌡️",
                            "timestamp": now_str,
                            "resolved": False
                        })
                except Exception:
                    pass
    except Exception:
        pass

    # 9. Energía & Seguridad Eléctrica: Sobrecarga Breaker Sótano, Termo/Secatoallas olvidados, Inversor Solar caliente
    try:
        brk_st = states.get("bf8572cd7ab61cd73dl1ln") or {}
        brk_w = float(brk_st.get("power") or brk_st.get("watts") or 0.0)
        if brk_w >= 2800 and (now_ts - DISMISSED_INCIDENTS_CACHE.get("energy_breaker_overload", 0) > 3600):
            active.append({
                "id": "energy_breaker_overload",
                "type": "high_load",
                "category": "grid",
                "source": "Breaker Sótano",
                "severity": "critical" if brk_w >= 3400 else "warning",
                "title": f"Consumo muy alto en Sótano ({int(brk_w)} W)",
                "description": "El disyuntor del sótano supera los 2800 W. Revisa si hay varios aparatos potentes a la vez.",
                "value": f"{int(brk_w)} W",
                "icon": "⚡",
                "timestamp": now_str,
                "resolved": False
            })

        # Termo (> 3.5h continuo) o Secatoallas (> 2.5h continuo) encendidos
        for dev_id, t_key, label, max_h in [
            ("bf75842d28c31e9943g0wz", "termo_on_since", "Termo Eléctrico", 3.5),
            ("1728645494b97e138251", "secatoallas_on_since", "Secatoallas", 2.5),
        ]:
            pst = states.get(dev_id) or {}
            if bool(pst.get("state", False)):
                if _INCIDENT_STATE_TRACKERS[t_key] is None:
                    _INCIDENT_STATE_TRACKERS[t_key] = now_ts
                hrs = (now_ts - _INCIDENT_STATE_TRACKERS[t_key]) / 3600.0
                inc_f = f"energy_forgotten_{dev_id}"
                if hrs >= max_h and (now_ts - DISMISSED_INCIDENTS_CACHE.get(inc_f, 0) > 7200):
                    active.append({
                        "id": inc_f,
                        "type": "appliance_long_on",
                        "category": "grid",
                        "source": label,
                        "severity": "warning",
                        "title": f"{label} encendido hace {hrs:.1f} h",
                        "description": f"Lleva más de {max_h} horas encendido de forma continua. Comprueba si fue un olvido.",
                        "value": f"{hrs:.1f} h",
                        "icon": "🔥",
                        "timestamp": now_str,
                        "resolved": False
                    })
            else:
                _INCIDENT_STATE_TRACKERS[t_key] = None

        # Temperatura alta en Microinversor Hoymiles (>= 65 °C)
        sol_f = Path("/tmp/domos_solar_status.json")
        if sol_f.exists():
            sd = json.loads(sol_f.read_text())
            inv_temp = float(sd.get("temperature_c") or 0.0)
            if inv_temp >= 65.0 and (now_ts - DISMISSED_INCIDENTS_CACHE.get("solar_inv_overheat", 0) > 14400):
                active.append({
                    "id": "solar_inv_overheat",
                    "type": "solar_overheat",
                    "category": "grid",
                    "source": "Inversor Hoymiles",
                    "severity": "critical" if inv_temp >= 75.0 else "warning",
                    "title": f"Inversor solar caliente ({inv_temp:.1f}°C)",
                    "description": "El microinversor Hoymiles alcanza temperatura elevada. El rendimiento puede reducirse por protección térmica.",
                    "value": f"{inv_temp:.1f}°C",
                    "icon": "☀️",
                    "timestamp": now_str,
                    "resolved": False
                })
    except Exception:
        pass

    # 10. Conectividad de equipos críticos de seguridad & Salud del sistema DOMOS (Disco / Backup)
    try:
        for cid, cname in [
            ("64326051e8db8480acc0", "Alarma Hogar"),
            ("bf77eed8534deaf66f2xpj", "Videoportero Exterior"),
            ("bf216abd6b1934fa11rl63", "Puerta Principal"),
            ("bf20349qicjyoh2g", "Cerradura"),
        ]:
            cst = states.get(cid)
            if isinstance(cst, dict) and cst.get("online") is False:
                inc_off = f"offline_{cid}"
                if now_ts - DISMISSED_INCIDENTS_CACHE.get(inc_off, 0) > 14400:
                    active.append({
                        "id": inc_off,
                        "type": "device_offline",
                        "category": "network",
                        "source": cname,
                        "severity": "warning",
                        "title": f"Dispositivo desconectado: {cname}",
                        "description": f"{cname} figura sin conexión en Tuya. Revisa su alimentación o señal Wi-Fi/Zigbee.",
                        "value": "Offline",
                        "icon": "📡",
                        "timestamp": now_str,
                        "resolved": False
                    })

        # Espacio en disco interno / SD (> 88%)
        for mount_p, label in [("/", "Disco interno DOMOS"), ("/media/storage", "Tarjeta SD")]:
            if Path(mount_p).exists():
                du = shutil.disk_usage(mount_p)
                used_pct = round((du.used / max(1, du.total)) * 100.0, 1)
                inc_d = f"disk_full_{label.replace(' ', '_')}"
                if used_pct >= 88.0 and (now_ts - DISMISSED_INCIDENTS_CACHE.get(inc_d, 0) > 43200):
                    active.append({
                        "id": inc_d,
                        "type": "disk_space",
                        "category": "system",
                        "source": label,
                        "severity": "critical" if used_pct >= 95.0 else "warning",
                        "title": f"Poco espacio libre en {label} ({used_pct}%)",
                        "description": f"Quedan {round(du.free / (1024**3), 1)} GB libres en {mount_p}.",
                        "value": f"{used_pct}%",
                        "icon": "💽",
                        "timestamp": now_str,
                        "resolved": False
                    })

        # Backup atrasado (> 36 horas sin copia)
        b_status = Path("/opt/domoskiosk/backups/backup_status.json")
        if b_status.exists():
            age_h = (now_ts - b_status.stat().st_mtime) / 3600.0
            if age_h > 36.0 and (now_ts - DISMISSED_INCIDENTS_CACHE.get("system_backup_overdue", 0) > 43200):
                active.append({
                    "id": "system_backup_overdue",
                    "type": "backup_overdue",
                    "category": "system",
                    "source": "Backups DOMOS",
                    "severity": "warning",
                    "title": f"Copia de seguridad atrasada ({int(age_h)} h)",
                    "description": "Han pasado más de 36 horas desde el último backup automático. Puedes lanzar uno desde Ajustes → Backup.",
                    "value": f"{int(age_h)} h",
                    "icon": "💾",
                    "timestamp": now_str,
                    "resolved": False
                })
    except Exception:
        pass

    # 11. Hallazgos críticos del último informe de Doctor DOMOS
    try:
        doc_f = Path("/opt/domoskiosk/doctor_report.json")
        if doc_f.exists():
            drep = json.loads(doc_f.read_text())
            for idx, f in enumerate(drep.get("findings") or []):
                if f.get("severity") == "critical":
                    inc_doc = f"doctor_crit_{f.get('area', idx)}"
                    if now_ts - DISMISSED_INCIDENTS_CACHE.get(inc_doc, 0) > 21600:
                        if not any(a.get("title") == f.get("title") for a in active):
                            active.append({
                                "id": inc_doc,
                                "type": "doctor_finding",
                                "category": "system",
                                "source": f"Doctor DOMOS ({f.get('area', 'Sistema')})",
                                "severity": "critical",
                                "title": f"🩺 {f.get('title', 'Hallazgo crítico')}",
                                "description": f.get("detail", "Detectado en el diagnóstico automático."),
                                "value": f"Salud {drep.get('health_score', '--')}/100",
                                "icon": "🩺",
                                "timestamp": drep.get("timestamp", now_str),
                                "resolved": False,
                            })
    except Exception:
        pass

    # Ordenar por severidad: critical primero, luego warning, luego info
    sev_order = {"critical": 0, "warning": 1, "info": 2}
    active.sort(key=lambda x: sev_order.get(x.get("severity", "warning"), 1))
    return active

@app.get("/api/incidents")
async def get_incidents():
    active = compute_system_incidents()
    history = []
    if INCIDENTS_FILE.exists():
        try:
            history = json.loads(INCIDENTS_FILE.read_text())
        except Exception:
            pass
    return {
        "count": len(active),
        "has_critical": any(i.get("severity") == "critical" for i in active),
        "incidents": active,
        "history": history[:30]
    }

@app.post("/api/incidents/log")
async def log_incident(request: Request):
    data = await request.json()
    incidents = []
    if INCIDENTS_FILE.exists():
        try:
            incidents = json.loads(INCIDENTS_FILE.read_text())
        except Exception:
            pass
            
    new_inc = {
        "id": f"inc_{int(time.time())}",
        "timestamp": datetime.datetime.now().isoformat(),
        "source": data.get("source", "Sistema"),
        "severity": data.get("severity", "warning"),
        "title": data.get("title", "Incidencia detectada"),
        "description": data.get("description", ""),
        "resolved": False
    }
    incidents.insert(0, new_inc)
    incidents = incidents[:50]
    INCIDENTS_FILE.write_text(json.dumps(incidents, indent=2))
    
    payload = json.dumps({"type": "INCIDENTS_UPDATED", "count": len(compute_system_incidents()), "incidents": compute_system_incidents()})
    for ws in list(ACTIVE_SOCKETS):
        try:
            await ws.send_text(payload)
        except Exception:
            pass
            
    return {"status": "logged", "incident": new_inc}

@app.post("/api/incidents/resolve")
async def resolve_incident(request: Request):
    data = await request.json()
    inc_id = data.get("id")
    if inc_id:
        DISMISSED_INCIDENTS_CACHE[inc_id] = time.time()
    else:
        for inc in compute_system_incidents():
            DISMISSED_INCIDENTS_CACHE[inc.get("id")] = time.time()

    if INCIDENTS_FILE.exists():
        try:
            incidents = json.loads(INCIDENTS_FILE.read_text())
            for inc in incidents:
                if inc.get("id") == inc_id or not inc_id:
                    inc["resolved"] = True
            INCIDENTS_FILE.write_text(json.dumps(incidents, indent=2))
        except Exception as e:
            pass

    active = compute_system_incidents()
    payload = json.dumps({"type": "INCIDENTS_UPDATED", "count": len(active), "incidents": active})
    for ws in list(ACTIVE_SOCKETS):
        try:
            await ws.send_text(payload)
        except Exception:
            pass

    return {"status": "resolved", "count": len(active), "incidents": active}

_ics_cache = {"ts": 0.0, "events": []}

def _parse_ics_events(ics_text: str, source_name: str = "ICS"):
    import re
    # Unfold folded lines (CRLF/LF followed by space or tab)
    unfolded = re.sub(r"\r?\n[ \t]", "", ics_text or "")
    events = []
    in_ev = False
    cur = {}
    for line in unfolded.splitlines():
        line = line.strip()
        if line == "BEGIN:VEVENT":
            in_ev = True
            cur = {}
            continue
        if line == "END:VEVENT":
            in_ev = False
            dt_raw = cur.get("DTSTART", "")
            m = re.match(r"^(\d{4})(\d{2})(\d{2})(?:T(\d{2})(\d{2}))?", dt_raw)
            if m and cur.get("SUMMARY"):
                date_str = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
                time_str = f"{m.group(4)}:{m.group(5)}" if m.group(4) and m.group(5) else ""
                summary = cur["SUMMARY"].replace("\\,", ",").replace("\\n", " ").replace("\\;", ";")
                uid = cur.get("UID", f"{date_str}_{summary[:16]}")
                events.append({
                    "id": f"ics_{abs(hash(uid))}",
                    "title": summary,
                    "date": date_str,
                    "type": "ics",
                    "source": source_name,
                    "reminder_time": time_str,
                })
            continue
        if in_ev and ":" in line:
            k_part, val = line.split(":", 1)
            k = k_part.split(";", 1)[0].upper()
            if k in ("DTSTART", "SUMMARY", "UID", "DESCRIPTION"):
                cur[k] = val
    return events

def _fetch_ics_events_sync(force: bool = False):
    import urllib.request
    now = time.time()
    if not force and (now - _ics_cache["ts"]) < 300:
        return _ics_cache["events"]
    cfg = get_kiosk_config()
    sources = cfg.get("calendar_ics_urls") or []
    all_ev = []
    for src in sources:
        url = (src.get("url") or "").strip() if isinstance(src, dict) else ""
        name = (src.get("name") or "Calendario").strip() if isinstance(src, dict) else "Calendario"
        if not url:
            continue
        if url.startswith("webcal://"):
            url = "https://" + url[len("webcal://"):]
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "DomosKiosk/1.0"})
            with urllib.request.urlopen(req, timeout=6) as resp:
                txt = resp.read().decode("utf-8", errors="ignore")
                all_ev.extend(_parse_ics_events(txt, name))
        except Exception as e:
            print(f"[Calendar] ICS fetch error ({name}): {e}", flush=True)
    _ics_cache["ts"] = now
    _ics_cache["events"] = all_ev
    return all_ev

def _load_local_calendar():
    if CALENDAR_FILE.exists():
        try:
            evs = json.loads(CALENDAR_FILE.read_text())
            if isinstance(evs, list):
                today_iso = datetime.date.today().isoformat()
                cur_year = datetime.date.today().year
                for e in evs:
                    e.setdefault("source", "Domos")
                    if e.get("repeat") == "yearly" and isinstance(e.get("date"), str) and len(e["date"]) >= 10:
                        mmdd = e["date"][5:10]
                        cand = f"{cur_year}-{mmdd}"
                        if cand < today_iso:
                            cand = f"{cur_year + 1}-{mmdd}"
                        e["date"] = cand
                return evs
        except Exception:
            pass
    return []

@app.get("/api/calendar")
async def get_calendar():
    local_evs = _load_local_calendar()
    ics_evs = await asyncio.to_thread(_fetch_ics_events_sync, False)
    merged = local_evs + ics_evs
    merged.sort(key=lambda x: (x.get("date", ""), x.get("reminder_time", "")))
    return merged

@app.post("/api/calendar")
async def add_calendar_event(request: Request):
    data = await request.json()
    events = _load_local_calendar()
    event = {
        "id": f"cal_{int(time.time() * 1000)}",
        "title": data.get("title", "Nuevo Recordatorio"),
        "date": data.get("date", ""),
        "type": data.get("type", "event"),
        "source": "Domos",
        "reminder_time": data.get("reminder_time", "09:00")
    }
    events.append(event)
    CALENDAR_FILE.write_text(json.dumps(events, indent=2, ensure_ascii=False))
    return {"status": "added", "event": event}

@app.delete("/api/calendar/{event_id}")
async def delete_calendar_event(event_id: str):
    events = _load_local_calendar()
    new_events = [e for e in events if e.get("id") != event_id]
    CALENDAR_FILE.write_text(json.dumps(new_events, indent=2, ensure_ascii=False))
    return {"status": "deleted", "id": event_id}

@app.get("/api/calendar/sources")
async def get_calendar_sources():
    cfg = get_kiosk_config()
    return {"sources": cfg.get("calendar_ics_urls") or []}

@app.post("/api/calendar/sources")
async def save_calendar_sources(request: Request):
    data = await request.json()
    sources = data.get("sources")
    if not isinstance(sources, list):
        return JSONResponse({"error": "sources list required"}, status_code=400)
    save_kiosk_config({"calendar_ics_urls": sources})
    _ics_cache["ts"] = 0.0
    events = await get_calendar()
    return {"status": "updated", "sources": sources, "events": events}

_last_screen_cache = None
_last_screen_time = 0.0

@app.get("/api/screen/live.png")
async def live_screen():
    global _last_screen_cache, _last_screen_time
    now = time.time()
    # Cache for 350ms to prevent multiple concurrent grim forks from thrashing
    if _last_screen_cache and (now - _last_screen_time) < 0.35:
        return Response(content=_last_screen_cache, media_type="image/png")

    env = os.environ.copy()
    env["WAYLAND_DISPLAY"] = "wayland-0"
    env["XDG_RUNTIME_DIR"] = "/run/user/1000"
    try:
        proc = await asyncio.create_subprocess_exec(
            "grim", "-",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
            env=env
        )
        stdout, _ = await proc.communicate()
        if stdout and stdout.startswith(b"\x89PNG"):
            _last_screen_cache = stdout
            _last_screen_time = now
            return Response(content=stdout, media_type="image/png")
    except Exception as e:
        print("[SCREEN_CAPTURE_ERR]", e)

    if _last_screen_cache:
        return Response(content=_last_screen_cache, media_type="image/png")
    return JSONResponse({"error": "Failed to capture"}, status_code=500)

from evdev import UInput, AbsInfo, ecodes as _e

VIRTUAL_TOUCH = None

@app.post("/api/debug_log")
async def debug_log(request: Request):
    data = await request.json()
    print("[CLIENT_DEBUG]", data, flush=True)
    return {"ok": True}


SCHEDULES_FILE = Path("/opt/domoskiosk/schedules.json")

def _load_schedules_sync() -> list:
    if not SCHEDULES_FILE.exists():
        default_schedules = [
            {
                "id": "sch_termo_eco",
                "name": "Termo (Aprovechamiento Solar)",
                "device_id": "bf75842d28c31e9943g0wz",
                "device_name": "Termo",
                "code": "switch_1",
                "action": "on",
                "time": "13:00",
                "days": [1, 2, 3, 4, 5, 6, 7],
                "enabled": True
            },
            {
                "id": "sch_termo_off",
                "name": "Apagado Termo",
                "device_id": "bf75842d28c31e9943g0wz",
                "device_name": "Termo",
                "code": "switch_1",
                "action": "off",
                "time": "16:00",
                "days": [1, 2, 3, 4, 5, 6, 7],
                "enabled": True
            }
        ]
        try:
            SCHEDULES_FILE.write_text(json.dumps(default_schedules, indent=2))
            return default_schedules
        except Exception:
            return []
    try:
        return json.loads(SCHEDULES_FILE.read_text())
    except Exception:
        return []

def _save_schedules_sync(data: list):
    try:
        SCHEDULES_FILE.write_text(json.dumps(data, indent=2))
    except Exception as e:
        print(f"[SAVE_SCHEDULES_ERR] {e}", flush=True)

_last_power_cache = {}
_last_power_cache_time = 0.0

def _get_monitored_devices_power_sync():
    global _last_power_cache, _last_power_cache_time
    now = time.time()
    if _last_power_cache and (now - _last_power_cache_time) < 5.0:
        return _last_power_cache

    devs_file = Path("/opt/domoskiosk/devices.json")
    if not devs_file.exists():
        return {"devices": [], "total_consumption_watts": 0, "net_balance_watts": 0}

    try:
        devs = json.loads(devs_file.read_text())
    except Exception:
        return {"devices": [], "total_consumption_watts": 0, "net_balance_watts": 0}

    import tinytuya
    monitored_ids = ["bf2989a92a26b9381drtlg", "bf75842d28c31e9943g0wz", "1728645494b97e138251", "bf8572cd7ab61cd73dl1ln", "bfe3804040d12a2822hzmp"]
    items = []
    tot_watts = 0.0

    for did in monitored_ids:
        dev = devs.get(did)
        if not dev or not dev.get("ip"):
            continue
        friendly_name = dev.get("name", "Enchufe")
        if did == "bf2989a92a26b9381drtlg":
            friendly_name = "Cargador Domos (Asus)"
        try:
            d = tinytuya.OutletDevice(dev["id"], dev["ip"], dev["key"])
            d.set_version(float(dev.get("version", 3.3)))
            d.set_socketPersistent(False)
            d.set_socketTimeout(0.8)
            st = d.status()
            dps = st.get("dps", {})
            p_val = round(dps.get("19", 0) / 10.0, 1)
            v_val = round(dps.get("20", 0) / 10.0, 1)
            i_val = round(dps.get("18", 0) / 1000.0, 3)
            is_on = bool(dps.get("1", False))
            if is_on:
                tot_watts += p_val
            items.append({
                "id": did,
                "name": friendly_name,
                "watts": p_val,
                "volts": v_val,
                "amps": i_val,
                "on": is_on
            })
        except Exception as ex:
            items.append({
                "id": did,
                "name": friendly_name,
                "watts": 0.0,
                "volts": 230.0,
                "amps": 0.0,
                "on": False,
                "error": str(ex)
            })

    solar_watts = 0.0
    solar_f = Path("/tmp/domos_solar_status.json")
    has_meter = False
    home_consumption = tot_watts
    net_balance = 0.0
    grid_watts = 0.0

    if solar_f.exists():
        try:
            s_data = json.loads(solar_f.read_text())
            solar_watts = float(s_data.get("watts", 0.0))
            meter_online = bool(s_data.get("meter_online", False))
            meter_load = float(s_data.get("home_consumption_w", 0.0))
            if meter_online and meter_load > 0:
                has_meter = True
                home_consumption = meter_load
                net_balance = round(solar_watts - home_consumption, 1)
                grid_watts = float(s_data.get("grid_watts", -net_balance))
            else:
                has_meter = False
                home_consumption = tot_watts
                net_balance = round(solar_watts - tot_watts, 1)
                grid_watts = round(-net_balance, 1)
        except Exception:
            pass

    result = {
        "devices": items,
        "total_consumption_watts": round(home_consumption, 1),
        "solar_generation_watts": round(solar_watts, 1),
        "net_balance_watts": round(net_balance, 1),
        "has_meter": has_meter,
        "grid_watts": round(grid_watts, 1),
        "updated_at": datetime.datetime.now().strftime("%H:%M:%S")
    }
    _last_power_cache = result
    _last_power_cache_time = now
    return result





# =========================================================
# GOOGLE CAST SPEAKERS (Salita, Dormitorio 1, Sótano)
# =========================================================

# =========================================================
# DOCTOR DOMOS (Hybrid Nightly Auditor + Safe Self-Healer + Gemini AI)
# =========================================================
@app.get("/api/doctor/report")
async def api_doctor_report():
    return await asyncio.to_thread(doctor_domos.get_latest_report)

@app.post("/api/doctor/run")
async def api_doctor_run():
    rep = await asyncio.to_thread(doctor_domos.run_diagnosis, "manual")
    cfg = doctor_domos.load_config()
    return {
        "report": rep,
        "config": {
            "auto_heal_enabled": bool(cfg.get("auto_heal_enabled", True)),
            "gemini_model": cfg.get("gemini_model", "gemini-3.8-flash"),
            "has_api_key": bool((cfg.get("gemini_api_key") or "").strip()),
            "nightly_time": cfg.get("nightly_time", "03:30"),
        },
    }

_doctor_tts_procs = []
_doctor_tts_lock = threading.Lock()

def _stop_doctor_tts():
    global _doctor_tts_procs
    with _doctor_tts_lock:
        for p in _doctor_tts_procs:
            try:
                if p.poll() is None:
                    p.terminate()
                    try:
                        p.wait(timeout=0.8)
                    except Exception:
                        p.kill()
            except Exception:
                pass
        _doctor_tts_procs = []

def _clean_text_for_spanish_tts(raw: str) -> str:
    import re
    t = str(raw or "")
    t = re.sub(r"\*\*(.+?)\*\*", r"\1", t)
    t = t.replace("*", "").replace("#", "").replace("`", "")
    t = t.replace("°C", " grados").replace("%", " por ciento").replace("·", ",")
    t = re.sub(r"(\d)\s*W\b", r"\1 vatios", t)
    t = re.sub(r"(\d)\s*kWh\b", r"\1 kilovatios hora", t)
    t = re.sub(r"(\d)\s*MB\b", r"\1 megas", t)
    t = re.sub(r"\bPM2\.5\b", "P M dos punto cinco", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t

async def _broadcast_ws_json(obj: dict):
    payload = json.dumps(obj)
    for ws in list(ACTIVE_SOCKETS):
        try:
            await ws.send_text(payload)
        except Exception:
            pass

async def _watch_doctor_tts(play_proc, piper_proc):
    try:
        while play_proc.poll() is None:
            await asyncio.sleep(0.4)
    except Exception:
        pass
    finally:
        with _doctor_tts_lock:
            global _doctor_tts_procs
            if play_proc in _doctor_tts_procs:
                _doctor_tts_procs = []
        try:
            if piper_proc.poll() is None:
                piper_proc.terminate()
        except Exception:
            pass
        await _broadcast_ws_json({"type": "ASSISTANT_STATE", "state": "idle", "prompt": "", "reply": ""})
        await _broadcast_ws_json({"type": "DOCTOR_SPEAK_STATE", "speaking": False})

@app.post("/api/doctor/speak")
async def api_doctor_speak():
    global _doctor_tts_procs
    _stop_doctor_tts()
    data = await asyncio.to_thread(doctor_domos.get_latest_report)
    rep = data.get("report") or {}
    raw_txt = (rep.get("ai") or {}).get("text") or ""
    if not raw_txt:
        return {"success": False, "error": "No hay diagnóstico disponible."}
    spoken = _clean_text_for_spanish_tts(raw_txt)
    await _broadcast_ws_json({"type": "ASSISTANT_STATE", "state": "speaking", "prompt": "🩺 Doctor DOMOS", "reply": "Leyendo el diagnóstico del sistema..."})
    await _broadcast_ws_json({"type": "DOCTOR_SPEAK_STATE", "speaking": True})
    try:
        env = dict(os.environ)
        env["XDG_RUNTIME_DIR"] = "/run/user/1000"
        piper_proc = subprocess.Popen(
            [cast_service.PIPER_BIN, "--model", cast_service.PIPER_MODEL, "--length_scale", "1.05", "--output-raw"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            env=env,
        )
        play_proc = subprocess.Popen(
            ["paplay", "--raw", "--rate=22050", "--format=s16le", "--channels=1"],
            stdin=piper_proc.stdout,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=env,
        )
        piper_proc.stdout.close()
        with _doctor_tts_lock:
            _doctor_tts_procs = [piper_proc, play_proc]
        def _feed_stdin():
            try:
                piper_proc.stdin.write((spoken + "\n").encode("utf-8"))
                piper_proc.stdin.close()
            except Exception:
                pass
        threading.Thread(target=_feed_stdin, daemon=True).start()
        asyncio.create_task(_watch_doctor_tts(play_proc, piper_proc))
        return {"success": True, "speaking": True, "streaming": True}
    except Exception as e:
        await _broadcast_ws_json({"type": "ASSISTANT_STATE", "state": "idle", "prompt": "", "reply": ""})
        await _broadcast_ws_json({"type": "DOCTOR_SPEAK_STATE", "speaking": False})
        return {"success": False, "error": str(e)}

@app.post("/api/doctor/speak/stop")
async def api_doctor_speak_stop():
    _stop_doctor_tts()
    await _broadcast_ws_json({"type": "ASSISTANT_STATE", "state": "idle", "prompt": "", "reply": ""})
    await _broadcast_ws_json({"type": "DOCTOR_SPEAK_STATE", "speaking": False})
    return {"success": True, "speaking": False}

@app.post("/api/doctor/config")
async def api_doctor_config(request: Request):
    data = await request.json()
    cfg = doctor_domos.save_config(data)
    return {
        "success": True,
        "config": {
            "auto_heal_enabled": bool(cfg.get("auto_heal_enabled", True)),
            "gemini_model": cfg.get("gemini_model", "gemini-3.8-flash"),
            "has_api_key": bool((cfg.get("gemini_api_key") or "").strip()),
            "nightly_time": cfg.get("nightly_time", "03:30"),
        },
    }

@app.get("/api/cast/speakers")
async def api_cast_speakers():
    return cast_service.service.get_speakers()

@app.post("/api/cast/discover")
async def api_cast_discover():
    return await asyncio.to_thread(cast_service.service.refresh_discovery, 5.0)

@app.post("/api/cast/config")
async def api_cast_config(request: Request):
    data = await request.json()
    return cast_service.service.update_config(data)

@app.post("/api/cast/announce")
async def api_cast_announce(request: Request):
    data = await request.json()
    targets = data.get("targets", "all")
    text = str(data.get("text") or "").strip()
    if not text:
        return JSONResponse({"error": "text is required"}, status_code=400)
    return await asyncio.to_thread(cast_service.service.announce, targets, text)

@app.post("/api/cast/play")
async def api_cast_play(request: Request):
    data = await request.json()
    targets = data.get("targets", "all")
    url = str(data.get("url") or "").strip()
    title = str(data.get("title") or "DOMOS Radio")
    if not url:
        return JSONResponse({"error": "url is required"}, status_code=400)
    return await asyncio.to_thread(cast_service.service.play_url, targets, url, title)

@app.post("/api/cast/stop")
async def api_cast_stop(request: Request):
    data = {}
    try:
        data = await request.json()
    except Exception:
        pass
    targets = data.get("targets", "all")
    return await asyncio.to_thread(cast_service.service.stop, targets)

@app.get("/api/cast/media/{filename}")
async def api_cast_media(filename: str):
    if "/" in filename or ".." in filename:
        return JSONResponse({"error": "Invalid filename"}, status_code=400)
    if filename == "doorbell_chime.wav":
        target = Path("/opt/domoskiosk/doorbell_chime.wav")
    else:
        target = cast_service.CAST_MEDIA_DIR / filename
    if not target.exists():
        return JSONResponse({"error": "File not found"}, status_code=404)
    return FileResponse(str(target), media_type="audio/wav")

@app.get("/api/system/backups")
async def api_list_backups():
    return backup_domos.list_backups()

@app.post("/api/system/backup")
async def api_create_backup():
    res = await asyncio.to_thread(backup_domos.create_backup, "manual")
    listing = backup_domos.list_backups()
    return {"created": res, **listing}

@app.get("/api/system/backup/download/{filename}")
async def api_download_backup(filename: str):
    if "/" in filename or ".." in filename or not filename.startswith("domos_backup_") or not filename.endswith(".tar.gz"):
        return JSONResponse({"error": "Invalid filename"}, status_code=400)
    target = backup_domos.LOCAL_BACKUP_DIR / filename
    if not target.exists():
        return JSONResponse({"error": "Backup not found"}, status_code=404)
    return FileResponse(str(target), media_type="application/gzip", filename=filename)

@app.get("/api/energy/savings")
async def api_get_energy_savings():
    return energy_savings.engine.evaluate(tuya_service.service, execute_commands=False)

@app.post("/api/energy/savings/config")
async def api_save_energy_savings_config(request: Request):
    data = await request.json()
    energy_savings.engine.update_config(data)
    res = energy_savings.engine.evaluate(tuya_service.service, execute_commands=False)
    payload = json.dumps({"type": "ENERGY_SAVINGS_UPDATED", "data": res})
    for ws in list(ACTIVE_SOCKETS):
        try:
            await ws.send_text(payload)
        except Exception:
            pass
    return {"success": True, **res}

@app.post("/api/energy/savings/mode")
async def api_set_energy_savings_mode(request: Request):
    data = await request.json()
    mode = str(data.get("mode") or "auto")
    energy_savings.engine.set_mode(mode)
    res = energy_savings.engine.evaluate(tuya_service.service, execute_commands=True)
    payload = json.dumps({"type": "ENERGY_SAVINGS_UPDATED", "data": res})
    for ws in list(ACTIVE_SOCKETS):
        try:
            await ws.send_text(payload)
        except Exception:
            pass
    return {"success": True, **res}

async def energy_savings_background_loop():
    await asyncio.sleep(12.0)
    print("[ENERGY_SAVINGS] Background smart autoconsumo loop started (every 30s)", flush=True)
    while True:
        try:
            res = await asyncio.to_thread(energy_savings.engine.evaluate, tuya_service.service, True)
            payload = json.dumps({"type": "ENERGY_SAVINGS_UPDATED", "data": res})
            for ws in list(ACTIVE_SOCKETS):
                try:
                    await ws.send_text(payload)
                except Exception:
                    pass
        except Exception as e:
            print(f"[ENERGY_SAVINGS] Loop error: {e}", flush=True)
        await asyncio.sleep(30.0)

@app.on_event("startup")
async def start_energy_savings_loop():
    asyncio.create_task(energy_savings_background_loop())

@app.get("/api/solar/details")
async def get_solar_details():
    summary = _all_devices_payload()
    solar = summary.get("solar") or {}
    battery = summary.get("battery") or {}
    extra = {}
    solar_f = Path("/tmp/domos_solar_status.json")
    if solar_f.exists():
        try:
            s_data = json.loads(solar_f.read_text())
            extra = {
                "inverter_sn": s_data.get("inverter_sn", "1164749041"),
                "dtu_sn": s_data.get("dtu_sn", "10FD74438586"),
                "temperature": s_data.get("temperature_c"),
                "frequency": s_data.get("frequency"),
                "port1_watts": s_data.get("port1", {}).get("watts"),
                "port1_volts": s_data.get("port1", {}).get("volts"),
                "port1_amps": s_data.get("port1", {}).get("amps"),
                "port2_watts": s_data.get("port2", {}).get("watts"),
                "port2_volts": s_data.get("port2", {}).get("volts"),
                "port2_amps": s_data.get("port2", {}).get("amps"),
                "port3_watts": s_data.get("port3", {}).get("watts"),
                "port3_volts": s_data.get("port3", {}).get("volts"),
                "port3_amps": s_data.get("port3", {}).get("amps"),
                "port4_watts": s_data.get("port4", {}).get("watts"),
                "port4_volts": s_data.get("port4", {}).get("volts"),
                "port4_amps": s_data.get("port4", {}).get("amps"),
                "total_forward_energy": int(s_data.get("daily_kwh", 0) * 100),
                "fault": 0,
                "breaker_number": f"HMS {s_data.get('inverter_sn', '')}",
                "switch": True,
                "last_update": s_data.get("timestamp")
            }
        except Exception as e:
            extra["error"] = str(e)
    
    power_data = await asyncio.to_thread(_get_monitored_devices_power_sync)
    return {"solar": solar, "battery": battery, "extra": extra, "power": power_data}

@app.get("/api/schedules")
async def api_get_schedules():
    return await asyncio.to_thread(_load_schedules_sync)

@app.post("/api/schedules")
async def api_save_schedule(request: Request):
    item = await request.json()
    schedules = await asyncio.to_thread(_load_schedules_sync)
    s_id = item.get("id") or f"sch_{int(time.time()*1000)}"
    item["id"] = s_id
    if "enabled" not in item:
        item["enabled"] = True
    
    idx = next((i for i, s in enumerate(schedules) if s.get("id") == s_id), -1)
    if idx >= 0:
        schedules[idx] = item
    else:
        schedules.append(item)
    
    await asyncio.to_thread(_save_schedules_sync, schedules)
    return {"success": True, "schedule": item}

@app.delete("/api/schedules/{schedule_id}")
async def api_delete_schedule(schedule_id: str):
    schedules = await asyncio.to_thread(_load_schedules_sync)
    schedules = [s for s in schedules if s.get("id") != schedule_id]
    await asyncio.to_thread(_save_schedules_sync, schedules)
    return {"success": True}

@app.post("/api/schedules/{schedule_id}/toggle")
async def api_toggle_schedule(schedule_id: str):
    schedules = await asyncio.to_thread(_load_schedules_sync)
    found = None
    for s in schedules:
        if s.get("id") == schedule_id:
            s["enabled"] = not s.get("enabled", True)
            found = s
            break
    if found:
        await asyncio.to_thread(_save_schedules_sync, schedules)
        return {"success": True, "schedule": found}
    return JSONResponse({"error": "Schedule not found"}, status_code=404)

@app.post("/api/devices/countdown")
async def api_device_countdown(request: Request):
    data = await request.json()
    dev_id = data.get("device_id")
    minutes = int(data.get("minutes", 30))
    action = data.get("action", "off")
    code = data.get("code", "switch_1")

    devs_file = Path("/opt/domoskiosk/devices.json")
    devs = {}
    if devs_file.exists():
        try:
            devs = json.loads(devs_file.read_text())
        except Exception:
            pass
    dev = devs.get(dev_id, {})

    success = False
    details = ""
    if dev and dev.get("ip") and dev.get("key"):
        try:
            import tinytuya
            d = tinytuya.OutletDevice(dev["id"], dev["ip"], dev["key"])
            d.set_version(float(dev.get("version", 3.3)))
            d.set_socketPersistent(False)
            d.set_socketTimeout(2.0)
            sec = minutes * 60
            d.set_value(9, sec)
            success = True
            details = f"Temporizador hardware fijado a {minutes} min ({sec}s) en {dev.get('name')}"
        except Exception as e:
            details = f"Fallo hardware ({e}), programando en servidor..."

    if not success:
        async def _run_timer():
            await asyncio.sleep(minutes * 60)
            val = False if action == "off" else True
            try:
                if ewelink_service.service.has_device(dev_id):
                    await asyncio.to_thread(ewelink_service.service.send_command, dev_id, val)
                else:
                    await asyncio.to_thread(tuya_service.service.send_command, dev_id, code, val)
            except Exception as e:
                print(f"[COUNTDOWN_EXEC_ERR] {e}", flush=True)
        asyncio.create_task(_run_timer())
        success = True
        details = f"Temporizador programado para {minutes} min"

    return {"success": success, "message": details}

@app.get("/api/cameras")
async def get_cameras():
    summary = _all_devices_payload()
    return summary.get("cameras", [])

def _go2rtc_register_sync(camera_id: str, rtsp_url: str):
    # Delete first to ensure any expired or stuck RTSP producer is evicted
    try:
        del_req = urllib.request.Request(f"http://127.0.0.1:1984/api/streams?src={urllib.parse.quote(camera_id)}", method="DELETE")
        with urllib.request.urlopen(del_req, timeout=2):
            pass
    except Exception:
        pass

    qs = urllib.parse.urlencode({"name": camera_id, "src": rtsp_url})
    req = urllib.request.Request(f"http://127.0.0.1:1984/api/streams?{qs}", method="PUT")
    with urllib.request.urlopen(req, timeout=5) as r:
        return r.status in (200, 201)

def _go2rtc_webrtc_sync(src: str, offer_sdp: bytes, content_type: str):
    qs = urllib.parse.urlencode({"src": src})
    req = urllib.request.Request(
        f"http://127.0.0.1:1984/api/webrtc?{qs}",
        data=offer_sdp,
        headers={"Content-Type": content_type or "application/sdp"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            return r.status, r.read(), r.headers.get("Content-Type", "application/sdp")
    except urllib.error.HTTPError as e:
        err_body = e.read() if hasattr(e, "read") else str(e).encode()
        return e.code, err_body, "text/plain"

async def allocate_low_latency_stream(camera_id: str, force_hls: bool = False):
    if not force_hls:
        try:
            rtsp_res = await asyncio.to_thread(tuya_service.service.get_camera_stream_url, camera_id, "RTSP")
            if rtsp_res.get("success") and rtsp_res.get("url"):
                ok = await asyncio.to_thread(_go2rtc_register_sync, camera_id, rtsp_res["url"])
                if ok:
                    return {
                        "success": True,
                        "mode": "webrtc",
                        "webrtc_url": f"/api/go2rtc/webrtc?src={urllib.parse.quote(camera_id)}",
                        "stream_name": camera_id,
                    }
        except Exception as e:
            print(f"[GO2RTC_REG_ERR] {camera_id}: {e}", flush=True)

    hls_res = await asyncio.to_thread(tuya_service.service.get_camera_stream_url, camera_id, "HLS")
    if hls_res.get("success"):
        hls_res["mode"] = "hls"
    return hls_res

@app.get("/api/camera/stream/{camera_id}")
async def get_camera_stream(camera_id: str, force_hls: int = 0):
    return await allocate_low_latency_stream(camera_id, force_hls=bool(force_hls))

@app.post("/api/go2rtc/webrtc")
async def proxy_go2rtc_webrtc(request: Request):
    src = request.query_params.get("src", "")
    if not src:
        return Response(content="Missing src", status_code=400)
    body = await request.body()
    ctype = request.headers.get("content-type", "application/sdp")
    try:
        status, ans, resp_ctype = await asyncio.to_thread(_go2rtc_webrtc_sync, src, body, ctype)
        return Response(content=ans, status_code=status, media_type=resp_ctype)
    except Exception as e:
        print(f"[GO2RTC_WEBRTC_ERR] {src}: {e}", flush=True)
        return Response(content=str(e), status_code=502)

@app.post("/api/devices/sync")
async def sync_devices():
    count = tuya_service.service.sync_cloud_devices()
    summary = _all_devices_payload()
    payload = json.dumps({"type": "DEVICE_UPDATE", "devices": summary})
    for ws in list(ACTIVE_SOCKETS):
        try:
            await ws.send_text(payload)
        except Exception:
            pass
    return {"status": "synced", "total_devices": count}

def _all_devices_payload():
    d = tuya_service.service.get_structured_devices()
    d["xiaomi"] = xiaomi_service.service.get_devices()
    ew_lights, ew_plugs = ewelink_service.service.get_structured_devices()
    d["lights"] = list(d.get("lights", [])) + ew_lights
    d["plugs"] = list(d.get("plugs", [])) + ew_plugs
    d["total_devices"] = d.get("total_devices", 0) + len(ew_lights) + len(ew_plugs)

    # Hoymiles Real-Time Local Telemetry Override
    solar_f = Path("/tmp/domos_solar_status.json")
    if solar_f.exists():
        try:
            s_data = json.loads(solar_f.read_text())
            d["solar"] = {
                "id": "bfe037c461c9c61da3pesr",
                "name": "Paneles Solares Hoymiles",
                "category": "solar",
                "icon": "solar_power",
                "type": "energy",
                "online": bool(s_data.get("online", True)),
                "state": {
                    "switch": bool(s_data.get("switch_on", True)),
                    "watts": s_data.get("watts", 0),
                    "volts": s_data.get("volts", 230),
                    "amps": s_data.get("amps", 0),
                    "frequency": s_data.get("frequency", 50.0),
                    "temperature": s_data.get("temperature_c", 0),
                    "port1": s_data.get("port1", {}),
                    "port2": s_data.get("port2", {}),
                    "port3": s_data.get("port3", {}),
                    "port4": s_data.get("port4", {}),
                    "daily_kwh": s_data.get("daily_kwh", 0),
                    "inverter_sn": s_data.get("inverter_sn", ""),
                    "dtu_sn": s_data.get("dtu_sn", ""),
                    "has_meter": bool(s_data.get("has_meter", False)) and bool(s_data.get("meter_online", False)),
                    "meter_online": bool(s_data.get("meter_online", False)),
                    "grid_watts": float(s_data.get("grid_watts", 0.0)),
                    "home_consumption_w": float(s_data.get("home_consumption_w", 0.0)),
                    "net_surplus_w": float(s_data.get("net_surplus_w", 0.0)),
                    "updated_at": s_data.get("timestamp", "")
                }
            }
        except Exception:
            pass
    return d

@app.get("/api/devices")
async def get_all_devices():
    return _all_devices_payload()

@app.get("/api/security/details")
async def api_security_details():
    tuya_devs = tuya_service.service.get_structured_devices()
    sec = tuya_devs.get("security", {})
    all_states = tuya_service.service.states
    all_cloud = tuya_service.service.all_cloud_devices
    
    battery_report = []
    for sec_key, sec_dev in sec.items():
        st = sec_dev.get("state", {})
        bat = st.get("battery")
        if bat is not None:
            battery_report.append({
                "id": sec_dev.get("id"),
                "name": sec_dev.get("name"),
                "category": "security",
                "type": sec_dev.get("type", "security"),
                "battery": bat,
                "alarm_state": st.get("alarm_lock") or ("Alarma Humo/CO" if st.get("is_alarm") else "normal"),
                "status_text": "Abierta" if st.get("is_open") else ("¡Movimiento!" if st.get("pir") == "pir" else "Normal")
            })
            
    for clim in tuya_devs.get("climate", []):
        st = clim.get("state", {})
        bat = st.get("battery")
        if bat is not None:
            battery_report.append({
                "id": clim.get("id"),
                "name": clim.get("name"),
                "category": "climate",
                "type": "climate",
                "battery": bat,
                "temperature": st.get("temperature"),
                "humidity": st.get("humidity"),
                "status_text": f"{st.get('temperature', '--')}°C · {st.get('humidity', '--')}%"
            })
            
    name_map = {d.get("id"): d.get("name") for d in all_cloud if isinstance(d, dict)}
    for dev_id, st in all_states.items():
        if isinstance(st, dict) and "battery" in st:
            if not any(b["id"] == dev_id for b in battery_report):
                dev_name = name_map.get(dev_id, dev_id)
                battery_report.append({
                    "id": dev_id,
                    "name": dev_name,
                    "category": "battery",
                    "type": "battery",
                    "battery": st["battery"],
                    "status_text": f"Nivel: {st['battery']}%" if isinstance(st["battery"], (int, float)) else str(st["battery"])
                })

    low_batteries = []
    for item in battery_report:
        b_val = item.get("battery")
        is_low = False
        if isinstance(b_val, (int, float)) and b_val <= 25:
            is_low = True
        elif isinstance(b_val, str) and b_val.lower() in ("low", "baja", "very_low", "0", "0%"):
            is_low = True
        elif item.get("alarm_state") == "low_battery":
            is_low = True
            
        if is_low:
            low_batteries.append(item)

    alarm_obj = sec.get("alarm", {})
    return {
        "status": "ok",
        "alarm_id": alarm_obj.get("id", "64326051e8db8480acc0"),
        "alarm_name": alarm_obj.get("name", "Alarma Hogar"),
        "alarm_mode": alarm_obj.get("state", {}).get("master_mode", "disarmed"),
        "alarm_battery": alarm_obj.get("state", {}).get("battery", 100),
        "security_devices": sec,
        "battery_inventory": battery_report,
        "low_battery_warnings": low_batteries
    }

@app.post("/api/xiaomi/control")
async def control_xiaomi(request: Request):
    data = await request.json()
    dev_id = data.get("device_id")
    action = data.get("action")
    value = data.get("value")
    if not dev_id or not action:
        return JSONResponse({"error": "device_id and action required"}, status_code=400)
    res = await asyncio.to_thread(xiaomi_service.service.send_command, dev_id, action, value)
    summary = _all_devices_payload()
    payload = json.dumps({
        "type": "DEVICE_UPDATE",
        "device_id": dev_id,
        "code": action,
        "value": value,
        "devices": summary
    })
    for ws in list(ACTIVE_SOCKETS):
        try:
            await ws.send_text(payload)
        except Exception:
            pass
    return {"result": res, "devices": summary}

@app.post("/api/devices/control")
async def control_device(request: Request):
    data = await request.json()
    dev_id = data.get("device_id")
    code = data.get("code", "switch_1")
    value = data.get("value")
    if not dev_id:
        return JSONResponse({"error": "device_id is required"}, status_code=400)
    
    if ewelink_service.service.has_device(dev_id):
        res = await asyncio.to_thread(ewelink_service.service.send_command, dev_id, value)
    else:
        res = tuya_service.service.send_command(dev_id, code, value)
        if dev_id == "64326051e8db8480acc0" and code == "master_mode":
            _append_security_event("Usuario (Kiosko)", f"Alarma -> {str(value).upper()}", f"Cambio manual a modo {value}.", "warning" if value != "disarmed" else "info", "🛡️")
    summary = _all_devices_payload()
    payload = json.dumps({
        "type": "DEVICE_UPDATE",
        "device_id": dev_id,
        "code": code,
        "value": value,
        "devices": summary
    })
    for ws in list(ACTIVE_SOCKETS):
        try:
            await ws.send_text(payload)
        except Exception:
            pass
            
    return res

@app.post("/api/modal/{name}")
async def trigger_modal(name: str):
    payload = json.dumps({"type": "OPEN_MODAL", "modal": name})
    for ws in list(ACTIVE_SOCKETS):
        try:
            await ws.send_text(payload)
        except Exception:
            pass
    return {"status": "ok", "modal": name}

@app.post("/api/screen/tap")
async def screen_tap(request: Request):
    data = await request.json()
    x_pct = float(data.get("x", 0.5))
    y_pct = float(data.get("y", 0.5))
    print(f"[TAP_LOG] Received tap at x_pct={x_pct:.4f}, y_pct={y_pct:.4f}, sockets={len(ACTIVE_SOCKETS)}", flush=True)
    
    set_brightness(80)

    payload = json.dumps({"type": "REMOTE_CLICK", "x": x_pct, "y": y_pct})
    for ws in list(ACTIVE_SOCKETS):
        try:
            await ws.send_text(payload)
        except Exception:
            pass

    x = max(0, min(1366, int(round(x_pct * 1366))))
    y = max(0, min(768, int(round(y_pct * 768))))
    # Handled directly via REMOTE_CLICK WebSocket in app.js (prevents double-click on Atom CPU)

    return {"status": "tapped", "x": x, "y": y}

@app.get("/api/solar")
async def get_solar_status():
    status_file = Path("/tmp/domos_solar_status.json")
    if status_file.exists():
        try:
            return json.loads(status_file.read_text())
        except Exception:
            pass
    return {"watts": 0, "volts": 230, "amps": 0, "is_sun": False}


import evdev

def _trigger_screen_wake():
    try:
        Path("/tmp/domos_wake_trigger").write_text("180")
        st_path = Path("/tmp/domos_presence_status.json")
        if st_path.exists():
            st = json.loads(st_path.read_text())
            if int(st.get("current_brightness", 45)) < 10:
                subprocess.Popen(["sudo", "brightnessctl", "set", "45%"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

async def monitor_physical_touchscreen():
    # Ensure I2C controller and SIS0817 touchscreen stay powered on
    for sys_p in [
        "/sys/devices/platform/80860F41:05/power/control",
        "/sys/bus/i2c/devices/i2c-SIS0817:00/power/control"
    ]:
        try:
            Path(sys_p).write_text("on")
        except Exception:
            pass

    target_dev = None
    for path in evdev.list_devices():
        try:
            d = evdev.InputDevice(path)
            if "SIS0817" in d.name or "0457:1084" in d.name:
                target_dev = d
                break
        except Exception:
            pass

    if not target_dev:
        print("[TOUCH_MONITOR] SIS0817 device not found", flush=True)
        return

    print(f"[TOUCH_MONITOR] Listening on {target_dev.path} ({target_dev.name})", flush=True)
    cur_x = 2048
    cur_y = 2048
    start_x = 2048
    start_y = 2048
    touch_down_time = 0.0
    is_touching = False

    need_start_pos = False
    last_pt_sent = 0.0
    try:
        async for ev in target_dev.async_read_loop():
            if ev.type == _e.EV_ABS:
                if ev.code in (_e.ABS_X, _e.ABS_MT_POSITION_X) and ev.value > 0:
                    cur_x = ev.value
                elif ev.code in (_e.ABS_Y, _e.ABS_MT_POSITION_Y) and ev.value > 0:
                    cur_y = ev.value
                elif ev.code == _e.ABS_MT_TRACKING_ID:
                    if ev.value >= 0 and not is_touching:
                        is_touching = True
                        need_start_pos = True
                        _trigger_screen_wake()
                        touch_down_time = time.time()
                    elif ev.value == -1 and is_touching:
                        is_touching = False
                        need_start_pos = False
                        dt = time.time() - touch_down_time
                        dist = abs(cur_x - start_x) + abs(cur_y - start_y)
                        if dt < 1.25 and dist < 550:
                            x_pct = max(0.0, min(1.0, cur_x / 4095.0))
                            y_pct = max(0.0, min(1.0, cur_y / 4095.0))
                            print(f"[PHYSICAL_TAP_SENT] MT x={x_pct:.3f} y={y_pct:.3f}", flush=True)
                            payload = json.dumps({"type": "PHYSICAL_TAP_FALLBACK", "x": x_pct, "y": y_pct})
                            for ws in list(ACTIVE_SOCKETS):
                                try:
                                    await ws.send_text(payload)
                                except Exception:
                                    pass
            elif ev.type == _e.EV_KEY and ev.code == _e.BTN_TOUCH:
                if ev.value == 1 and not is_touching:
                    is_touching = True
                    need_start_pos = True
                    _trigger_screen_wake()
                    touch_down_time = time.time()
                elif ev.value == 0 and is_touching:
                    is_touching = False
                    need_start_pos = False
                    dt = time.time() - touch_down_time
                    dist = abs(cur_x - start_x) + abs(cur_y - start_y)
                    if dt < 1.25 and dist < 550:
                        x_pct = max(0.0, min(1.0, cur_x / 4095.0))
                        y_pct = max(0.0, min(1.0, cur_y / 4095.0))
                        print(f"[PHYSICAL_TAP_SENT] BTN_TOUCH x={x_pct:.3f} y={y_pct:.3f}", flush=True)
                        payload = json.dumps({"type": "PHYSICAL_TAP_FALLBACK", "x": x_pct, "y": y_pct})
                        for ws in list(ACTIVE_SOCKETS):
                            try:
                                await ws.send_text(payload)
                            except Exception:
                                pass
            elif ev.type == _e.EV_SYN and ev.code == _e.SYN_REPORT:
                if need_start_pos:
                    start_x, start_y = cur_x, cur_y
                    need_start_pos = False
                if is_touching and ACTIVE_SOCKETS and (time.time() - last_pt_sent > 0.032):
                    last_pt_sent = time.time()
                    x_pct = max(0.0, min(1.0, cur_x / 4095.0))
                    y_pct = max(0.0, min(1.0, cur_y / 4095.0))
                    pt_payload = json.dumps({"type": "PHYSICAL_TOUCH_POINT", "x": x_pct, "y": y_pct})
                    for ws in list(ACTIVE_SOCKETS):
                        try:
                            await ws.send_text(pt_payload)
                        except Exception:
                            pass
    except Exception as ex:
        print("[TOUCH_MONITOR_ERR]", ex, flush=True)

@app.on_event("startup")
async def start_touch_monitor():
    asyncio.create_task(monitor_physical_touchscreen())


@app.post("/api/system/reboot")
async def system_reboot():
    print("[SYSTEM] Reboot requested via Domos Control Center", flush=True)
    asyncio.get_event_loop().call_later(0.8, lambda: subprocess.Popen(["sudo", "systemctl", "reboot"]))
    return {"status": "rebooting"}


@app.post("/api/system/poweroff")
async def system_poweroff():
    print("[SYSTEM] Poweroff requested via Domos Control Center", flush=True)
    asyncio.get_event_loop().call_later(0.8, lambda: subprocess.Popen(["sudo", "systemctl", "poweroff"]))
    return {"status": "powering_off"}



# =========================================================
# DOORBELL CHIME PLAYBACK (Asus Speaker via PulseAudio)
# =========================================================
import socket as _socket
import threading

AUDIO_VOLUMES_FILE = Path("/opt/domoskiosk/audio_volumes.json")
MPV_RADIO_IPC_SOCK = "/tmp/domos_mpv_radio.sock"
DEFAULT_AUDIO_VOLUMES = {
    "master": 70,
    "radio": 75,
    "doorbell": 85,
    "cameras": 85,
}

def load_audio_volumes() -> dict:
    vols = dict(DEFAULT_AUDIO_VOLUMES)
    if AUDIO_VOLUMES_FILE.exists():
        try:
            saved = json.loads(AUDIO_VOLUMES_FILE.read_text())
            for k in DEFAULT_AUDIO_VOLUMES:
                if k in saved:
                    vols[k] = max(0, min(100, int(saved[k])))
        except Exception:
            pass
    try:
        raw_hw = _get_raw_sink_volume_pct()
        if raw_hw is not None:
            vols["master"] = max(0, min(100, int(round(raw_hw * 100.0 / float(MAX_HW_VOLUME_PCT)))))
    except Exception:
        pass
    return vols

def save_audio_volumes(vols: dict):
    clean = {k: max(0, min(100, int(vols.get(k, DEFAULT_AUDIO_VOLUMES[k])))) for k in DEFAULT_AUDIO_VOLUMES}
    try:
        AUDIO_VOLUMES_FILE.write_text(json.dumps(clean, indent=2))
    except Exception as e:
        print(f"[AUDIO_VOLUMES] Save error: {e}", flush=True)
    return clean

def _set_mpv_radio_volume_live(vol_pct: int):
    if not Path(MPV_RADIO_IPC_SOCK).exists():
        return
    try:
        s = _socket.socket(_socket.AF_UNIX, _socket.SOCK_STREAM)
        s.settimeout(0.6)
        s.connect(MPV_RADIO_IPC_SOCK)
        cmd = json.dumps({"command": ["set_property", "volume", max(0, min(100, int(vol_pct)))]}) + "\n"
        s.sendall(cmd.encode("utf-8"))
        s.close()
    except Exception:
        pass

@app.get("/api/audio/volumes")
async def api_get_audio_volumes():
    return {"success": True, "volumes": load_audio_volumes()}

@app.post("/api/audio/volumes")
async def api_set_audio_volumes(request: Request):
    data = await request.json()
    vols = load_audio_volumes()
    if "master" in data:
        m = max(0, min(100, int(data["master"])))
        vols["master"] = m
        _set_exact_hw_volume(m)
    if "radio" in data:
        r = max(0, min(100, int(data["radio"])))
        vols["radio"] = r
        _set_mpv_radio_volume_live(r)
    if "doorbell" in data:
        vols["doorbell"] = max(0, min(100, int(data["doorbell"])))
    if "cameras" in data:
        vols["cameras"] = max(0, min(100, int(data["cameras"])))
    clean = save_audio_volumes(vols)
    payload = json.dumps({"type": "AUDIO_VOLUMES_UPDATED", "volumes": clean})
    for ws in list(ACTIVE_SOCKETS):
        try:
            await ws.send_text(payload)
        except Exception:
            pass
    return {"success": True, "volumes": clean}

DOORBELL_CHIME_WAV = Path("/opt/domoskiosk/doorbell_chime.wav")
_doorbell_chime_proc = None
_doorbell_chime_lock = threading.Lock()
_doorbell_chime_watcher_task = None

def is_doorbell_chime_ringing() -> bool:
    global _doorbell_chime_proc
    with _doorbell_chime_lock:
        return _doorbell_chime_proc is not None and _doorbell_chime_proc.poll() is None

async def _broadcast_chime_state(ringing: bool):
    payload = json.dumps({"type": "DOORBELL_CHIME_STATE", "ringing": bool(ringing)})
    for ws in list(ACTIVE_SOCKETS):
        try:
            await ws.send_text(payload)
        except Exception:
            pass

def stop_doorbell_chime() -> bool:
    global _doorbell_chime_proc
    stopped = False
    with _doorbell_chime_lock:
        if _doorbell_chime_proc is not None:
            try:
                if _doorbell_chime_proc.poll() is None:
                    _doorbell_chime_proc.terminate()
                    try:
                        _doorbell_chime_proc.wait(timeout=1.5)
                    except Exception:
                        _doorbell_chime_proc.kill()
                    stopped = True
            except Exception as e:
                print(f"[DOORBELL_CHIME] Stop error: {e}", flush=True)
            _doorbell_chime_proc = None
    return stopped

async def _watch_chime_completion(proc):
    try:
        while proc.poll() is None:
            await asyncio.sleep(0.5)
    except Exception:
        pass
    finally:
        with _doorbell_chime_lock:
            global _doorbell_chime_proc
            if _doorbell_chime_proc is proc:
                _doorbell_chime_proc = None
        await _broadcast_chime_state(False)

async def _auto_stop_chime_after(proc, delay_sec: float):
    await asyncio.sleep(delay_sec)
    with _doorbell_chime_lock:
        if _doorbell_chime_proc is proc and proc.poll() is None:
            try:
                proc.terminate()
            except Exception:
                pass

def start_doorbell_chime(test_short: bool = False) -> bool:
    global _doorbell_chime_proc
    if not DOORBELL_CHIME_WAV.exists():
        print(f"[DOORBELL_CHIME] Missing WAV file: {DOORBELL_CHIME_WAV}", flush=True)
        return False
    stop_doorbell_chime()
    vols = load_audio_volumes()
    db_vol = max(0, min(100, int(vols.get("doorbell", 85))))
    if db_vol == 0:
        print("[DOORBELL_CHIME] Doorbell volume is 0%, skipping playback", flush=True)
        return False
    pa_vol = int(round(65536 * (db_vol / 100.0)))
    try:
        env = dict(os.environ)
        env["XDG_RUNTIME_DIR"] = "/run/user/1000"
        proc = subprocess.Popen(
            ["paplay", f"--volume={pa_vol}", str(DOORBELL_CHIME_WAV)],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        with _doorbell_chime_lock:
            _doorbell_chime_proc = proc
        print(f"[DOORBELL_CHIME] Playing {DOORBELL_CHIME_WAV.name} at {db_vol}% (pa_vol={pa_vol}, pid={proc.pid}, test={test_short})", flush=True)
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(_watch_chime_completion(proc))
            if test_short:
                loop.create_task(_auto_stop_chime_after(proc, 3.4))
        except RuntimeError:
            pass
        return True
    except Exception as e:
        print(f"[DOORBELL_CHIME] Playback error: {e}", flush=True)
        return False

@app.post("/api/doorbell/test_chime")
async def api_test_doorbell_chime():
    started = start_doorbell_chime(test_short=True)
    return {"success": True, "playing": started}

@app.post("/api/doorbell/silence")
async def api_silence_doorbell_chime():
    stopped = stop_doorbell_chime()
    await _broadcast_chime_state(False)
    print(f"[DOORBELL_CHIME] Silenced via API (was_ringing={stopped})", flush=True)
    return {"success": True, "ringing": False, "stopped": stopped}

@app.get("/api/doorbell/chime_status")
async def api_doorbell_chime_status():
    return {"ringing": is_doorbell_chime_ringing()}

async def monitor_doorbell_ring():
    dev_id = "bf77eed8534deaf66f2xpj"
    last_trigger_time = 0.0
    await asyncio.sleep(2.0)
    last_seen_seq = getattr(tuya_service.service, "doorbell_ring_seq", 0)

    print("[DOORBELL_MONITOR] Watching Videoportero Exterior via strict real-time MQTT Push ONLY (0 polling/motion false triggers)", flush=True)
    while True:
        await asyncio.sleep(0.3)
        try:
            cur_seq = getattr(tuya_service.service, "doorbell_ring_seq", 0)
            if cur_seq <= last_seen_seq:
                continue
            last_seen_seq = cur_seq
            if time.time() - last_trigger_time <= 20.0:
                continue
            last_trigger_time = time.time()
            print(f"[DOORBELL_RING_DETECTED] Real MQTT ring seq={cur_seq}! Opening fullscreen videoportero...", flush=True)
            _append_security_event("Videoportero", "🔔 Timbre pulsado", "Alguien ha llamado al videoportero exterior.", "warning", "🔔")
            set_brightness(100)
            chime_started = start_doorbell_chime()
            try:
                cast_service.service.ring_doorbell_multiroom()
            except Exception:
                pass
            stream_res = await allocate_low_latency_stream(dev_id)
            payload = json.dumps({
                "type": "DOORBELL_ALERT",
                "title": "🔔 ¡Alguien está en la puerta!",
                "cameraId": dev_id,
                "ringing": chime_started,
                "stream_url": stream_res.get("url", "") if stream_res.get("success") else "",
                "stream_data": stream_res if stream_res.get("success") else None
            })
            for ws in list(ACTIVE_SOCKETS):
                try:
                    await ws.send_text(payload)
                except Exception:
                    pass
        except Exception as ex:
            print("[DOORBELL_MONITOR_ERR]", ex, flush=True)

@app.on_event("startup")
async def start_doorbell_monitor():
    asyncio.create_task(monitor_doorbell_ring())


SAFE_VOLUME_LIMIT = 70  # Acoustic safety ceiling (prevents distortion/tear on internal speakers)
MAX_HW_VOLUME_PCT = 80  # Hardware ceiling (-20% below 100%, eliminates 120% overdrive/clipping)

def _get_raw_sink_volume_pct():
    try:
        res = subprocess.run(
            ["sudo", "-u", "domos", "XDG_RUNTIME_DIR=/run/user/1000", "pactl", "get-sink-volume", "@DEFAULT_SINK@"],
            capture_output=True,
            text=True,
            check=False,
            timeout=2
        )
        m = re.search(r"(\d+)%", res.stdout or "")
        if m:
            return int(m.group(1))
    except Exception as e:
        print("[AUDIO_VOL_GET_ERR]", e, flush=True)
    return None

def _set_exact_hw_volume(target_ui_pct: int):
    target_hw = max(0, min(MAX_HW_VOLUME_PCT, int(round(target_ui_pct * MAX_HW_VOLUME_PCT / 100.0))))
    subprocess.run(
        ["sudo", "-u", "domos", "XDG_RUNTIME_DIR=/run/user/1000", "pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{target_hw}%"],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    return target_hw

def get_system_volume_pct():
    raw = _get_raw_sink_volume_pct()
    if raw is None:
        return None
    if raw > MAX_HW_VOLUME_PCT:
        subprocess.run(
            ["sudo", "-u", "domos", "XDG_RUNTIME_DIR=/run/user/1000", "pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{MAX_HW_VOLUME_PCT}%"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        raw = MAX_HW_VOLUME_PCT
    return min(100, int(round(raw * 100.0 / MAX_HW_VOLUME_PCT)))

def adjust_system_volume(delta: str, force_unlock: bool = False):
    try:
        cur_ui = get_system_volume_pct()
        if cur_ui is None:
            cur_ui = 50
        m = re.match(r"^([+-]?\d+)%$", delta.strip())
        step_ui = int(m.group(1)) if m else 10
        raw_target = cur_ui + step_ui

        cfg = get_kiosk_config()
        is_unlocked = bool(cfg.get("high_volume_unlocked", False)) or force_unlock

        limit_triggered = False
        if step_ui > 0 and not is_unlocked and raw_target > SAFE_VOLUME_LIMIT:
            new_ui = SAFE_VOLUME_LIMIT
            limit_triggered = True
        else:
            new_ui = max(0, min(100, int(round(raw_target / 5.0) * 5)))

        target_hw = _set_exact_hw_volume(new_ui)
        print(f"[AUDIO_VOL] Adjusted volume by {delta} -> UI {new_ui}% (HW {target_hw}%, limit_triggered={limit_triggered})", flush=True)
        return new_ui, limit_triggered, raw_target
    except Exception as e:
        print("[AUDIO_VOL_ERR]", e, flush=True)
        return None, False, None

async def broadcast_volume_osd(pct, delta: str):
    payload = json.dumps({"type": "VOLUME_OSD", "volume": pct, "delta": delta})
    for ws in list(ACTIVE_SOCKETS):
        try:
            await ws.send_text(payload)
        except Exception:
            pass

async def broadcast_volume_safety_warning(current_vol: int, requested_vol: int):
    payload = json.dumps({
        "type": "VOLUME_SAFETY_LIMIT",
        "current": current_vol,
        "requested": requested_vol
    })
    for ws in list(ACTIVE_SOCKETS):
        try:
            await ws.send_text(payload)
        except Exception:
            pass

@app.post("/api/audio/volume")
async def api_audio_volume(request: Request):
    data = await request.json()
    delta = str(data.get("delta", "+10%"))
    force_unlock = bool(data.get("force_unlock", False))
    if delta in ("mute", "unmute", "toggle_mute"):
        arg = "1" if delta == "mute" else ("0" if delta == "unmute" else "toggle")
        subprocess.run(
            ["sudo", "-u", "domos", "XDG_RUNTIME_DIR=/run/user/1000", "pactl", "set-sink-mute", "@DEFAULT_SINK@", arg],
            check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        mres = subprocess.run(
            ["sudo", "-u", "domos", "XDG_RUNTIME_DIR=/run/user/1000", "pactl", "get-sink-mute", "@DEFAULT_SINK@"],
            capture_output=True, text=True, check=False
        )
        is_muted = "yes" in (mres.stdout or "").lower() or "sí" in (mres.stdout or "").lower()
        pct = 0 if is_muted else get_system_volume_pct()
        await broadcast_volume_osd(pct, delta)
        return {"status": "ok", "delta": delta, "muted": is_muted, "volume": pct}

    if delta not in ("+10%", "-10%", "+5%", "-5%"):
        delta = "+10%"
    subprocess.run(
        ["sudo", "-u", "domos", "XDG_RUNTIME_DIR=/run/user/1000", "pactl", "set-sink-mute", "@DEFAULT_SINK@", "0"],
        check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    pct, limit_trig, requested = adjust_system_volume(delta, force_unlock=force_unlock)
    if pct is not None:
        await broadcast_volume_osd(pct, delta)
        if limit_trig:
            await broadcast_volume_safety_warning(pct, requested or 80)
    return {
        "status": "limit_reached" if limit_trig else "ok",
        "delta": delta,
        "volume": pct,
        "safety_limit": SAFE_VOLUME_LIMIT,
        "limit_triggered": limit_trig,
        "requested": requested
    }

@app.post("/api/audio/volume/unlock")
async def api_audio_volume_unlock(request: Request):
    data = await request.json()
    unlocked = bool(data.get("unlocked", False))
    cfg = get_kiosk_config()
    cfg["high_volume_unlocked"] = unlocked
    save_kiosk_config(cfg)
    target = data.get("target_volume")
    if unlocked and target is not None:
        target_pct = max(0, min(100, int(target)))
        _set_exact_hw_volume(target_pct)
        await broadcast_volume_osd(target_pct, "set")
        current_vol = target_pct
    else:
        current_vol = get_system_volume_pct()
    return {"status": "ok", "high_volume_unlocked": unlocked, "volume": current_vol}

async def monitor_hardware_volume_keys():
    vol_devs = []
    for path in evdev.list_devices():
        try:
            d = evdev.InputDevice(path)
            if "gpio-keys" in d.name or "Asus WMI" in d.name:
                keys = d.capabilities().get(_e.EV_KEY, [])
                if _e.KEY_VOLUMEUP in keys or _e.KEY_VOLUMEDOWN in keys:
                    vol_devs.append(d)
        except Exception:
            pass

    if not vol_devs:
        print("[VOL_MONITOR] No hardware volume key device found", flush=True)
        return

    print(f"[VOL_MONITOR] Listening on {[d.path + ':' + d.name for d in vol_devs]}", flush=True)

    async def _watch(dev):
        try:
            async for ev in dev.async_read_loop():
                if ev.type == _e.EV_KEY and ev.value in (1, 2):
                    if ev.code == _e.KEY_VOLUMEUP:
                        pct, limit_trig, requested = adjust_system_volume("+10%")
                        if pct is not None:
                            await broadcast_volume_osd(pct, "+10%")
                            if limit_trig:
                                await broadcast_volume_safety_warning(pct, requested or 80)
                    elif ev.code == _e.KEY_VOLUMEDOWN:
                        pct, _, _ = adjust_system_volume("-10%")
                        if pct is not None:
                            await broadcast_volume_osd(pct, "-10%")
        except Exception:
            pass

    await asyncio.gather(*[_watch(d) for d in vol_devs])

@app.on_event("startup")
async def start_volume_monitor():
    get_system_volume_pct()
    asyncio.create_task(monitor_hardware_volume_keys())


# --- Cached Online Landscapes (Batch of 20) & Voice Arm ---
LANDSCAPES_CACHE_DIR = Path("/opt/domoskiosk/landscapes_cache")
LANDSCAPES_CACHE_DIR.mkdir(parents=True, exist_ok=True)
LANDSCAPE_URLS = [
    "https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1366&h=768&q=80",
    "https://images.unsplash.com/photo-1469474968028-56623f02e42e?auto=format&fit=crop&w=1366&h=768&q=80",
    "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?auto=format&fit=crop&w=1366&h=768&q=80",
    "https://images.unsplash.com/photo-1472214103451-9374bd1c798e?auto=format&fit=crop&w=1366&h=768&q=80",
    "https://images.unsplash.com/photo-1426604966848-d7adac402bff?auto=format&fit=crop&w=1366&h=768&q=80",
    "https://images.unsplash.com/photo-1501785888041-af3ef285b470?auto=format&fit=crop&w=1366&h=768&q=80",
    "https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1366&h=768&q=80",
    "https://images.unsplash.com/photo-1511497584788-87676104235f?auto=format&fit=crop&w=1366&h=768&q=80",
    "https://images.unsplash.com/photo-1519681393784-d120267933ba?auto=format&fit=crop&w=1366&h=768&q=80",
    "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1366&h=768&q=80",
    "https://images.unsplash.com/photo-1433086966358-54859d0ed716?auto=format&fit=crop&w=1366&h=768&q=80",
    "https://images.unsplash.com/photo-1534447677768-be436bb09401?auto=format&fit=crop&w=1366&h=768&q=80",
    "https://images.unsplash.com/photo-1518495973542-4542c06a5843?auto=format&fit=crop&w=1366&h=768&q=80",
    "https://images.unsplash.com/photo-1502082553048-f009c37129b9?auto=format&fit=crop&w=1366&h=768&q=80",
    "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=1366&h=768&q=80",
    "https://images.unsplash.com/photo-1439066615861-d1af74d74000?auto=format&fit=crop&w=1366&h=768&q=80",
    "https://images.unsplash.com/photo-1447752875215-b2761acb3c5d?auto=format&fit=crop&w=1366&h=768&q=80",
    "https://images.unsplash.com/photo-1475924156734-496f6cac6ec1?auto=format&fit=crop&w=1366&h=768&q=80",
    "https://images.unsplash.com/photo-1500534314209-a25ddb2bd429?auto=format&fit=crop&w=1366&h=768&q=80",
    "https://images.unsplash.com/photo-1493246507139-91e8fad9978e?auto=format&fit=crop&w=1366&h=768&q=80",
]

def _download_landscapes_batch_sync(force: bool = False):
    for idx, url in enumerate(LANDSCAPE_URLS):
        dest = LANDSCAPES_CACHE_DIR / f"land_{idx:02d}.jpg"
        if dest.exists() and dest.stat().st_size > 10000 and not force:
            continue
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "DomosKiosk/1.0"})
            with urllib.request.urlopen(req, timeout=12) as r:
                data = r.read()
                if len(data) > 10000:
                    dest.write_bytes(data)
        except Exception as e:
            print(f"[LANDSCAPE_CACHE_ERR] {idx}: {e}", flush=True)

@app.on_event("startup")
async def warmup_landscapes_cache():
    asyncio.create_task(asyncio.to_thread(_download_landscapes_batch_sync, False))

@app.get("/api/landscapes")
async def api_list_landscapes():
    files = sorted(LANDSCAPES_CACHE_DIR.glob("land_*.jpg"))
    return {"photos": [f"/api/landscapes/img/{f.name}" for f in files if f.stat().st_size > 10000]}

@app.post("/api/landscapes/refresh")
async def api_refresh_landscapes():
    await asyncio.to_thread(_download_landscapes_batch_sync, True)
    files = sorted(LANDSCAPES_CACHE_DIR.glob("land_*.jpg"))
    return {"count": len(files)}

@app.get("/api/landscapes/img/{filename}")
async def api_get_landscape_img(filename: str):
    safe_name = Path(filename).name
    target = LANDSCAPES_CACHE_DIR / safe_name
    if not target.exists():
        return Response(status_code=404)
    return FileResponse(target, media_type="image/jpeg")

VOICE_ARMED_UNTIL = 0.0


RADIO_PROCESS = None

@app.post("/api/radio/play")
async def api_radio_play(request: Request):
    global RADIO_PROCESS
    data = await request.json()
    url = data.get("url")
    station = data.get("station", "Radio")
    target = data.get("target", "domos")

    if RADIO_PROCESS:
        try:
            RADIO_PROCESS.terminate()
            await asyncio.sleep(0.15)
            if RADIO_PROCESS.poll() is None:
                RADIO_PROCESS.kill()
        except Exception:
            pass
        RADIO_PROCESS = None

    if str(target).startswith("cast_") and url:
        cast_t = str(target)[5:]
        cres = await asyncio.to_thread(cast_service.service.play_url, cast_t, url, f"Radio: {station}")
        if cres.get("success"):
            return {"status": "playing", "stream_verified": True, "target": target, "station": station}
        return {"status": "error", "target": target, "station": station, "error": cres.get("error") or "No se pudo conectar al altavoz Google"}

    if target == "domos" and url:
        try:
            env = os.environ.copy()
            env["XDG_RUNTIME_DIR"] = "/run/user/1000"
            radio_vol = int(load_audio_volumes().get("radio", 75))
            try:
                if Path(MPV_RADIO_IPC_SOCK).exists():
                    Path(MPV_RADIO_IPC_SOCK).unlink()
            except Exception:
                pass
            RADIO_PROCESS = subprocess.Popen([
                "mpv",
                "--no-video",
                "--msg-level=all=error",
                "--network-timeout=6",
                "--ao=pulse",
                f"--volume={radio_vol}",
                f"--input-ipc-server={MPV_RADIO_IPC_SOCK}",
                url
            ], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)

            # Verify stream actually starts (up to 3.2s) instead of blindly returning "playing"
            stream_active = False
            for _ in range(16):
                await asyncio.sleep(0.2)
                if RADIO_PROCESS.poll() is not None:
                    err_txt = ""
                    try:
                        err_txt = (RADIO_PROCESS.stderr.read() or "").strip().splitlines()[-1]
                    except Exception:
                        pass
                    RADIO_PROCESS = None
                    return {
                        "status": "error",
                        "target": "domos",
                        "station": station,
                        "error": err_txt or "La emisora cerró la conexión o no responde."
                    }
                if Path(MPV_RADIO_IPC_SOCK).exists():
                    try:
                        s = _socket.socket(_socket.AF_UNIX, _socket.SOCK_STREAM)
                        s.settimeout(0.25)
                        s.connect(MPV_RADIO_IPC_SOCK)
                        s.sendall(b'{"command":["get_property","core-idle"]}\n')
                        resp = s.recv(512).decode("utf-8", errors="ignore")
                        s.close()
                        if '"data":false' in resp.replace(" ", ""):
                            stream_active = True
                            break
                    except Exception:
                        pass

            vols = load_audio_volumes()
            return {
                "status": "playing",
                "stream_verified": stream_active,
                "target": "domos",
                "station": station,
                "master_volume": vols.get("master", 70),
                "radio_volume": vols.get("radio", 75),
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    return {"status": "ready", "target": target}

@app.post("/api/radio/stop")
async def api_radio_stop():
    global RADIO_PROCESS
    if RADIO_PROCESS:
        try:
            RADIO_PROCESS.terminate()
            RADIO_PROCESS = None
        except Exception:
            pass
    try:
        asyncio.create_task(asyncio.to_thread(cast_service.service.stop, "all"))
    except Exception:
        pass
    for ws in list(ACTIVE_SOCKETS):
        try:
            await ws.send_text(json.dumps({"type": "RADIO_STOP"}))
        except Exception:
            pass
    return {"status": "stopped"}

@app.post("/api/radio/control")
async def api_radio_control(request: Request):
    data = await request.json()
    payload = json.dumps({
        "type": "RADIO_CONTROL",
        "action": data.get("action", "open"),
        "station": data.get("station", "")
    })
    for ws in list(ACTIVE_SOCKETS):
        try:
            await ws.send_text(payload)
        except Exception:
            pass
    return {"status": "ok"}

@app.post("/api/voice/arm")
async def api_arm_voice(seconds: float = 9.0):
    global VOICE_ARMED_UNTIL
    VOICE_ARMED_UNTIL = time.time() + seconds if seconds > 0 else 0.0
    try:
        Path("/tmp/domos_voice_arm").write_text(str(VOICE_ARMED_UNTIL))
    except Exception:
        pass
    return {"armed": seconds > 0, "until": VOICE_ARMED_UNTIL}

@app.get("/api/voice/arm")
async def api_get_voice_arm():
    return {"armed": time.time() < VOICE_ARMED_UNTIL}


@app.websocket("/ws/radio-vu")
async def ws_radio_vu(websocket: WebSocket):
    import struct
    import math
    await websocket.accept()
    proc = None
    try:
        proc = await asyncio.create_subprocess_exec(
            "env", "XDG_RUNTIME_DIR=/run/user/1000",
            "parec", "-d", "@DEFAULT_MONITOR@",
            "--rate=8000", "--channels=1", "--format=s16le", "--latency-msec=40",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        chunk_bytes = 640  # 320 samples @ 8kHz = 40ms
        bars = [0] * 16
        while True:
            try:
                raw = await asyncio.wait_for(proc.stdout.readexactly(chunk_bytes), timeout=1.0)
            except asyncio.TimeoutError:
                await websocket.send_text(json.dumps([0] * 16))
                continue
            samples = struct.unpack("<320h", raw)
            # 16-band real-time spectrum (80Hz..3600Hz) with Hann window + dB scaling
            if not hasattr(ws_radio_vu, "_basis"):
                n_s = 320
                win = [0.5 * (1.0 - math.cos(2.0 * math.pi * n / (n_s - 1))) for n in range(n_s)]
                freqs = [80 * (45.0 ** (i / 15.0)) for i in range(16)]
                ws_radio_vu._basis = [
                    [(win[n] * math.cos(2.0 * math.pi * f * n / 8000.0),
                      win[n] * math.sin(2.0 * math.pi * f * n / 8000.0)) for n in range(n_s)]
                    for f in freqs
                ]
            norm_s = [x / 32768.0 for x in samples]
            new_bars = []
            for i, b in enumerate(ws_radio_vu._basis):
                re = sum(norm_s[n] * b[n][0] for n in range(320))
                im = sum(norm_s[n] * b[n][1] for n in range(320))
                mag = math.sqrt(re * re + im * im) / 80.0
                # Tilt slightly up for higher frequencies so treble bars stay lively
                mag *= (1.0 + i * 0.14)
                db = 20.0 * math.log10(max(mag, 1e-5))
                lvl = max(0, min(100, int((db + 42.0) * (100.0 / 38.0))))
                bars[i] = max(lvl, int(bars[i] * 0.65))
                new_bars.append(bars[i])
            await websocket.send_text(json.dumps(new_bars))
    except Exception:
        pass
    finally:
        if proc and proc.returncode is None:
            try:
                proc.terminate()
                await asyncio.wait_for(proc.wait(), timeout=1.0)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass

def _adguard_request(path: str, method: str = "GET", payload: dict = None):
    import base64
    import urllib.request
    adguard_auth = os.environ.get("ADGUARD_BASIC_AUTH", "admin:admin")
    token = base64.b64encode(adguard_auth.encode("utf-8")).decode("ascii")
    headers = {"Authorization": f"Basic {token}"}
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(f"http://127.0.0.1:3000{path}", data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=3) as resp:
        raw = resp.read().decode("utf-8")
        return json.loads(raw) if raw else {}

@app.get("/api/adguard/stats")
async def api_adguard_stats():
    try:
        st = await asyncio.to_thread(_adguard_request, "/control/status")
        stats = await asyncio.to_thread(_adguard_request, "/control/stats")
        total = int(stats.get("num_dns_queries", 0) or 0)
        blocked = int(stats.get("num_blocked_filtering", 0) or 0)
        pct = round((blocked / total) * 100, 1) if total > 0 else 0.0
        avg_ms = round(float(stats.get("avg_processing_time", 0.0) or 0.0) * 1000.0, 1) if float(stats.get("avg_processing_time", 0.0) or 0.0) < 0.5 else round(float(stats.get("avg_processing_time", 0.0) or 0.0), 1)
        return {
            "online": True,
            "protection_enabled": bool(st.get("protection_enabled", False)),
            "version": st.get("version", ""),
            "num_dns_queries": total,
            "num_blocked_filtering": blocked,
            "block_pct": pct,
            "num_malware_blocked": int(stats.get("num_replaced_safebrowsing", 0) or 0),
            "num_parental_blocked": int(stats.get("num_replaced_parental", 0) or 0),
            "avg_processing_ms": avg_ms,
            "top_blocked_domains": (stats.get("top_blocked_domains") or [])[:8],
            "top_clients": (stats.get("top_clients") or [])[:6],
            "top_queried_domains": (stats.get("top_queried_domains") or [])[:6],
        }
    except Exception as e:
        return {"online": False, "error": str(e)}

@app.post("/api/adguard/toggle")
async def api_adguard_toggle(request: Request):
    data = await request.json()
    enabled = bool(data.get("enabled", True))
    await asyncio.to_thread(_adguard_request, "/control/protection", "POST", {"enabled": enabled})
    return await api_adguard_stats()


async def monitor_power_history_loop():
    print("[POWER_LOGGER] Smart plug power historian started", flush=True)
    await asyncio.to_thread(power_logger.load_store)
    while True:
        await asyncio.sleep(60)
        try:
            pdata = await asyncio.to_thread(_get_monitored_devices_power_sync)
            await asyncio.to_thread(power_logger.record_power_sample, pdata.get("devices", []), 60.0)
        except Exception as e:
            print(f"[POWER_LOGGER_ERR] {e}", flush=True)

async def monitor_climate_history_loop():
    print("[CLIMATE_LOGGER] Climate telemetry logger started", flush=True)
    await asyncio.to_thread(climate_logger.init_climate_history_store)
    while True:
        try:
            clim_devs = tuya_service.service.get_structured_devices().get("climate", [])
            xm_devs = xiaomi_service.service.get_devices()
            await asyncio.to_thread(climate_logger.record_current_sample, clim_devs, None, None, xm_devs)
        except Exception as e:
            print(f"[CLIMATE_LOGGER_ERR] {e}", flush=True)
        await asyncio.sleep(600)

async def monitor_schedules_loop():
    print("[SCHEDULES] Smart plug & device scheduler started", flush=True)
    while True:
        try:
            now = datetime.datetime.now()
            cur_time = now.strftime("%H:%M")
            cur_weekday = now.isoweekday() # 1=Mon, 7=Sun
            today_date = now.strftime("%Y-%m-%d")

            schedules = _load_schedules_sync()
            changed = False
            for s in schedules:
                if not s.get("enabled", True):
                    continue
                if s.get("time") == cur_time and cur_weekday in s.get("days", [1,2,3,4,5,6,7]):
                    if s.get("last_run_date") != today_date:
                        dev_id = s.get("device_id")
                        code = s.get("code", "switch_1")
                        val = True if s.get("action") == "on" else False
                        print(f"[SCHEDULE] Executing {s.get('name')}: {dev_id} -> {val}", flush=True)
                        try:
                            if ewelink_service.service.has_device(dev_id):
                                await asyncio.to_thread(ewelink_service.service.send_command, dev_id, val)
                            else:
                                await asyncio.to_thread(tuya_service.service.send_command, dev_id, code, val)
                            s["last_run_date"] = today_date
                            s["last_run_time"] = now.strftime("%Y-%m-%d %H:%M:%S")
                            changed = True
                        except Exception as e_cmd:
                            print(f"[SCHEDULE_ERR] {e_cmd}", flush=True)
            if changed:
                _save_schedules_sync(schedules)
        except Exception as e:
            print(f"[SCHEDULES_LOOP_ERR] {e}", flush=True)
        await asyncio.sleep(25)

@app.on_event("startup")
async def start_schedules_scheduler():
    asyncio.create_task(monitor_schedules_loop())

@app.on_event("startup")
async def start_climate_logger():
    asyncio.create_task(monitor_climate_history_loop())
    asyncio.create_task(monitor_power_history_loop())


app.mount("/", StaticFiles(directory="/opt/domoskiosk/static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)


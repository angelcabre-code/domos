#!/usr/bin/env python3
"""
Doctor DOMOS — Hybrid Nightly System Auditor, Safe Self-Healer & Optional Gemini AI Advisor
- Runs nightly at 03:30 AM (or on-demand via API/UI).
- Audits 8 subsystems with 0% extra RAM/CPU footprint.
- Executes strictly safe, reversible self-healing actions when auto_heal_enabled=True.
- Optionally enriches diagnosis via Gemini API (Google AI Studio key in doctor_config.json).
"""
import json
import os
import shutil
import socket
import subprocess
import time
import urllib.request
from datetime import datetime
from pathlib import Path

BASE_DIR = Path("/opt/domoskiosk")
CONFIG_FILE = BASE_DIR / "doctor_config.json"
REPORT_FILE = BASE_DIR / "doctor_report.json"

DEFAULT_CONFIG = {
    "auto_heal_enabled": True,
    "gemini_api_key": "",
    "gemini_model": "gemini-3.8-flash",
    "nightly_time": "03:30",
}

SAFE_RESTARTABLE_SERVICES = [
    "domoskiosk-solar",
    "domoskiosk-battery",
    "domoskiosk-presence",
    "domoskiosk-go2rtc",
    "domoskiosk-voice",
]

ALL_MONITORED_SERVICES = [
    "domoskiosk-server",
    "domoskiosk-cage",
    "domoskiosk-solar",
    "domoskiosk-battery",
    "domoskiosk-presence",
    "domoskiosk-go2rtc",
    "domoskiosk-voice",
    "domoskiosk-nosleep",
]


def load_config() -> dict:
    cfg = dict(DEFAULT_CONFIG)
    if CONFIG_FILE.exists():
        try:
            saved = json.loads(CONFIG_FILE.read_text())
            if isinstance(saved, dict):
                cfg.update(saved)
        except Exception:
            pass
    return cfg


def save_config(updates: dict) -> dict:
    cfg = load_config()
    if "auto_heal_enabled" in updates:
        cfg["auto_heal_enabled"] = bool(updates["auto_heal_enabled"])
    if "gemini_model" in updates and updates["gemini_model"]:
        cfg["gemini_model"] = str(updates["gemini_model"]).strip()
    if "gemini_api_key" in updates:
        key_val = str(updates["gemini_api_key"] or "").strip()
        if key_val != "********":
            cfg["gemini_api_key"] = key_val
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2, ensure_ascii=False))
    try:
        os.chmod(CONFIG_FILE, 0o600)
    except Exception:
        pass
    return cfg


def _read_json(path: Path, default=None):
    try:
        if path.exists():
            return json.loads(path.read_text())
    except Exception:
        pass
    return default if default is not None else {}


def _check_service(name: str) -> str:
    try:
        r = subprocess.run(["systemctl", "is-active", name], capture_output=True, text=True, timeout=3)
        return (r.stdout or "").strip() or "unknown"
    except Exception:
        return "unknown"


def _tcp_ping(host: str, port: int, timeout: float = 1.2) -> bool:
    try:
        s = socket.create_connection((host, port), timeout=timeout)
        s.close()
        return True
    except Exception:
        return False


def _call_gemini(api_key: str, model: str, audit_summary: dict) -> dict:
    prompt = (
        "Eres 'Doctor DOMOS', el ingeniero experto del sistema domótico doméstico DOMOS (Asus Transformer Mini Linux + Tuya LAN/Sharing + Hoymiles Solar + Xiaomi Purifier + Google Cast).\n"
        "Analiza este diagnóstico técnico en JSON y responde en español de forma clara, concisa y práctica (máximo 180 palabras):\n"
        "1) Resumen ejecutivo del estado general del hogar.\n"
        "2) 2 o 3 recomendaciones concretas de optimización, ahorro energético o mantenimiento preventivo basadas exclusivamente en los datos reales.\n"
        "No inventes datos que no estén en el JSON.\n\n"
        f"DATOS:\n{json.dumps(audit_summary, ensure_ascii=False)}"
    )
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 2048},
    }).encode("utf-8")
    candidates = [model] + [m for m in ("gemini-3.8-flash", "gemini-3.8-flash-lite", "gemini-3.1-flash", "gemini-3.1-pro") if m != model]
    last_err = None
    for cand in candidates:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{cand}:generateContent?key={api_key}"
            req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=18) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                return {"used": True, "model": cand, "text": text, "error": None}
        except Exception as e:
            last_err = f"{cand}: {e}"
            continue
    raise RuntimeError(last_err or "Gemini API call failed")


def run_diagnosis(trigger: str = "manual") -> dict:
    cfg = load_config()
    auto_heal = bool(cfg.get("auto_heal_enabled", True))
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    now_ts = time.time()

    score = 100
    checks = []
    findings = []
    actions_taken = []
    recommendations = []

    # 1. Servicios Systemd
    svc_states = {s: _check_service(s) for s in ALL_MONITORED_SERVICES}
    down_svcs = [s for s, st in svc_states.items() if st != "active"]
    if down_svcs:
        for ds in list(down_svcs):
            if auto_heal and ds in SAFE_RESTARTABLE_SERVICES:
                try:
                    subprocess.run(["sudo", "systemctl", "restart", ds], timeout=10, check=False)
                    time.sleep(1.5)
                    new_st = _check_service(ds)
                    if new_st == "active":
                        svc_states[ds] = "active"
                        down_svcs.remove(ds)
                        actions_taken.append(f"🛠️ Reiniciado automáticamente el servicio caído `{ds}` (recuperado).")
                except Exception:
                    pass
    if down_svcs:
        score -= 20
        findings.append({"severity": "critical", "area": "Servicios", "title": f"Servicios detenidos: {', '.join(down_svcs)}", "detail": "Requieren revisión manual."})
        checks.append({"id": "services", "icon": "⚙️", "name": "Servicios DOMOS", "status": "critical", "summary": f"{len(ALL_MONITORED_SERVICES)-len(down_svcs)}/{len(ALL_MONITORED_SERVICES)} activos"})
    else:
        checks.append({"id": "services", "icon": "⚙️", "name": "Servicios DOMOS", "status": "ok", "summary": f"Todos activos ({len(ALL_MONITORED_SERVICES)}/{len(ALL_MONITORED_SERVICES)})"})

    # 2. Hardware ASUS (RAM, Disco, Temperatura, Uptime)
    du_root = shutil.disk_usage("/")
    root_pct = round(du_root.used * 100.0 / max(1, du_root.total), 1)
    sd_pct = None
    if Path("/media/storage").is_mount():
        du_sd = shutil.disk_usage("/media/storage")
        sd_pct = round(du_sd.used * 100.0 / max(1, du_sd.total), 1)
    mem_avail_mb = 0
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemAvailable:"):
                mem_avail_mb = int(line.split()[1]) // 1024
                break
    except Exception:
        pass
    uptime_h = 0.0
    try:
        uptime_h = round(float(Path("/proc/uptime").read_text().split()[0]) / 3600.0, 1)
    except Exception:
        pass

    hw_status = "ok"
    if root_pct >= 88.0:
        hw_status = "critical" if root_pct >= 94.0 else "warning"
        score -= 15 if root_pct >= 94.0 else 8
        findings.append({"severity": hw_status, "area": "Hardware", "title": f"Disco interno al {root_pct}%", "detail": "Conviene liberar espacio en /."})
    if mem_avail_mb and mem_avail_mb < 250:
        hw_status = "warning"
        score -= 6
        recommendations.append(f"RAM disponible baja ({mem_avail_mb} MB); vigilar pestañas o reiniciar el kiosko si se nota lentitud.")
    checks.append({"id": "hardware", "icon": "💻", "name": "Hardware ASUS", "status": hw_status, "summary": f"Disco {root_pct}% · SD {sd_pct or '--'}% · RAM libre {mem_avail_mb} MB · {uptime_h}h up"})

    # 3. Backups & Limpieza segura
    b_status = _read_json(BASE_DIR / "backups/backup_status.json", {})
    b_path = BASE_DIR / "backups/backup_status.json"
    b_age_h = round((now_ts - b_path.stat().st_mtime) / 3600.0, 1) if b_path.exists() else 999.0
    if b_age_h > 36.0 and auto_heal:
        try:
            import backup_domos
            res_b = backup_domos.create_backup(reason="doctor_auto")
            if res_b.get("success"):
                b_age_h = 0.0
                b_status = res_b
                actions_taken.append(f"💾 Backup automático ejecutado por Doctor DOMOS ({res_b.get('size_kb')} KB, SD={res_b.get('sd_mirrored')}).")
        except Exception:
            pass
    # Safe cleanup of stale TTS files > 1h
    cast_tmp = Path("/tmp/domos_cast_media")
    cleaned = 0
    if cast_tmp.exists():
        for f in cast_tmp.glob("tts_*.wav"):
            try:
                if now_ts - f.stat().st_mtime > 3600:
                    f.unlink()
                    cleaned += 1
            except Exception:
                pass
    if cleaned > 0:
        actions_taken.append(f"🧹 Limpiados {cleaned} archivos temporales de audio TTS.")

    b_st = "ok" if (b_age_h <= 36.0 and b_status.get("sd_mirrored")) else "warning"
    if b_st != "ok":
        score -= 6
        findings.append({"severity": "warning", "area": "Backups", "title": f"Último backup hace {b_age_h} h", "detail": "Revisa el espejo en tarjeta SD."})
    checks.append({"id": "backups", "icon": "💾", "name": "Copias de Seguridad", "status": b_st, "summary": f"Última hace {b_age_h} h · Espejo SD {'OK' if b_status.get('sd_mirrored') else 'No'}"})

    # 4. Dispositivos Tuya, Baterías y Seguridad
    states = _read_json(Path("/tmp/domos_tuya_states.json"), {})
    devs = _read_json(BASE_DIR / "devices.json", {})
    low_bats = []
    offline_crit = []
    for cid, cname in [
        ("64326051e8db8480acc0", "Alarma"),
        ("bf77eed8534deaf66f2xpj", "Videoportero"),
        ("bf216abd6b1934fa11rl63", "Puerta Principal"),
        ("bf20349qicjyoh2g", "Cerradura"),
    ]:
        st = states.get(cid)
        if isinstance(st, dict) and st.get("online") is False:
            offline_crit.append(cname)
    seen_b = set()
    for did, st in states.items():
        if not isinstance(st, dict) or did == "bf29b1a036ad20f17079pv":
            continue
        dinfo = devs.get(did, {})
        name = dinfo.get("name", did)
        if str(dinfo.get("category", "")).lower() == "dcb" or "smart 20" in name.lower():
            continue
        bv = st.get("battery") if st.get("battery") is not None else st.get("battery_percentage")
        try:
            if bv is not None and int(bv) <= 20 and name.lower() not in seen_b:
                seen_b.add(name.lower())
                low_bats.append(f"{name} ({int(bv)}%)")
        except Exception:
            pass
    sec_st = "ok"
    if offline_crit:
        sec_st = "critical"
        score -= 15
        findings.append({"severity": "critical", "area": "Seguridad", "title": f"Desconectados: {', '.join(offline_crit)}", "detail": "Revisar Wi-Fi/Zigbee o alimentación."})
    if low_bats:
        sec_st = "warning" if sec_st == "ok" else sec_st
        score -= 5 * min(3, len(low_bats))
        findings.append({"severity": "warning", "area": "Baterías", "title": f"Pilas bajas: {', '.join(low_bats)}", "detail": "Conviene sustituir las pilas pronto."})
        recommendations.append(f"Cambiar pilas en: {', '.join(low_bats)}.")
    checks.append({"id": "security", "icon": "🛡️", "name": "Seguridad y Sensores", "status": sec_st, "summary": f"{len(offline_crit)} offline · {len(low_bats)} pilas bajas"})

    # 5. Calidad del Aire & Filtro Xiaomi
    air_st = "ok"
    pm25 = None
    filter_life = None
    co2_sot = (states.get("bf3aa055b420138596m0cs") or {}).get("co2")
    try:
        r_air = urllib.request.urlopen("http://127.0.0.1:8080/api/air/quality", timeout=3)
        aq = json.loads(r_air.read().decode("utf-8"))
        pur = (aq.get("indoor") or {}).get("purifier") or {}
        pm25 = pur.get("aqi")
        filter_life = pur.get("filter_life")
        if filter_life is not None and int(filter_life) <= 20:
            air_st = "warning"
            recommendations.append(f"El filtro del purificador Xiaomi está al {filter_life}%; conviene pedir recambio pronto.")
        if pm25 is not None and float(pm25) >= 60 and not pur.get("is_on") and auto_heal:
            req_p = urllib.request.Request(
                "http://127.0.0.1:8080/api/xiaomi/control",
                data=json.dumps({"device_id": "314954236", "action": "power", "value": True}).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            urllib.request.urlopen(req_p, timeout=3)
            actions_taken.append(f"🌀 Purificador encendido automáticamente por PM2.5 crítico ({pm25}).")
    except Exception:
        pass
    pm_s = pm25 if pm25 is not None else "--"
    co2_s = co2_sot if co2_sot is not None else "--"
    fl_s = filter_life if filter_life is not None else "--"
    checks.append({"id": "air", "icon": "🌿", "name": "Calidad del Aire", "status": air_st, "summary": f"PM2.5: {pm_s} · CO₂ Sótano: {co2_s} · Filtro: {fl_s}%"})

    # 6. Energía Solar y Ahorro
    sol = _read_json(Path("/tmp/domos_solar_status.json"), {})
    es_st = _read_json(BASE_DIR / "energy_savings_state.json", {})
    saved_wh = sum(float(v.get("saved_wh", 0)) for v in (es_st.get("daily") or {}).values() if isinstance(v, dict))
    inv_t = float(sol.get("temperature_c") or 0.0)
    en_status = "warning" if inv_t >= 65.0 else "ok"
    if inv_t >= 65.0:
        score -= 8
        findings.append({"severity": "warning", "area": "Solar", "title": f"Inversor Hoymiles a {inv_t:.1f}°C", "detail": "Temperatura alta en microinversor."})
    if not sol.get("meter_online"):
        recommendations.append("Doble pinza amperimétrica aún pendiente de instalación: en cuanto llegue, Ahorro Solar pasará a Excedente Neto real.")
    checks.append({"id": "energy", "icon": "☀️", "name": "Energía y Autoconsumo", "status": en_status, "summary": f"Solar {sol.get('watts', 0)} W · Ahorro hoy {round(saved_wh/1000.0, 2)} kWh · Inv {inv_t:.1f}°C"})

    # 7. Altavoces Google Cast
    cast_cfg = _read_json(BASE_DIR / "cast_config.json", {})
    sps = cast_cfg.get("speakers") or []
    sp_ok = sum(1 for s in sps if _tcp_ping(s.get("host", ""), int(s.get("port", 8009))))
    cast_status = "ok" if sp_ok == len(sps) else ("warning" if sp_ok > 0 else "critical")
    if sp_ok < len(sps):
        score -= 5
    checks.append({"id": "cast", "icon": "📢", "name": "Altavoces Google", "status": cast_status, "summary": f"{sp_ok}/{len(sps)} accesibles en LAN"})

    # 8. Resumen final + Capa opcional Gemini IA
    score = max(0, min(100, int(score)))
    if not recommendations:
        recommendations.append("Todos los subsistemas principales operan dentro de parámetros normales. Ninguna acción urgente requerida.")

    compact_for_ai = {
        "timestamp": now_str,
        "health_score": score,
        "checks": checks,
        "findings": findings,
        "actions_taken": actions_taken,
        "local_recommendations": recommendations,
    }

    ai_block = {"used": False, "model": cfg.get("gemini_model", "gemini-3.8-flash"), "text": "", "error": None}
    api_key = (cfg.get("gemini_api_key") or "").strip()
    if api_key:
        try:
            ai_block = _call_gemini(api_key, cfg.get("gemini_model", "gemini-3.8-flash"), compact_for_ai)
        except Exception as e:
            ai_block["error"] = str(e)[:180]
            ai_block["text"] = "No se pudo contactar con Gemini API; mostrando diagnóstico local completo."
    else:
        ai_block["text"] = (
            f"Diagnóstico local completado ({score}/100). "
            + (f"Se detectaron {len(findings)} puntos de atención. " if findings else "Sistema estable y sin incidencias críticas. ")
            + (f"Auto-reparación ejecutó {len(actions_taken)} acción(es). " if actions_taken else "")
            + "Puedes añadir tu API Key de Google AI Studio (Gemini) abajo para activar el análisis avanzado en lenguaje natural."
        )

    report = {
        "timestamp": now_str,
        "trigger": trigger,
        "health_score": score,
        "status": "ok" if score >= 85 else ("warning" if score >= 65 else "critical"),
        "checks": checks,
        "findings": findings,
        "actions_taken": actions_taken,
        "recommendations": recommendations,
        "ai": ai_block,
    }
    try:
        REPORT_FILE.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    except Exception:
        pass
    return report


def get_latest_report() -> dict:
    cfg = load_config()
    rep = _read_json(REPORT_FILE, None)
    if not rep:
        rep = run_diagnosis(trigger="initial")
    return {
        "report": rep,
        "config": {
            "auto_heal_enabled": bool(cfg.get("auto_heal_enabled", True)),
            "gemini_model": cfg.get("gemini_model", "gemini-3.8-flash"),
            "has_api_key": bool((cfg.get("gemini_api_key") or "").strip()),
            "nightly_time": cfg.get("nightly_time", "03:30"),
        },
    }


if __name__ == "__main__":
    import sys
    trig = sys.argv[1] if len(sys.argv) > 1 else "scheduled"
    r = run_diagnosis(trigger=trig)
    print(json.dumps({"timestamp": r["timestamp"], "score": r["health_score"], "findings": len(r["findings"]), "actions": r["actions_taken"]}, ensure_ascii=False))

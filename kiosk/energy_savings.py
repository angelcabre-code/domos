import json
import time
from datetime import datetime
from pathlib import Path

CONFIG_FILE = Path("/opt/domoskiosk/energy_savings_config.json")
STATE_FILE = Path("/opt/domoskiosk/energy_savings_state.json")
SOLAR_STATUS_FILE = Path("/tmp/domos_solar_status.json")
PRESENCE_STATUS_FILE = Path("/tmp/domos_presence_status.json")
ALARM_DEV_ID = "64326051e8db8480acc0"

DEFAULT_CONFIG = {
    "mode": "auto",        # "auto" | "paused" | "vacation"
    "source": "auto",      # "auto" | "solar_gen" | "net_surplus"
    "rules": [
        {
            "id": "bf75842d28c31e9943g0wz",
            "name": "Termo Eléctrico",
            "icon": "🔥",
            "code": "switch_1",
            "enabled": True,
            "priority": 1,
            "on_threshold_w": 600,
            "off_threshold_w": 300,
            "sustain_on_min": 3,
            "sustain_off_min": 5,
            "min_on_min": 15,
            "max_daily_min": 180,
            "time_start": "10:00",
            "time_end": "18:30",
            "presence_condition": "any",  # "any" | "away_only" | "home_only"
            "auto_cutoff_idle": True,
            "idle_watts": 35,
            "idle_cutoff_min": 10,
        },
        {
            "id": "1728645494b97e138251",
            "name": "Secatoallas",
            "icon": "♨️",
            "code": "switch_1",
            "enabled": False,
            "priority": 2,
            "on_threshold_w": 450,
            "off_threshold_w": 200,
            "sustain_on_min": 3,
            "sustain_off_min": 5,
            "min_on_min": 15,
            "max_daily_min": 120,
            "time_start": "10:30",
            "time_end": "18:00",
            "presence_condition": "any",
            "auto_cutoff_idle": False,
            "idle_watts": 25,
            "idle_cutoff_min": 10,
        },
    ],
}


def _today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def _hhmm_to_min(hhmm: str) -> int:
    try:
        h, m = str(hhmm).strip().split(":")
        return int(h) * 60 + int(m)
    except Exception:
        return 0


class EnergySavingsEngine:
    def __init__(self):
        self.config = self._load_config()
        self.state = self._load_state()
        self.last_eval_ts = 0.0
        self.runtime = {}  # ephemeral per-rule timers (above_since, below_since, idle_since, turned_on_ts, status_text)

    def _load_config(self) -> dict:
        if CONFIG_FILE.exists():
            try:
                data = json.loads(CONFIG_FILE.read_text())
                if isinstance(data, dict) and isinstance(data.get("rules"), list):
                    return data
            except Exception:
                pass
        self._save_config_raw(DEFAULT_CONFIG)
        return json.loads(json.dumps(DEFAULT_CONFIG))

    def _save_config_raw(self, cfg: dict):
        try:
            CONFIG_FILE.write_text(json.dumps(cfg, indent=2, ensure_ascii=False))
        except Exception as e:
            print(f"[ENERGY_SAVINGS] Config save error: {e}", flush=True)

    def _load_state(self) -> dict:
        today = _today_str()
        if STATE_FILE.exists():
            try:
                st = json.loads(STATE_FILE.read_text())
                if isinstance(st, dict) and st.get("date") == today:
                    return st
            except Exception:
                pass
        return {"date": today, "daily": {}, "history": []}

    def _save_state(self):
        try:
            STATE_FILE.write_text(json.dumps(self.state, indent=2, ensure_ascii=False))
        except Exception as e:
            print(f"[ENERGY_SAVINGS] State save error: {e}", flush=True)

    def _ensure_today(self):
        today = _today_str()
        if self.state.get("date") != today:
            prev_hist = (self.state.get("history") or [])[:15]
            self.state = {"date": today, "daily": {}, "history": prev_hist}
            self._save_state()

    def _log_event(self, device_name: str, action: str, detail: str, icon: str = "🌱"):
        entry = {
            "ts": datetime.now().strftime("%H:%M"),
            "date": _today_str(),
            "device": device_name,
            "action": action,
            "detail": detail,
            "icon": icon,
        }
        hist = self.state.setdefault("history", [])
        hist.insert(0, entry)
        self.state["history"] = hist[:30]
        self._save_state()
        print(f"[ENERGY_SAVINGS] {device_name} -> {action}: {detail}", flush=True)

    def update_config(self, new_cfg: dict) -> dict:
        mode = str(new_cfg.get("mode", self.config.get("mode", "auto")))
        if mode not in ("auto", "paused", "vacation"):
            mode = "auto"
        source = str(new_cfg.get("source", self.config.get("source", "auto")))
        if source not in ("auto", "solar_gen", "net_surplus"):
            source = "auto"

        rules_in = new_cfg.get("rules")
        if isinstance(rules_in, list) and len(rules_in) > 0:
            clean_rules = []
            for idx, r in enumerate(rules_in):
                clean_rules.append({
                    "id": str(r.get("id") or ""),
                    "name": str(r.get("name") or "Dispositivo"),
                    "icon": str(r.get("icon") or "⚡"),
                    "code": str(r.get("code") or "switch_1"),
                    "enabled": bool(r.get("enabled", False)),
                    "priority": max(1, min(10, int(r.get("priority", idx + 1)))),
                    "on_threshold_w": max(50, min(5000, int(r.get("on_threshold_w", 500)))),
                    "off_threshold_w": max(0, min(4900, int(r.get("off_threshold_w", 250)))),
                    "sustain_on_min": max(0, min(60, int(r.get("sustain_on_min", 3)))),
                    "sustain_off_min": max(0, min(60, int(r.get("sustain_off_min", 5)))),
                    "min_on_min": max(0, min(120, int(r.get("min_on_min", 15)))),
                    "max_daily_min": max(10, min(720, int(r.get("max_daily_min", 180)))),
                    "time_start": str(r.get("time_start") or "10:00"),
                    "time_end": str(r.get("time_end") or "18:30"),
                    "presence_condition": str(r.get("presence_condition") or "any")
                        if str(r.get("presence_condition") or "any") in ("any", "away_only", "home_only") else "any",
                    "auto_cutoff_idle": bool(r.get("auto_cutoff_idle", False)),
                    "idle_watts": max(5, min(200, int(r.get("idle_watts", 35)))),
                    "idle_cutoff_min": max(2, min(60, int(r.get("idle_cutoff_min", 10)))),
                })
            clean_rules.sort(key=lambda x: x["priority"])
        else:
            clean_rules = self.config.get("rules", DEFAULT_CONFIG["rules"])

        self.config = {"mode": mode, "source": source, "rules": clean_rules}
        self._save_config_raw(self.config)
        return self.config

    def set_mode(self, mode: str) -> dict:
        if mode in ("auto", "paused", "vacation"):
            self.config["mode"] = mode
            self._save_config_raw(self.config)
            lbl = {"auto": "Autoconsumo Activo", "paused": "Pausado (Manual)", "vacation": "Modo Vacaciones"}[mode]
            self._log_event("Sistema", f"Modo → {lbl}", "Cambio manual desde panel DOMOS", "⚙️")
        return self.config

    def _read_telemetry(self, tuya_svc) -> dict:
        solar_w = 0.0
        meter_online = False
        net_surplus_w = 0.0
        home_load_w = 0.0
        grid_w = 0.0
        if SOLAR_STATUS_FILE.exists():
            try:
                sd = json.loads(SOLAR_STATUS_FILE.read_text())
                solar_w = float(sd.get("watts") or 0.0)
                meter_online = bool(sd.get("meter_online", False))
                grid_w = float(sd.get("grid_watts") or 0.0)
                home_load_w = float(sd.get("home_consumption_w") or 0.0)
                net_surplus_w = float(sd.get("net_surplus_w") or 0.0)
                if meter_online and net_surplus_w == 0.0 and grid_w < 0:
                    net_surplus_w = abs(grid_w)
            except Exception:
                pass

        # Fallback solar watts from tuya_svc if file unavailable
        if solar_w == 0.0 and tuya_svc is not None:
            st_sol = tuya_svc.states.get("bfe037c461c9c61da3pesr") or {}
            solar_w = float(st_sol.get("watts") or 0.0)

        # Auto-detect Tuya Dual-Clamp CT Meter (e.g. PJ-1203A / PC321-TY) if Hoymiles meter is offline
        meter_source_name = "Hoymiles DTU" if meter_online else None
        if not meter_online and tuya_svc is not None:
            for cid, cst in (tuya_svc.states or {}).items():
                if not isinstance(cst, dict):
                    continue
                if any(k in cst for k in ("power_a", "cur_power_a", "phase_a_power", "clamp_a_w")):
                    pa = float(cst.get("power_a") or cst.get("cur_power_a") or cst.get("phase_a_power") or cst.get("clamp_a_w") or 0.0)
                    pb = float(cst.get("power_b") or cst.get("cur_power_b") or cst.get("phase_b_power") or cst.get("clamp_b_w") or 0.0)
                    # Tuya PJ-1203A often reports in 0.1 W if raw, normalize if > 20000
                    if abs(pa) > 20000:
                        pa /= 10.0
                    if abs(pb) > 20000:
                        pb /= 10.0
                    dir_a = str(cst.get("direction_a") or "").lower()
                    dir_b = str(cst.get("direction_b") or "").lower()
                    if dir_a == "reverse":
                        pa = -abs(pa)
                    if dir_b == "reverse":
                        pb = -abs(pb)
                    # Assume Clamp A = Grid (negative = exporting surplus), Clamp B = Solar (or Hoymiles solar_w)
                    grid_w = round(pa, 1)
                    if solar_w == 0.0 and abs(pb) > 0:
                        solar_w = round(abs(pb), 1)
                    net_surplus_w = round(max(0.0, -grid_w), 1)
                    home_load_w = round(max(0.0, solar_w + grid_w), 1)
                    meter_online = True
                    meter_source_name = "Doble Pinza Tuya"
                    break

        alarm_st = (tuya_svc.states.get(ALARM_DEV_ID) or {}) if tuya_svc else {}
        alarm_mode = str(alarm_st.get("master_mode") or "disarmed").lower()
        is_away = alarm_mode in ("armed", "arm", "away")

        src_pref = self.config.get("source", "auto")
        if src_pref == "net_surplus" or (src_pref == "auto" and meter_online):
            effective_source = "net_surplus"
            base_avail_w = net_surplus_w if meter_online else solar_w
        else:
            effective_source = "solar_gen"
            base_avail_w = solar_w

        return {
            "solar_w": round(solar_w, 1),
            "meter_online": meter_online,
            "meter_source": meter_source_name or "En espera",
            "grid_w": round(grid_w, 1),
            "home_load_w": round(home_load_w, 1),
            "net_surplus_w": round(net_surplus_w, 1),
            "effective_source": effective_source,
            "base_avail_w": round(base_avail_w, 1),
            "alarm_mode": alarm_mode,
            "is_away": is_away,
        }

    def get_hot_water_advisor(self, tel: dict) -> dict:
        month = datetime.now().month
        solar_w = float(tel.get("solar_w") or 0.0)
        # Estimate today's solar energy from Hoymiles status if available
        solar_kwh_today = 0.0
        if SOLAR_STATUS_FILE.exists():
            try:
                sd = json.loads(SOLAR_STATUS_FILE.read_text())
                for k in ("port1", "port2", "port3", "port4"):
                    solar_kwh_today += float((sd.get(k) or {}).get("wh") or 0.0) / 1000.0
            except Exception:
                pass
        solar_kwh_today = round(solar_kwh_today, 2)
        is_summer_season = month in (5, 6, 7, 8, 9)
        if is_summer_season and (solar_kwh_today >= 2.8 or solar_w >= 650):
            rec_mode = "direct_solar"
            rec_label = "Modo A · Directo Termosifón (0 W eléctrico)"
            reason = f"Alta radiación ({solar_kwh_today} kWh hoy / {int(solar_w)} W). El termosifón basta por sí solo."
            badge_color = "#10b981"
        else:
            rec_mode = "series_backup"
            rec_label = "Modo B · Serie (Termosifón → Termo Eléctrico)"
            reason = f"Temporada fría o radiación moderada ({solar_kwh_today} kWh hoy). Precalentar con termosifón + apoyo termo solar garantiza ducha caliente."
            badge_color = "#f59e0b"
        return {
            "recommended_mode": rec_mode,
            "recommended_label": rec_label,
            "reason": reason,
            "badge_color": badge_color,
            "solar_kwh_today": solar_kwh_today,
            "valves_configured": False,
            "valve_direct_id": None,
            "valve_series_id": None,
            "safe_switch_overlap_sec": 5,
        }

    def evaluate(self, tuya_svc, execute_commands: bool = True) -> dict:
        self._ensure_today()
        now = time.time()
        dt_sec = min(120.0, max(0.0, now - self.last_eval_ts)) if self.last_eval_ts > 0 else 0.0
        self.last_eval_ts = now

        tel = self._read_telemetry(tuya_svc)
        mode = self.config.get("mode", "auto")
        now_dt = datetime.now()
        now_min = now_dt.hour * 60 + now_dt.minute

        rules_sorted = sorted(self.config.get("rules", []), key=lambda x: x.get("priority", 99))
        remaining_w = tel["base_avail_w"]
        rule_statuses = []

        for r in rules_sorted:
            dev_id = r["id"]
            dev_st = (tuya_svc.states.get(dev_id) or {}) if tuya_svc else {}
            is_on = bool(dev_st.get("state", False))
            dev_power_w = float(dev_st.get("power") or dev_st.get("watts") or 0.0)

            rt = self.runtime.setdefault(dev_id, {
                "above_since": None,
                "below_since": None,
                "idle_since": None,
                "turned_on_ts": None,
                "auto_active": False,
                "done_by_idle_today": False,
                "done_date": _today_str(),
            })
            if rt.get("done_date") != _today_str():
                rt["done_by_idle_today"] = False
                rt["done_date"] = _today_str()

            daily = self.state.setdefault("daily", {}).setdefault(dev_id, {
                "on_seconds": 0.0,
                "saved_wh": 0.0,
            })

            # Accumulate daily runtime whenever device is ON (manual OR auto) to prevent double cycles
            if is_on and dt_sec > 0:
                daily["on_seconds"] = round(daily.get("on_seconds", 0.0) + dt_sec, 1)
                if tel["solar_w"] > 0:
                    solar_share_w = min(dev_power_w, max(0.0, tel["solar_w"]))
                    daily["saved_wh"] = round(daily.get("saved_wh", 0.0) + (solar_share_w * dt_sec / 3600.0), 2)

            today_min = round(daily.get("on_seconds", 0.0) / 60.0, 1)
            today_kwh = round(daily.get("saved_wh", 0.0) / 1000.0, 3)

            # Effective watts available for THIS rule (add back own draw if using net_surplus while already ON)
            eval_w = remaining_w + (dev_power_w if (is_on and tel["effective_source"] == "net_surplus" and tel["meter_online"]) else 0.0)

            status_code = "waiting"
            status_label = f"En espera ({int(eval_w)}/{r['on_threshold_w']} W)"

            if mode == "vacation":
                status_code = "vacation"
                status_label = "Modo Vacaciones (apagado)"
                rt["above_since"] = None
                rt["below_since"] = None
                if is_on and r.get("enabled") and execute_commands and tuya_svc is not None:
                    tuya_svc.send_command(dev_id, r.get("code", "switch_1"), False)
                    rt["auto_active"] = False
                    self._log_event(r["name"], "Apagado (Vacaciones)", "Apagado automático por Modo Vacaciones", "✈️")
            elif mode == "paused":
                status_code = "paused"
                status_label = "Pausado (control manual)"
                rt["above_since"] = None
                rt["below_since"] = None
            elif not r.get("enabled"):
                status_code = "disabled"
                status_label = "Regla desactivada"
                rt["above_since"] = None
                rt["below_since"] = None
            else:
                start_m = _hhmm_to_min(r.get("time_start", "10:00"))
                end_m = _hhmm_to_min(r.get("time_end", "18:30"))
                in_window = (start_m <= now_min <= end_m) if start_m <= end_m else (now_min >= start_m or now_min <= end_m)
                pres_cond = r.get("presence_condition", "any")
                pres_ok = (
                    pres_cond == "any"
                    or (pres_cond == "away_only" and tel["is_away"])
                    or (pres_cond == "home_only" and not tel["is_away"])
                )
                under_daily_cap = today_min < float(r.get("max_daily_min", 180))

                if not in_window:
                    status_code = "blocked_schedule"
                    status_label = f"Fuera de horario ({r['time_start']}–{r['time_end']})"
                    rt["above_since"] = None
                    if is_on and rt.get("auto_active") and execute_commands and tuya_svc is not None:
                        tuya_svc.send_command(dev_id, r.get("code", "switch_1"), False)
                        rt["auto_active"] = False
                        self._log_event(r["name"], "Apagado (Fin horario)", f"Fin de franja {r['time_end']}", "🕒")
                elif not pres_ok:
                    status_code = "blocked_presence"
                    status_label = "Esperando casa vacía (Alarma)" if pres_cond == "away_only" else "Solo con gente en casa"
                    rt["above_since"] = None
                    if is_on and rt.get("auto_active") and execute_commands and tuya_svc is not None:
                        tuya_svc.send_command(dev_id, r.get("code", "switch_1"), False)
                        rt["auto_active"] = False
                        self._log_event(r["name"], "Apagado (Presencia)", status_label, "🏠")
                elif not under_daily_cap:
                    status_code = "done_today"
                    status_label = f"Límite diario cumplido ({int(today_min)} min)"
                    rt["above_since"] = None
                    if is_on and rt.get("auto_active") and execute_commands and tuya_svc is not None:
                        tuya_svc.send_command(dev_id, r.get("code", "switch_1"), False)
                        rt["auto_active"] = False
                        self._log_event(r["name"], "Apagado (Límite diario)", f"Alcanzados {int(today_min)} min hoy", "✅")
                elif rt.get("done_by_idle_today"):
                    status_code = "done_today"
                    status_label = f"Temperatura alcanzada hoy ({int(today_min)} min)"
                else:
                    # Eligible to turn ON or stay ON
                    if not is_on:
                        rt["below_since"] = None
                        rt["idle_since"] = None
                        if eval_w >= float(r["on_threshold_w"]):
                            if rt["above_since"] is None:
                                rt["above_since"] = now
                            elapsed_min = (now - rt["above_since"]) / 60.0
                            need_min = float(r.get("sustain_on_min", 3))
                            if elapsed_min >= need_min:
                                if execute_commands and tuya_svc is not None:
                                    tuya_svc.send_command(dev_id, r.get("code", "switch_1"), True)
                                    rt["auto_active"] = True
                                    rt["turned_on_ts"] = now
                                    rt["above_since"] = None
                                    self._log_event(
                                        r["name"],
                                        "Encendido solar",
                                        f"{int(eval_w)} W ≥ {r['on_threshold_w']} W durante {int(need_min)} min",
                                        "☀️",
                                    )
                                status_code = "active_auto"
                                status_label = f"Activo por excedente ({int(eval_w)} W)"
                            else:
                                rem_s = max(1, int((need_min - elapsed_min) * 60))
                                status_code = "arming"
                                status_label = f"Excedente OK ({int(eval_w)} W) · Activa en {rem_s}s"
                        else:
                            rt["above_since"] = None
                            status_code = "waiting"
                            status_label = f"Esperando excedente ({int(eval_w)} / {r['on_threshold_w']} W)"
                    else:
                        # Device is currently ON
                        rt["above_since"] = None
                        status_code = "active_auto" if rt.get("auto_active") else "active_manual"
                        status_label = f"Activo · {int(dev_power_w)} W ({int(today_min)} min hoy)"

                        # Check auto-cutoff when thermostat reaches target temp (< idle_watts for idle_cutoff_min)
                        if rt.get("auto_active") and r.get("auto_cutoff_idle"):
                            if dev_power_w <= float(r.get("idle_watts", 35)):
                                if rt["idle_since"] is None:
                                    rt["idle_since"] = now
                                idle_elapsed = (now - rt["idle_since"]) / 60.0
                                if idle_elapsed >= float(r.get("idle_cutoff_min", 10)):
                                    if execute_commands and tuya_svc is not None:
                                        tuya_svc.send_command(dev_id, r.get("code", "switch_1"), False)
                                        rt["auto_active"] = False
                                        rt["done_by_idle_today"] = True
                                        rt["idle_since"] = None
                                        self._log_event(
                                            r["name"],
                                            "Fin de calentamiento",
                                            f"Consumo < {r.get('idle_watts', 35)} W durante {r.get('idle_cutoff_min', 10)} min → excedente liberado",
                                            "🌡️",
                                        )
                                    status_code = "done_today"
                                    status_label = "Temperatura alcanzada · Excedente libre"
                            else:
                                rt["idle_since"] = None

                        # Check low surplus shutdown with cloud hysteresis & min_on_min
                        if rt.get("auto_active"):
                            on_elapsed_min = ((now - rt["turned_on_ts"]) / 60.0) if rt.get("turned_on_ts") else 999.0
                            if eval_w < float(r["off_threshold_w"]):
                                if rt["below_since"] is None:
                                    rt["below_since"] = now
                                below_elapsed = (now - rt["below_since"]) / 60.0
                                if on_elapsed_min >= float(r.get("min_on_min", 15)) and below_elapsed >= float(r.get("sustain_off_min", 5)):
                                    if execute_commands and tuya_svc is not None:
                                        tuya_svc.send_command(dev_id, r.get("code", "switch_1"), False)
                                        rt["auto_active"] = False
                                        rt["below_since"] = None
                                        self._log_event(
                                            r["name"],
                                            "Apagado (Baja generación)",
                                            f"{int(eval_w)} W < {r['off_threshold_w']} W durante {r['sustain_off_min']} min",
                                            "☁️",
                                        )
                                    status_code = "waiting"
                                    status_label = f"En espera ({int(eval_w)}/{r['on_threshold_w']} W)"
                            else:
                                rt["below_since"] = None

            # Cascade: reserve power consumed by this active rule before evaluating lower priorities
            if is_on and tel["effective_source"] == "solar_gen":
                remaining_w = max(0.0, remaining_w - dev_power_w)

            rule_statuses.append({
                "id": dev_id,
                "name": r["name"],
                "icon": r["icon"],
                "priority": r["priority"],
                "enabled": r["enabled"],
                "is_on": is_on,
                "power_w": round(dev_power_w, 1),
                "auto_active": bool(rt.get("auto_active")),
                "status_code": status_code,
                "status_label": status_label,
                "today_min": today_min,
                "today_kwh": today_kwh,
            })

        self._save_state()
        total_kwh = round(sum(x["today_kwh"] for x in rule_statuses), 3)
        total_min = round(sum(x["today_min"] for x in rule_statuses), 1)
        return {
            "hot_water": self.get_hot_water_advisor(tel),
            "config": self.config,
            "telemetry": tel,
            "rules_status": rule_statuses,
            "summary": {
                "total_saved_kwh_today": total_kwh,
                "total_auto_min_today": total_min,
                "active_rules_count": sum(1 for x in rule_statuses if x["enabled"]),
                "running_auto_count": sum(1 for x in rule_statuses if x["auto_active"]),
            },
            "history": self.state.get("history", [])[:15],
        }


engine = EnergySavingsEngine()
